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
            state.patient = args[0]
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


def test_real_sdk_nonmessage_events_are_preserved_without_counting_as_dialogue(worker):
    from livekit.agents.llm import AgentHandoff, ChatMessage, FunctionCall, FunctionCallOutput
    from livekit.agents.voice.events import ConversationItemAddedEvent, FunctionToolsExecutedEvent

    ctx, state = worker

    async def run():
        await agent.entrypoint(ctx)
        callback = state.handlers["conversation_item_added"]
        callback(
            ConversationItemAddedEvent(item=AgentHandoff(old_agent_id="old", new_agent_id="new"))
        )
        callback(ConversationItemAddedEvent.model_validate({"item": {"type": "unknown"}}))
        callback(
            ConversationItemAddedEvent(item=ChatMessage(role="system", content=["Not dialogue"]))
        )
        for _ in range(3):
            callback(
                ConversationItemAddedEvent(
                    item=ChatMessage(id="same-message", role="user", content=["Hello"])
                )
            )
        callback(
            ConversationItemAddedEvent(
                item=ChatMessage(id="patient-reply", role="assistant", content=["Hi"])
            )
        )
        state.handlers["function_tools_executed"](
            FunctionToolsExecutedEvent(
                function_calls=[
                    FunctionCall(call_id="tool-fixture", name="end_call", arguments="{}")
                ],
                function_call_outputs=[
                    FunctionCallOutput(call_id="tool-fixture", output="ended", is_error=False)
                ],
            )
        )
        assert agent._calls[ctx.job.id].seen_turns == {"same-message", "patient-reply"}
        raw = (agent._calls[ctx.job.id].directory / "events.jsonl").read_text()
        assert "agent_handoff" in raw and "unknown" in raw and "function_tools_executed" in raw
        state.shutdown.assert_not_called()
        for callback in state.callbacks:
            await callback()

    asyncio.run(run())


def test_stop_marker_before_worker_acceptance_prevents_any_sip_call(worker, tmp_path):
    ctx, state = worker
    directory = tmp_path / "calls" / "call-fixture"
    directory.mkdir(parents=True)
    (directory / "operator-stop.json").write_text('{"reason":"operator_stop"}')
    asyncio.run(agent.entrypoint(ctx))
    state.connect.assert_not_awaited()
    ctx.api.sip.create_sip_participant.assert_not_awaited()
    assert agent._calls[ctx.job.id].meta["ended_by"] == "operator_stop"


@pytest.mark.parametrize("marker", ['{"reason":"controller_shutdown"}', "[]", "{broken"])
def test_stop_during_audio_preparation_prevents_sip_and_preserves_reason(worker, tmp_path, marker):
    ctx, state = worker

    async def stop_while_starting():
        (tmp_path / "calls/call-fixture/operator-stop.json").write_text(marker)

    state.start.side_effect = stop_while_starting
    asyncio.run(agent.entrypoint(ctx))
    ctx.api.sip.create_sip_participant.assert_not_awaited()
    ctx.delete_room.assert_awaited_once()
    assert agent._calls[ctx.job.id].meta["ended_by"] == (
        "controller_shutdown" if "controller_shutdown" in marker else "operator_stop"
    )


def test_repeated_call_identity_preserves_evidence_and_never_redials(worker, tmp_path):
    """Issue #46: replaying initialization must fail before any provider connection."""
    ctx, state = worker
    directory = tmp_path / "calls/call-fixture"
    directory.mkdir(parents=True)
    originals = {
        "events.jsonl": b'{"type":"conversation_item_added","data":{"item":{"type":"agent_handoff"}}}\n',
        "meta.json": b'{"status":"worker_started","sip":{"status":"dialing"}}\n',
        "recording.ogg": b"original-partial-audio-fixture",
    }
    for name, content in originals.items():
        (directory / name).write_bytes(content)

    with pytest.raises(FileExistsError) as raised:
        asyncio.run(agent.entrypoint(ctx))

    assert raised.value.errno == 17
    assert ctx.job.id not in agent._calls
    state.connect.assert_not_awaited()
    state.start.assert_not_awaited()
    ctx.api.sip.create_sip_participant.assert_not_awaited()
    assert {p.name: p.read_bytes() for p in directory.iterdir()} == originals


def test_real_worker_wires_pending_transcript_guard_before_end_metadata(worker):
    from livekit.agents.llm import ChatMessage, StopResponse
    from livekit.agents.voice.events import ConversationItemAddedEvent, UserInputTranscribedEvent

    ctx, state = worker

    async def run():
        await agent.entrypoint(ctx)
        patient = state.patient
        partial = state.handlers["user_input_transcribed"]
        partial(UserInputTranscribedEvent(transcript="You're all set.", is_final=True))
        partial(UserInputTranscribedEvent(transcript="Your appointment", is_final=False))
        state.handlers["conversation_item_added"](
            ConversationItemAddedEvent(item=ChatMessage(role="user", content=["You're all set."]))
        )
        state.handlers["user_state_changed"](
            SimpleNamespace(
                new_state="listening", model_dump=lambda **kw: {"new_state": "listening"}
            )
        )
        tool_ctx = SimpleNamespace(
            session=SimpleNamespace(user_state="listening"),
            speech_handle=SimpleNamespace(interrupted=False, add_done_callback=Mock()),
        )
        with pytest.raises(StopResponse):
            await patient.tools[0](tool_ctx)
        tool_ctx.speech_handle.add_done_callback.assert_not_called()
        artifacts = agent._calls[ctx.job.id]
        assert artifacts.meta["ended_by"] is None
        assert "remote_transcript_pending" in (artifacts.directory / "events.jsonl").read_text()
        state.shutdown.assert_not_called()
        for callback in state.callbacks:
            await callback()

    asyncio.run(run())
