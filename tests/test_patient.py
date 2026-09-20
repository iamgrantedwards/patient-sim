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


def test_all_scenarios_keep_evaluation_fields_out_of_prompt():
    from src.caller.scenarios import SCENARIOS

    for scenario in SCENARIOS.values():
        altered = replace(
            scenario, known_traps=("SECRET_TRAP",), success_criteria=("SECRET_CHECK",)
        )
        prompt = build_instructions(DEFAULT_PATIENT, altered)
        assert prompt == build_instructions(DEFAULT_PATIENT, scenario)
        assert scenario.objective in prompt
        assert "demo patient profile" in prompt


def test_workflows_do_not_assume_a_prior_booking():
    from src.caller.scenarios import CANCEL, RESCHEDULE

    for scenario in (CANCEL, RESCHEDULE):
        assert "Only if" in scenario.objective
        assert "If none is found" in scenario.objective
