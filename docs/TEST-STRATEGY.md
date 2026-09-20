# Ten-call evaluation strategy

Originally planned 2026-09-19; reconciled against the implementation on 2026-09-20
UTC (September 19 Pacific), #77. Ten candidate conversations have been captured;
[COLLECTION.md](COLLECTION.md) records actual IDs, coverage and acceptance.
This document explains evaluation intent and the implemented coverage. It is **not
loaded by the application or sent to the AI judge**. Use [SUBMISSION.md](SUBMISSION.md)
for remaining delivery work and [EVALUATION.md](EVALUATION.md) for the exact rubric,
request payload, score calculation and test boundaries.

## What we are testing

Our bot is the patient, their AI is the office, and we are the reviewers. The patient
receives a realistic goal, fixed synthetic facts and conversational behavior. It answers
what is actually asked and follows the conversation. It does not receive expected
answers, bug hypotheses, evaluator criteria or instructions to manufacture a failure.

After each call, we listen and compare the transcript with the audio. We evaluate two
separate things: whether our caller produced a fair, coherent interaction, and whether
the office handled the request appropriately. An observed problem is not automatically
a defect in their system. Refusal, unavailable slots, missing facts and identity checks
can all be correct. Spoken confirmation proves a claim, not a backend transaction.

The deliverable is **at least ten full conversations**, each with playable two-sided
OGG/MP3 audio and a transcript. Ten attempts is insufficient. No fixed bug quota; a
small set of supported findings beats speculative complaints. Typical 1–3-minute length
is guidance, not a reason to stretch or cut a natural conversation.

## Current execution status

- Athena exploration #8 is complete by Grant's firsthand report. Calendar/SMS details
  are recollected, not independently checked; shared state with the assessment line
  remains unknown. Never dial the confirmation number.
- Debugging was recorded; #46's lifecycle/duplicate-assignment fix landed in #58 and
  passed later connected retests. The native SIGSEGV cause remains unknown.
- All ten current scenarios are implemented. Original audio, transcript and per-call
  revision/configuration are retained. Capture does not establish human acceptance.
- Configuration comparison #13 and audio-aligned timing #15 are deferred. Controlled
  barge-in was not implemented. Neither a partial turn nor a prompt proves interruption.
- The optional AI assessment is implemented. It evaluates a single transcript with a
  generic office-agent rubric plus dedicated patient, turn-taking and ending text checks.
  All seven listening topics are surfaced, but audio-only judgments still require listening.

## Implemented coverage and the AI assessment

The live call uses [scenarios.py](../src/caller/scenarios.py). The patient receives
its objective, opening posture and synthetic facts. Evaluator fields stay outside
the patient prompt. The judge receives the saved scenario ID, projected transcript
turns and allowlisted capture/termination metadata; it does **not** receive the scenario objective, `success_criteria`,
`known_traps`, this plan, prior calls or a policy reference. A scenario's name is
context, not an executable assertion that its complete objective was achieved.

| Captured scenario ID | Text assessment can help inspect | Additional review needed |
| --- | --- | --- |
| `smoke` | Request handling and clear next steps | Audio/closing; externally correct hours/location are unknown without independent facts. |
| `schedule` | Options versus final confirmation within the call | Audible dates/names and actual booking remain separate questions. |
| `reschedule` | Lookup explanation and replacement summary | Compare prior-call claims manually; the judge does not load the scheduling call. |
| `cancel` | Cancellation explanation and next steps | Prior-slot consistency and actual backend deletion are not automatically verified. |
| `refill` | Response to the request, legitimate boundaries, next steps | Chart content and authority are unknown; a refusal alone is not a defect. |
| `refill-details` | Clarification when information is missing | Do not assume this isolates one variable against the refill call. |
| `insurance` | Qualification/uncertainty and suggested next steps | No independent policy source is supplied to the model. |
| `correction` | Whether the corrected afternoon preference is retained | Not a controlled barge-in test; confirm consequential wording in audio. |
| `ambiguity` | Whether the office clarifies a vague request | Coherence, pacing and the audible ending still need listening. |
| `proxy` | Handling of a general third-party request | No blanket legal/privacy-compliance grade or actual record-access verification. |

