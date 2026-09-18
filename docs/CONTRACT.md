# patient-sim — implementation contract

Revision 5. Supersedes the planning notes. Earlier external-review decisions retain
their **[R3]** and **[R4]** markers. **[R5]** records Grant's 2026-09-18 instruction to
build the local UI before recording the debugging video; call-quality gates are unchanged.

## What this is

A Python voice bot that calls a healthcare voice AI test line at **+1-805-439-8008**,
behaves like a patient, and produces defensible findings about that agent's behavior.

Mandated stack: **LiveKit Agents, pipeline mode** (separate STT / LLM / TTS). Realtime
and speech-to-speech models are disqualifying, as are hosted voice-agent platforms.

Grading order, from the brief: (1) does the bot hold a coherent voice conversation —
failing this is rejected unread; (2) quality of findings; (3) working code that makes
real calls; (4) clear reasoning about provider, turn-detection and latency choices;
(5) evidence of iteration; (6) readable code. Explicitly unwanted: over-engineering,
production infrastructure, fancy diagrams.

**Governing idea.** We are not building an impressive evaluation system. We are
conducting an impressive evaluation. Framework only where it makes the experiment
repeatable.

## Verified environment

Introspected from the installed package, not from documentation.

- `livekit-agents==1.8.2`, `requires-python >=3.10,<3.15`. **Python 3.12 pinned for
  variance control, not compatibility.** `onnxruntime` is not pulled in — it arrives
  only with the local turn-detector plugin.
- `AgentSession` accepts `turn_handling=TurnHandlingOptions{turn_detection, endpointing,
  interruption, preemptive_generation, user_turn_limit}` as well as the legacy flat args.
- `EndpointingOptions{mode: 'fixed'|'dynamic', min_delay, max_delay, alpha}`.
- `InterruptionOptions{mode: 'adaptive'|'vad', min_duration, min_words,
  backchannel_boundary, ...}`.
- **[R4]** `ivr_detection=True` enables proactive IVR behavior, not a standalone
  voicemail classifier. Source inspection showed replies after silence and DTMF tools.
  Keep it off for initial observation; answered-call classification remains unknown.
- `EndCallTool` lives in `livekit.agents.beta`, with `delete_room=True`,
  `end_instructions='say goodbye to the user'`, and `on_tool_completed`.
- `record` takes `RecordingOptions{audio, traces, logs, transcript, redaction}`.
  **Redaction defaults off locally, but a project-level setting overrides a local
  `False`.** Verify redaction is off in the LiveKit console before collecting evidence,
  or the privacy-boundary findings arrive scrubbed.
- `JobContext` exposes `add_sip_participant`, `api`, `session_directory`,
  `make_session_report`, `init_recording`, `add_shutdown_callback`.
- `CreateSIPParticipantRequest` carries `max_call_duration`, `ringing_timeout`,
  `wait_until_answered`, `hide_phone_number` — server-side failsafes, preferred over
  client-side timers alone.

## Frozen decisions

| Decision | Choice |
|---|---|
| Providers | LiveKit Inference (`deepgram/*` STT, `openai/*` LLM, `cartesia/*` TTS) — one account, same model choice, plugin swap kept as a one-line escape hatch |
| Telephony | Twilio Elastic SIP Trunk, one DID, reported in E.164 on the submission form |
| Recording | `record={"audio": True, "transcript": True, "traces": True, "redaction": False}` — no Egress, no external bucket |
| Noise cancellation | **Off.** With NC on, recorded remote audio is post-cancellation. The recording is evidence about their audio; processing it first destroys the measurement. |
| Call ending | `EndCallTool` with `end_instructions=None` **[R3]** plus server-side `max_call_duration` |
| Judge | Optional throughout. Produces candidates, never findings. **First findings are written by hand.** **[R3]** |
| Report | `BUGS.md` required. `report.html` is a derivative and is the first thing cut. |
| Repo | `github.com/iamgrantedwards/patient-sim`, public, real-name commits |

## [R3] Claims are not outcomes

The earlier draft recorded `observed_state_after`. That name was false: it was derived
from what the agent *said*. "Your appointment is booked" proves a confirmation was
spoken. It does not prove an appointment exists.

Three separate concepts, never collapsed:

