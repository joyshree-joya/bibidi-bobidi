import asyncio
import json
import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


class LLMInterpretationError(Exception):
    pass


OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-5.6-luna"
)


def _get_client():
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise LLMInterpretationError(
            "OPENAI_API_KEY is not configured"
        )

    return OpenAI(api_key=api_key)


SYSTEM_PROMPT = """
You are an energy optimization operator-note interpreter.

Convert each natural-language operator note into exactly ONE
structured energy directive.

IMPORTANT RULES:

1. Return exactly one directive for every input note.

2. Preserve the input order using note_index.
   The first note has note_index 0.

3. Allowed directive types are ONLY:

   - solar_reduction
   - minimum_battery_reserve
   - no_charge_window
   - no_discharge_window
   - max_grid_window
   - no_op

4. Non-no_op directives must have:
   applies = true

5. no_op must have:
   applies = false
   structured_adjustment = null

6. Time ranges use start-inclusive, end-exclusive semantics.

   Example:
   "1 PM to 3 PM" -> [13, 14]

   Example:
   "11 PM to 2 AM" -> [23, 0, 1]

7. solar_reduction:

   structured_adjustment:
   {
       "hours": [...],
       "factor": number
   }

8. Percentage interpretation:

   "reduce by 80%" -> factor = 0.2
   "reduce to 80%" -> factor = 0.8
   "drop by half" -> factor = 0.5

9. minimum_battery_reserve:

   structured_adjustment:
   {
       "hours": [...],
       "minimum_energy_kwh": number
   }

10. no_charge_window:

    structured_adjustment:
    {
        "hours": [...]
    }

11. no_discharge_window:

    structured_adjustment:
    {
        "hours": [...]
    }

12. max_grid_window:

    structured_adjustment:
    {
        "hours": [...],
        "max_grid_kwh": number
    }

13. Notes unrelated to energy optimization must become no_op.

14. Do not invent values that are not present in the note.

15. Keep explanations concise.

16. Return JSON only.
"""


# Structured output schema


DIRECTIVE_SCHEMA = {
    "type": "object",
    "properties": {
        "note_index": {
            "type": "integer"
        },
        "applies": {
            "type": "boolean"
        },
        "directive_type": {
            "type": "string",
            "enum": [
                "solar_reduction",
                "minimum_battery_reserve",
                "no_charge_window",
                "no_discharge_window",
                "max_grid_window",
                "no_op"
            ]
        },
        "structured_adjustment": {
            "anyOf": [

                # solar_reduction
                {
                    "type": "object",
                    "properties": {
                        "hours": {
                            "type": "array",
                            "items": {
                                "type": "integer"
                            }
                        },
                        "factor": {
                            "type": "number"
                        }
                    },
                    "required": [
                        "hours",
                        "factor"
                    ],
                    "additionalProperties": False
                },

                # minimum_battery_reserve
                {
                    "type": "object",
                    "properties": {
                        "hours": {
                            "type": "array",
                            "items": {
                                "type": "integer"
                            }
                        },
                        "minimum_energy_kwh": {
                            "type": "number"
                        }
                    },
                    "required": [
                        "hours",
                        "minimum_energy_kwh"
                    ],
                    "additionalProperties": False
                },

                # no_charge_window
                {
                    "type": "object",
                    "properties": {
                        "hours": {
                            "type": "array",
                            "items": {
                                "type": "integer"
                            }
                        }
                    },
                    "required": [
                        "hours"
                    ],
                    "additionalProperties": False
                },

                # no_discharge_window
                {
                    "type": "object",
                    "properties": {
                        "hours": {
                            "type": "array",
                            "items": {
                                "type": "integer"
                            }
                        }
                    },
                    "required": [
                        "hours"
                    ],
                    "additionalProperties": False
                },

                # max_grid_window
                {
                    "type": "object",
                    "properties": {
                        "hours": {
                            "type": "array",
                            "items": {
                                "type": "integer"
                            }
                        },
                        "max_grid_kwh": {
                            "type": "number"
                        }
                    },
                    "required": [
                        "hours",
                        "max_grid_kwh"
                    ],
                    "additionalProperties": False
                },

                # no_op
                {
                    "type": "null"
                }
            ]
        },
        "explanation": {
            "type": "string"
        }
    },
    "required": [
        "note_index",
        "applies",
        "directive_type",
        "structured_adjustment",
        "explanation"
    ],
    "additionalProperties": False
}


# LLM call


async def _call_llm(
    notes: list[str],
    battery_capacity_kwh: float
) -> list[dict]:

    client = _get_client()

    user_input = {
        "battery_capacity_kwh": battery_capacity_kwh,
        "notes": notes
    }

    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(
                client.responses.create,
                model=OPENAI_MODEL,
                instructions=SYSTEM_PROMPT,
                input=json.dumps(
                    user_input,
                    ensure_ascii=False
                ),
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "energy_directives",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "directives": {
                                    "type": "array",
                                    "items": DIRECTIVE_SCHEMA
                                }
                            },
                            "required": [
                                "directives"
                            ],
                            "additionalProperties": False
                        }
                    }
                }
            ),
            timeout=12
        )

    except asyncio.TimeoutError as exc:
        raise LLMInterpretationError(
            "LLM request timed out"
        ) from exc

    except Exception as exc:
        raise LLMInterpretationError(
            "LLM request failed"
        ) from exc

    output_text = response.output_text

    if not output_text:
        raise LLMInterpretationError(
            "LLM returned an empty response"
        )

    try:
        parsed = json.loads(output_text)

    except json.JSONDecodeError as exc:
        raise LLMInterpretationError(
            "LLM returned malformed JSON"
        ) from exc

    if not isinstance(parsed, dict):
        raise LLMInterpretationError(
            "LLM response must be an object"
        )

    directives = parsed.get("directives")

    if not isinstance(directives, list):
        raise LLMInterpretationError(
            "LLM response does not contain a directives list"
        )

    return directives


# Public function


async def interpret_operator_notes(
    notes: list[str],
    battery_capacity_kwh: float
) -> list[dict]:

    # Validate notes
    if not isinstance(notes, list):
        raise LLMInterpretationError(
            "notes must be a list"
        )

    if not 1 <= len(notes) <= 3:
        raise LLMInterpretationError(
            "notes must contain between 1 and 3 items"
        )

    for note in notes:
        if not isinstance(note, str):
            raise LLMInterpretationError(
                "Each note must be a string"
            )

        if not note.strip():
            raise LLMInterpretationError(
                "Each note must be non-empty"
            )

    # Validate battery capacity
    if (
        isinstance(battery_capacity_kwh, bool)
        or not isinstance(
            battery_capacity_kwh,
            (int, float)
        )
        or battery_capacity_kwh < 0
    ):
        raise LLMInterpretationError(
            "battery_capacity_kwh must be a non-negative number"
        )

    last_error = None

    # Retry once if interpretation fails
    for _ in range(2):

        try:
            directives = await _call_llm(
                notes,
                battery_capacity_kwh
            )

            # Exactly one directive per note
            if len(directives) != len(notes):
                raise LLMInterpretationError(
                    "LLM returned an incorrect number of directives"
                )

            # Validate note indices
            expected_indices = set(
                range(len(notes))
            )

            actual_indices = {
                directive.get("note_index")
                for directive in directives
                if isinstance(directive, dict)
            }

            if actual_indices != expected_indices:
                raise LLMInterpretationError(
                    "LLM returned invalid note indices"
                )

            return directives

        except LLMInterpretationError as exc:
            last_error = exc

    raise LLMInterpretationError(
        "Unable to obtain a valid interpretation from the LLM"
    ) from last_error