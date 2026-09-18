import pytest
from pydantic import ValidationError

from app.schemas import OptimizeEnergyRequest


def create_valid_request() -> dict:
    return {
        "scenario_id": "GRID-101",
        "operator_notes": [
            "Do not charge the battery between 2 PM and 4 PM."
        ],
        "hours": [
            {
                "hour": hour,
                "demand_kwh": 100,
                "solar_kwh": 20 if 8 <= hour <= 16 else 0,
                "tariff_bdt_per_kwh": 10,
            }
            for hour in range(24)
        ],
        "battery": {
            "capacity_kwh": 500,
            "initial_energy_kwh": 200,
            "minimum_energy_kwh": 50,
            "max_charge_kwh_per_hour": 100,
            "max_discharge_kwh_per_hour": 100,
        },
    }


def test_valid_request_is_accepted():
    request = OptimizeEnergyRequest(**create_valid_request())

    assert request.scenario_id == "GRID-101"
    assert len(request.hours) == 24
    assert len(request.operator_notes) == 1
    assert request.hours[0].hour == 0
    assert request.hours[23].hour == 23


def test_hours_are_sorted_automatically():
    data = create_valid_request()
    data["hours"].reverse()

    request = OptimizeEnergyRequest(**data)

    assert [item.hour for item in request.hours] == list(range(24))


def test_request_requires_exactly_24_hours():
    data = create_valid_request()
    data["hours"] = data["hours"][:23]

    with pytest.raises(
        ValidationError,
        match="exactly 24 entries",
    ):
        OptimizeEnergyRequest(**data)


def test_duplicate_hour_is_rejected():
    data = create_valid_request()
    data["hours"][23]["hour"] = 22

    with pytest.raises(
        ValidationError,
        match="Each hour must appear exactly once",
    ):
        OptimizeEnergyRequest(**data)


def test_empty_operator_note_is_rejected():
    data = create_valid_request()
    data["operator_notes"] = ["   "]

    with pytest.raises(
        ValidationError,
        match="Operator notes cannot be empty",
    ):
        OptimizeEnergyRequest(**data)


def test_more_than_three_notes_are_rejected():
    data = create_valid_request()
    data["operator_notes"] = [
        "Note 1",
        "Note 2",
        "Note 3",
        "Note 4",
    ]

    with pytest.raises(ValidationError):
        OptimizeEnergyRequest(**data)


def test_negative_demand_is_rejected():
    data = create_valid_request()
    data["hours"][5]["demand_kwh"] = -10

    with pytest.raises(ValidationError):
        OptimizeEnergyRequest(**data)


def test_initial_energy_above_capacity_is_rejected():
    data = create_valid_request()
    data["battery"]["initial_energy_kwh"] = 600

    with pytest.raises(
        ValidationError,
        match="initial_energy_kwh cannot exceed capacity_kwh",
    ):
        OptimizeEnergyRequest(**data)


def test_initial_energy_below_minimum_is_rejected():
    data = create_valid_request()
    data["battery"]["initial_energy_kwh"] = 20
    data["battery"]["minimum_energy_kwh"] = 50

    with pytest.raises(
        ValidationError,
        match="initial_energy_kwh cannot be below minimum_energy_kwh",
    ):
        OptimizeEnergyRequest(**data)


def test_unknown_field_is_rejected():
    data = create_valid_request()
    data["unknown_field"] = "not allowed"

    with pytest.raises(ValidationError):
        OptimizeEnergyRequest(**data)