| Concept | Meaning | Source |
|---|---|---|
| `claimed_state` | what the agent asserted on this call | the transcript |
| `consistency` | whether a later call's claim agrees with an earlier one | across transcripts |
| `verified_state` | independently confirmed | usually **null** — we have no backend access |

Calls 02/04/06 can establish *consistency across conversations*. They cannot establish
backend persistence. Say so in BUGS.md rather than implying more.

**Corollary, and the most important line in this document:** failing to recognize our
caller ID is **not automatically a defect**. Requiring identity verification on every
call may be correct, even required, behavior for PHI. Every finding must carry an
`expected_behavior` and a `basis_for_expectation`. A finding without a stated basis is
an opinion.

Fallback: if the environment turns out not to support cross-call state at all, the
sequence degrades gracefully into independent scenarios. That is a documented
environment fact, not a failed experiment.

## [R3] Calibration is a screen, not a proof

Three **configurations**, not three STT models — C3 varies STT *and* turn detection
together, and LiveKit's default turn detection is already a trained audio model, not a
silence threshold. One call per configuration is an exploratory screen. Repeat the
promising ones if the difference is unclear.

| Config | STT | Turn detection |
|---|---|---|
| A | `deepgram/nova-3` | LiveKit audio detector, pinned `v1-mini` **[R4]** |
| B | `deepgram/nova-2-phonecall` | LiveKit audio detector, pinned `v1-mini` **[R4]** |
| C | `deepgram/flux-general-en` | `turn_detection="stt"` |

Held fixed across all three: voice, TTS model, LLM, temperature, scenario, patient facts.

**Calibration must use a read-only scenario** (hours / location / insurance). Booking an
appointment during calibration would populate the patient record before the state tests
begin and silently invalidate calls 01–06.

Scored on: accuracy of dates, provider names, medication names and insurance names;
count of overlapping speech; our response delay; their response delay.

## [R3] Timing and transcript integrity

Three distinct measurements, not one ambiguous "gap":

- `our_response_ms` — their last audio to our first audio
- `their_response_ms` — our last audio to their first audio
- `overlap_ms` — audio present from both sides simultaneously

All derived from **audio timestamps against a common recording offset**, never from the
wall-clock time a transcript callback happened to fire.

`conversation_item_added` already covers **both** participants. `user_input_transcribed`
is used only for interim/partial capture and is explicitly reconciled against committed
items, or every remote turn is double-counted. **[R3]**

Events are appended to `events.jsonl` **as they arrive** and finalized into
`transcript.json` on shutdown. A writer that only runs on `close` loses the evidence
in exactly the crash that would have been most interesting. **[R3]**

The raw transcript is preserved verbatim. Any correction made after listening is marked
as a correction, with both versions retained. Byte-exact quote verification proves we
did not fabricate a quote; it cannot prove the STT heard correctly. **[R3]**

Per-call provenance, recorded in `meta.json`: git revision, scenario version, resolved
model ids, voice id, all turn-handling settings, caller id, and SIP status.

## [R3] The patient must be specified enough to be consistent

Name, DOB and a speaking style are not enough. A refill call will be asked for the
medication, the pharmacy, the prescriber and the last fill date; an appointment call for
the reason, availability and insurance. An underspecified persona improvises differently
on every call — which destroys the state experiment and manufactures "bugs" when the
agent correctly balks at inconsistent data.

`PatientRecord` carries the synthetic facts each scenario needs, plus an explicit rule
for unknowns: say you do not have it handy rather than inventing it.

Natural behavior rules: answer the question actually asked; disclose details gradually
rather than reciting everything at once; tolerate reasonable pauses; do not restate the
objective every turn.

**Hard separation: `known_traps` and `success_criteria` never reach the prompt.**
`build_instructions()` may read only the patient facts, `objective`, and
`opening_posture`. A patient who knows the trap steers into it, and the failure is
manufactured rather than discovered. Enforced by a test.

## [R3] Lifecycle

One component owns the call. Dispatch preceding SIP does not by itself prove the worker
is ready, so the agent places its own SIP call from inside the session, after it is in
the room.

