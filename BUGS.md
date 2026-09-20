# Findings and engineering iteration

This report distinguishes defects in our simulator from observations of the office
agent. **No office-agent defect is confirmed yet.** Call transcripts have been inspected
and saved recordings decode, but end-to-end listening and audio-offset verification
are still pending. A refusal or identity check is not automatically a defect.

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
- **Verification:** prompt regression covers all scenarios; live retest is pending.
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

See [collection results](docs/COLLECTION.md) for coverage, evidence status and remaining
checks. No automatic judge or invented bug quota is used.
