# Findings and engineering iteration

Final review reconciliation — September 20, 2026. Grant listened to and saved reviews
for the [primary ten](calls/README.md), plus four additional usable calls and one recheck.
This report distinguishes transcript-supported contradictions, human-reported audible
problems and unresolved causes. It does not treat AI scores as proof or infer backend
state. The ending guard was diagnosed, fixed and retested in #92/#93 before this final publication.

## Office response: explicit “no injury” is reversed during intake

- **Call / locator:** [scheduling transcript](calls/call-20260920-152827-c782d723/transcript.txt),
  turns 001, 004 and 005; [original audio](calls/call-20260920-152827-c782d723/recording.ogg).
  Audio-aligned seconds were not measured; turn numbers are exact transcript locators.
- **Expected / basis:** preserve the patient's explicitly stated injury and urgency
  information. If uncertain, ask neutrally instead of confirming the opposite.
- **Evidence:** patient 001: “It's not urgent or due to an injury.” Remote 004:
  “Just to confirm, you'd like to schedule a visit for knee discomfort that started after an injury.”
  Patient 005: “Actually, the knee discomfort is not from an injury, and it's not urgent.”
- **Impact / severity:** medium; the caller must correct intake information that could
  affect appointment selection or urgency handling. No actual clinical outcome is claimed.
- **Attribution / confidence:** office-side conversational contradiction in the captured
  transcript. Grant's [listening review](calls/call-20260920-152827-c782d723/review.json)
  independently notes that the assessment agent was not fully listening. This supports
  investigation, but a word-level audio offset/independent transcription was not recorded.
- **Suggested improvement:** retain explicit negations in the intake summary and
  confirm uncertain details without presupposing an injury. No access to their prompt or
  internal STT exists, so the internal cause and any backend effect are unknown.

## Audible office introductions: choppy or dropping voice

- **Expected / basis:** the greeting and recording notice should be intelligible without
  missing syllables; otherwise patients can miss the identity or opening question.
- **Human evidence:** Grant reports “voice dropping in the intro” in
  [scheduling](calls/call-20260920-152827-c782d723/review.json), “voice drops on intro” in
  [insurance](calls/call-20260920-155626-e98e0c8f/review.json), “choppy” in
  [correction](calls/call-20260920-155843-a34fb22c/review.json), and “dropped assessment
  agent intro” in [unclear request](calls/call-20260920-160135-0dc99449/review.json).
  Inspect the opening greeting, turn 000, in each linked call's original recording.
  These are verbatim review excerpts, not fabricated transcript quotes or exact audio offsets.
- **Impact / severity:** moderate audible quality concern; conversations still proceeded.
- **Attribution / uncertainty:** the symptom is heard on the office speaker, but office
  synthesis, telephony transport and our capture path have not been isolated. Do not
  label a specific provider defective. A complete transcript does not disprove an audio glitch.
- **Suggested next check:** compare the two recorded channels with Cloud session evidence
  around the greeting before changing a provider. This was not performed for submission.

## Call endings: usable interactions can still stop before a complete close

- **Expected / basis:** allow the active response and final confirmation to finish before
  hanging up. A tool invocation or `ended` status is not evidence of a natural farewell.
- **Human evidence:** Grant flags dropped/incomplete endings in
  [rescheduling](calls/call-20260920-153210-b4de979e/review.json),
  [insurance](calls/call-20260920-155626-e98e0c8f/review.json),
  [correction](calls/call-20260920-155843-a34fb22c/review.json) and
  [third-party request](calls/call-20260920-162313-7544c7c2/review.json).
  The [unclear-request review](calls/call-20260920-160135-0dc99449/review.json) leaves
  the ending grade unassessed but records an early-ending concern; preserve that distinction.
- **Exact transcript evidence:** correction turn 015 ends “Your appointment is confirmed
  for Monday, September twenty first at two thirty PM with doctor zed”. The
  [raw transcript](calls/call-20260920-155843-a34fb22c/transcript.txt) labels it completed
  despite the unfinished content. Audio alignment is unmeasured; inspect the final exchange.
- **Impact / severity:** medium; final details or a closing question may be lost.
- **Attribution / uncertainty:** the final reviewed calls report `end_call_tool`, so our
  caller had a confirmed protection gap: the end tool could schedule shutdown while
  newer remote input remained pending. #93 adds a guard before SDK shutdown side effects.
  This is separate from the first call's `remote_hangup`, and it does not explain every
  missing farewell or identify an office-side defect.
