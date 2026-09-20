# patient-sim

A Python patient simulator for a healthcare voice-agent assessment. It uses a LiveKit
Agents STT / LLM / TTS pipeline to call the designated test line and preserve recordings
and transcripts for manually verified findings.

**Submission package:** [ten human-reviewed conversations and the full call archive](calls/README.md),
[findings and iteration](BUGS.md), and [architecture](ARCHITECTURE.md).
The archive contains **47 records and 46 original recordings/transcripts**. The primary
ten cover all ten scenarios; other attempts are retained as clearly labeled development
evidence. Human review notes include remaining quality concerns.

- [Application demo](https://www.loom.com/share/0db55c95dd894cd388593a33c5d9a2b1)
- [AI-assisted debugging](https://www.loom.com/share/12245c3a689549f69ff08590087fc83e)
- Caller number: **+19062567632**

Both final Loom links are publicly reachable. The walkthrough is **2:59** and the
debugging recording is **3:46**. [Submission checklist](docs/SUBMISSION.md) contains
the handoff fields and remaining human playback/form confirmation.
Application development is frozen after the verified ending guard in PR #93.
The initiating cause of the earlier native worker crash remains unresolved.

## Review recordings locally

```sh
uv sync --locked
uv run python -m src.review
```

Open **http://127.0.0.1:8765**. The read-only interface shows the actual local `calls/`
folders, original audio, raw transcript, partial speech, recorded pipeline provenance,
and the current controls and data handling. It needs no provider credentials and cannot place calls.
Use `--calls-dir /path/to/calls` for another evidence directory or `--port 8767` for a
free local port. Node.js is only required for UI development checks, not to run the viewer.
Missing recordings and unknown review/timing/state remain explicit. Opening or playing
an artifact never marks it human-reviewed. Original call evidence stays unchanged.

Calls open in a horizontal card rail. Use the Cards/List icons to switch to full-width rows in
the same area; your choice stays in this browser. The magnifying glass beside the call count opens search
and filters. Select a card or list entry to open its evidence. Cards show the current
AI score or assessment status and a separate human-review indicator. Scores marked
**prior** are historical; **Notes saved** does not mean listening was confirmed.
**Human reviewed** and **Usable** are separate judgments.

For each attempt, follow the [call-review workflow](docs/CALL-REVIEW.md) and use its
[review sheet](docs/CALL-REVIEW-TEMPLATE.md) to record listening observations and next actions.
To save reviews, start with `uv run python -m src.review --enable-reviews`.
Open **Review** beside a call's recording. Save an outcome and any useful notes.
The detailed checklist is optional; the UI's **Usable** outcome requires listening
confirmation and **Complete evidence: OK**. Other checks can remain not assessed.
**Add AI summary** inserts an existing assessment as labeled draft notes, without
marking anything listened to or approved. Add `--enable-calls`
only when you also want call controls. Review saving needs no provider credentials.

Reviews persist in `calls/<call-id>/review.json` with dated revisions and SHA-256
fingerprints of the original evidence. Changed evidence requires a recheck. Legacy
metadata listening flags remain provenance; they do not count as current reviewed or
usable conversations. Manual `review.md` sheets are optional and are not imported.
Review files stay local/ignored with the call until deliberately published.

Use the light bulb for optional hover, focus or tap explanations. The book icon beside
it opens a short guide with the call/review flow and recovery help. These controls
work locally without changing calls or evidence.

## Run the caller locally

Requires Python 3.12, [uv](https://docs.astral.sh/uv/), and `ffmpeg`/`ffprobe` on PATH.
Start with the [personal account setup](docs/SETUP.md).

```sh
uv sync --locked
uv run pytest
uv run python -m src.caller.dial --scenario smoke --dry-run
```

Dry runs need no credentials, do not connect to providers, and place no call.
After filling the ignored `.env`, enable the local call console:

```sh
uv run python -m src.review --enable-calls --enable-reviews
```

Open **http://127.0.0.1:8765**. Choose a scenario, select **Review & call**, and confirm
one call in the dialog. The console starts a dedicated worker, waits for LiveKit to
acknowledge registration, and only then dispatches that call. Live status and committed
dialogue appear in the console. Live transcript opens for a new call, shows connection/
waiting progress, follows new turns unless you scroll back, and closes when the call
ends. You can collapse it manually. **Stop call** requests termination and preserves the
available evidence; it is recorded as an operator stop, not a natural ending.

For an explicit call without the UI, the CLI manages the same dedicated worker:

```sh
uv run python -m src.caller.dial --scenario smoke --call
```

UI and CLI share an OS call lock in ignored `.runtime/`. Refresh and reconnection never
place calls. A saved unresolved operation blocks another call until **Stop / recover**
confirms the worker has stopped and the room is absent. Do not delete recovery files to
bypass the lock. Ctrl-C closes an active console/CLI call; recordings can be incomplete
if interrupted. See [call operations and recovery](docs/OPERATIONS.md).

The console includes office information, scheduling, rescheduling, cancellation, refill,
missing refill information, insurance, availability correction, unclear requests and
third-party workflow questions. Each scenario has a versioned objective; unknown
patient facts and unverified prior bookings are never supplied as facts.
There is no initial caller greeting or automatic redial. Provider/model settings remain
fixed; the managed worker requires this same checkout and Python environment.

## Automated checks and builds

GitHub Actions checks formatting/lint, types, workflows, shell scripts, secrets, and
locked dependencies. Biome checks the UI; Playwright and axe test responsive layouts,
keyboard access, audio seeking, and failure states in Chromium and WebKit. Network-isolated Python tests enforce a 90% coverage floor with branch
measurement enabled. Passing every check permits package builds and CLI smoke tests. Successful runs
provide downloadable packages with commit provenance and checksums. Run the same checks
locally with `./scripts/verify.sh`; see [CI and artifact delivery](docs/CI.md).

Cloud deployment is not required. CI delivers verified code packages; it does not
publish local call files or approve their voice quality. Evidence and final public links
are tracked separately in the submission checklist.

## Evidence

During collection, each call uses `calls/<call-id>/` with `meta.json`, incremental
`events.jsonl`, readable `transcript.txt`, `transcript.json`, and `recording.ogg` when
the SDK recording is available. Shutdown preserves the local SDK audio and checks its
container and complete decoding. A successful decode does not mean anyone listened.

Incremental journals remain on the collection machine and are not in the public archive.
Only committed conversation items become dialogue turns;
unfinished STT remains explicitly separate. For a local collection that retains its event journal, recover after a crash:

```sh
uv run python -m src.caller.transcript calls/<call-id>
```

Audio-derived timing is pending: delay and overlap fields are `null`, never filled from
callback arrival times. Claimed state, consistency, and verified state remain separate.
Controlled interruption and audio-aligned latency measurement remain untested. Credentials and newly collected call artifacts remain ignored by default. This delivery
explicitly includes the reviewed publication files listed in calls/manifest.json.

## Design and progress

- [Cloud session verification and screenshot](src/review/evidence/call-20260918-231955-765427d8/verification.md)
- [AI governance, control evidence, and open obligations](docs/AI-GOVERNANCE.md)
- [Current submission checklist](docs/SUBMISSION.md)
- [Historical recording preparation](docs/MORNING.md)
- [Build order, GitHub issues, and PR workflow](docs/ROADMAP.md)
- [Assessment compliance and remaining deliverables](docs/ASSESSMENT.md)
- [How strategy, AI assessment and listening fit together](docs/EVALUATION.md)
- [Implementation contract](docs/CONTRACT.md)
- [Debugging history, fixes and retests](docs/DEBUGGING.md)
- [Build notebook](docs/NOTEBOOK.md)
- [Architecture](ARCHITECTURE.md)

The local console, assessments, human reviews and failure-handling fixes are merged.
Grant completed the recordings and saved the final reviews. Both video links appear
above; [the findings report](BUGS.md) preserves concrete observations and uncertainty.
Configuration comparison and audio-aligned latency measurement were not performed.
Submit through the team's required form, not a direct assessment email.

## Personal GitHub account

```sh
./scripts/gh-personal auth status
./scripts/bootstrap-github.sh
```

The account helper isolates this project's CLI credentials. The bootstrap verifies the
account and skips existing issue/milestone titles. Git uses a repository-local credential
helper and noreply commit email.

The [ten-call test strategy](docs/TEST-STRATEGY.md) defines planned scenario coverage,
review checkpoints and how evidence leads to a fix or finding. The implementation now exposes the scenarios; actual captured and reviewed counts
are tracked separately in the collection results. The strategy is a human planning
document; the AI judge uses its own code-defined rubric. [EVALUATION.md](docs/EVALUATION.md)
maps their overlap, actual inputs and the criteria that still require listening.

### AI transcript assessments

Start with `uv run python -m src.review --enable-reviews --enable-assessments`
(add `--enable-calls` only when you also want outbound controls). Open **AI assessment**
in a call's details and choose **Assess transcript**. This sends the saved transcript,
scenario ID and capture/termination metadata to LiveKit Inference using the existing local credentials; `JUDGE_MODEL=gpt-4.1` selects
`openai/gpt-4.1`, separately from the caller's model. Each explicit assessment uses
account credits. Identical evidence/model/rubric results are reused, not regenerated.

Five text-only dimensions use anchored 0/1/2 grades or not-assessable. The provisional
0–100 aggregate is calculated from assessed dimensions and withheld below 3/5 coverage.
It is not a success probability or a benchmark. Exact quote validation rejects unsupported
references but cannot establish that STT heard correctly. Follow-up suggestions never
change prompts or start calls. Results do not confirm backend state or audio quality.

A separate **Call quality** checklist covers all seven review topics: local capture
checks, AI text checks for patient behavior, turn-taking and ending, and explicit
Needs listening states for transcription accuracy, pacing and audio clarity. Ending
opens expanded with termination context; caller hangup is never treated as proof of
a clean farewell. These checks do not alter the office-agent score or human review.

`calls/<call-id>/assessment.json` holds up to ten revisions with the input fingerprints,
model, prompt hash, rubric version and generation time. Changed evidence/settings make
old results stale. The card may show their score labeled **prior**; the detail panel
withholds a current aggregate until explicit reassessment. Raw artifacts and `review.json` remain unchanged. Saved results included in this delivery were explicitly reviewed for publication;
newly generated local files remain ignored by default. Compare judge observations with
your listening review; this small, uncalibrated grader does not replace that acceptance.
