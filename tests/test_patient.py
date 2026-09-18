from dataclasses import replace

from src.caller.patient import DEFAULT_PATIENT, build_instructions
from src.caller.scenarios import SMOKE


def test_evaluator_fields_cannot_change_patient_instructions():
    altered = replace(SMOKE, known_traps=("TRAP_CANARY",), success_criteria=("SUCCESS_CANARY",))
    assert build_instructions(DEFAULT_PATIENT, altered) == build_instructions(
        DEFAULT_PATIENT, SMOKE
    )


def test_patient_facts_and_callback_are_stable():
    prompt = build_instructions(DEFAULT_PATIENT, SMOKE, "+12025550123")
    assert "Dana Whitfield" in prompt
    assert "March 4, 1986" in prompt
    assert "+12025550123" in prompt
    assert "prescriber" in prompt and "Name not available" in prompt
