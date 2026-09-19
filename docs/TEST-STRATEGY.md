# Ten-call evaluation strategy

Planned 2026-09-19 at Grant's request, before the debugging video. This is a coverage
plan, not a record of executed calls or implemented scenarios. Only office information
is currently implemented. Collection is tracked in #18; caller recovery in #46;
required product exploration in #8; findings in #19.

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

## Before collecting

1. Verify the required Athena product exploration (#8): supported flows, demo patient
   setup and any stated policies. Never dial its confirmation number. Record observed
   facts and unknowns instead of assuming office hours, refill eligibility or insurance.
2. Record the genuine #46 investigation and verify the caller can complete and preserve
   a conversation. The existing first call awaits listening; the second has no final
   audio/transcript. Neither is currently accepted toward the ten.
3. Implement the scenario matrix with versioned synthetic facts. Patient objectives go
   into the caller; evaluation expectations stay outside its prompt. A routine visit
   should fit the observed practice. Current generic facts, unknown pharmacy/prescriber
   and possibly out-of-scope medication are not proof of a supported refill workflow.
4. Freeze a baseline configuration: STT, LLM, TTS/voice, turn handling and caller number.
   Record the revision/configuration for every call. A model swap is an experiment, not
   an automatic response to any bad outcome.

Use the existing Review panel for checks/notes, GitHub for actual bugs and changes, and
this document for coverage. No extra dashboard or automatic judge is required.

## Ten coverage slots

These are coverage slots, **not historical call IDs**. Assign actual call IDs only after
running them. Do not label existing attempts retrospectively as planned experiments.

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

## Run in small batches and adjust deliberately

- **Baseline:** complete and listen to 01. Fix caller defects that would invalidate the
  evaluation before accumulating more calls. A qualifying debugging retest may fill this
  slot if it genuinely covers the objective; otherwise it remains separate.
- **Transactions:** run 02–04 individually, reviewing between calls so later patient facts
  match only prior claims. Keep a short state ledger with actual call ID, identity,
  appointment details claimed, corrections, and independent verification or “unknown.”
- **Breadth:** run 05–08 individually. Review after each. Choose the final edge/reproduction
  focus from actual evidence, rather than forcing ten unrelated tricks.
- **Depth:** run 09–10. Add a call when a recording is incomplete, an edge was not actually
  exercised, or a meaningful finding needs reproduction. Ten is a minimum, not an attempt cap.

The planned #13 read-only configuration screen belongs before transaction calls because
calibration must not modify patient state. Its three options vary configurations, not
just one isolated model. Full reviewed calibration conversations may count toward the
minimum, but do not replace scenario diversity. Running all three plus this coverage
plan can require more than ten calls; do not promise exactly ten attempts or a fixed cost.
If time is tight, explicitly defer the screen and describe provider choices as initial
engineering rationale. Never claim model comparison or “best latency” without results.

## What gets saved after each call

The existing recording/transcript/provenance is the original evidence. Use **Review**
to save the seven checks, your name, timestamped observations, explicit full listening,
and a separate result: usable conversation, incomplete attempt or needs recheck.
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

## What to say in the debugging video

“I need ten complete patient conversations across normal workflows and edge cases.
Before collecting them, I'm fixing a reliability problem in my own caller: the second
attempt lost its child worker while the UI kept waiting. I'll show the evidence, ask AI
to help test the hypothesis, make the justified change, and verify it. Then I'll review
a comparable call before using this system to evaluate the office agent.”

That is the bridge between debugging and the assessment. The debugging video need not
contain all ten calls. Later, the short final walkthrough can show the coverage, one
strong supported finding if found, and an actual before/after improvement. Do not stage
previously completed work as new discovery. Current cause of the native worker crash
remains unresolved; do not promise that one monitoring fix explains it.

## Immediate order

Agree the strategy → verify product context → film #46 diagnosis/fix → review a controlled
retest → implement/verify the missing scenarios → collect in small batches → reproduce
useful findings → publish at least ten reviewed pairs and the two required videos.
Planning and scenario implementation can be done before filming if helpful; disclose
that preparation. Do not spend another pass polishing the UI before caller reliability.
