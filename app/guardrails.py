class DirectiveValidationError(Exception):
    pass


ALLOWED_DIRECTIVE_TYPES = {
    "solar_reduction",
    "minimum_battery_reserve",
    "no_charge_window",
    "no_discharge_window",
    "max_grid_window",
    "no_op",
}


def _validate_hours(hours):
    """
    Validate and normalize a list of hours.

    - Must be a list
    - Every value must be an integer
    - bool is not accepted as an integer
    - Hours must be between 0 and 23
    - Duplicate hours are removed
    - Hours are sorted
    """

    if not isinstance(hours, list):
        raise DirectiveValidationError(
            "hours must be a list"
        )

    for hour in hours:
        if isinstance(hour, bool) or not isinstance(hour, int):
            raise DirectiveValidationError(
                "hours must contain integers"
            )

        if hour < 0 or hour > 23:
            raise DirectiveValidationError(
                "hour must be between 0 and 23"
            )

    return sorted(set(hours))


def _validate_adjustment(
    directive_type,
    adjustment,
    battery_capacity_kwh
):
    """
    Validate and normalize structured_adjustment
    according to the directive type.
    """

    # no_op must not have an adjustment
    if directive_type == "no_op":
        if adjustment is not None:
            raise DirectiveValidationError(
                "no_op must have structured_adjustment=null"
            )

        return None

    # Every non-no_op directive needs an object
    if not isinstance(adjustment, dict):
        raise DirectiveValidationError(
            "structured_adjustment must be an object"
        )


    # solar_reduction


    if directive_type == "solar_reduction":

        required_fields = {"hours", "factor"}

        if set(adjustment.keys()) != required_fields:
            raise DirectiveValidationError(
                "solar_reduction requires only hours and factor"
            )

        hours = _validate_hours(
            adjustment["hours"]
        )

        factor = adjustment["factor"]

        if isinstance(factor, bool) or not isinstance(
            factor, (int, float)
        ):
            raise DirectiveValidationError(
                "factor must be a number"
            )

        if not 0 <= factor <= 1:
            raise DirectiveValidationError(
                "factor must be between 0 and 1"
            )

        return {
            "hours": hours,
            "factor": factor
        }


    # minimum_battery_reserve


    if directive_type == "minimum_battery_reserve":

        required_fields = {
            "hours",
            "minimum_energy_kwh"
        }

        if set(adjustment.keys()) != required_fields:
            raise DirectiveValidationError(
                "minimum_battery_reserve requires only "
                "hours and minimum_energy_kwh"
            )

        hours = _validate_hours(
            adjustment["hours"]
        )

        reserve = adjustment["minimum_energy_kwh"]

        if isinstance(reserve, bool) or not isinstance(
            reserve, (int, float)
        ):
            raise DirectiveValidationError(
                "minimum_energy_kwh must be a number"
            )

        if reserve < 0:
            raise DirectiveValidationError(
                "minimum_energy_kwh cannot be negative"
            )

        if reserve > battery_capacity_kwh:
            raise DirectiveValidationError(
                "minimum_energy_kwh cannot exceed battery capacity"
            )

        return {
            "hours": hours,
            "minimum_energy_kwh": reserve
        }


    # no_charge_window


    if directive_type == "no_charge_window":

        required_fields = {"hours"}

        if set(adjustment.keys()) != required_fields:
            raise DirectiveValidationError(
                "no_charge_window requires only hours"
            )

        return {
            "hours": _validate_hours(
                adjustment["hours"]
            )
        }

    # no_discharge_window
  

    if directive_type == "no_discharge_window":

        required_fields = {"hours"}

        if set(adjustment.keys()) != required_fields:
            raise DirectiveValidationError(
                "no_discharge_window requires only hours"
            )

        return {
            "hours": _validate_hours(
                adjustment["hours"]
            )
        }

   
    # max_grid_window


    if directive_type == "max_grid_window":

        required_fields = {
            "hours",
            "max_grid_kwh"
        }

        if set(adjustment.keys()) != required_fields:
            raise DirectiveValidationError(
                "max_grid_window requires only hours "
                "and max_grid_kwh"
            )

        hours = _validate_hours(
            adjustment["hours"]
        )

        max_grid = adjustment["max_grid_kwh"]

        if isinstance(max_grid, bool) or not isinstance(
            max_grid, (int, float)
        ):
            raise DirectiveValidationError(
                "max_grid_kwh must be a number"
            )

        if max_grid < 0:
            raise DirectiveValidationError(
                "max_grid_kwh cannot be negative"
            )

        return {
            "hours": hours,
            "max_grid_kwh": max_grid
        }

    raise DirectiveValidationError(
        "Unsupported directive type"
    )


