import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from livekit import api, rtc

from src.caller import agent


@pytest.fixture
def worker(monkeypatch, tmp_path, configured):
    state = SimpleNamespace(
        handlers={},
        room_handlers={},
        callbacks=[],
        tasks=[],
        start=AsyncMock(),
        connect=AsyncMock(),
        shutdown=Mock(),
    )

    class Session:
        def __init__(self, **kwargs):
            pass

        def on(self, event):
            def register(callback):
                state.handlers[event] = callback
                return callback

            return register

        async def start(self, *args, **kwargs):
            await state.start()

        def shutdown(self, **kwargs):
            state.handlers["close"](SimpleNamespace(reason=SimpleNamespace(value="user_initiated")))

    def on_room(event):
        def register(callback):
            state.room_handlers[event] = callback
            return callback

        return register

    create_task = asyncio.create_task

    def record_task(coro):
        task = create_task(coro)
        state.tasks.append(task)
        return task

    ctx = SimpleNamespace(
        job=SimpleNamespace(
            id="failure-job", metadata=json.dumps({"call_id": "call-fixture", "scenario": "smoke"})
        ),
        room=SimpleNamespace(name="call-fixture", on=on_room),
        connect=state.connect,
        shutdown=state.shutdown,
        api=SimpleNamespace(
            sip=SimpleNamespace(
                create_sip_participant=AsyncMock(
                    return_value=SimpleNamespace(sip_call_id="sip-fixture")
                )
            )
        ),
        delete_room=AsyncMock(),
        add_shutdown_callback=state.callbacks.append,
    )
    monkeypatch.setattr(agent, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(agent, "load", lambda: configured)
    monkeypatch.setattr(agent, "AgentSession", Session)
    monkeypatch.setattr(agent.subprocess, "check_output", lambda *a, **kw: "revision")
    monkeypatch.setattr(agent.asyncio, "create_task", record_task)
    for name in ("STT", "LLM", "TTS"):
        monkeypatch.setattr(agent.inference, name, lambda *a, **kw: SimpleNamespace())
    yield ctx, state
    artifacts = agent._calls.pop(ctx.job.id, None)
    if artifacts is not None:
        artifacts.events.close()


def test_session_start_failure_never_dials(worker):
    ctx, state = worker
    state.start.side_effect = RuntimeError("provider-private-detail")
    asyncio.run(agent.entrypoint(ctx))
    ctx.api.sip.create_sip_participant.assert_not_awaited()
    ctx.delete_room.assert_awaited_once()
    state.shutdown.assert_called_with(reason="worker_error")
    artifacts = agent._calls[ctx.job.id]
    assert artifacts.meta["error_type"] == "RuntimeError"
    assert "provider-private-detail" not in (artifacts.directory / "meta.json").read_text()


def test_cleanup_api_failure_still_shuts_down_worker(worker):
    ctx, state = worker
    state.start.side_effect = RuntimeError("provider failure")
    ctx.delete_room.side_effect = OSError("room API down")
    with pytest.raises(OSError, match="room API down"):
        asyncio.run(agent.entrypoint(ctx))
    state.shutdown.assert_called_once_with(reason="worker_error")


def test_sip_rejection_is_recorded_without_retry(worker):
    ctx, state = worker
    ctx.api.sip.create_sip_participant.side_effect = api.SipCallError(
        code="unavailable", msg="Busy Here", status=503, metadata={"sip_status_code": "486"}
    )
    asyncio.run(agent.entrypoint(ctx))
    ctx.api.sip.create_sip_participant.assert_awaited_once()
    assert agent._calls[ctx.job.id].meta["ended_by"] == "rejected"
    state.shutdown.assert_called_once_with(reason="rejected")


def test_media_failure_ends_call_and_preserves_partial_stt(worker):
    ctx, state = worker

    async def run():
        await agent.entrypoint(ctx)
        state.handlers["user_input_transcribed"](
            SimpleNamespace(model_dump=lambda **kw: {"transcript": "Could you", "is_final": False})
        )
        handler = state.room_handlers["participant_disconnected"]
        handler(SimpleNamespace(identity="unrelated-participant"))
        state.shutdown.assert_not_called()
        handler(
            SimpleNamespace(
                identity="assessment-line", disconnect_reason=rtc.DisconnectReason.MEDIA_FAILURE
            )
        )
        for callback in state.callbacks:
            await callback()

    asyncio.run(run())
    artifacts = agent._calls[ctx.job.id]
    assert artifacts.meta["ended_by"] == "telephony_error"
    assert artifacts.meta["sip"]["disconnect_reason"] == "MEDIA_FAILURE"
    assert "Could you" in (artifacts.directory / "events.jsonl").read_text()


def test_duration_deadline_deletes_room_and_shuts_down(worker, monkeypatch):
    ctx, state = worker
    monkeypatch.setattr(agent.asyncio, "sleep", AsyncMock())

    async def run():
        await agent.entrypoint(ctx)
        await asyncio.gather(*state.tasks)

    asyncio.run(run())
    ctx.delete_room.assert_awaited_once()
    state.shutdown.assert_called_once_with(reason="failsafe")
    assert agent._calls[ctx.job.id].meta["failsafe_reason"] == "max_call_seconds"


def test_invalid_dispatch_metadata_fails_before_providers(worker):
    ctx, state = worker
    ctx.job.metadata = json.dumps({"call_id": "../escape"})
    with pytest.raises(ValueError, match="valid call_id"):
        asyncio.run(agent.entrypoint(ctx))
    state.connect.assert_not_awaited()
    ctx.api.sip.create_sip_participant.assert_not_awaited()
