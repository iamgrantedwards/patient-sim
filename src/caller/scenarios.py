"""Patient instructions and evaluator expectations are separate fields."""
from dataclasses import dataclass


@dataclass(frozen=True)
class CallScenario:
    id: str
    kind: str
    objective: str
    opening_posture: str
    success_criteria: tuple[str, ...] = ()
    known_traps: tuple[str, ...] = ()
    version: int = 1


SMOKE = CallScenario(
    id="smoke",
    kind="office_information",
    objective=(
        "You are considering a routine visit. Find out the office's weekday hours, "
        "where it is located, and whether you need to bring your insurance card. "
        "Ask these as separate follow-up questions. Do not book, change, cancel, "
        "or refill anything on this call. Accept it if they cannot answer."
    ),
    opening_posture="After their greeting, ask what time the office closes on weekdays.",
    success_criteria=("Both sides exchange multiple relevant turns", "Caller closes naturally"),
    known_traps=("Long pauses may be mistaken for a completed turn",),
)

SCENARIOS = {"smoke": SMOKE, "calibration": SMOKE}


def get_scenario(name: str) -> CallScenario:
    try:
        return SCENARIOS[name]
    except KeyError:
        raise ValueError(f"Unknown scenario: {name}") from None
