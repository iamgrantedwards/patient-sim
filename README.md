# patient-sim

A Python patient simulator for a healthcare voice-agent assessment. It will call the
assessment test line using LiveKit Agents with separate STT, LLM, and TTS, and retain
recordings and transcripts for manually verified findings.

**Status:** initial scaffold. No real calls or findings yet. M1 requires one natural
conversation, a clean ending, and matching playable audio and transcript.

## Development

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```sh
uv sync --locked
uv run pytest
```

The [implementation contract](docs/CONTRACT.md) records design decisions and acceptance
criteria. The [notebook](docs/NOTEBOOK.md) records discoveries and limitations.
LiveKit Cloud and Twilio credentials are still needed before telephony verification.

## Personal GitHub account

This checkout uses `iamgrantedwards` and a separate GitHub CLI profile:

```sh
./scripts/gh-personal auth status
./scripts/bootstrap-github.sh
```

The bootstrap checks the account and skips existing issue and milestone titles.
Credentials and raw call artifacts are ignored by Git; recordings will be reviewed
before explicit inclusion in the public submission.
