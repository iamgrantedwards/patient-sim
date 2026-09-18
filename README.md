# patient-sim

A Python patient simulator for a healthcare voice-agent assessment. It uses a LiveKit
Agents STT / LLM / TTS pipeline to call the designated test line and preserve recordings
and transcripts for manually verified findings.

**Status:** first-call implementation under local verification. No real calls or findings
yet. M1 remains open until a natural conversation ends cleanly and its recording has
been listened to alongside its transcript. LiveKit Cloud and Twilio setup is pending.

## Run locally

Requires Python 3.12, [uv](https://docs.astral.sh/uv/), and `ffmpeg`/`ffprobe` on PATH.
Start with the [personal account setup](docs/SETUP.md).

```sh
uv sync --locked
uv run pytest
uv run python -m src.caller.dial --scenario smoke --dry-run
```

Dry runs need no credentials, do not connect to providers, and place no call.
After filling the ignored `.env`, run the worker in one terminal:

```sh
uv run python -m src.caller.agent download-files
uv run python -m src.caller.agent dev
```

In a second terminal, explicitly place one call:

```sh
uv run python -m src.caller.dial --scenario smoke --call
```

The local dispatcher and worker must use this same checkout. The worker prepares audio
and recording, then dials the sole allowlisted destination. The scenario asks about
office information without changing appointments. There is no initial caller greeting
or automatic redial. Stop the worker with Ctrl-C after the session has finalized.

## Evidence

Each call uses `calls/<call-id>/` with dispatch status, `meta.json`, incremental
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

- [Implementation contract](docs/CONTRACT.md)
- [Build notebook](docs/NOTEBOOK.md)
- [Architecture](ARCHITECTURE.md)

The first milestone is one good recorded call. Calibration, broader scenario collection,
findings, and submission videos follow it. There are no confirmed bugs yet.

## Personal GitHub account

```sh
./scripts/gh-personal auth status
./scripts/bootstrap-github.sh
```

The account helper isolates this project's CLI credentials. The bootstrap verifies the
account and skips existing issue/milestone titles. Git uses a repository-local credential
helper and noreply commit email.
