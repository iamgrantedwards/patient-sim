"""Serve generated test evidence only; never touch a developer's calls or credentials."""

import json
import subprocess
import tempfile
from pathlib import Path

import uvicorn

from src.review.server import create_app


def build_fixtures(root: Path):
    for suffix, scenario in (("03", "smoke"), ("02", "reschedule"), ("01", "missing_recording")):
        call = root / f"call-fixture-{suffix}"
        call.mkdir()
        meta = {
            "call_id": call.name,
            "scenario_id": scenario,
            "started_at": 1e200 if suffix == "02" else 1789770000,
            "status": "ended",
            "ended_by": "remote_hangup" if suffix == "03" else "end_call_tool",
            "git_revision": "fixture-revision-only",
            "git_dirty": False,
            "pipeline": {"stt": "fixture-stt", "llm": "fixture-llm", "tts": "fixture-tts"},
            "recording": {
                "listened_by_human": suffix == "02",
                "probe": {"format": {"duration": "3"}},
            },
        }
        transcript = {
            "call_id": call.name,
            "turns": [
                {
                    "idx": 0,
                    "role": "remote",
                    "status": "completed",
                    "text": 'Synthetic fixture: <img src=x onerror="alert(1)">',
                    "audio_start_ms": 500 if suffix == "02" else None,
                },
                {
                    "idx": 1,
                    "role": "patient",
                    "text": "Synthetic patient fixture.",
                    "status": "partial" if suffix == "03" else "completed",
                },
            ],
        }
        (call / "meta.json").write_text(json.dumps(meta))
        (call / "transcript.json").write_text(json.dumps(transcript))
        if suffix != "01":
            subprocess.run(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "sine=frequency=440:duration=3",
                    "-ar",
                    "48000",
                    "-ac",
                    "2",
                    str(call / "recording.mp3"),
                ],
                check=True,
            )
    broken = root / "call-fixture-00"
    broken.mkdir()
    (broken / "meta.json").write_text("{broken")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="patient-review-browser-") as directory:
        root = Path(directory)
        build_fixtures(root)
        uvicorn.run(create_app(root), host="127.0.0.1", port=8766, access_log=False)
