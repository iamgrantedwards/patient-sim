# Debugging journal

Starting record written **2026-09-19**, after the first two attempts. Earlier sections
below describe that historical state, not the current checkout. Reconciled 2026-09-20
UTC in #77; original observations and failing results remain intact.

## Current resolution and remaining limits

- Callback defect #21: fixed in #28 and verified on a later completed live call.
- Child-failure reporting/repeated initialization #46: fixed in #58, regression/CI
  verified, then retested on connected calls; issue closed during #75 reconciliation.
- The initiating native SIGSEGV and historical reassignment mechanism remain unknown.
  Containment/diagnostics are implemented; no native-library cure is claimed.
- The debugging recording is complete per Grant and [linked here](https://www.loom.com/share/648e67f4f08d4d75af16477e1995304e).
  Logged-out playback/content verification remains #25; do not repeat the staged outline.
- Ten later candidate pairs are captured; [COLLECTION.md](COLLECTION.md) gives actual
  IDs. Natural-ending listening #12 and suitability/publication #18 remain open.

See the dated post-fix outcomes at the end, [EVALUATION.md](EVALUATION.md) for AI review
limits, and [SUBMISSION.md](SUBMISSION.md) for the current finishing order.

## Historical starting point — first two attempts

| Attempt | Code revision at the call | Observed result | Evidence and review |
| --- | --- | --- | --- |
| [First call](https://github.com/iamgrantedwards/patient-sim/issues/21): `call-20260918-231955-765427d8` | `b1a6cda329665c4f595509a82ca9fa8e0d011e24a` (clean) | Conversation captured; callback error; remote hangup during the patient's follow-up. | 70.29-second stereo OGG, seven committed turns including partial final speech. Decoding passed; human listening review pending. |
| [Second attempt](https://github.com/iamgrantedwards/patient-sim/issues/46): `call-20260919-194206-bc3ae8e3` | `d0ecd5b477ff31bc8dcad8275b12433381ccf48e` (clean) | Child worker exited `-11`; a subsequent initialization hit `FileExistsError`; UI remained Dialing until Stop call. | Metadata and one non-dialogue journal event; no finalized recording/transcript. Controller confirmed cleanup; a separate Cloud query found zero active rooms. |

Both used Office information (`smoke`). At this checkpoint, two attempts were visible;
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

**Remaining at this checkpoint:** call two saved an `agent_handoff` without the original callback
exception, but did not finish a conversation. #21 was therefore still open for full
live confirmation; it subsequently closed after the retest documented below. The first call's interrupted closing remains
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
regression, smallest justified fix and separately authorized live retest. **At this checkpoint, no fix
had been made.** [#24](https://github.com/iamgrantedwards/patient-sim/issues/24)
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

## Historical plan for the first debugging recording

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


## 2026-09-19 — issue #46 offline investigation checkpoint

This checkpoint changes tests and documentation only. No new call was placed, no
worker was restarted, no dependency was changed, and original call artifacts were
not edited. It is a before-fix investigation, not a completed remediation.

### Native crash: matching report found

The local macOS report `python3.12-2026-09-19-124216.ips` records a crash at
**2026-09-19 12:42:11.4483 -0700**, shortly after the second attempt started.
The crashing process is PID **20955**; its parent is PID **20951**, matching the
second attempt's private worker-registration receipt.

The report identifies `EXC_BAD_ACCESS`, `SIGSEGV`, and
`KERN_INVALID_ADDRESS at 0x0000000000000000`. The first nine frames of the faulting
thread are in `liblivekit_ffi.dylib`; the named boundary is `livekit_ffi_request`,
followed by Python ctypes frames. The environment has `livekit==1.1.18` and
`livekit-agents==1.8.2`.

This narrows the failure to a native LiveKit FFI call with an invalid address. It
does **not** identify the originating Python operation, prove an upstream library
bug, or establish a safe dependency change. Most native frames are unsymbolicated.
The private report is retained locally, not published with its machine details.
Its SHA-256 is `dff57d0c4dd38a222f3de9d0085eb87b3b3fb10da5a65a2ecd3b6a0f155047aa`.

### Later initialization: protection works; assignment cause remains unknown

`test_repeated_call_identity_preserves_evidence_and_never_redials` seeds a fixture
call directory with an existing journal, metadata, and partial-audio placeholder.
It invokes the real agent entrypoint with the same call identity. The result is
`FileExistsError` / errno 17 before session connection, session start, or any SIP
request. All seeded files remain byte-identical, with no extra files.

The exclusive-create guard is doing useful work and should remain. This test
reproduces the duplicate-identity boundary, not the historical server reassignment.
The pinned SDK's default request handler accepts offered jobs, and its process pool
reports failed jobs back to Cloud. Neither fact proves the precise reason for the
later job assignment seen in the original log. That log lacks timestamps, job IDs,
and dispatch IDs needed to settle this. The managed entrypoint calls `server.run`
directly without configuring the CLI's structured logging. Recording assignment
identity and lifecycle events is a justified follow-up; automatic redial is not.

### Stale Dialing: reproduced offline

The regression runs the real managed-worker wrapper, `CallManager`, and
`LiveBackend.exited`, with provider operations and the OS process boundary replaced
by offline fixtures. It exercises the pinned SDK's real failed-job status mapping
and delivers its `process_closed` notification to the server's process pool. The
parent remains running. No actual segmentation fault is induced.

After a two-second offline observation window, well before the controller's
330-second fixture deadline, the expected failed state is absent:

```text
SDK emitted process_closed / JS_FAILED, but the local controller reports
'dialing'; parent returncode=None, cleanup_confirmed=False
```

The browser renders `operation.phase` from the controller; `dialing` maps directly
to the Dialing label. This is a missing failure signal in orchestration, not evidence
of a browser rendering failure. Existing controller checks notice parent exit or
finalized metadata, but the native child crash supplies neither.

Reproduce the before-fix result only in an isolated checkout of the preserved
regression checkpoint `5a5ecb4`, not current main:

```sh
uv run pytest tests/test_child_failure_regression.py tests/test_worker_failures.py \
  -q --runxfail --tb=short
```

Result: **1 failed, 13 passed**. The failure is the missing failed-state transition.
The default suite keeps that one assertion as a **strict expected failure** linked
to #46. Only its dedicated exception type is allowed to xfail; unexpected setup or
other assertion failures remain failures. An unexpected pass fails CI so the marker
must be removed when the fix lands. A green suite with this marker does not mean
#46 is fixed.

### Next decision

Add an explicit child-failure signal to the managed controller and route it through
existing cleanup/recovery handling. Retain exclusive evidence creation and record
job/dispatch identity so repeated assignment can be explained. A pinned-SDK process
lifecycle adapter is one candidate; its private API dependency needs explicit tests.
Do not guess a dependency upgrade from the native stack alone.

The follow-up must cover failure delivery, cleanup uncertainty, duplicate assignment,
normal completion, and removal of this expected-failure marker. A separately
authorized live call is still required. Native crash resolution remains distinct
from detecting it correctly.


## 2026-09-19 — targeted fixes after the before-fix checkpoint

The previous checkpoint remains above as the historical failing result. The strict
xfail has now been removed; the controller regression passes as a normal test.

### Child failure reporting and cleanup

The managed server subscribes to `process_closed` after `worker_started`, when the
pinned SDK pool exists and before job dispatch runs. A failed child writes a
separate `.runtime/<call-id>-failure.json` receipt with call identity, parent/child
PIDs, job ID, exit code, and observation time. The receipt includes the existing
worker nonce; the controller accepts only the current call/nonce/parent combination
and never returns the nonce to the browser. The dedicated server stops accepting
work and drains after a failure. Clean child exits do not generate failure receipts.

The controller checks this signal before interpreting stale call metadata. It
records `worker_child_exit` and routes through the existing room deletion, process
shutdown, and room-absence verification. Successful cleanup produces Failed;
unsuccessful cleanup produces Recovery required and blocks a new start. Original
call metadata and event files are untouched. The regression verifies these outcomes,
exit -11 provenance, one dispatch, and the absence of a redial.

This adapter uses a private SDK pool event because AgentServer 1.8.2 exposes no
public child-exit event. Tests bind that assumption to the pinned SDK. Dependency
updates must review this integration. This is a worker-failure handling fix, not a
repair to LiveKit's native memory access.

### Repeated assignment

A public `on_request` callback admits only one matching job for each managed worker.
The slot is consumed before awaiting acceptance, so concurrent offers and uncertain
acceptance cannot start another job. Mismatched room/call identities and existing
evidence are rejected. Exclusive journal creation remains as a second protection.

A private `.runtime/<call-id>-jobs.jsonl` journal records time, job ID, dispatch ID,
room, and admission decision; it does not serialize complete requests or credentials.
If the journal cannot be written, the job is rejected. This prevents repeated
initialization; it does not retroactively prove the historical reassignment cause.

### Native crash investigation and diagnostics

The installed arm64 library UUID matches the crash report. `atos` still resolves
most faulting frames only to offsets, so the originating Python operation remains
unknown. No dependency or model configuration was changed on that evidence.

Ran the opt-in local native probe in five isolated Python processes:

```sh
uv run python -X faulthandler scripts/probe-native-audio.py
```

Each process completed 20 audio source/track/stream, resampling, capture/read, and
teardown cycles and exited 0: **100 cycles total** with `livekit==1.1.18`.
The probe opens no Cloud room and makes no SIP or inference requests. It does not
exercise remote media, call recording, or the full agent session. Consequently,
this failed to reproduce the original crash and does **not** prove it is fixed.

New managed workers inherit `PYTHONFAULTHANDLER=1` so a future native failure can
include Python stacks in the private worker log. Their entrypoint now enables the
SDK's structured INFO logging, retaining timestamps and job/process fields that the
original warning-only log omitted. These are diagnostics, not crash prevention.

A separately authorized call remains the next end-to-end check after code review.
If it crashes, correlate the failure receipt, assignment journal, fault-handler
stack, and native report before selecting a dependency change or upstream reproducer.


Validation after the unassigned-process edge-case guard: **248 Python tests passed,
no xfails**, 96.1% branch-inclusive coverage, and lint/types passed. The full local
protocol also passed 60 browser/accessibility tests, secret/dependency checks, and
package build/install verification before that final Python-only guard; affected
Python coverage and type checks were rerun afterward. Hosted CI validates the final
pushed revision independently. No live conversation was used as verification.


## 2026-09-20 UTC — post-fix calls and closeout reconciliation

- PR #58 merged after all required checks passed. It removed the strict xfail and
  delivered child-failure receipts, cleanup propagation and single-job admission.
- `call-20260920-011336-9e2e5e9b` connected, then received an operator stop. The
  12.26-second recording decoded and cleanup was confirmed. It is not a full
  regression conversation and is excluded from the ten candidates.
- `call-20260920-011456-fe6d34a0` completed eight turns, finalized decoded audio and
  ended via `end_call_tool`, without the original callback/duplicate-init errors.
  The patient declined offered demo onboarding; this led to #59 / PR #60, not an
  office-agent finding. The next smoke call `call-20260920-011714-108d161e` accepted
  onboarding and captured hours/location/insurance guidance.
- PR #61 added an actual killed-process journal-recovery check. PR #63 corrected
  acceptance of offered transfers after `call-20260920-012849-8a9bc2d4`; the later
  refill retest declined the transfer. See BUGS.md and COLLECTION.md for evidence.
- During #75 closeout, #46 was closed on its scoped fix/retest evidence. The native
  failure remains an unresolved limitation. The original ending in #12, Cloud/local
  duration discrepancy, and end-to-end human acceptance have not been resolved by CI.

If the child crashes again, preserve `.runtime/<call-id>-failure.json`,
`.runtime/<call-id>-jobs.jsonl`, the worker log/fault-handler stack and the matching
macOS native report. Correlate call/job/PID/nonce and event order; verify cleanup before
starting another explicit call. Reproduce narrowly before changing dependencies.
Do not remove the existing journal, silently append a new attempt or automatically redial.


## 2026-09-20 UTC — ending audit and assessment coverage (#85, related #12)

Recent calls with suspected cutoffs record `ended_by=end_call_tool`, no failsafe
reason and no provider duration-limit indicator. For example,
`call-20260920-034355-fa5b226a` lasted about 93 seconds and
`call-20260920-043854-fd9ce1a5` about 142 seconds, both below the 240-second bound.
Their final committed remote transcript turns trail off. A committed/completed STT
item is not evidence that a sentence or its audible playback finished. Audio confirmation
and a focused ending retest remain necessary; this is not yet a confirmed causal diagnosis.

Source inspection: our end-tool callback sets termination metadata, not final ended
status. The controller waits through finalization, so it is not proven to delete the
room immediately upon seeing that callback. LiveKit Agents 1.8.2's EndCallTool waits
for the current patient speech handle and then shuts down the session; it does not
explicitly wait for another remote closing turn. A premature tool decision is a
plausible cause to test. Do not remove the duration bound to address this evidence.

The v2 assessment now checks final turns with this metadata and distinguishes our
caller behavior from office-agent quality. No hangup behavior is changed and #12
remains open. Offline checks validate schema/citations and incomplete-ending rejection;
they cannot establish an audible fix.


## Application freeze — 2026-09-20 UTC (#90)

Grant closed development scope after the UI, assessment and local-access corrections.
The debug video is already recorded; historical speaking notes remain historical. No
prompt/model experiment is planned. Grant later specified one final presentation call
before publishing all records. The native SIGSEGV cause and audible
ending diagnosis remain limitations, not silently completed fixes. #87/#88 improve
review coverage, visibility and browser access; they do not fix premature hangup.

## 2026-09-20 — pending remote speech at caller hangup (#92)

Grant reopened caller behavior work narrowly after reviewing cut-off endings. This is
separate from the original remote hangup in #12 and the earlier native worker crash.
The replacement debugging recording covers this current investigation, not a replay
of the already-fixed worker failure handling.

For `call-20260920-155843-a34fb22c` (Correction), the raw event receipt sequence is:

| Seconds from local initialization | Event |
| --- | --- |
| 142.375 | Final STT: “You're all set.” |
| 143.101 | New partial STT: “Your appointment” |
| 148.083 | The older “You're all set.” message commits |
| 149.150 | `end_call` tool execution reported |
| 150.168 | The next message commits, ending “…with doctor zed” |
| 150.228 | Session closes, `user_initiated`; metadata says `end_call_tool` |

These are event receipt times, **not audio offsets**. Grant's saved listening review
flags “fail, assessment agent is cut off.” No duration failsafe is recorded. The
sequence supports a caller-side protection gap, without proving every poor ending
has this cause or independently verifying word-level audio timing.

The installed LiveKit 1.8.2 end tool schedules session shutdown without checking for
new remote speech. Crucially, it registers its shutdown callback before invoking
`on_tool_called`, so rejecting inside that callback would be too late. An offline
regression invoking the real registered SDK tool with remote state `speaking` failed
before the change: the tool accepted the request instead of stopping it.

The correction guards entry to that same SDK tool. It rejects interrupted responses,
active remote speech, or uncommitted remote transcription; waits for the patient's
current playout plus a one-second closing-only pause; then checks again and cancels
if remote activity changed. An older committed turn cannot clear a newer partial.
The next incoming turn drives a fresh decision. There is no automatic hangup retry
and no spoken error over the remote agent. Accepted/deferred decisions and remote
speech-state changes are journaled; metadata records `closing_policy=pending-input-v1`.

Historical replay of available end-tool event records found pending input in 10 of
36 records at tool completion. In reviewed calls this included Correction,
Rescheduling and Proxy; none of the reviewed `ending=ok` calls had pending input
there. Insurance's missing-signoff concern did not match. This is a retrospective
state check, not 36 new calls or proof of causation. Timing limits and original files
remain unchanged. Prompt, STT, LLM, TTS and ordinary turn detection are unchanged.

Limits: the pause is an initial conservative value, not a measured optimum. Missing
or mismatched STT commits can conservatively defer an ending until another turn or
the existing failsafe. Speech starting after acceptance remains possible. This guard
does not establish whether a semantic outcome or goodbye is complete. Focused tests
cover the original ordering, clean closing, newer turns during playout/pause,
interruption, cancellation and real worker callback wiring. A follow-up real call
and listening confirmation remain required to claim audible improvement.
