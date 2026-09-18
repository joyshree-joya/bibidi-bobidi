import pytest

from app.optimizer import OptimizationError, optimize_energy_schedule
from app.schemas import (
    DirectiveInterpretation,
    OptimizeEnergyRequest,
)


def create_request() -> OptimizeEnergyRequest:
    tariffs = [10.0] * 24
    tariffs[0] = 1.0
    tariffs[23] = 20.0

    return OptimizeEnergyRequest(
        scenario_id="OPTIMIZER-TEST-001",
        operator_notes=[
            "The cafeteria menu changes tomorrow."
        ],
        hours=[
            {
                "hour": hour,
                "demand_kwh": 100,
                "solar_kwh": 30 if 10 <= hour <= 14 else 0,
                "tariff_bdt_per_kwh": tariffs[hour],
            }
            for hour in range(24)
        ],
        battery={
            "capacity_kwh": 100,
            "initial_energy_kwh": 50,
            "minimum_energy_kwh": 0,
            "max_charge_kwh_per_hour": 50,
            "max_discharge_kwh_per_hour": 50,
        },
    )


def create_no_op_directive() -> DirectiveInterpretation:
    return DirectiveInterpretation(
        note_index=0,
        applies=False,
        directive_type="no_op",
        structured_adjustment=None,
        explanation="The note does not affect energy scheduling.",
    )


def test_optimizer_returns_24_hour_plan():
    request = create_request()

    result = optimize_energy_schedule(
        request=request,
        directives=[create_no_op_directive()],
    )

    assert len(result.hourly_plan) == 24
    assert [item.hour for item in result.hourly_plan] == list(range(24))


def test_optimizer_returns_battery_to_initial_energy():
    request = create_request()

    result = optimize_energy_schedule(
        request=request,
        directives=[create_no_op_directive()],
    )

    final_energy = result.hourly_plan[23].battery_energy_after_kwh

    assert final_energy == pytest.approx(
        request.battery.initial_energy_kwh,
        abs=1e-5,
    )


def test_optimizer_charges_when_tariff_is_low():
    request = create_request()

    result = optimize_energy_schedule(
        request=request,
        directives=[create_no_op_directive()],
    )

    first_hour = result.hourly_plan[0]

    assert first_hour.battery_action == "charge"
    assert first_hour.battery_kwh > 0


def test_optimizer_discharges_when_tariff_is_high():
    request = create_request()

    result = optimize_energy_schedule(
        request=request,
        directives=[create_no_op_directive()],
    )

    last_hour = result.hourly_plan[23]

    assert last_hour.battery_action == "discharge"
    assert last_hour.battery_kwh > 0


def test_solar_is_used_without_exceeding_availability():
    request = create_request()

    result = optimize_energy_schedule(
        request=request,
        directives=[create_no_op_directive()],
    )

    for hour in range(24):
        plan = result.hourly_plan[hour]
        available_solar = request.hours[hour].solar_kwh

        assert plan.solar_used_kwh <= available_solar + 1e-5
        assert plan.solar_used_kwh >= 0


def test_hourly_energy_balance():
    request = create_request()

    result = optimize_energy_schedule(
        request=request,
        directives=[create_no_op_directive()],
    )

    for hour in range(24):
        plan = result.hourly_plan[hour]
        demand = request.hours[hour].demand_kwh

        charge = 0.0
        discharge = 0.0

        if plan.battery_action == "charge":
            charge = plan.battery_kwh
        elif plan.battery_action == "discharge":
            discharge = plan.battery_kwh

        supply = (
            plan.grid_kwh
            + plan.solar_used_kwh
            + discharge
        )

        consumption = demand + charge

        assert supply == pytest.approx(consumption, abs=1e-5)


def test_no_charge_directive_is_applied():
    request = create_request()
    request.operator_notes[0] = (
        "Do not charge the battery between midnight and 1 AM."
    )

    directive = DirectiveInterpretation(
        note_index=0,
        applies=True,
        directive_type="no_charge_window",
        structured_adjustment={
            "hours": [0]
        },
        explanation="Charging is prohibited during hour 0.",
    )

    result = optimize_energy_schedule(
        request=request,
        directives=[directive],
    )

    assert result.hourly_plan[0].battery_action != "charge"


def test_solar_reduction_directive_is_applied():
    request = create_request()
    request.operator_notes[0] = (
        "Solar output will fall to 20 percent from 10 AM to 11 AM."
    )

    directive = DirectiveInterpretation(
        note_index=0,
        applies=True,
        directive_type="solar_reduction",
        structured_adjustment={
            "hours": [10],
            "factor": 0.2,
        },
        explanation="Usable solar is limited to 20 percent.",
    )

    result = optimize_energy_schedule(
        request=request,
        directives=[directive],
    )

    original_solar = request.hours[10].solar_kwh
    effective_solar = original_solar * 0.2

    assert result.hourly_plan[10].solar_used_kwh <= (
        effective_solar + 1e-5
    )


def test_directive_count_mismatch_is_rejected():
    request = create_request()

    with pytest.raises(
        OptimizationError,
        match="Directive count does not match",
    ):
        optimize_energy_schedule(
            request=request,
            directives=[],
        )