# Debugging journal

Starting record written **2026-09-19**, after the first two attempts. This is a
retrospective based on preserved artifacts and issue history. The debugging video
has not been recorded. Future entries should record the work when it happens.

## The starting point

| Attempt | Code revision at the call | Observed result | Evidence and review |
| --- | --- | --- | --- |
| [First call](https://github.com/iamgrantedwards/patient-sim/issues/21): `call-20260918-231955-765427d8` | `b1a6cda329665c4f595509a82ca9fa8e0d011e24a` (clean) | Conversation captured; callback error; remote hangup during the patient's follow-up. | 70.29-second stereo OGG, seven committed turns including partial final speech. Decoding passed; human listening review pending. |
| [Second attempt](https://github.com/iamgrantedwards/patient-sim/issues/46): `call-20260919-194206-bc3ae8e3` | `d0ecd5b477ff31bc8dcad8275b12433381ccf48e` (clean) | Child worker exited `-11`; a subsequent initialization hit `FileExistsError`; UI remained Dialing until Stop call. | Metadata and one non-dialogue journal event; no finalized recording/transcript. Controller confirmed cleanup; a separate Cloud query found zero active rooms. |

Both used Office information (`smoke`). Two attempts are visible in the console;
only one has an audio/transcript pair, and neither has a recorded human listening
review. **Neither establishes the first-good-call acceptance gate.** No defect in
the remote assessment agent has been confirmed.

## What the first call taught us

**Observed:** the SDK emitted an `AgentHandoff` through `conversation_item_added`.
Our callback accessed its nonexistent `role` property. The raw event was preserved;
the call continued and recorded dialogue. This was our event-handler defect, not a
whole-call crash. See [#21](https://github.com/iamgrantedwards/patient-sim/issues/21).

**Changed before filming:** [PR #28](https://github.com/iamgrantedwards/patient-sim/pull/28)
added pinned-SDK regressions, kept non-message events in the journal, and counted
only unique dialogue items toward the turn limit. Offline and hosted checks passed.
Do not present this completed fix as a new discovery on video.

**Remaining:** call two saved an `agent_handoff` without the original callback
exception, but did not finish a conversation. #21 therefore remains open for full
live confirmation. The first call's interrupted closing remains
[#12](https://github.com/iamgrantedwards/patient-sim/issues/12); listen before assigning
cause or claiming a fix.

The first call's [Cloud snapshot and verification note](../src/review/evidence/call-20260918-231955-765427d8/verification.md)
confirm a matching Cloud session. They do not establish audio quality. The Cloud
player timeline (97.06 seconds) and local recording duration (70.29 seconds) have
not been reconciled.

## What failed on the second attempt

**Observed sequence:** one explicit UI confirmation started one operation. Status
progressed to Dialing, with zero committed dialogue. The private worker log contains
these messages in this order, with unrelated lines omitted and the local path shortened:

```text
no warmed process available for job, waiting for one to be created
process exited with non-zero exit code -11
no warmed process available for job, waiting for one to be created
unhandled exception while running the job task
FileExistsError: .../calls/call-20260919-194206-bc3ae8e3/events.jsonl
```

`CallArtifacts` opens `events.jsonl` exclusively to protect original evidence. The
existing journal contains one agent-handoff event. The supervising worker process
remained alive after its child failed. The operator selected **Stop call** once.
The controller then reported `operator_stop`, `cleanup_confirmed: true`, and
`evidence_status: partial_or_unavailable`.

Original `meta.json` still says `worker_started`, SIP `dialing`, with no ending.
That explains the difference between the attempt's saved metadata and the top
operation status. Cleanup establishes termination, not a successful conversation.
An answered call has not been established; this does not prove no SIP request was sent.

| Question | Current evidence | Next investigation |
| --- | --- | --- |
| Why did the child exit `-11`? | The process exit is recorded; its cause is unknown. | Inspect the earliest worker/native diagnostics and the pinned SDK job lifecycle. |
| Why was the same call initialized again? | Exclusive journal creation failed after the child exit. Reassignment/retry is a hypothesis. | Trace job identities and dispatch behavior before changing initialization. |
| Why did Dialing remain visible? | The parent stayed alive while the child failed. Pre-recording code inspection confirmed that the controller exit check watches that parent, not the child job. | Reproduce the missing failure propagation offline; determine a reliable job-failure signal and verify cleanup. |
| How can evidence stay safe? | The exclusive-create failure preserved the existing journal. | Test repeated identities without overwriting evidence or dialing twice; do not merely switch to append mode. |

[#46](https://github.com/iamgrantedwards/patient-sim/issues/46) owns this investigation,
regression, smallest justified fix and separately authorized live retest. **No fix
has been made yet.** [#24](https://github.com/iamgrantedwards/patient-sim/issues/24)
remains blocked on this failure and a complete, listened-to UI call.

## Pre-recording clarification — 2026-09-19

These observations came from reading the code and preserved log with Grant before
recording. They must be introduced as prior preparation, not discoveries made on camera.
No caller code was changed, no failure regression was run, and no new call was placed.

A worker is a running program, not a generated file. Our execution hierarchy is:

```text
Local application server / call controller
  -> managed agent server process
       -> LiveKit child call-job process running our patient code
```

All three run on the Mac in this implementation. The managed agent server registers
with LiveKit Cloud; explicit dispatch assigns a job; the installed LiveKit Agents
1.8.2 framework starts the job process. Cloud rooms, telephony and Inference are remote
services. A Cloud session does not establish that our Python worker is hosted there.

| Code reference | Confirmed responsibility |
| --- | --- |
| [control.py](../src/caller/control.py), `CallManager.run()` | Polls saved call metadata, checks `backend.exited()`, and enforces a deadline. |
| [control_backend.py](../src/caller/control_backend.py), `LiveBackend.prepare()` | Launches `python -m src.caller.managed_worker`, passing the call identity and routing standard output/error to the local worker log. |
| [control_backend.py](../src/caller/control_backend.py), `LiveBackend.exited()` | Checks the managed process's `returncode`; it does not directly check the child call job. |
| [managed_worker.py](../src/caller/managed_worker.py), `run()` | Runs `AgentServer`, reports registration, watches its application parent and handles shutdown. |
| [agent.py](../src/caller/agent.py), `entrypoint()` | The SDK runs our patient pipeline, event capture and SIP request inside a call job. |

The inspected controller, backend and managed-worker files are unchanged between
call two's revision `d0ecd5b` and preparation baseline `bbdafcf`. The parent-only exit
check is therefore present in the code used for that attempt, not just the latest UI.
A surviving managed process is insufficient evidence that its conversation job is
healthy. Combined with unfinished metadata, this is a supported explanation for the
stale-status symptom; it still needs a focused regression and verified correction.
It does not explain the original `-11` crash or establish why initialization ran again.

The SDK is configured with `server.run(devmode=True)`. In the pinned SDK, development
mode defaults to zero idle job processes. The message about no warmed process is
therefore not, by itself, evidence of a fault. The non-zero process exit is the actual
failure evidence. Do not infer a crash cause from the warm-process message.

The reviewed log is `.runtime/call-20260919-194206-bc3ae8e3-worker.log`.
It records the `-11` exit before the later `FileExistsError` traceback. That traceback
locates exclusive journal creation in `CallArtifacts`; it does not locate the cause
of the earlier process crash. The log excerpt alone lacks enough process/job identity
and native diagnostics to settle that cause or the subsequent assignment mechanism.

For context, the call path is local job -> LiveKit room/telephony bridge -> configured
Twilio SIP trunk -> telephone network -> assessment line. SIP controls call setup and
ending; media travels separately. Our local job coordinates separate STT, LLM and TTS
services through LiveKit Inference. Nothing in the current evidence establishes that
Twilio, a model provider or the assessment agent caused the worker crash.

Next on camera: validate these observations, reproduce child-job failure with the
managed process still alive, trace repeated initialization, and choose the smallest
supported correction. Preserve existing evidence and prevent duplicate dialing.
If the native crash remains unexplained, report a containment/failure-reporting fix
as such, rather than claiming that the underlying crash is solved.

## Where the evidence lives

- `calls/<call-id>/`: original metadata, incremental journal, and audio/transcripts
  when finalized. A missing file is a result to document, not fill in.
- `.runtime/<call-id>-worker.log`: local worker diagnostics. Runtime state also
  records controller progress and cleanup, which can differ from unfinished metadata.
- This journal: a curated public account with call IDs, revisions and issue/PR links.
  It is not a replacement for the raw files or an export of chat/prompt history.

Raw calls, runtime logs and credentials remain ignored. Review content before
publishing any selected artifact; never paste credentials or unreviewed transcript
content into an issue or video. Keep original files unchanged and label derived notes.

## First debugging recording

Use the [copyable Loom speaking notes](DEBUGGING-SCRIPT.md). This is an outline for
real work, not a script with a predetermined successful ending.

1. Show the two attempts in the UI: one pair, one incomplete attempt, no completed
   listening reviews. Open #46 and state what is observed versus suspected.
2. With voice/webcam recording active, show the reviewed log and process map. State
   that the parent-only exit check was identified during preparation. Show the actual
   new prompts, responses and experiments. Explain that #21 was fixed earlier; do not
   reenact it or the pre-recording inspection as a new discovery.
3. Build the smallest offline regression for the demonstrated failure, show it fail,
   then implement and explain the correction. Preserve evidence and prevent redial.
4. Run the relevant checks, link the focused PR to #46, and append the results below.
   If diagnosis remains uncertain, record that honestly.
5. After separate authorization, make one live retest and compare its artifacts. Listen
   end to end before recording quality acceptance. An offline pass alone is not enough.

See [#25](https://github.com/iamgrantedwards/patient-sim/issues/25) for the debugging-video
deliverable and [the assessment checklist](ASSESSMENT.md) for final submission requirements.
The application itself stays focused on operating and reviewing calls.

## Entry format for the next fix

Copy this section only when there is actual work to record; leave unknowns explicit.

```markdown
### YYYY-MM-DD HH:MM TZ — short observation
- Issue / recording segment:
- Baseline call ID and code revision (clean/dirty):
- Observed behavior and exact evidence location:
- Expected behavior and why:
- Hypothesis (unproven until checked):
- Investigation result / remaining uncertainty:
- Change and PR / commit (or no change):
- Verification: failing regression before, result after, hosted checks:
- Live retest call ID / revision (or not performed):
- Human listening review and outcome (or pending):
- Next action / acceptance still open:
```
