# patient-sim

A Python patient simulator for a healthcare voice-agent assessment. It uses a LiveKit
Agents STT / LLM / TTS pipeline to call the designated test line and preserve recordings
and transcripts for manually verified findings.

**Status:** ten candidate audio/transcript pairs are captured across office information,
appointments, refills and edge cases (20.59 minutes). Original recordings decode; human
listening acceptance is still pending. Caller recovery and scenario fixes are merged.
Start with the [submission checklist](docs/SUBMISSION.md), [collection results](docs/COLLECTION.md),
and [findings and iteration](BUGS.md).
The native crash's root cause remains unresolved. Candidate files remain local until
reviewed for publication.

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
and filters. Select a card or list entry to open its evidence.

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
dialogue appear in the console. **Stop call** requests termination and preserves the
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

Cloud deployment is not required. Delivery currently means a verified package; call controls
and the first-good-call milestone remain separate acceptance gates.

## Evidence

Each call uses `calls/<call-id>/` with `meta.json`, incremental
`events.jsonl`, readable `transcript.txt`, `transcript.json`, and `recording.ogg` when
the SDK recording is available. Shutdown preserves the local SDK audio and checks its
container and complete decoding. A successful decode does not mean anyone listened.

Raw STT events are retained. Only committed conversation items become dialogue turns;
unfinished STT remains explicitly separate. To recover after a crash:

```sh
uv run python -m src.caller.transcript calls/<call-id>
```

Audio-derived timing is pending: delay and overlap fields are `null`, never filled from
callback arrival times. Claimed state, consistency, and verified state remain separate.
Controlled interruption and audio-aligned latency measurement remain untested. Credentials and raw call artifacts are ignored; review recordings before
explicitly adding selected submission evidence to the public repository.

## Design and progress

- [Cloud session verification and screenshot](src/review/evidence/call-20260918-231955-765427d8/verification.md)
- [AI governance, control evidence, and open obligations](docs/AI-GOVERNANCE.md)
- [Current submission checklist](docs/SUBMISSION.md)
- [Earlier recording preparation](docs/MORNING.md)
- [Build order, GitHub issues, and PR workflow](docs/ROADMAP.md)
- [Assessment compliance and remaining deliverables](docs/ASSESSMENT.md)
- [How strategy, AI assessment and listening fit together](docs/EVALUATION.md)
- [Implementation contract](docs/CONTRACT.md)
- [Debugging history, fixes and retests](docs/DEBUGGING.md)
- [Build notebook](docs/NOTEBOOK.md)
- [Architecture](ARCHITECTURE.md)

The local review UI and opt-in controls are merged, and the callback defect has passed
live verification (#21). Child-failure handling is merged (#58); subsequent calls reached the end-call tool,
while natural endings still await listening review. The debugging video is recorded per Grant's report;
the [debug recording](https://www.loom.com/share/648e67f4f08d4d75af16477e1995304e)
is linked here, with logged-out playback/content verification still pending. The final
walkthrough and listening/publication review remain submission work.
The optional model-configuration comparison is deferred; no best-model claim is made.

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
old results stale. Raw artifacts and `review.json` remain unchanged. These local files
stay ignored until explicitly reviewed for publication. Compare judge observations with
your listening review; this small, uncalibrated grader does not replace that acceptance.
