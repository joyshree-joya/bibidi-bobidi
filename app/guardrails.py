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

def validate_and_normalize_directives(
    raw_directives: list[dict],
    notes_count: int,
    battery_capacity_kwh: float
) -> list[dict]:
        if not isinstance(raw_directives, list):
            raise DirectiveValidationError(
            "Directives must be a list"
            )

        if len(raw_directives) != notes_count:
            raise DirectiveValidationError(
            "Number of directives must match number of notes"
            )

        seen_indices = set()

        for directive in raw_directives:
            if not isinstance(directive, dict):
                raise DirectiveValidationError(
                    "Each directive must be an object"
                )
            if "note_index" not in directive:
                raise DirectiveValidationError(
                    "Missing note_index"
                )

            note_index = directive["note_index"]

            if note_index in seen_indices:
                raise DirectiveValidationError(
                    "Duplicate note_index"
                )

            seen_indices.add(note_index)

            if isinstance(note_index, bool) or not isinstance(note_index, int):
                raise DirectiveValidationError(
                    "note_index must be an integer"
                )

            if note_index < 0 or note_index >= notes_count:
                raise DirectiveValidationError(
                    "Invalid note_index"
                )

            if seen_indices != set(range(notes_count)):
                raise DirectiveValidationError(
                "Missing note_index"
                )