- **Fix / retest:** [Correction follow-up](calls/call-20260920-175412-c28bccad/transcript.txt)
  used the same pipeline and patient prompt. Local events show one deferred hangup while
  the remote agent was speaking, dialogue continuing, then a later accepted close with
  no failsafe. The final turns contain the patient's goodbye and the office's full
  confirmation/farewell. [Grant's saved review](calls/call-20260920-175412-c28bccad/review.json)
  confirms listening and marks the call usable; the optional Ending grade is unassessed.
  Do not infer a comprehensive audio-quality grade or that all cutoff causes are fixed.
  The office reported existing appointments, so this was not an identical dialogue replay.
  [DEBUGGING.md](docs/DEBUGGING.md) records the offline regression and implementation.

## Patient repetition: one duplicated question needs audio confirmation

In [third-party request](calls/call-20260920-162313-7544c7c2/transcript.txt), patient turn
003 contains the same three-sentence question twice. Grant's saved note asks whether
there was patient-agent repetition. Expected behavior is one question unless clarification
is needed. Attribution remains our generation, capture/reconciliation or mixed until
compared against the audio; do not count it as an office-agent bug. The duplicate is
preserved verbatim, not silently cleaned from the submission transcript.

## Earlier implementation findings and iteration

The following dated findings preserve the earlier build evidence. Their original
listening caveats apply to those specific earlier calls, not the final reviewed set.

## Our caller: child failure did not reach the controller (#46)

- **Expected / basis:** a failed call worker must move the controller out of Dialing and
  preserve partial evidence; this is the local lifecycle contract.
- **Actual:** the second attempt's child exited with `-11`; its parent remained alive,
  the UI kept waiting, and a later initialization hit the exclusive journal guard.
- **Evidence:** `call-20260919-194206-bc3ae8e3`, private worker log and matching macOS crash
  report; no usable recording exists, so there is no invented audio timestamp.
- **Impact / severity / attribution:** lost conversation evidence and misleading live
  status; high; ours/environment, with the native crash's initiating cause unresolved.
- **Change:** PR #58 propagates child failures, rejects repeated assignments, retains
  the exclusive journal guard, and enables fault-handler diagnostics.
- **Verification:** offline failure/cleanup/duplicate-admission regressions pass. Later
  calls completed through the same controller. A real killed-process test in PR #61
  recovered persisted journal turns as partial evidence.
- **Uncertainty:** the native SIGSEGV has not been reproduced or fixed at its source.
  Successful subsequent calls do not establish a native-library fix.

## Our caller: office-information objective displaced onboarding (#59)

- **Expected / basis:** follow the office's offered demo setup with synthetic facts
  before pursuing questions; a fair evaluation must reach the supported workflow.
- **Actual:** a generic onboarding instruction lost to the scenario's question-first
  opening, and the patient declined the offered profile.
- **Evidence:** `call-20260920-011456-fe6d34a0`, patient turn 3:
  “Thanks for the offer, but I just want to know some information first. Can you tell me where the office is located?”
  Turn index is a transcript locator, not an audio timestamp.
- **Impact / severity / attribution:** unnecessarily constrained access to office
  information; medium; ours.
- **Change:** PR #60 made acceptance of offered onboarding the first action (smoke v3).
- **Verification:** one matched follow-up, `call-20260920-011714-108d161e`, accepted
  onboarding and obtained hours, location and insurance-card guidance. Both calls
  completed with decoded recordings. This is one before/after observation, not a rate.
- **Uncertainty:** listening must still confirm the raw STT and naturalness.

## Our caller: accepted an offered support transfer (#62)

- **Expected / basis:** keep the assessment conversation on the designated line;
  decline transfers and staff callbacks as a caller-scope constraint.
- **Actual / evidence:** `call-20260920-012849-8a9bc2d4`, patient turn 13:
  “Yes, please connect me to the patient support team for further help.”
  Remote turn 14: “Transferring you now. Thank you.”
- **Impact / severity / attribution:** the caller could leave the intended test path;
  medium; ours. The office's offer is not itself a defect.
- **Cause / change:** the old instruction prohibited requesting a transfer to another
  number but did not explicitly reject offered team transfers. The new rule covers both
  acceptance and staff callbacks, then requests general next steps and a clean ending.
- **Verification:** prompt regression covers all scenarios; a subsequent live retest declined
  the offered transfer and requested general next steps. PR #63 is merged.
  The original attempt ended through end_call_tool with confirmed controller cleanup.
- **Uncertainty:** a spoken transfer announcement does not prove a transfer completed.
  Prompting cannot guarantee protection from unsolicited remote routing.

## Office-agent observations

The scheduling → rescheduling → cancellation sequence retrieved the prior appointment
and confirmed successive changes consistently in the transcripts. Identity checks were
retained. These are **claimed state** and **cross-call consistency**; **verified state
is unknown** because no independent backend record was inspected.

The refill conversation declined a medication absent from the chart and offered next
steps. That boundary can be appropriate; the simulator's supplied medication is not
proof of an authorized prescription in the demo record. Several provider-name spellings
vary in raw STT. Audio review is required before attributing that to the office.

### Candidate for listening review: provider-name consistency

- **Expected / basis:** when confirming the same provider, the spoken identity should
  remain consistent with the earlier confirmation unless a change is explained.
- **Observation:** Grant reported a possible audible name variation; raw transcripts
  also show spelling variations. The scheduling/rescheduling sequence and the
  availability-correction candidate are the listening targets in the collection ledger.
- **Evidence limit:** no human-verified audio offset or pronunciation comparison has
  been saved yet. Transcript spelling alone cannot establish changed pronunciation.
- **Attribution:** unknown; remote speech, our STT, our patient's repetition, or mixed
  effects remain possible. Severity is unassigned until the audio establishes impact.
- **Next action:** listen to the original audio, record both timestamps and exact words
  in the Review notes, and distinguish a transcription error from an audible change.

See [collection results](docs/COLLECTION.md) for coverage, evidence status and remaining
checks. Optional AI transcript assessments propose observations; their scores are uncalibrated
and do not confirm audio quality or backend claims. No invented bug quota is used.
