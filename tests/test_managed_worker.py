import asyncio
import json
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from livekit.agents import utils
from livekit.agents.ipc.job_executor import JobStatus

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


@pytest.mark.parametrize("exit_code", [0, -11])
@pytest.mark.parametrize("assigned", [True, False])
def test_child_exit_receipt_distinguishes_success_from_failure(
    tmp_path, monkeypatch, exit_code, assigned
):
    (tmp_path / ".runtime").mkdir()

    async def run():
        handlers = {}
        pool = utils.EventEmitter()
        closed = asyncio.Event()

        class Server:
            _proc_pool = pool
            drain = AsyncMock()

            def on(self, event):
                def register(callback):
                    handlers[event] = callback
                    return callback

                return register

            async def run(self, **kwargs):
                handlers["worker_started"]()

                class Process:
                    exitcode = exit_code
                    pid = 4567
                    running_job = (
                        SimpleNamespace(job=SimpleNamespace(id="job-test")) if assigned else None
                    )

                    @property
                    def status(self):
                        if not assigned:
                            raise RuntimeError("job status not available")
                        return JobStatus.SUCCESS if exit_code == 0 else JobStatus.FAILED

                proc = Process()
                pool.emit("process_closed", proc)
                pool.emit("process_closed", proc)  # A repeated notification must not overwrite.
                if exit_code == 0:
                    assert not (tmp_path / ".runtime/call-test-failure.json").exists()
                    handlers["signal"]()
                await closed.wait()

            async def aclose(self):
                closed.set()

        monkeypatch.setattr(module, "server", Server())
        monkeypatch.setattr(module, "PROJECT_ROOT", tmp_path)
        monkeypatch.setenv("PATIENT_SIM_CALL_ID", "call-test")
        monkeypatch.setenv("PATIENT_SIM_WORKER_NONCE", "fixture")
        monkeypatch.setenv("PATIENT_SIM_PARENT_PID", str(os.getppid()))
        loop = asyncio.get_running_loop()
        monkeypatch.setattr(loop, "add_signal_handler", lambda sig, cb: handlers.update(signal=cb))
        monkeypatch.setattr(loop, "remove_signal_handler", lambda sig: True)
        await module.run()
        if exit_code:
            receipt = json.loads((tmp_path / ".runtime/call-test-failure.json").read_text())
            assert receipt["exit_code"] == -11
            assert receipt["job_id"] == ("job-test" if assigned else None)
            assert receipt["parent_pid"] == os.getpid()
        else:
            assert not (tmp_path / ".runtime/call-test-failure.json").exists()

    asyncio.run(run())
