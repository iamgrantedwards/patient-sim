import shutil
import subprocess

import pytest

from src.caller.recording import preserve_recording


def test_missing_recording_is_not_a_completed_pair(tmp_path):
    assert preserve_recording(None, tmp_path) == {"status": "missing"}


@pytest.mark.skipif(
    not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="ffmpeg required"
)
def test_preserved_ogg_decodes_and_is_not_claimed_as_listened(tmp_path):
    source = tmp_path / "source.ogg"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=0.15",
            "-ac",
            "2",
            str(source),
        ],
        check=True,
    )
    result = preserve_recording(source, tmp_path)
    assert result["status"] == "decoded"
    assert result["listened_by_human"] is False
    assert (tmp_path / "recording.ogg").read_bytes() == source.read_bytes()
