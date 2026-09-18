import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


SAMPLE_FILE = Path(
    "BUP_CSE_FEST_2026_Preli_Public_Sample_Cases.json"
)

client = TestClient(app)


def load_public_cases():
    with SAMPLE_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return data["cases"]


CASES = load_public_cases()


@pytest.mark.parametrize(
    "case",
    CASES,
    ids=[case["id"] for case in CASES],
)
def test_public_sample(case):
    response = client.post(
        "/optimize-energy",
        json=case["input"],
    )

    assert response.status_code == 200, (
        f"{case['id']} failed with "
        f"{response.status_code}: {response.text}"
    )

    result = response.json()
    expected = case["expected_output"]

    # -------------------------------------------------
    # 1. Basic response structure
    # -------------------------------------------------

    assert result["scenario_id"] == expected["scenario_id"]

    assert "directive_interpretation" in result
    assert "hourly_plan" in result
    assert "total_grid_kwh" in result
    assert "total_cost_bdt" in result
    assert "peak_grid_kwh" in result
    assert "plan_summary" in result

    # -------------------------------------------------
    # 2. Directive interpretation
    # -------------------------------------------------

    actual_directives = result["directive_interpretation"]
    expected_directives = expected["directive_interpretation"]

    assert len(actual_directives) == len(
        case["input"]["operator_notes"]
    )

    assert len(actual_directives) == len(expected_directives)

    for actual, expected_directive in zip(
        actual_directives,
        expected_directives,
    ):
        assert actual["note_index"] == expected_directive["note_index"]

        assert actual["applies"] == expected_directive["applies"]

        assert (
            actual["directive_type"]
            == expected_directive["directive_type"]
        )

        assert (
            actual["structured_adjustment"]
            == expected_directive["structured_adjustment"]
        )

        # Explanation does not need exact matching.
        assert isinstance(actual["explanation"], str)
        assert actual["explanation"].strip()

    # -------------------------------------------------
    # 3. Hourly plan must contain all 24 hours
    # -------------------------------------------------

    hourly_plan = result["hourly_plan"]

    assert len(hourly_plan) == 24

    actual_hours = [
        item["hour"]
        for item in hourly_plan
    ]

    assert sorted(actual_hours) == list(range(24))

    # -------------------------------------------------
    # 4. Basic hourly values
    # -------------------------------------------------

    for item in hourly_plan:
        assert item["grid_kwh"] >= -0.01
        assert item["solar_used_kwh"] >= -0.01
        assert item["battery_kwh"] >= -0.01
        assert item["battery_energy_after_kwh"] >= -0.01

        assert item["battery_action"] in {
            "charge",
            "discharge",
            "idle",
        }

    # -------------------------------------------------
    # 5. Total values should be close to reference
    # -------------------------------------------------

    assert result["total_grid_kwh"] == pytest.approx(
        expected["total_grid_kwh"],
        abs=0.01,
    )

    assert result["total_cost_bdt"] == pytest.approx(
        expected["total_cost_bdt"],
        abs=0.01,
    )

    calculated_peak = max(
    item["grid_kwh"]
    for item in hourly_plan
)

    assert result["peak_grid_kwh"] == pytest.approx(
        calculated_peak,
        abs=0.01,
    )