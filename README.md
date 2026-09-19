# patient-sim

A Python patient simulator for a healthcare voice-agent assessment. It uses a LiveKit
Agents STT / LLM / TTS pipeline to call the designated test line and preserve recordings
and transcripts for manually verified findings.

**Status:** the first live assessment call connected and saved a 70-second stereo OGG
recording with a transcript. Audio decoding passes; listening review is still pending.
The run exposed a non-dialogue event-handler error, and the remote agent hung up while
the patient began another question. M1 remains open until the caller ends naturally and
its recording has been listened to alongside its transcript.

## Review recordings locally

```sh
uv sync --locked
uv run python -m src.review
```

Open **http://127.0.0.1:8765**. The read-only interface shows the actual local `calls/`
folders, original audio, raw transcript, partial speech, recorded pipeline provenance,
and AI governance controls. It needs no provider credentials and cannot place calls.
Use `--calls-dir /path/to/calls` for another evidence directory or `--port 8767` for a
free local port. Node.js is only required for UI development checks, not to run the viewer.
Missing recordings and unknown review/timing/state remain explicit. Opening or playing
an artifact never marks it human-reviewed. Original call evidence stays unchanged.

Use the **Learn** light bulb for optional hover, focus or tap explanations. **Guide**
beside it opens a short manual with the call/review flow, testing steps and recovery
help. Both work locally without changing calls or evidence.

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
uv run python -m src.review --enable-calls
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

The first supported scenario asks about office information without changing appointments.
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
IVR/voicemail classification and the full scenario suite are also pending real-line
inspection. Credentials and raw call artifacts are ignored; review recordings before
explicitly adding selected submission evidence to the public repository.

## Design and progress

- [Cloud session verification and screenshot](src/review/evidence/call-20260918-231955-765427d8/verification.md)
- [AI governance, control evidence, and open obligations](docs/AI-GOVERNANCE.md)
- [Morning recording session and remaining gates](docs/MORNING.md)
- [Build order, GitHub issues, and PR workflow](docs/ROADMAP.md)
- [Assessment compliance and remaining deliverables](docs/ASSESSMENT.md)
- [Implementation contract](docs/CONTRACT.md)
- [Build notebook](docs/NOTEBOOK.md)
- [Architecture](ARCHITECTURE.md)

The local review UI (#23) and opt-in outbound controls (#24) are implemented on dependent
draft PRs. The controls still need a real UI call with human review. The first-good-call gate remains open;
calibration, broader call collection, findings, and the final walkthrough follow it.
The first run exposed a simulator event-handler bug (#21), now fixed with pinned-SDK
regression tests but awaiting live confirmation, and an unresolved closing issue (#12). No bug in the assessment agent has been confirmed.

## Personal GitHub account

```sh
./scripts/gh-personal auth status
./scripts/bootstrap-github.sh
```

The account helper isolates this project's CLI credentials. The bootstrap verifies the
account and skips existing issue/milestone titles. Git uses a repository-local credential
helper and noreply commit email.
