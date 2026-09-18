import asyncio

from app.llm_interpreter import interpret_operator_notes
from app.guardrails import validate_and_normalize_directives


async def main():

    notes = [
        "Reduce solar generation from 1 PM to 3 PM by 80%",
        "Keep at least 150 kWh in the battery from 5 PM to 8 PM",
    ]

    # Step 1: Ask LLM to interpret the notes
    raw_directives = await interpret_operator_notes(
        notes,
        battery_capacity_kwh=300
    )

    print("\nRAW LLM OUTPUT:\n")

    for directive in raw_directives:
        print(directive)

    # Step 2: Validate and normalize LLM output
    validated_directives = validate_and_normalize_directives(
        raw_directives,
        notes_count=len(notes),
        battery_capacity_kwh=300
    )

    print("\nVALIDATED OUTPUT:\n")

    for directive in validated_directives:
        print(directive)


asyncio.run(main())