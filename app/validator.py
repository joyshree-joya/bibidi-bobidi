from dataclasses import dataclass
from math import isfinite

from app.schemas import (
    BatteryAction,
    DirectiveInterpretation,
    DirectiveType,
    OptimizeEnergyRequest,
)
from app.optimizer import OptimizationResult


TOLERANCE = 1e-5


class ScheduleValidationError(Exception):
    """Raised when an optimization schedule fails replay validation."""


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]
    total_grid_kwh: float = 0.0
    total_cost_bdt: float = 0.0
    peak_grid_kwh: float = 0.0


def _fail(errors: list[str]) -> None:
    if errors:
        raise ScheduleValidationError("; ".join(errors))


def validate_schedule(
    request_data,
    directives: list[DirectiveInterpretation],
    hourly_plan,
    tolerance: float = TOLERANCE,
) -> dict:
    """
    Independently replay and validate a 24-hour optimization schedule.

    hourly_plan may be either:
      - list[HourlyPlanItem]
      - OptimizationResult
    """

    # Support OptimizationResult so reported totals can also be checked.
    reported_totals = None

    if isinstance(hourly_plan, OptimizationResult):
        reported_totals = {
            "total_grid_kwh": hourly_plan.total_grid_kwh,
            "total_cost_bdt": hourly_plan.total_cost_bdt,
            "peak_grid_kwh": hourly_plan.peak_grid_kwh,
        }
        hourly_plan = hourly_plan.hourly_plan

    if isinstance(request_data, dict):
        request = OptimizeEnergyRequest.model_validate(request_data)
    else:
        request = request_data

    errors: list[str] = []

    # ---------------------------------------------------------
    # 1-3. Basic 24-hour structure
    # ---------------------------------------------------------
    if len(hourly_plan) != 24:
        errors.append(
            f"Expected exactly 24 hourly entries, got {len(hourly_plan)}"
        )
        _fail(errors)

    hours = [item.hour for item in hourly_plan]

    if sorted(hours) != list(range(24)):
        errors.append("Hourly plan must contain each hour exactly once (0..23)")

    if len(set(hours)) != 24:
        errors.append("Duplicate or missing hours detected")

    _fail(errors)

    # Replay by hour, independent of supplied ordering.
    plan_by_hour = {item.hour: item for item in hourly_plan}

    battery = request.battery

    # ---------------------------------------------------------
    # Rebuild directive constraints independently
    # ---------------------------------------------------------
    effective_solar = {
        h.hour: h.solar_kwh
        for h in request.hours
    }

    minimum_reserve = {
        h.hour: battery.minimum_energy_kwh
        for h in request.hours
    }

    no_charge_hours = set()
    no_discharge_hours = set()
    max_grid_by_hour = {}

    for directive in directives:
        if not directive.applies:
            continue

        adjustment = directive.structured_adjustment

        if directive.directive_type == DirectiveType.NO_OP:
            continue

        if adjustment is None:
            errors.append(
                f"Missing adjustment for directive {directive.directive_type}"
            )
            continue

        if directive.directive_type == DirectiveType.SOLAR_REDUCTION:
            for hour in adjustment.hours:
                if hour in effective_solar:
                    effective_solar[hour] *= adjustment.factor

        elif directive.directive_type == DirectiveType.MINIMUM_BATTERY_RESERVE:
            for hour in adjustment.hours:
                if hour in minimum_reserve:
                    minimum_reserve[hour] = max(
                        minimum_reserve[hour],
                        adjustment.minimum_energy_kwh,
                    )

        elif directive.directive_type == DirectiveType.NO_CHARGE_WINDOW:
            no_charge_hours.update(adjustment.hours)

        elif directive.directive_type == DirectiveType.NO_DISCHARGE_WINDOW:
            no_discharge_hours.update(adjustment.hours)

        elif directive.directive_type == DirectiveType.MAX_GRID_WINDOW:
            for hour in adjustment.hours:
                old = max_grid_by_hour.get(hour)
                if old is None:
                    max_grid_by_hour[hour] = adjustment.max_grid_kwh
                else:
                    max_grid_by_hour[hour] = min(
                        old,
                        adjustment.max_grid_kwh,
                    )

    _fail(errors)

    # ---------------------------------------------------------
    # Replay every hour
    # ---------------------------------------------------------
    previous_energy = battery.initial_energy_kwh

    total_grid = 0.0
    total_cost = 0.0
    peak_grid = 0.0

    for hour in range(24):
        item = plan_by_hour[hour]
        request_hour = request.hours[hour]

        values = {
            "grid_kwh": item.grid_kwh,
            "solar_used_kwh": item.solar_used_kwh,
            "battery_kwh": item.battery_kwh,
            "battery_energy_after_kwh": item.battery_energy_after_kwh,
        }

        for name, value in values.items():
            if not isfinite(value):
                errors.append(f"Hour {hour}: {name} is not finite")

        grid = item.grid_kwh
        solar = item.solar_used_kwh
        battery_kwh = item.battery_kwh
        after = item.battery_energy_after_kwh

        # 4-7. Non-negative values
        if grid < -tolerance:
            errors.append(f"Hour {hour}: grid_kwh is negative")

        if solar < -tolerance:
            errors.append(f"Hour {hour}: solar_used_kwh is negative")

        if battery_kwh < -tolerance:
            errors.append(f"Hour {hour}: battery_kwh is negative")

        if after < -tolerance:
            errors.append(
                f"Hour {hour}: battery_energy_after_kwh is negative"
            )

        # 6. Effective solar availability
        if solar > effective_solar[hour] + tolerance:
            errors.append(
                f"Hour {hour}: solar_used_kwh exceeds effective solar"
            )

        # 8-9. Battery action
        if not isinstance(item.battery_action, BatteryAction):
            errors.append(f"Hour {hour}: invalid battery action")

        if item.battery_action == BatteryAction.IDLE:
            if abs(battery_kwh) > tolerance:
                errors.append(
                    f"Hour {hour}: idle action must have zero battery_kwh"
                )

        # 10-11. Charge/discharge limits
        if item.battery_action == BatteryAction.CHARGE:
            if battery_kwh > battery.max_charge_kwh_per_hour + tolerance:
                errors.append(f"Hour {hour}: charge limit exceeded")

        if item.battery_action == BatteryAction.DISCHARGE:
            if battery_kwh > battery.max_discharge_kwh_per_hour + tolerance:
                errors.append(f"Hour {hour}: discharge limit exceeded")

        # 12. Battery transition
        expected_after = previous_energy

        if item.battery_action == BatteryAction.CHARGE:
            expected_after += battery_kwh
        elif item.battery_action == BatteryAction.DISCHARGE:
            expected_after -= battery_kwh

        if abs(after - expected_after) > tolerance:
            errors.append(
                f"Hour {hour}: incorrect battery transition "
                f"(expected {expected_after}, got {after})"
            )

        # 13-14. Battery capacity/reserve
        if after > battery.capacity_kwh + tolerance:
            errors.append(f"Hour {hour}: battery capacity exceeded")

        if after < minimum_reserve[hour] - tolerance:
            errors.append(f"Hour {hour}: minimum battery reserve violated")

        # Directive: no charge
        if (
            hour in no_charge_hours
            and item.battery_action == BatteryAction.CHARGE
            and battery_kwh > tolerance
        ):
            errors.append(f"Hour {hour}: charging forbidden")

        # Directive: no discharge
        if (
            hour in no_discharge_hours
            and item.battery_action == BatteryAction.DISCHARGE
            and battery_kwh > tolerance
        ):
            errors.append(f"Hour {hour}: discharging forbidden")

        # Directive: max grid
        if (
            hour in max_grid_by_hour
            and grid > max_grid_by_hour[hour] + tolerance
        ):
            errors.append(f"Hour {hour}: maximum grid limit exceeded")

        # 15. Energy balance
        demand = request_hour.demand_kwh

        if item.battery_action == BatteryAction.CHARGE:
            charge = battery_kwh
            discharge = 0.0
        elif item.battery_action == BatteryAction.DISCHARGE:
            charge = 0.0
            discharge = battery_kwh
        else:
            charge = 0.0
            discharge = 0.0

        lhs = grid + solar + discharge
        rhs = demand + charge

        if abs(lhs - rhs) > tolerance:
            errors.append(
                f"Hour {hour}: energy balance violated "
                f"(lhs={lhs}, rhs={rhs})"
            )

        # Recalculated totals
        total_grid += grid
        total_cost += grid * request_hour.tariff_bdt_per_kwh
        peak_grid = max(peak_grid, grid)

        previous_energy = after

    # 16. End-of-day neutrality
    if (
        abs(previous_energy - battery.initial_energy_kwh)
        > tolerance
    ):
        errors.append(
            "Final battery energy does not equal initial battery energy"
        )

    # 23-25. Recalculated totals
    total_grid = round(total_grid, 6)
    total_cost = round(total_cost, 6)
    peak_grid = round(peak_grid, 6)

    # 26. Compare against reported optimizer totals when available
    if reported_totals is not None:
        if (
            abs(total_grid - reported_totals["total_grid_kwh"])
            > tolerance
        ):
            errors.append("Reported total_grid_kwh does not match replay")

        if (
            abs(total_cost - reported_totals["total_cost_bdt"])
            > tolerance
        ):
            errors.append("Reported total_cost_bdt does not match replay")

        if (
            abs(peak_grid - reported_totals["peak_grid_kwh"])
            > tolerance
        ):
            errors.append("Reported peak_grid_kwh does not match replay")

    # 27. Raise on any violation
    _fail(errors)

    return {
        "valid": True,
        "total_grid_kwh": total_grid,
        "total_cost_bdt": total_cost,
        "peak_grid_kwh": peak_grid,
    }


def validate_optimization_result(
    request: OptimizeEnergyRequest,
    result: OptimizationResult,
) -> ValidationResult:
    """Compatibility wrapper for the optimizer result."""

    try:
        replay = validate_schedule(
            request,
            [],
            result,
        )

        return ValidationResult(
            valid=True,
            errors=[],
            total_grid_kwh=replay["total_grid_kwh"],
            total_cost_bdt=replay["total_cost_bdt"],
            peak_grid_kwh=replay["peak_grid_kwh"],
        )

    except ScheduleValidationError as error:
        return ValidationResult(
            valid=False,
            errors=[str(error)],
        )