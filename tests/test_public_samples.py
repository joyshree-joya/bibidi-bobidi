import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# Public sample JSON file
SAMPLE_FILE = (
    Path(__file__).resolve().parent.parent
    / "BUP_CSE_FEST_2026_Preli_Public_Sample_Cases.json"
)


with open(SAMPLE_FILE, "r", encoding="utf-8") as file:
    PUBLIC_SAMPLES = json.load(file)


def get_expected_adjustment(directive):
    """Return only the machine-checkable directive fields."""
    return {
        "note_index": directive["note_index"],
        "applies": directive["applies"],
        "directive_type": directive["directive_type"],
        "structured_adjustment": directive["structured_adjustment"],
    }


@pytest.mark.parametrize(
    "case",
    PUBLIC_SAMPLES,
    ids=lambda case: case["id"],
)
def test_public_sample(case):
    """
    Test one complete public sample through the real API.

    Pipeline:
        Public Sample
            ↓
        FastAPI
            ↓
        OpenAI LLM
            ↓
        Guardrails
            ↓
        Optimizer
            ↓
        Final Response
    """

    sample_id = case["id"]
    request_data = case["input"]
    expected = case["reference"]

    response = client.post(
        "/optimize-energy",
        json=request_data,
    )

    assert response.status_code == 200, (
        f"{sample_id} failed with status "
        f"{response.status_code}: {response.text}"
    )

    result = response.json()

  
    # Basic response structure
   

    assert result["scenario_id"] == request_data["scenario_id"]

    assert "directive_interpretation" in result
    assert "hourly_plan" in result
    assert "total_grid_kwh" in result
    assert "total_cost_bdt" in result
    assert "peak_grid_kwh" in result
    assert "plan_summary" in result

    # Directive interpretation


    actual_directives = result["directive_interpretation"]
    expected_directives = expected["directive_interpretation"]

    # Exactly one directive per note
    assert len(actual_directives) == len(
        request_data["operator_notes"]
    )

    # Correct order
    for index, directive in enumerate(actual_directives):
        assert directive["note_index"] == index

    # Compare machine-checkable directive semantics.
    # Explanation text is intentionally NOT compared.
    actual_semantics = [
        get_expected_adjustment(directive)
        for directive in actual_directives
    ]

    expected_semantics = [
        get_expected_adjustment(directive)
        for directive in expected_directives
    ]

    assert actual_semantics == expected_semantics


    # Hourly plan


    hourly_plan = result["hourly_plan"]

    assert len(hourly_plan) == 24

    hours = [item["hour"] for item in hourly_plan]

    assert len(set(hours)) == 24
    assert set(hours) == set(range(24))

    # Basic numeric validation


    for item in hourly_plan:
        assert item["grid_kwh"] >= 0
        assert item["solar_used_kwh"] >= 0
        assert item["battery_kwh"] >= 0
        assert item["battery_energy_after_kwh"] >= 0

    assert result["total_grid_kwh"] >= 0
    assert result["total_cost_bdt"] >= 0
    assert result["peak_grid_kwh"] >= 0

    # Totals should match the public reference.
    #
    # Equivalent optimal schedules are allowed, so we compare
    # objective values rather than requiring the exact hourly plan.
   
    assert result["total_grid_kwh"] == pytest.approx(
        expected["total_grid_kwh"],
        abs=0.01,
    )

    assert result["total_cost_bdt"] == pytest.approx(
        expected["total_cost_bdt"],
        abs=0.01,
    )

    
    # Peak grid usage
    #
    # The public cases allow equivalent optimal schedules.
    # Therefore calculated peak from OUR returned schedule.
   

    calculated_peak = max(
        item["grid_kwh"]
        for item in hourly_plan
    )

    assert result["peak_grid_kwh"] == pytest.approx(
        calculated_peak,
        abs=0.01,
    )