These are opportunities for the five generic rubric dimensions, not ten dedicated
AI test cases. The model can return not assessable when a dimension was not exercised.
See [the evaluation mapping](EVALUATION.md) for deterministic checks versus model judgment.

## Original planned coverage slots (historical)

The table below preserves the original plan, **not an execution ledger**. Actual
coverage changed: separate correction and ambiguity calls plus a third-party request
were implemented; controlled interruption and a dedicated office-defect reproduction
were not. The implemented table above and COLLECTION.md describe what was actually
captured. Do not relabel these calls as experiments that were never performed.

| Slot | Patient goal | Main observation for us | Preparation / fallback |
| --- | --- | --- | --- |
| 01 · Office information | Ask weekday hours, location and what to bring, with relevant follow-ups. | Coherent turns, grounded answers or honest uncertainty, sensible ending. | Follow legitimate demo-profile setup if required; do not intentionally reject onboarding and then call missing access a bug. First establish what information is actually available. |
| 02 · Schedule | Arrange one routine, nonurgent visit within supplied availability. | Relevant intake, actual date/time clarification, consistency between options and final summary. | Use the observed practice and fixed synthetic identity. Save exactly what the agent claims was arranged; never invent an appointment identifier. |
| 03 · Reschedule | Move the appointment claimed in 02 to another supplied availability window. | Finds the intended appointment or asks for clarification; confirms the proposed replacement consistently. | Reference only the prior spoken claim. If no appointment was established, ask whether one exists and how to reschedule; document the limitation, not a fictional prior booking. |
| 04 · Cancel | Cancel the appointment most recently claimed in the sequence. | Identity/appointment clarification, accurate cancellation summary, no contradictory confirmation. | If cross-call lookup is unsupported, ask how to cancel an existing appointment. Record this as a cancellation-workflow conversation, not a verified cancellation. |
| 05 · Refill request | Request a refill using a prepared synthetic medication and available supporting details. | Appropriate intake, correct handling of missing authority, and clear next steps rather than unsupported fulfillment claims. | Prefer a refill supported by the demo context. If the practice cannot handle it or facts are unavailable, a clear refusal/routing explanation can be correct. Do not promise a successful refill. |
| 06 · Refill with one missing fact | Make a comparable request while honestly lacking one detail, such as the last fill date. | Clarifies the gap or gives a safe next step without inventing patient data. | Hold other facts fixed where possible. If 05 was unsupported, probe that stated boundary rather than repeating an identical unsupported request as if it were new coverage. |
| 07 · Insurance | Ask whether the supplied plan is accepted and what information is needed before a visit. | Distinguishes known policy from uncertainty; asks for necessary details without inventing coverage. | Use a demo-supported plan when available. A fictional unrecognized plan is an uncertainty test, not evidence the agent failed to know a real policy. |
| 08 · Ambiguity and correction | Begin with a plausible vague request, then clarify it and correct one detail. | Asks a useful clarifying question and carries the corrected fact forward. | Example: ask to “change my visit,” then clarify the intended action. Keep the scenario internally consistent; record the exact correction. |
| 09 · Interruption and recovery | Make one relevant correction during a longer response, then allow the agent to respond. | Distinguishes intentional barge-in from accidental overlap; retains the correction and resumes sensibly. | Requires controlled interruption behavior not yet implemented. Verify from audio that interruption actually occurred. Otherwise mark this coverage untested and repeat; a prompt alone is not proof. |
| 10 · Targeted reproduction | Revisit the strongest observed failure under comparable conditions. | Does the same problem recur, and is it still attributable to their agent? | Choose the target after reviewing early calls. If there is no credible candidate, repeat an ambiguous scenario for consistency. If our caller caused the issue, first fix it and use a matched retest; do not present our bug as theirs. |

The sequence 02–04 measures conversational claims and cross-call consistency. Without
independent backend evidence, `verified_state` stays unknown. Re-verifying identity is
not itself a failure. If state is not supported, retain that explicit limitation and
use standalone workflow conversations instead; do not claim they tested actual mutation.

## Collection method for any further calls

- **Baseline:** complete and listen to 01. Fix caller defects that would invalidate the
  evaluation before accumulating more calls. A qualifying debugging retest may fill this
  slot if it genuinely covers the objective; otherwise it remains separate.
