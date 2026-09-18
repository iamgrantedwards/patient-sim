"""Preserve SDK audio before its temporary directory is removed."""

import json
import shutil
import subprocess
from pathlib import Path


def preserve_recording(source: Path | None, directory: Path) -> dict:
    if source is None or not source.is_file():
        return {"status": "missing"}
    destination = directory / "recording.ogg"
    shutil.copyfile(source, destination)
    # The pinned SDK writes OGG; check content and decode the entire stream, not its suffix.
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=format_name,duration:stream=codec_name,channels,sample_rate",
            "-of",
            "json",
            str(destination),
        ],
        capture_output=True,
        text=True,
        timeout=20,
        check=True,
    )
    info = json.loads(result.stdout)
    if "ogg" not in info.get("format", {}).get("format_name", "").split(","):
        raise ValueError("SDK recording is not an OGG container")
    if float(info.get("format", {}).get("duration", 0)) <= 0:
        raise ValueError("Recording has no positive duration")
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-xerror",
            "-i",
            str(destination),
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        timeout=30,
        check=True,
    )
    return {
        "status": "decoded",
        "file": destination.name,
        "probe": info,
        "listened_by_human": False,
    }
