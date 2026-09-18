import pytest

from app.guardrails import (
    DirectiveValidationError,
    validate_and_normalize_directives,
)


def valid_solar_directive() -> dict:
    return {
        "note_index": 0,
        "applies": True,
        "directive_type": "solar_reduction",
        "structured_adjustment": {
            "hours": [13, 14],
            "factor": 0.2,
        },
        "explanation": "Solar availability is reduced to 20 percent.",
    }


def valid_no_op_directive() -> dict:
    return {
        "note_index": 0,
        "applies": False,
        "directive_type": "no_op",
        "structured_adjustment": None,
        "explanation": "The note does not affect energy scheduling.",
    }


def validate(
    directives: list[dict],
    notes_count: int = 1,
    capacity: float = 500,
) -> list[dict]:
    return validate_and_normalize_directives(
        raw_directives=directives,
        notes_count=notes_count,
        battery_capacity_kwh=capacity,
    )


def test_valid_solar_reduction_is_accepted():
    result = validate([valid_solar_directive()])

    assert len(result) == 1
    assert result[0]["note_index"] == 0
    assert result[0]["applies"] is True
    assert result[0]["directive_type"] == "solar_reduction"
    assert result[0]["structured_adjustment"]["hours"] == [13, 14]
    assert result[0]["structured_adjustment"]["factor"] == 0.2


def test_valid_no_op_is_accepted():
    result = validate([valid_no_op_directive()])

    assert result[0]["applies"] is False
    assert result[0]["directive_type"] == "no_op"
    assert result[0]["structured_adjustment"] is None


def test_hours_are_sorted_and_duplicates_removed():
    directive = valid_solar_directive()
    directive["structured_adjustment"]["hours"] = [14, 13, 14]

    result = validate([directive])

    assert result[0]["structured_adjustment"]["hours"] == [13, 14]


def test_results_are_returned_in_note_index_order():
    first = valid_no_op_directive()

    second = {
        "note_index": 1,
        "applies": True,
        "directive_type": "no_charge_window",
        "structured_adjustment": {
            "hours": [14, 15],
        },
        "explanation": "Charging is prohibited.",
    }

    result = validate(
        directives=[second, first],
        notes_count=2,
    )

    assert [item["note_index"] for item in result] == [0, 1]


def test_duplicate_note_index_is_rejected():
    first = valid_no_op_directive()
    duplicate = valid_solar_directive()

    with pytest.raises(DirectiveValidationError):
        validate(
            directives=[first, duplicate],
            notes_count=2,
        )


def test_missing_note_is_rejected():
    with pytest.raises(DirectiveValidationError):
        validate(
            directives=[valid_no_op_directive()],
            notes_count=2,
        )


def test_invalid_directive_type_is_rejected():
    directive = valid_solar_directive()
    directive["directive_type"] = "turn_off_campus"

    with pytest.raises(DirectiveValidationError):
        validate([directive])


@pytest.mark.parametrize("invalid_hour", [-1, 24, 100])
def test_invalid_hour_is_rejected(invalid_hour):
    directive = valid_solar_directive()
    directive["structured_adjustment"]["hours"] = [invalid_hour]

    with pytest.raises(DirectiveValidationError):
        validate([directive])


@pytest.mark.parametrize("invalid_factor", [-0.1, 1.1, True])
def test_invalid_solar_factor_is_rejected(invalid_factor):
    directive = valid_solar_directive()
    directive["structured_adjustment"]["factor"] = invalid_factor

    with pytest.raises(DirectiveValidationError):
        validate([directive])


def test_reserve_above_battery_capacity_is_rejected():
    directive = {
        "note_index": 0,
        "applies": True,
        "directive_type": "minimum_battery_reserve",
        "structured_adjustment": {
            "hours": [17, 18],
            "minimum_energy_kwh": 600,
        },
        "explanation": "Maintain a minimum battery reserve.",
    }

    with pytest.raises(DirectiveValidationError):
        validate(
            directives=[directive],
            capacity=500,
        )


def test_negative_reserve_is_rejected():
    directive = {
        "note_index": 0,
        "applies": True,
        "directive_type": "minimum_battery_reserve",
        "structured_adjustment": {
            "hours": [17],
            "minimum_energy_kwh": -10,
        },
        "explanation": "Maintain a minimum battery reserve.",
    }

    with pytest.raises(DirectiveValidationError):
        validate([directive])


def test_negative_grid_cap_is_rejected():
    directive = {
        "note_index": 0,
        "applies": True,
        "directive_type": "max_grid_window",
        "structured_adjustment": {
            "hours": [18],
            "max_grid_kwh": -1,
        },
        "explanation": "Limit grid import.",
    }

    with pytest.raises(DirectiveValidationError):
        validate([directive])


def test_no_op_with_applies_true_is_rejected():
    directive = valid_no_op_directive()
    directive["applies"] = True

    with pytest.raises(DirectiveValidationError):
        validate([directive])


def test_no_op_with_adjustment_is_rejected():
    directive = valid_no_op_directive()
    directive["structured_adjustment"] = {
        "hours": [1]
    }

    with pytest.raises(DirectiveValidationError):
        validate([directive])


def test_non_no_op_with_applies_false_is_rejected():
    directive = valid_solar_directive()
    directive["applies"] = False

    with pytest.raises(DirectiveValidationError):
        validate([directive])


def test_non_no_op_with_null_adjustment_is_rejected():
    directive = valid_solar_directive()
    directive["structured_adjustment"] = None

    with pytest.raises(DirectiveValidationError):
        validate([directive])


def test_empty_explanation_is_rejected():
    directive = valid_solar_directive()
    directive["explanation"] = "   "

    with pytest.raises(DirectiveValidationError):
        validate([directive])


def test_non_list_output_is_rejected():
    with pytest.raises(DirectiveValidationError):
        validate_and_normalize_directives(
            raw_directives={
                "note_index": 0
            },
            notes_count=1,
            battery_capacity_kwh=500,
        )