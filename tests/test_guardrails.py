import pytest

from app.guardrails import (
    DirectiveValidationError,
    validate_and_normalize_directives,
)


BATTERY_CAPACITY = 300.0


# --------------------------------------------------
# Valid directive
# --------------------------------------------------

def test_valid_solar_reduction():
    raw = [
        {
            "note_index": 0,
            "applies": True,
            "directive_type": "solar_reduction",
            "structured_adjustment": {
                "hours": [13, 14],
                "factor": 0.2,
            },
            "explanation": "Solar generation is reduced.",
        }
    ]

    result = validate_and_normalize_directives(
        raw,
        notes_count=1,
        battery_capacity_kwh=BATTERY_CAPACITY,
    )

    assert result == raw


# --------------------------------------------------
# Valid no_op
# --------------------------------------------------

def test_valid_no_op():
    raw = [
        {
            "note_index": 0,
            "applies": False,
            "directive_type": "no_op",
            "structured_adjustment": None,
            "explanation": "The note is not energy related.",
        }
    ]

    result = validate_and_normalize_directives(
        raw,
        notes_count=1,
        battery_capacity_kwh=BATTERY_CAPACITY,
    )

    assert result == raw


# --------------------------------------------------
# Missing note
# --------------------------------------------------

def test_missing_note_index():
    raw = [
        {
            "applies": True,
            "directive_type": "solar_reduction",
            "structured_adjustment": {
                "hours": [13],
                "factor": 0.5,
            },
            "explanation": "Solar is reduced.",
        }
    ]

    with pytest.raises(DirectiveValidationError):
        validate_and_normalize_directives(
            raw,
            notes_count=1,
            battery_capacity_kwh=BATTERY_CAPACITY,
        )


# --------------------------------------------------
# Duplicate note_index
# --------------------------------------------------

def test_duplicate_note_index():
    raw = [
        {
            "note_index": 0,
            "applies": True,
            "directive_type": "solar_reduction",
            "structured_adjustment": {
                "hours": [13],
                "factor": 0.5,
            },
            "explanation": "Solar is reduced.",
        },
        {
            "note_index": 0,
            "applies": True,
            "directive_type": "no_charge_window",
            "structured_adjustment": {
                "hours": [14],
            },
            "explanation": "Charging is disabled.",
        },
    ]

    with pytest.raises(DirectiveValidationError):
        validate_and_normalize_directives(
            raw,
            notes_count=2,
            battery_capacity_kwh=BATTERY_CAPACITY,
        )


# --------------------------------------------------
# Wrong note order -> should normalize
# --------------------------------------------------

def test_wrong_note_order_is_normalized():
    raw = [
        {
            "note_index": 1,
            "applies": True,
            "directive_type": "no_charge_window",
            "structured_adjustment": {
                "hours": [14],
            },
            "explanation": "Charging is disabled.",
        },
        {
            "note_index": 0,
            "applies": True,
            "directive_type": "solar_reduction",
            "structured_adjustment": {
                "hours": [13],
                "factor": 0.5,
            },
            "explanation": "Solar is reduced.",
        },
    ]

    result = validate_and_normalize_directives(
        raw,
        notes_count=2,
        battery_capacity_kwh=BATTERY_CAPACITY,
    )

    assert [item["note_index"] for item in result] == [0, 1]


# --------------------------------------------------
# Invalid directive type
# --------------------------------------------------

def test_invalid_directive_type():
    raw = [
        {
            "note_index": 0,
            "applies": True,
            "directive_type": "turn_off_everything",
            "structured_adjustment": {},
            "explanation": "Invalid directive.",
        }
    ]

    with pytest.raises(DirectiveValidationError):
        validate_and_normalize_directives(
            raw,
            notes_count=1,
            battery_capacity_kwh=BATTERY_CAPACITY,
        )


# --------------------------------------------------
# Invalid hour
# --------------------------------------------------

def test_invalid_hour():
    raw = [
        {
            "note_index": 0,
            "applies": True,
            "directive_type": "no_charge_window",
            "structured_adjustment": {
                "hours": [25],
            },
            "explanation": "Charging is disabled.",
        }
    ]

    with pytest.raises(DirectiveValidationError):
        validate_and_normalize_directives(
            raw,
            notes_count=1,
            battery_capacity_kwh=BATTERY_CAPACITY,
        )


# --------------------------------------------------
# Duplicate hours -> should normalize
# --------------------------------------------------

def test_duplicate_hours_are_normalized():
    raw = [
        {
            "note_index": 0,
            "applies": True,
            "directive_type": "no_charge_window",
            "structured_adjustment": {
                "hours": [15, 13, 15, 14],
            },
            "explanation": "Charging is disabled.",
        }
    ]

    result = validate_and_normalize_directives(
        raw,
        notes_count=1,
        battery_capacity_kwh=BATTERY_CAPACITY,
    )

    assert result[0]["structured_adjustment"]["hours"] == [
        13,
        14,
        15,
    ]


