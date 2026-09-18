from dataclasses import dataclass

import pulp

from app.schemas import (
    BatteryAction,
    DirectiveInterpretation,
    DirectiveType,
    HourlyPlanItem,
    OptimizeEnergyRequest,
)


class OptimizationError(Exception):
    """Controlled error raised when optimization cannot produce a valid plan."""


@dataclass
class OptimizationResult:
    hourly_plan: list[HourlyPlanItem]
    total_grid_kwh: float
    total_cost_bdt: float
    peak_grid_kwh: float


def _prepare_hourly_constraints(
    request: OptimizeEnergyRequest,
    directives: list[DirectiveInterpretation],
) -> tuple[
    list[float],
    list[float],
    set[int],
    set[int],
    dict[int, float],
]:
    """
    Convert validated directives into deterministic hourly constraints.

    Returns:
        effective_solar
        minimum_reserve
        no_charge_hours
        no_discharge_hours
        max_grid_by_hour
    """

    effective_solar = [
        hour_data.solar_kwh
        for hour_data in request.hours
    ]

    minimum_reserve = [
        request.battery.minimum_energy_kwh
        for _ in range(24)
    ]

    no_charge_hours: set[int] = set()
    no_discharge_hours: set[int] = set()
    max_grid_by_hour: dict[int, float] = {}

    for directive in directives:
        if not directive.applies:
            continue

        adjustment = directive.structured_adjustment

        if adjustment is None:
            continue

        hours = adjustment.hours

        if directive.directive_type == DirectiveType.SOLAR_REDUCTION:
            factor = adjustment.factor

            for hour in hours:
                effective_solar[hour] *= factor

        elif (
            directive.directive_type
            == DirectiveType.MINIMUM_BATTERY_RESERVE
        ):
            required_reserve = adjustment.minimum_energy_kwh

            for hour in hours:
                minimum_reserve[hour] = max(
                    minimum_reserve[hour],
                    required_reserve,
                )

        elif directive.directive_type == DirectiveType.NO_CHARGE_WINDOW:
            no_charge_hours.update(hours)

        elif directive.directive_type == DirectiveType.NO_DISCHARGE_WINDOW:
            no_discharge_hours.update(hours)

        elif directive.directive_type == DirectiveType.MAX_GRID_WINDOW:
            grid_limit = adjustment.max_grid_kwh

            for hour in hours:
                if hour in max_grid_by_hour:
                    max_grid_by_hour[hour] = min(
                        max_grid_by_hour[hour],
                        grid_limit,
                    )
                else:
                    max_grid_by_hour[hour] = grid_limit

    return (
        effective_solar,
        minimum_reserve,
        no_charge_hours,
        no_discharge_hours,
        max_grid_by_hour,
    )


