"""Prevent a stale closing decision from cutting off incoming office speech."""

import asyncio
from collections.abc import Callable
from typing import Any

from livekit.agents import RunContext
from livekit.agents.beta.tools import EndCallTool
from livekit.agents.llm import StopResponse

# Closing-only grace period, not a global endpointing/latency adjustment.
CLOSING_PAUSE_SECONDS = 1.0


class RemoteInput:
    def __init__(self) -> None:
        self.pending = False
        self.revision = 0
        self._latest = ""
        self._final = False

    def transcribed(self, text: str, is_final: bool) -> None:
        if not text.strip():
            return
        self._latest = " ".join(text.split())
        self._final = is_final
        self.pending = True
        self.revision += 1

    def committed(self, text: str) -> None:
        self.revision += 1
        # STT can begin the NEXT utterance before an older message is committed.
        # Only the latest final transcript can clear the outstanding input. The SDK
        # may combine several final STT segments into one committed message.
        normalized = " ".join(text.split())
        if self._final and normalized.endswith(self._latest):
            self.pending = False

    def speech_started(self) -> None:
        self.revision += 1


class GuardedEndCallTool(EndCallTool):
    def __init__(
        self,
        remote_input: RemoteInput,
        record: Callable[[str, dict[str, Any]], None],
        **kwargs: Any,
    ) -> None:
        self.remote_input = remote_input
        self.record = record
        super().__init__(**kwargs)

    def _defer(self, reason: str) -> None:
        self.record("end_call_deferred", {"reason": reason})
        # No spoken tool-error response over the office's ongoing turn. The next
        # incoming turn drives a fresh decision; this request never auto-retries.
        raise StopResponse()

    def _check_input(self, ctx: RunContext) -> None:
        if ctx.speech_handle.interrupted:
            self._defer("interrupted")
        if ctx.session.user_state == "speaking":
            self._defer("remote_speaking")
        if self.remote_input.pending:
            self._defer("remote_transcript_pending")

    async def _end_call(self, ctx: RunContext) -> Any | None:
        self._check_input(ctx)
        revision = self.remote_input.revision
        await ctx.wait_for_playout()
        await asyncio.sleep(CLOSING_PAUSE_SECONDS)
        self._check_input(ctx)
        if self.remote_input.revision != revision:
            self._defer("remote_input_changed")
        self.record("end_call_accepted", {"closing_pause_seconds": CLOSING_PAUSE_SECONDS})
        # The SDK registers shutdown callbacks before calling on_tool_called.
        # Therefore the guard must run BEFORE entering the SDK implementation.
        return await super()._end_call(ctx)
