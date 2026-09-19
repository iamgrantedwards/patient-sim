import asyncio
import json
import os
from unittest.mock import AsyncMock

import pytest

from src.caller import managed_worker as module


@pytest.mark.parametrize("mode", ["parent_gone", "signal", "server_finished", "server_error"])
def test_managed_worker_registration_and_shutdown_receipts(tmp_path, monkeypatch, mode):
    (tmp_path / ".runtime").mkdir()
    (tmp_path / "calls/call-worker").mkdir(parents=True)
    handlers = {}

    class Server:
        def __init__(self):
            self.closed = asyncio.Event()
            self.drain = AsyncMock()

        def on(self, event):
            def register(callback):
                handlers[event] = callback
                return callback

            return register

        async def run(self, **kwargs):
            assert kwargs == {"devmode": True}
            handlers["worker_registered"]("worker-id", {})
            if mode == "server_finished":
                return
            if mode == "server_error":
                raise RuntimeError("Registration lost")
            if mode == "signal":
                handlers["signal"]()
            await self.closed.wait()

        async def aclose(self):
            self.closed.set()

    monkeypatch.setattr(module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("PATIENT_SIM_CALL_ID", "call-worker")
    monkeypatch.setenv("PATIENT_SIM_WORKER_NONCE", "fixture-nonce")
    monkeypatch.setenv("PATIENT_SIM_PARENT_PID", str(os.getppid() + (mode == "parent_gone")))
    server = Server()
    monkeypatch.setattr(module, "server", server)

    async def run():
        loop = asyncio.get_running_loop()
        monkeypatch.setattr(
            loop, "add_signal_handler", lambda sig, callback: handlers.update(signal=callback)
        )
        monkeypatch.setattr(loop, "remove_signal_handler", lambda sig: True)
        if mode == "server_error":
            with pytest.raises(RuntimeError, match="Registration lost"):
                await module.run()
        else:
            await module.run()

    asyncio.run(run())
    ready = json.loads((tmp_path / ".runtime/call-worker-worker.json").read_text())
    assert ready == {"nonce": "fixture-nonce", "pid": os.getpid(), "registered": True}
    assert json.loads((tmp_path / ".runtime/call-worker-stopped.json").read_text())["stopped"]
    assert server.drain.await_count == (1 if mode in ("parent_gone", "signal") else 0)
    if mode == "parent_gone":
        assert (
            json.loads((tmp_path / "calls/call-worker/operator-stop.json").read_text())["reason"]
            == "controller_shutdown"
        )


def test_invalid_managed_call_id_never_runs_server(monkeypatch):
    monkeypatch.setenv("PATIENT_SIM_CALL_ID", "../escape")
    with pytest.raises(ValueError, match="Invalid managed call"):
        asyncio.run(module.run())