def optimize_energy_schedule(
    request: OptimizeEnergyRequest,
    directives: list[DirectiveInterpretation],
) -> OptimizationResult:
    """
    Create a minimum-cost 24-hour energy schedule.

    The model includes:
    - Grid import
    - Solar consumption
    - Battery charging
    - Battery discharging
    - Battery state of energy
    - Charge/discharge mode control
    - End-of-day battery neutrality
    - All validated operator directives
    """

    if len(directives) != len(request.operator_notes):
        raise OptimizationError(
            "Directive count does not match operator note count"
        )

    (
        effective_solar,
        minimum_reserve,
        no_charge_hours,
        no_discharge_hours,
        max_grid_by_hour,
    ) = _prepare_hourly_constraints(request, directives)

    battery = request.battery
    hours = range(24)

    model = pulp.LpProblem(
        name="gridwise_energy_optimization",
        sense=pulp.LpMinimize,
    )

    # Continuous energy variables
    grid = pulp.LpVariable.dicts(
        "grid_kwh",
        hours,
        lowBound=0,
        cat=pulp.LpContinuous,
    )

    solar_used = pulp.LpVariable.dicts(
        "solar_used_kwh",
        hours,
        lowBound=0,
        cat=pulp.LpContinuous,
    )

    charge = pulp.LpVariable.dicts(
        "battery_charge_kwh",
        hours,
        lowBound=0,
        cat=pulp.LpContinuous,
    )

    discharge = pulp.LpVariable.dicts(
        "battery_discharge_kwh",
        hours,
        lowBound=0,
        cat=pulp.LpContinuous,
    )

    battery_energy = pulp.LpVariable.dicts(
        "battery_energy_after_kwh",
        hours,
        lowBound=0,
        cat=pulp.LpContinuous,
    )

    # Binary variables prevent simultaneous charge and discharge.
    charge_mode = pulp.LpVariable.dicts(
        "charge_mode",
        hours,
        cat=pulp.LpBinary,
    )

    discharge_mode = pulp.LpVariable.dicts(
        "discharge_mode",
        hours,
        cat=pulp.LpBinary,
    )

    # Primary objective: minimize grid electricity cost.
    model += pulp.lpSum(
        grid[hour]
        * request.hours[hour].tariff_bdt_per_kwh
        for hour in hours
    )

    for hour in hours:
        hour_data = request.hours[hour]

        # Solar usage cannot exceed effective solar availability.
        model += (
            solar_used[hour] <= effective_solar[hour],
            f"solar_availability_hour_{hour}",
        )

        # Charge/discharge hourly rate limits.
        model += (
            charge[hour]
            <= battery.max_charge_kwh_per_hour * charge_mode[hour],
            f"charge_rate_hour_{hour}",
        )

        model += (
            discharge[hour]
            <= battery.max_discharge_kwh_per_hour
            * discharge_mode[hour],
            f"discharge_rate_hour_{hour}",
        )

        # Battery cannot charge and discharge simultaneously.
        model += (
            charge_mode[hour] + discharge_mode[hour] <= 1,
            f"battery_mode_hour_{hour}",
        )

        # Hourly energy balance:
        # grid + solar + battery discharge
        # = demand + battery charge
        model += (
            grid[hour]
            + solar_used[hour]
            + discharge[hour]
            == hour_data.demand_kwh + charge[hour],
            f"energy_balance_hour_{hour}",
        )

        # Battery state transition.
        if hour == 0:
            previous_energy = battery.initial_energy_kwh
        else:
            previous_energy = battery_energy[hour - 1]

        model += (
            battery_energy[hour]
            == previous_energy + charge[hour] - discharge[hour],
            f"battery_transition_hour_{hour}",
        )

        # Battery capacity.
        model += (
            battery_energy[hour] <= battery.capacity_kwh,
            f"battery_capacity_hour_{hour}",
        )

        # Base minimum and directive reserve.
        model += (
            battery_energy[hour] >= minimum_reserve[hour],
            f"battery_reserve_hour_{hour}",
        )

        # Directive: no charge window.
        if hour in no_charge_hours:
            model += (
                charge[hour] == 0,
                f"no_charge_hour_{hour}",
            )

        # Directive: no discharge window.
        if hour in no_discharge_hours:
            model += (
                discharge[hour] == 0,
                f"no_discharge_hour_{hour}",
            )

        # Directive: maximum grid window.
        if hour in max_grid_by_hour:
            model += (
                grid[hour] <= max_grid_by_hour[hour],
                f"maximum_grid_hour_{hour}",
            )

    # Final battery energy must return to the initial level.
    model += (
        battery_energy[23] == battery.initial_energy_kwh,
        "end_of_day_battery_neutrality",
    )

    solver = pulp.PULP_CBC_CMD(
        msg=False,
        timeLimit=20,
    )

    try:
        status_code = model.solve(solver)
    except pulp.PulpSolverError as error:
        raise OptimizationError(
            "The optimization solver could not be executed"
        ) from error

    status_name = pulp.LpStatus[status_code]

    if status_name != "Optimal":
        raise OptimizationError(
            f"No optimal schedule could be produced. Solver status: "
            f"{status_name}"
        )

    tolerance = 1e-6
    hourly_plan: list[HourlyPlanItem] = []

    for hour in hours:
        grid_value = max(0.0, float(pulp.value(grid[hour]) or 0.0))
        solar_value = max(
            0.0,
            float(pulp.value(solar_used[hour]) or 0.0),
        )
        charge_value = max(
            0.0,
            float(pulp.value(charge[hour]) or 0.0),
        )
        discharge_value = max(
            0.0,
            float(pulp.value(discharge[hour]) or 0.0),
        )
        energy_value = max(
            0.0,
            float(pulp.value(battery_energy[hour]) or 0.0),
        )

        if charge_value > tolerance:
            action = BatteryAction.CHARGE
            battery_kwh = charge_value
        elif discharge_value > tolerance:
            action = BatteryAction.DISCHARGE
            battery_kwh = discharge_value
        else:
            action = BatteryAction.IDLE
            battery_kwh = 0.0

        hourly_plan.append(
            HourlyPlanItem(
                hour=hour,
                grid_kwh=round(grid_value, 6),
                solar_used_kwh=round(solar_value, 6),
                battery_action=action,
                battery_kwh=round(battery_kwh, 6),
                battery_energy_after_kwh=round(energy_value, 6),
            )
        )

    total_grid_kwh = sum(
        item.grid_kwh
        for item in hourly_plan
    )

    total_cost_bdt = sum(
        hourly_plan[hour].grid_kwh
        * request.hours[hour].tariff_bdt_per_kwh
        for hour in hours
    )

    peak_grid_kwh = max(
        item.grid_kwh
        for item in hourly_plan
    )

    return OptimizationResult(
        hourly_plan=hourly_plan,
        total_grid_kwh=round(total_grid_kwh, 6),
        total_cost_bdt=round(total_cost_bdt, 6),
        peak_grid_kwh=round(peak_grid_kwh, 6),
    )