def validate_and_normalize_directives(
    raw_directives: list[dict],
    notes_count: int,
    battery_capacity_kwh: float
) -> list[dict]:
    """
    Validate and normalize LLM-generated directives.

    Returns directives sorted by note_index.
    Raises DirectiveValidationError for malformed or
    unsafe data.
    """

  
    # Basic validation


    if not isinstance(raw_directives, list):
        raise DirectiveValidationError(
            "Directives must be a list"
        )

    if not isinstance(notes_count, int) or isinstance(
        notes_count, bool
    ):
        raise DirectiveValidationError(
            "notes_count must be an integer"
        )

    if notes_count < 0:
        raise DirectiveValidationError(
            "notes_count cannot be negative"
        )

    if isinstance(battery_capacity_kwh, bool) or not isinstance(
        battery_capacity_kwh, (int, float)
    ):
        raise DirectiveValidationError(
            "battery_capacity_kwh must be a number"
        )

    if battery_capacity_kwh < 0:
        raise DirectiveValidationError(
            "battery_capacity_kwh cannot be negative"
        )

    # Number of directives must match number of notes
    if len(raw_directives) != notes_count:
        raise DirectiveValidationError(
            "Number of directives must match number of notes"
        )

    seen_indices = set()
    normalized = []

   
    # Validate every directive


    for directive in raw_directives:

        if not isinstance(directive, dict):
            raise DirectiveValidationError(
                "Each directive must be an object"
            )

        # note_index
        if "note_index" not in directive:
            raise DirectiveValidationError(
                "Missing note_index"
            )

        note_index = directive["note_index"]

        if isinstance(note_index, bool) or not isinstance(
            note_index, int
        ):
            raise DirectiveValidationError(
                "note_index must be an integer"
            )

        if note_index < 0 or note_index >= notes_count:
            raise DirectiveValidationError(
                "Invalid note_index"
            )

        if note_index in seen_indices:
            raise DirectiveValidationError(
                "Duplicate note_index"
            )

        seen_indices.add(note_index)

        # directive_type
        directive_type = directive.get(
            "directive_type"
        )

        if directive_type not in ALLOWED_DIRECTIVE_TYPES:
            raise DirectiveValidationError(
                "Invalid directive_type"
            )

        # applies
        applies = directive.get("applies")

        if not isinstance(applies, bool):
            raise DirectiveValidationError(
                "applies must be a boolean"
            )

        if directive_type == "no_op":

            if applies is not False:
                raise DirectiveValidationError(
                    "no_op must have applies=false"
                )

        else:

            if applies is not True:
                raise DirectiveValidationError(
                    "Non-no_op directives must have applies=true"
                )

        # explanation
        explanation = directive.get(
            "explanation"
        )

        if not isinstance(explanation, str):
            raise DirectiveValidationError(
                "explanation must be a string"
            )

        if not explanation.strip():
            raise DirectiveValidationError(
                "explanation must be a non-empty string"
            )

        # structured_adjustment
        adjustment = _validate_adjustment(
            directive_type,
            directive.get("structured_adjustment"),
            battery_capacity_kwh
        )

        normalized.append({
            "note_index": note_index,
            "applies": applies,
            "directive_type": directive_type,
            "structured_adjustment": adjustment,
            "explanation": explanation.strip()
        })


    expected_indices = set(range(notes_count))

    if seen_indices != expected_indices:
        raise DirectiveValidationError(
            "Missing note_index"
        )

    # Normalize order
  

    normalized.sort(
        key=lambda directive: directive["note_index"]
    )

    return normalized