# --------------------------------------------------
# Invalid factor
# --------------------------------------------------

def test_invalid_factor():
    raw = [
        {
            "note_index": 0,
            "applies": True,
            "directive_type": "solar_reduction",
            "structured_adjustment": {
                "hours": [13],
                "factor": 1.5,
            },
            "explanation": "Solar is reduced.",
        }
    ]

    with pytest.raises(DirectiveValidationError):
        validate_and_normalize_directives(
            raw,
            notes_count=1,
            battery_capacity_kwh=BATTERY_CAPACITY,
        )


# --------------------------------------------------
# Negative battery reserve
# --------------------------------------------------

def test_negative_battery_reserve():
    raw = [
        {
            "note_index": 0,
            "applies": True,
            "directive_type": "minimum_battery_reserve",
            "structured_adjustment": {
                "hours": [17],
                "minimum_energy_kwh": -50,
            },
            "explanation": "Battery reserve is maintained.",
        }
    ]

    with pytest.raises(DirectiveValidationError):
        validate_and_normalize_directives(
            raw,
            notes_count=1,
            battery_capacity_kwh=BATTERY_CAPACITY,
        )


# --------------------------------------------------
# Reserve above battery capacity
# --------------------------------------------------

def test_reserve_above_battery_capacity():
    raw = [
        {
            "note_index": 0,
            "applies": True,
            "directive_type": "minimum_battery_reserve",
            "structured_adjustment": {
                "hours": [17],
                "minimum_energy_kwh": 500,
            },
            "explanation": "Battery reserve is maintained.",
        }
    ]

    with pytest.raises(DirectiveValidationError):
        validate_and_normalize_directives(
            raw,
            notes_count=1,
            battery_capacity_kwh=BATTERY_CAPACITY,
        )


# --------------------------------------------------
# Negative grid cap
# --------------------------------------------------

def test_negative_grid_cap():
    raw = [
        {
            "note_index": 0,
            "applies": True,
            "directive_type": "max_grid_window",
            "structured_adjustment": {
                "hours": [17],
                "max_grid_kwh": -100,
            },
            "explanation": "Grid usage is capped.",
        }
    ]

    with pytest.raises(DirectiveValidationError):
        validate_and_normalize_directives(
            raw,
            notes_count=1,
            battery_capacity_kwh=BATTERY_CAPACITY,
        )


# --------------------------------------------------
# no_op with applies=True
# --------------------------------------------------

def test_no_op_with_applies_true():
    raw = [
        {
            "note_index": 0,
            "applies": True,
            "directive_type": "no_op",
            "structured_adjustment": None,
            "explanation": "No action required.",
        }
    ]

    with pytest.raises(DirectiveValidationError):
        validate_and_normalize_directives(
            raw,
            notes_count=1,
            battery_capacity_kwh=BATTERY_CAPACITY,
        )


# --------------------------------------------------
# Non-no_op with applies=False
# --------------------------------------------------

def test_non_no_op_with_applies_false():
    raw = [
        {
            "note_index": 0,
            "applies": False,
            "directive_type": "solar_reduction",
            "structured_adjustment": {
                "hours": [13],
                "factor": 0.5,
            },
            "explanation": "Solar is reduced.",
        }
    ]

    with pytest.raises(DirectiveValidationError):
        validate_and_normalize_directives(
            raw,
            notes_count=1,
            battery_capacity_kwh=BATTERY_CAPACITY,
        )


# --------------------------------------------------
# Wrong adjustment fields
# --------------------------------------------------

def test_wrong_adjustment_fields():
    raw = [
        {
            "note_index": 0,
            "applies": True,
            "directive_type": "solar_reduction",
            "structured_adjustment": {
                "hours": [13],
                "factor": 0.5,
                "extra_field": 123,
            },
            "explanation": "Solar is reduced.",
        }
    ]

    with pytest.raises(DirectiveValidationError):
        validate_and_normalize_directives(
            raw,
            notes_count=1,
            battery_capacity_kwh=BATTERY_CAPACITY,
        )


# --------------------------------------------------
# Boolean used as numeric value
# --------------------------------------------------

def test_boolean_numeric_value_is_rejected():
    raw = [
        {
            "note_index": 0,
            "applies": True,
            "directive_type": "solar_reduction",
            "structured_adjustment": {
                "hours": [13],
                "factor": True,
            },
            "explanation": "Solar is reduced.",
        }
    ]

    with pytest.raises(DirectiveValidationError):
        validate_and_normalize_directives(
            raw,
            notes_count=1,
            battery_capacity_kwh=BATTERY_CAPACITY,
        )


# --------------------------------------------------
# Malformed LLM response
# --------------------------------------------------

def test_malformed_llm_response():
    raw = "this is not a JSON list"

    with pytest.raises(DirectiveValidationError):
        validate_and_normalize_directives(
            raw,
            notes_count=1,
            battery_capacity_kwh=BATTERY_CAPACITY,
        )