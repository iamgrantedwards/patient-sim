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
        "First accept any offer to create a demo patient profile and give your supplied "
        "name when asked. Then, once onboarding is complete, find out the office's weekday hours, "
        "where it is located, and whether you need to bring your insurance card. "
        "Ask these as separate follow-up questions. Do not book, change, cancel, "
        "or refill anything on this call. Accept it if they cannot answer."
    ),
    opening_posture="If they offer demo onboarding, say yes and give your supplied name first. Otherwise ask what time the office closes on weekdays.",
    success_criteria=("Both sides exchange multiple relevant turns", "Caller closes naturally"),
    known_traps=("Long pauses may be mistaken for a completed turn",),
    version=3,
)

# Workflow scenarios intentionally ask the office to look up state. No prior booking
# is supplied until it has actually been observed; an unavailable lookup is an outcome.
SCHEDULE = CallScenario(
    id="schedule",
    kind="appointment_scheduling",
    objective="Arrange a nonurgent consultation for mild knee discomfort lasting two weeks, without an injury or urgent symptoms. Ask for a weekday afternoon. Clarify the full date, time and location before agreeing; if no suitable slot is offered, ask about the next available option and accept the outcome.",
    opening_posture="After any demo onboarding, ask to schedule a visit for knee discomfort.",
)
RESCHEDULE = CallScenario(
    id="reschedule",
    kind="rescheduling",
    objective="Ask whether there is an appointment on file under your supplied identity. You do not have a date or confirmation number handy. Only if the office finds an appointment, ask to move it to a different weekday afternoon and confirm the full replacement date and time. If none is found, ask how rescheduling works; do not claim a booking exists or create a new one.",
    opening_posture="Ask whether they can check for an appointment under your name because you may need to change the time.",
)
CANCEL = CallScenario(
    id="cancel",
    kind="cancellation",
    objective="Ask whether there is an appointment on file under your supplied identity. Only if they find one, identify which appointment they mean and request cancellation, then ask whether anything else is needed. If none is found, ask how cancellation works. Do not invent an appointment or schedule a new one.",
    opening_posture="Ask for help checking and, if present, canceling an appointment under your name.",
)
REFILL = CallScenario(
    id="refill",
    kind="medication_refill",
    objective="Ask whether this office can help with a refill of your supplied medication. Give its name and dose when asked. You do not know the prescriber's name or last fill date and have no pharmacy contact details handy; say so honestly. Ask what the next step would be if they cannot refill it. Do not request a change in dose or claim approval.",
    opening_posture="Ask whether they handle medication refill requests.",
)
REFILL_DETAILS = CallScenario(
    id="refill-details",
    kind="refill_missing_information",
    objective="You want to understand how to request a refill when you do not have your prescription number or last fill date handy. Your supplied medication name and dose are available. Ask what information to gather and whom to contact if this office cannot handle it. Do not claim a previous refill request was approved.",
    opening_posture="Say you have a refill question but do not have the prescription number with you.",
)
INSURANCE = CallScenario(
    id="insurance",
    kind="insurance_questions",
    objective="Ask whether the office accepts your supplied Example Health PPO plan and what insurance information to bring. You do not have a member number handy. If they cannot confirm coverage, ask how you could check before a visit. Do not demand a guarantee or schedule an appointment.",
    opening_posture="Ask how to find out whether your insurance is accepted.",
)
CORRECTION = CallScenario(
    id="correction",
    kind="availability_correction",
    objective="Ask about arranging a nonurgent knee consultation. Initially ask about a morning appointment; on your next relevant turn correct yourself that you meant a weekday afternoon. Use the corrected afternoon preference thereafter, and clarify the full date and time before agreeing. Do not interrupt deliberately or invent a prior booking.",
    opening_posture="After onboarding, ask about a morning appointment for knee discomfort.",
)
AMBIGUITY = CallScenario(
    id="ambiguity",
    kind="unclear_request",
    objective="Begin by asking for help with a visit. When asked what help you need, clarify that you only want to know how to prepare for a first orthopedic visit, including what records or imaging to bring. Ask one relevant follow-up, accept unknown information, and do not book anything.",
    opening_posture="Say you need some help with a visit, then let them ask what you need.",
)
PROXY = CallScenario(
    id="proxy",
    kind="third_party_request",
    objective="Ask generally what is required to arrange an appointment for an adult family member. You have not obtained their authorization and have no identifying details to provide. Do not invent a family member's record or request private information. Ask whether that person needs to call themselves and accept the stated process. Do not book anything.",
    opening_posture="Ask whether an adult family member needs to call themselves to arrange a visit.",
)
SCENARIOS = {
    item.id: item
    for item in (
        SMOKE,
        SCHEDULE,
        RESCHEDULE,
        CANCEL,
        REFILL,
        REFILL_DETAILS,
        INSURANCE,
        CORRECTION,
        AMBIGUITY,
        PROXY,
    )
}
SCENARIOS["calibration"] = SMOKE


def get_scenario(name: str) -> CallScenario:
    try:
        return SCENARIOS[name]
    except KeyError:
        raise ValueError(f"Unknown scenario: {name}") from None
