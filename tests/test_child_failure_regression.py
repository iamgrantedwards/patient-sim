"""Issue #46 investigation: actual SDK status reporting and local controller gap.

Network access is disabled by pytest-socket. Provider operations and the process
boundary are replaced; CallManager and LiveBackend.exited remain production code.
The regression failed before child-failure receipts were introduced.
This verifies failure handling, not a remedy for the native segmentation fault.
"""

import asyncio
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from livekit.agents import AgentServer, utils
from livekit.agents.ipc.job_executor import JobStatus
from livekit.protocol import agent as protocol

from src.caller import managed_worker
from src.caller.control import CallManager
from src.caller.control_backend import LiveBackend
from src.caller.transcript import write_json


async def report_failed_child(monkeypatch):
    server = AgentServer(host="127.0.0.1", port=0)
    outgoing = AsyncMock()
    monkeypatch.setattr(server, "_queue_msg", outgoing)
    child = SimpleNamespace(
        status=JobStatus.FAILED,
        running_job=SimpleNamespace(job=SimpleNamespace(id="fixture-child-job")),
    )
    # Exercise the pinned SDK's real failure-to-protocol mapping without a server connection.
    await server._update_job_status(child)
    outgoing.assert_awaited_once()
    update = outgoing.await_args.args[0].update_job
    assert update.job_id == "fixture-child-job"
    assert update.status == protocol.JobStatus.JS_FAILED


def test_pinned_sdk_reports_failed_child_to_cloud(monkeypatch):
    asyncio.run(report_failed_child(monkeypatch))


@pytest.mark.parametrize("cleanup_fails", [False, True])
def test_child_failure_reaches_controller_before_call_deadline(
    tmp_path, configured, monkeypatch, cleanup_fails
):
    async def run():
        registered = asyncio.Event()
        closed = asyncio.Event()
        pool = utils.EventEmitter()
        server = AgentServer(host="127.0.0.1", port=0)
        outgoing = AsyncMock()
        signal_handlers = {}
        monkeypatch.setattr(server, "_proc_pool", pool, raising=False)
        monkeypatch.setattr(server, "_queue_msg", outgoing)
        monkeypatch.setattr(managed_worker, "server", server)
        monkeypatch.setattr(managed_worker, "PROJECT_ROOT", tmp_path)
        monkeypatch.setenv("PATIENT_SIM_WORKER_NONCE", "fixture-nonce")
        monkeypatch.setenv("PATIENT_SIM_PARENT_PID", str(os.getppid()))
        loop = asyncio.get_running_loop()
        monkeypatch.setattr(
            loop, "add_signal_handler", lambda sig, cb: signal_handlers.update({sig: cb})
        )
        monkeypatch.setattr(loop, "remove_signal_handler", lambda sig: True)

        async def serve(**kwargs):
            # Replace network serving, but run the real managed-worker wrapper around it.
            server.emit("worker_registered", "fixture-worker", {})
            server.emit("worker_started")
            registered.set()
            await closed.wait()

        async def close_server():
            closed.set()

        monkeypatch.setattr(server, "run", serve)
        monkeypatch.setattr(server, "aclose", close_server)
        monkeypatch.setattr(server, "drain", AsyncMock())

        class ParentProcess:
            def __init__(self, task):
                self.task = task
                self.pid = os.getpid()

            @property
            def returncode(self):
                if not self.task.done():
                    return None
                return 1 if self.task.exception() else 0

        class OfflineBackend(LiveBackend):
            def __init__(self):
                super().__init__(tmp_path, configured)
                self.dispatches = 0
                self.hangups = 0

            async def prepare(self, call_id):
                self.call_id = call_id
                self.nonce = "fixture-nonce"
                monkeypatch.setenv("PATIENT_SIM_CALL_ID", call_id)
                self.process = ParentProcess(asyncio.create_task(managed_worker.run()))
                await registered.wait()

            async def dispatch(self, call_id, scenario):
                self.dispatches += 1
                write_json(
                    tmp_path / "calls" / call_id / "meta.json",
                    {"status": "worker_started", "sip": {"status": "dialing"}},
                )
                return "fixture-dispatch"

            async def hangup(self, call_id):
                self.hangups += 1
                if cleanup_fails:
                    raise OSError("fixture room cleanup failed")

            async def close(self):
                closed.set()
                await self.process.task

        backend = OfflineBackend()
        manager = CallManager(tmp_path, lambda: backend, max_seconds=240, poll=0.001)
        started = await manager.start("smoke", manager.start_token, "child-crash-fixture")
        call_id = started["call_id"]
        try:
            async with asyncio.timeout(2):
                while manager.snapshot()["phase"] != "dialing":
                    await asyncio.sleep(0.001)
            evidence = tmp_path / "calls" / call_id / "meta.json"
            original = evidence.read_bytes()
            child = SimpleNamespace(
                status=JobStatus.FAILED,
                exitcode=-11,
                pid=4242,
                running_job=SimpleNamespace(
                    job=SimpleNamespace(id="fixture-child-job", room=SimpleNamespace(name=call_id))
                ),
            )
            # Both pinned SDK paths are exercised: Cloud status message and pool notification.
            # No native crash is induced, and no real provider or phone call is made.
            await server._update_job_status(child)
            assert outgoing.await_args.args[0].update_job.status == protocol.JobStatus.JS_FAILED
            pool.emit("process_closed", child)
            # A two-second offline bound is well below the 330-second call deadline.
            await asyncio.wait([manager.task], timeout=2)
            observed = manager.snapshot()
            assert backend.dispatches == 1
            assert evidence.read_bytes() == original
            assert observed["phase"] == ("recovery_required" if cleanup_fails else "failed"), (
                observed
            )
            assert observed["error"] == ("cleanup" if cleanup_fails else "worker_child_exit")
            assert observed["worker_failure"]["exit_code"] == -11
            assert observed["worker_failure"]["job_id"] == "fixture-child-job"
            assert observed["evidence_status"] == "partial_or_unavailable"
            assert "fixture-nonce" not in str(observed)
            assert observed["cleanup_confirmed"] is not cleanup_fails
            assert backend.hangups == 2
            if cleanup_fails:
                from src.caller.control import ControlError

                with pytest.raises(ControlError, match="unresolved"):
                    await manager.start("smoke", manager.start_token, "must-not-redial")
                assert backend.dispatches == 1
        finally:
            await manager.shutdown()

    asyncio.run(run())
