import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

from livekit.agents.llm import ChatMessage
from livekit.agents.voice.events import ConversationItemAddedEvent

from src.caller import agent


def test_worker_prepares_audio_before_dialing_and_uses_server_limits(
    monkeypatch, tmp_path, configured
):
    order = []
    sessions = []

    class Session:
        def __init__(self, **options):
            self.options = options
            self.handlers = {}
            sessions.append(self)

        def on(self, name):
            def register(handler):
                self.handlers[name] = handler
                return handler

            return register

        async def start(self, patient, **options):
            self.patient = patient
            self.start_options = options
            order.append("session_ready")

        def shutdown(self, **kwargs):
            self.handlers["close"](SimpleNamespace(reason=SimpleNamespace(value="user_initiated")))

    async def connect():
        order.append("room_connected")

    async def place(request, **kwargs):
        order.append("dialed")
        assert request.sip_call_to == "+18054398008"
        assert request.sip_number == configured.caller_id
        assert request.max_call_duration.seconds == 240
        assert request.ringing_timeout.seconds == 30
        assert not request.krisp_enabled
        return SimpleNamespace(sip_call_id="fixture-sip")

    monkeypatch.setattr(agent, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(agent, "load", lambda: configured)
    monkeypatch.setattr(agent, "AgentSession", Session)
    monkeypatch.setattr(
        agent.subprocess,
        "check_output",
        lambda args, **kw: "testrevision" if args[1] == "rev-parse" else "",
    )
    for provider in ("STT", "LLM", "TTS"):
        monkeypatch.setattr(agent.inference, provider, lambda *a, **kw: SimpleNamespace())
    callbacks = []
    shutdown_reasons = []

    class Room:
        name = "call-fixture"

        def on(self, _name):
            return lambda callback: callback

    ctx = SimpleNamespace(
        job=SimpleNamespace(
            id="job-fixture", metadata=json.dumps({"call_id": "call-fixture", "scenario": "smoke"})
        ),
        room=Room(),
        connect=connect,
        api=SimpleNamespace(sip=SimpleNamespace(create_sip_participant=place)),
        add_shutdown_callback=callbacks.append,
        shutdown=lambda **kw: shutdown_reasons.append(kw["reason"]),
        delete_room=AsyncMock(),
    )

    async def run():
        await agent.entrypoint(ctx)
        assert order == ["room_connected", "session_ready", "dialed"]
        assert sessions[0].options["ivr_detection"] is False
        assert sessions[0].start_options["record"]["audio"] is True
        assert sessions[0].start_options["room_options"].audio_input.auto_gain_control is False
        # Hitting the turn cap ends locally instead of waiting for another model response.
        for index in range(configured.max_turns):
            event = ConversationItemAddedEvent(
                item=ChatMessage(role="user", id=str(index), content=["fixture"])
            )
            sessions[0].handlers["conversation_item_added"](event)
        assert shutdown_reasons[-1] == "failsafe"
        for callback in callbacks:
            await callback()
        artifacts = agent._calls.pop("job-fixture")
        assert artifacts.meta["ended_by"] == "failsafe"
        artifacts.events.close()

    asyncio.run(run())
