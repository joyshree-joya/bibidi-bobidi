import asyncio
import os

import pytest
from dotenv import load_dotenv


# Load .env before importing the LLM module.
load_dotenv()

from app.llm_interpreter import interpret_operator_notes


def test_live_llm_interpretation():
    """
    Live integration test.

    This test runs only when OPENAI_API_KEY is configured.
    Otherwise, it is safely skipped.
    """

    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip(
            "OPENAI_API_KEY is not configured; skipping live LLM test"
        )

    notes = [
        "Do not charge the battery between 2 PM and 4 PM."
    ]

    directives = asyncio.run(
        interpret_operator_notes(
            notes=notes,
            battery_capacity_kwh=500,
        )
    )

    assert isinstance(directives, list)
    assert len(directives) == 1

    directive = directives[0]

    assert directive["note_index"] == 0
    assert directive["applies"] is True
    assert directive["directive_type"] == "no_charge_window"
    assert directive["structured_adjustment"]["hours"] == [14, 15]
    assert isinstance(directive["explanation"], str)
    assert directive["explanation"].strip()