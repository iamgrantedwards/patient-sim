"""Hangup safety: exercise the registered SDK tool without providers or a phone call."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from livekit.agents.llm import StopResponse

from src.caller.ending import GuardedEndCallTool, RemoteInput


def context():
    handle = SimpleNamespace(add_done_callback=Mock(), interrupted=False)
    session = SimpleNamespace(
        user_state="speaking",
        current_agent=SimpleNamespace(
            _get_activity_or_raise=lambda: SimpleNamespace(llm=Mock(), realtime_llm_session=None)
        ),
        once=Mock(),
        shutdown=Mock(),
    )
    return SimpleNamespace(session=session, speech_handle=handle, wait_for_playout=AsyncMock())


def test_end_call_must_not_arm_shutdown_while_remote_is_speaking():
    """Expected policy: no irreversible callback may be registered during incoming speech."""
    ctx = context()
    mark_ended = AsyncMock()
    tool = GuardedEndCallTool(
        RemoteInput(), Mock(), end_instructions=None, on_tool_called=mark_ended
    )
    with pytest.raises(StopResponse):
        asyncio.run(tool.tools[0](ctx))
    ctx.speech_handle.add_done_callback.assert_not_called()
    ctx.session.once.assert_not_called()
    mark_ended.assert_not_awaited()


def tool_for(remote, events, mark_ended=None):
    return GuardedEndCallTool(
        remote,
        lambda kind, data: events.append((kind, data)),
        end_instructions=None,
        on_tool_called=mark_ended,
    )


def test_recorded_correction_order_keeps_new_partial_pending():
    """Replay the decisive ordering from call-20260920-155843-a34fb22c."""
    remote = RemoteInput()
    remote.transcribed("You're all set.", True)
    remote.transcribed("Your appointment", False)  # arrives before old turn commits
    remote.committed("You're all set.")
    ctx = context()
    ctx.session.user_state = "listening"  # do not rely solely on a speech-state signal
    events = []
    with pytest.raises(StopResponse):
        asyncio.run(tool_for(remote, events).tools[0](ctx))
    ctx.speech_handle.add_done_callback.assert_not_called()
    assert events == [("end_call_deferred", {"reason": "remote_transcript_pending"})]


def test_final_transcript_still_needs_its_matching_commit():
    remote = RemoteInput()
    remote.transcribed("Your appointment is confirmed.", True)
    remote.committed("You're all set.")
    assert remote.pending
    remote.committed("Your appointment is confirmed.")
    assert not remote.pending


def test_merged_segments_clear_pending_but_empty_updates_do_not():
    remote = RemoteInput()
    remote.transcribed("Goodbye.", True)
    remote.transcribed("  ", False)
    assert remote.pending
    remote.committed("Thanks for calling.\nGoodbye.")
    assert not remote.pending


def test_matching_interim_text_does_not_clear_pending():
    remote = RemoteInput()
    remote.transcribed("Thank you", False)
    remote.committed("Thank you")
    assert remote.pending


def test_quiet_completed_turn_retains_sdk_closing_and_metadata(monkeypatch):
    from src.caller import ending

    monkeypatch.setattr(ending, "CLOSING_PAUSE_SECONDS", 0)
    remote = RemoteInput()
    remote.transcribed("Goodbye.", True)
    remote.committed("Goodbye.")
    ctx = context()
    ctx.session.user_state = "listening"
    mark_ended = AsyncMock()
    events = []
    assert asyncio.run(tool_for(remote, events, mark_ended).tools[0](ctx)) is None
    ctx.wait_for_playout.assert_awaited_once()
    ctx.speech_handle.add_done_callback.assert_called_once()
    ctx.session.once.assert_called_once()
    mark_ended.assert_awaited_once()
    assert events == [("end_call_accepted", {"closing_pause_seconds": 0})]
    # Exercise the SDK callback, not a fake replacement shutdown implementation.
    ctx.speech_handle.add_done_callback.call_args.args[0](ctx.speech_handle)
    ctx.session.shutdown.assert_called_once()


@pytest.mark.parametrize("when", ["playout", "pause"])
def test_new_remote_turn_during_closing_cancels_old_decision(monkeypatch, when):
    from src.caller import ending

    remote = RemoteInput()
    ctx = context()
    ctx.session.user_state = "listening"
    events = []

    async def new_turn(*args):
        remote.transcribed("Would you like a text confirmation?", True)
        remote.committed("Would you like a text confirmation?")

    ctx.wait_for_playout.side_effect = new_turn if when == "playout" else None
    monkeypatch.setattr(
        ending.asyncio, "sleep", AsyncMock(side_effect=new_turn if when == "pause" else None)
    )
    with pytest.raises(StopResponse):
        asyncio.run(tool_for(remote, events).tools[0](ctx))
    ctx.speech_handle.add_done_callback.assert_not_called()
    assert events[-1] == ("end_call_deferred", {"reason": "remote_input_changed"})


def test_speech_without_a_transcript_also_invalidates_closing(monkeypatch):
    from src.caller import ending

    remote = RemoteInput()
    ctx = context()
    ctx.session.user_state = "listening"
    events = []

    async def new_speech(*args):
        remote.speech_started()
        ctx.session.user_state = "speaking"

    monkeypatch.setattr(ending.asyncio, "sleep", AsyncMock(side_effect=new_speech))
    with pytest.raises(StopResponse):
        asyncio.run(tool_for(remote, events).tools[0](ctx))
    ctx.speech_handle.add_done_callback.assert_not_called()
    assert events[-1] == ("end_call_deferred", {"reason": "remote_speaking"})


def test_interrupted_response_never_arms_shutdown():
    ctx = context()
    ctx.speech_handle.interrupted = True
    events = []
    with pytest.raises(StopResponse):
        asyncio.run(tool_for(RemoteInput(), events).tools[0](ctx))
    assert events[-1] == ("end_call_deferred", {"reason": "interrupted"})
    ctx.speech_handle.add_done_callback.assert_not_called()


def test_cancellation_during_playout_does_not_end_call():
    ctx = context()
    ctx.session.user_state = "listening"
    ctx.wait_for_playout.side_effect = asyncio.CancelledError()
    events = []
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(tool_for(RemoteInput(), events).tools[0](ctx))
    assert events == []
    ctx.speech_handle.add_done_callback.assert_not_called()