- **Transactions:** run 02–04 individually, reviewing between calls so later patient facts
  match only prior claims. Keep a short state ledger with actual call ID, identity,
  appointment details claimed, corrections, and independent verification or “unknown.”
- **Breadth:** run 05–08 individually. Review after each. Choose the final edge/reproduction
  focus from actual evidence, rather than forcing ten unrelated tricks.
- **Depth:** add a call only for an unusable pair or a justified reproduction. The
  planned interruption/reproduction slots were not completed; they do not require
  automatic additional calls now that ten varied candidate pairs exist.

The deferred #13 read-only configuration screen would belong before transaction calls because
calibration must not modify patient state. Its three options vary configurations, not
just one isolated model. Full reviewed calibration conversations may count toward the
minimum, but do not replace scenario diversity. Running all three plus this coverage
plan can require more than ten calls; do not promise exactly ten attempts or a fixed cost.
If time is tight, explicitly defer the screen and describe provider choices as initial
engineering rationale. Never claim model comparison or “best latency” without results.

## What gets saved after each call

The existing recording/transcript/provenance is the original evidence. Use **Review**
to save an outcome and useful notes. The detailed seven-row checklist is optional;
the UI's Usable outcome requires listening confirmation and Complete evidence: OK.
Other rows can remain not assessed. Add AI summary inserts an existing model assessment
as labeled draft notes; it does not approve the call or set checklist grades.
No playback action approves a call. Review revisions remain separate from raw evidence;
changed files require a recheck. See [CALL-REVIEW.md](CALL-REVIEW.md).

For an observation worth investigating, record:

- Actual call ID, audio offset and exact raw quote; label any transcription correction.
- What happened and its consequence for the patient.
- What we expected and the basis: observed product behavior, a stated policy, a prior
  claim or an explained conversational norm. Unknown policy means uncertain grounding.
- Attribution: ours, theirs, environment, mixed or unknown; evidence and remaining doubt.
- Next action and linked issue. For repetitions, record the condition and actual n/N,
  including attempts that did not reproduce it. Never extrapolate a success rate from one call.

Track coverage in #18 with rows: `slot | actual call ID(s) | current review result |
coverage actually exercised | issue/finding | next action`. Replace missing qualifying
pairs deliberately and keep every failed attempt available as debugging evidence.
A complete conversation containing a remote-agent defect or polite refusal can qualify;
a crashed attempt or a single question followed by a hangup does not.

## How observations turn into changes

| What we observe | What we do next |
| --- | --- |
| Our worker dies or loses artifacts | Investigate our lifecycle/evidence code, add a regression, fix in a linked PR, then repeat the same scenario. Preserve the failed attempt. |
| Our caller loops, invents facts or misses a correction | Inspect the audio/transcript and patient instructions. Change the smallest supported cause; compare a matched retest. |
| Awkward delay, mishearing or overlap | Separate STT, turn detection, LLM, TTS and transport evidence. Change one relevant variable where feasible. Audio offsets support timing; text callback times do not. |
| Their agent gives a questionable answer | Check the expectation and product context first. Reproduce if useful and write an evidence-backed finding. We cannot patch their system; do not tune the patient to force a desired failure. |
| The product refuses or cannot access a prior appointment | Check whether that is correct or a demo limitation. Document the supported boundary and adjust subsequent scenarios honestly. |

A change record says: baseline call → hypothesis → issue/PR → exact change → offline
verification → retest call → improvement/regression/uncertainty. A code fix passing tests
is not a live-call result. Freeze the new baseline after a justified change and record
the boundary; earlier recordings remain valid evidence of the earlier configuration.

## Current closeout order

The debugging recording is complete per Grant's report. Listen to the captured pairs,
validate meaningful observations, publish the reviewed evidence, finish the final
walkthrough and verify public links. No new model comparison, UI or infrastructure
is needed just to finish. See [SUBMISSION.md](SUBMISSION.md).

For the final walkthrough, distinguish the intended strategy, actual call coverage,
automated transcript suggestions and human-verified findings. The debug journal
preserves the actual failure → regression → fix → retest progression. Never stage
completed work as new discovery or claim the containment fix resolved native memory access.