Explicit handling required for: dispatch failure · ringing timeout / no answer · remote
hangup · IVR or voicemail answering · our own crash mid-call · recording completion.
`ended_by` ∈ `end_call_tool | failsafe | remote_hangup | dispatch_error | no_answer |
rejected | sip_error | worker_error | worker_shutdown | telephony_error | unknown_disconnect`.
**[R4]** Preserve specific provider/network failure causes rather than labeling them as
no-answer. IVR/voicemail classification is an unresolved first-call observation.

The worker start command is documented in the README, not assumed.

**Ending on a negative outcome is a valid end.** Refusal, unavailability and an
unresolved request are legitimate results. The patient acknowledges the outcome and
closes normally rather than persisting until a failsafe fires.

## Finding schema

```
expected_behavior      what should have happened
basis_for_expectation  why we expect it — brief, stated policy, prior call, safety, norm
actual_behavior        what happened
evidence               call id + mm:ss + verbatim quote from the raw transcript
reproduction           conditions, and n of m attempts
impact                 who is harmed and how
attribution            theirs | ours | environment | mixed | unknown
uncertainty            what would need to be true to be sure; what we could not check
severity               critical | high | medium | low
```

Categories: `TRANSACTION · FACTUAL_GROUNDING · PATIENT_SAFETY · PRIVACY_IDENTITY ·
ESCALATION · CONVERSATION · STATE_CONSISTENCY · TELEPHONY`.

`unknown` and `mixed` attribution are first-class **[R3]**: a recording can prove an
audible failure without proving whether their agent, our endpointing, or the phone
connection caused it.

## Milestones

The 12-call / 8-kind plan and safety/privacy mix below are internal targets. The employer
requires at least 10 complete call pairs and varied scenarios, not those exact counts.
See [the original-brief compliance review](ASSESSMENT.md) for submission requirements.

**M1 remains the first call-quality gate:** one natural conversation, a clean ending,
and a downloaded recording that matches the saved transcript, reviewed by listening.
**[R5]** The first technical call has been captured. Grant explicitly requested a usable
UI before recording the debugging session: build the call-review UI and explicit
outbound controls first, then record genuine debugging and finish M1. This UI is a
requested local interface, not a new employer requirement. [ROADMAP.md](ROADMAP.md)
links the issues, dependencies, and focused PRs; recording readiness does not block UI work.

| # | Milestone | Done when |
|---|---|---|
| M0 | Accounts and context | Twilio DID + Elastic SIP Trunk registered in LiveKit; redaction confirmed off; required Athena product exploration documented |
| UI | **[R5] Local call console** | Existing recordings/transcripts reviewable; explicit outbound controls and real status; browser-verified before debugging video |
| M1 | **First good call** | One 1–3 min conversation · ends via `EndCallTool`, not a failsafe · recording downloaded, playable, and matching the transcript |
| M2 | Calibration screen | Three configurations on a read-only scenario; one chosen with a written reason |
| M3 | Evidence pipeline | Incremental events · reconciled turns · timing from audio offsets · provenance per call |
| M4 | Call collection | At least 10 complete reviewed call pairs across varied scenarios; 12 calls/≥8 kinds are stretch targets; state support documented |
| M5 | Findings | Hand-written findings with basis and uncertainty; quote verification passing |
| M6 | Submission | README · architecture doc · two Looms · public repo |

**[R3] Two working sessions, not one.** The brief's "up to 6 hours" does not fit account
setup, implementation, twelve calls, listening, reproduction, documentation and two
videos. Session two is reserved for reproductions and submission review. If time runs
short, cut the automated judge and the HTML report — never the listening time.

## Submission gates

1. **Ten complete, playable transcript–recording pairs** — pairs, not a count of call
   records **[R3]**
2. Every quote in BUGS.md verified byte-exact against a raw transcript
3. Varied realistic scenarios; internal stretch target: ≥8 kinds, ≥1 safety, ≥1 privacy
4. Fixture tests passing: evidence validation · transcript reconciliation · termination
   behavior · prompt does not leak traps **[R3]**
5. `.env` absent from `git log -p`; `uv.lock` committed
6. Repo public in an incognito window; both Looms play logged out
7. The one DID, in E.164, on the submission form

## Standing constraint

**Only ever dial +1-805-439-8008.** Enforced in `src/caller/config.py`, which raises
`NotPermittedError` rather than trusting an environment variable. Never the number shown
on the athena confirmation screen. Do not contact anyone at the company about the
assessment.
