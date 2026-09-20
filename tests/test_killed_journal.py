import os
import select
import signal
import subprocess
import sys
from pathlib import Path

from src.caller.transcript import finalize


def test_sigkill_preserves_durable_journal(tmp_path):
    code = """
import sys,time
from pathlib import Path
from src.caller.transcript import CallArtifacts
p=Path(sys.argv[1])
a=CallArtifacts(p,{"call_id":"killed-fixture","scenario_id":"smoke","status":"connected"})
a.append("user_input_transcribed",{"transcript":"We close at five","is_final":True})
for key,role,text in [("remote-1","user","We close at five"),("patient-1","assistant","Thank you")]:
 a.append("conversation_item_added",{"item":{"id":key,"type":"message","role":role,"content":[text]}})
print("durable",flush=True)
while True: time.sleep(1)
"""
    process = subprocess.Popen(
        [sys.executable, "-c", code, str(tmp_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=Path.cwd(),
    )
    try:
        assert process.stdout is not None
        ready, _, _ = select.select([process.stdout], [], [], 10)
        assert ready, "Child did not acknowledge persisted events"
        assert process.stdout.readline().strip() == "durable"
        journal = (tmp_path / "events.jsonl").read_bytes()
        assert not (tmp_path / "transcript.json").exists()
        os.kill(process.pid, signal.SIGKILL)
        assert process.wait(timeout=10) == -signal.SIGKILL
        result = finalize(tmp_path)
        assert (tmp_path / "events.jsonl").read_bytes() == journal
        assert result["status"] == "recovered_partial"
        assert [(t["role"], t["text"]) for t in result["turns"]] == [
            ("remote", "We close at five"),
            ("patient", "Thank you"),
        ]
        assert result["uncommitted_transcriptions"] == []
        assert result["verified_state"] is None
        assert not (tmp_path / "recording.ogg").exists()
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=10)
