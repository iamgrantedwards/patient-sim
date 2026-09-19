# Call review and improvement workflow

Prepared 2026-09-19. Use one repeatable loop: **choose a purpose -> call -> listen ->
record evidence -> decide -> change if justified -> retest**. The employer asks for
coherent conversations and useful findings; this checklist supports those goals.
It is not an additional employer-mandated scoring system.

## Where each part belongs

| Surface | What belongs there |
| --- | --- |
| App | Scenario choice, explicit start/stop, actual status, recording, transcript and call provenance. A future compact Review control belongs beside the selected call. |
| Learn / Guide | Short explanations of controls and review criteria, available when requested. |
| Per-call review | What a human heard, exact moments, outcome, uncertainties and next action. |
| GitHub issue and PR | The problem, basis, proposed change, regression, verification and linked retest. |
| Debugging journal | The actual progression of diagnosis, changed hypotheses and unresolved questions. |
| Loom / submission docs | Your reasoning, selected evidence and required deliverables. Hiring instructions stay here. |

**Current capability:** the viewer displays a legacy listening flag from metadata;
it does not provide a structured review editor or read the manual sheet below.
[Issue #54](https://github.com/iamgrantedwards/patient-sim/issues/54) tracks a compact
review-save feature after the caller investigation. Do not edit original metadata
just to make its badge green. We can start useful reviews now without that feature.

## Before each call: choose one purpose

Write one sentence describing what the patient wants and what you want to observe.
Keep expected evaluator behavior separate from the patient's prompt. A refusal or
unavailable appointment can be a legitimate outcome; do not force success.

Record whether this is an exploratory call, a reproduction, or a before/after retest.
For a retest, name the prior call and the issue/change being tested. Keep the same
scenario, synthetic facts, caller number and unrelated settings where practical.
Recorded provenance supplies the exact revision and pipeline; reference it rather
than copying every configuration field into handwritten notes.

Currently only the read-only office-information scenario is implemented. Scheduling,
rescheduling/cancellation, refills and realistic edge cases are the upcoming coverage
plan in #18, not scenarios we have already run. Fix #46 and establish a usable caller
before expanding. Product exploration in #8 is still unverified.

## After each call: listen once, then revisit specific moments

Open the call's audio and transcript together. Listen end to end. Use **OK**, **issue**
or **not assessed** for each row; an issue needs a timestamp and a short description.

| Check | What to listen or look for |
| --- | --- |
| Evidence and completeness | Both sides are audible, the recording plays through, and a transcript exists. Did this capture a full conversation or an incomplete attempt? |
| Transcript accuracy | Do consequential words match the audio: dates, names, medication, location or insurance? Mark uncertain/corrected text separately; preserve the raw transcript. |
| Patient behavior | Does our caller answer the actual question, use the supplied facts, stay in role and pursue its objective without looping or inventing information? |
| Turn-taking | Does it wait for the other side, handle pauses and recover from interruptions? Label intentional barge-in separately from accidental overlap. |
| Pacing | Where are the awkward waits? Identify which side is waiting. Use audio offsets for measurements; an impression is not a measured latency result. |
| Voice and audio | Are words intelligible, speech natural enough to follow, and audio free of disruptive clipping, gaps or glitches? |
| Ending and outcome | Is the request completed, refused or left unresolved? Is the closing sensible, or is speech cut off? Distinguish natural closing, remote hangup, operator stop and failsafe. |

Two decisions are separate:

- **Listening complete:** a person listened to all available audio and checked the transcript.
- **Submission suitability:** this is a coherent, full conversation with usable two-sided
  audio and transcript. A remote-agent bug does not automatically make a call unusable;
  finding those bugs is the assignment. An incomplete/crashed attempt does not qualify.

The brief says calls are typically 1–3 minutes; length alone is not a pass/fail rule.
Our stricter first-good-call gate is an internal milestone, not a claim that every
submitted call must use one specific hangup mechanism.

## Record the result now

Use [CALL-REVIEW-TEMPLATE.md](CALL-REVIEW-TEMPLATE.md). Copy a sheet into the actual
call folder as `review.md` when doing a review. That folder is currently Git-ignored;
notes remain local until deliberately reviewed and included with submission evidence.
The viewer will not update from this file until a review integration is implemented.
Do not confuse a completed sheet with a saved UI review.

Use playback offsets such as 00:42, not transcript row numbers. If precise timing is
unavailable, say so. Separate a quote from your interpretation. A spoken booking
confirmation proves a claim, not a backend appointment. Attribution can be ours,
theirs, environment, mixed or unknown.

Record partial attempts too: list what exists and what is missing. Keep unavailable
criteria as not assessed; no need to manufacture a seven-item review of absent audio.

## Use an observation to choose the next action

| Observation | First investigation | A possible change only if supported |
| --- | --- | --- |
| Worker dies; UI stays Dialing | Child-job lifecycle, parent monitoring, metadata and cleanup (#46) | Failure propagation and bounded cleanup |
| Important words are misheard | Compare audio with raw STT; inspect source audio quality | STT configuration/model comparison |
| Caller interrupts a pause | Compare both audio tracks and turn/interruption events | Turn detection or endpointing configuration |
| Long delay before our reply | Separate end-of-turn wait, LLM response, TTS startup and transport | Adjust the stage contributing the delay |
| Patient loops or invents facts | Prompt, scenario facts and conversation context | Prompt/fact correction before assuming a model swap is needed |
| Voice is hard to understand | Inspect source/generated audio versus telephone artifacts | Voice/TTS or transport investigation |
| Office gives a questionable answer | Quote, context, expected behavior and basis | Finding candidate; do not tune the patient to manufacture the failure |

Do not swap all providers after one bad call. For #13, the planned comparison changes
STT and turn detection together, so call it a comparison of configurations, not an
isolated model test. One run per option is a screen, not proof. Keep other variables
fixed and repeat when the difference is ambiguous. Provider descriptions justify an
initial hypothesis; our recordings establish what happened in this application.

For our bug: link the observation to a task/bug issue, add a focused regression where
appropriate, open a labeled draft PR and link actual verification. For a defect in
the office agent: use the finding template, including expected behavior, basis,
timestamp/quote, impact, attribution and uncertainty. Leave an observation unconfirmed
when the evidence is insufficient. No confirmed office-agent findings exist yet.

Each change needs a short before/after record:

```text
Observation and baseline call:
Expected behavior and basis:
Hypothesis / what would disprove it:
Change and issue/PR:
Offline verification:
Retest call and comparable settings (or not performed):
What improved, regressed or remained uncertain:
Decision: keep / revise / revert / gather more evidence
```

## What to show in the recordings

**Debugging video:** show the actual problem in the app/log, the question you ask AI,
its response, your follow-up, the real regression/change and verification. State what
was learned before filming. The parent-only monitoring check is already known; the
original crash cause remains unresolved. Use [the speaking notes](DEBUGGING-SCRIPT.md).
A follow-up can show a controlled call and its actual review; disclose off-camera work.

**Final walkthrough, at most three minutes:** show a representative conversation,
one strong evidenced finding if found, the short technical rationale and a real
before/after improvement. Keep your own voice and webcam on for both deliverables.
You do not need to narrate every checklist row, install tools on camera, or show private
keys/account pages. Model-choice claims must distinguish initial reasoning from measured results.

## Handoff

Keep the app usable without assessment prose. Repository docs explain setup,
architecture, limitations and reproduction. Deliberately publish at least ten reviewed
complete OGG/MP3-plus-transcript pairs with their selected review/finding context;
ignored local artifacts do not become a submission automatically. Check public repo
and video links while logged out, the exact caller number, and a fresh-clone setup.
Keep credentials private; supply `.env.example`, not an encrypted credential bundle.

Immediate order: record the #46 investigation (#25), verify the caller and complete
listening acceptance (#24/#21/#12 as applicable), then expand scenarios and collect #18.
The review-save enhancement #54 follows the caller fix and should stay small.
