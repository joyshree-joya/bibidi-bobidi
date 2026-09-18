from fastapi.testclient import TestClient

from app import main as main_module
from app.schemas import DirectiveInterpretation


client = TestClient(main_module.app)


def create_valid_payload() -> dict:
    tariffs = [10.0] * 24
    tariffs[0] = 5.0
    tariffs[23] = 20.0

    return {
        "scenario_id": "API-TEST-001",
        "operator_notes": [
            "The cafeteria menu changes tomorrow."
        ],
        "hours": [
            {
                "hour": hour,
                "demand_kwh": 100,
                "solar_kwh": 25 if 10 <= hour <= 14 else 0,
                "tariff_bdt_per_kwh": tariffs[hour],
            }
            for hour in range(24)
        ],
        "battery": {
            "capacity_kwh": 100,
            "initial_energy_kwh": 50,
            "minimum_energy_kwh": 10,
            "max_charge_kwh_per_hour": 50,
            "max_discharge_kwh_per_hour": 50,
        },
    }


async def fake_interpreter(request):
    return [
        {
            "note_index": 0,
            "applies": False,
            "directive_type": "no_op",
            "structured_adjustment": None,
            "explanation": (
                "The note does not affect energy scheduling."
            ),
        }
    ]


def fake_guardrail(raw_directives, request):
    return [
        DirectiveInterpretation.model_validate(directive)
        for directive in raw_directives
    ]


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_optimize_energy_returns_complete_response(monkeypatch):
    monkeypatch.setattr(
        main_module,
        "_call_interpreter",
        fake_interpreter,
    )

    monkeypatch.setattr(
        main_module,
        "_validate_directives",
        fake_guardrail,
    )

    response = client.post(
        "/optimize-energy",
        json=create_valid_payload(),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["scenario_id"] == "API-TEST-001"
    assert len(body["directive_interpretation"]) == 1
    assert len(body["hourly_plan"]) == 24

    assert body["directive_interpretation"][0]["directive_type"] == "no_op"
    assert body["directive_interpretation"][0]["applies"] is False

    assert body["total_grid_kwh"] >= 0
    assert body["total_cost_bdt"] >= 0
    assert body["peak_grid_kwh"] >= 0

    assert isinstance(body["plan_summary"], str)
    assert len(body["plan_summary"]) > 0


def test_hourly_plan_contains_required_fields(monkeypatch):
    monkeypatch.setattr(
        main_module,
        "_call_interpreter",
        fake_interpreter,
    )

    monkeypatch.setattr(
        main_module,
        "_validate_directives",
        fake_guardrail,
    )

    response = client.post(
        "/optimize-energy",
        json=create_valid_payload(),
    )

    assert response.status_code == 200

    first_hour = response.json()["hourly_plan"][0]

    assert set(first_hour.keys()) == {
        "hour",
        "grid_kwh",
        "solar_used_kwh",
        "battery_action",
        "battery_kwh",
        "battery_energy_after_kwh",
    }


def test_invalid_23_hour_request_is_rejected():
    payload = create_valid_payload()
    payload["hours"] = payload["hours"][:23]

    response = client.post(
        "/optimize-energy",
        json=payload,
    )

    assert response.status_code == 422


def test_empty_operator_note_is_rejected():
    payload = create_valid_payload()
    payload["operator_notes"] = ["   "]

    response = client.post(
        "/optimize-energy",
        json=payload,
    )

    assert response.status_code == 422


def test_negative_demand_is_rejected():
    payload = create_valid_payload()
    payload["hours"][5]["demand_kwh"] = -1

    response = client.post(
        "/optimize-energy",
        json=payload,
    )

    assert response.status_code == 422