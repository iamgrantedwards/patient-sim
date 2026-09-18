import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from src.caller import agent
from src.caller.transcript import CallArtifacts


@pytest.fixture
def saved_call(tmp_path):
    artifacts = CallArtifacts(tmp_path, {"call_id": "call-fixture", "scenario_id": "smoke"})
    artifacts.append(
        "conversation_item_added",
        {
            "item": {
                "id": "message-1",
                "type": "message",
                "role": "user",
                "content": ["We close at five."],
            }
        },
    )
    report = SimpleNamespace(
        audio_recording_started_at=1234,
        sdk_version="1.8.2",
        audio_recording_path=None,
        options=SimpleNamespace(
            endpointing={}, interruption={}, preemptive_generation={}, recording_options={}
        ),
        model_usage=[],
    )
    ctx = SimpleNamespace(
        job=SimpleNamespace(id="saved-job"),
        make_session_report=Mock(return_value=report),
        delete_room=AsyncMock(),
    )
    agent._calls[ctx.job.id] = artifacts
    yield ctx, artifacts
    agent._calls.pop(ctx.job.id, None)
    artifacts.events.close()


@pytest.mark.parametrize("failure", ["none", "recording", "report"])
def test_audio_failures_preserve_transcript_and_disconnect(saved_call, monkeypatch, failure):
    ctx, artifacts = saved_call
    if failure == "recording":
        monkeypatch.setattr(
            agent, "preserve_recording", Mock(side_effect=OSError("private-detail"))
        )
    elif failure == "report":
        ctx.make_session_report.side_effect = RuntimeError("private-detail")
    asyncio.run(agent.save_call(ctx))
    ctx.delete_room.assert_awaited_once()
    assert artifacts.events.closed
    transcript = json.loads((artifacts.directory / "transcript.json").read_text())
    assert transcript["turns"][0]["text"] == "We close at five."
    assert transcript["verified_state"] is None
    meta = (artifacts.directory / "meta.json").read_text()
    assert "private-detail" not in meta
    assert json.loads(meta)["recording"]["status"] == ("missing" if failure == "none" else "error")


@pytest.mark.parametrize("failure", ["transcript", "metadata"])
def test_evidence_write_failure_still_closes_journal_and_disconnects(
    saved_call, monkeypatch, failure
):
    ctx, artifacts = saved_call
    if failure == "transcript":
        monkeypatch.setattr(agent, "finalize", Mock(side_effect=OSError("disk full")))
    else:
        monkeypatch.setattr(artifacts, "save", Mock(side_effect=OSError("disk full")))
    with pytest.raises(OSError, match="disk full"):
        asyncio.run(agent.save_call(ctx))
    ctx.delete_room.assert_awaited_once()
    assert artifacts.events.closed
    assert "We close at five." in (artifacts.directory / "events.jsonl").read_text()


def test_finalization_is_idempotent_after_success(saved_call):
    ctx, _ = saved_call
    asyncio.run(agent.save_call(ctx))
    asyncio.run(agent.save_call(ctx))
    ctx.delete_room.assert_awaited_once()
