import asyncio
import json
import signal
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from livekit import api

from src.caller import control_backend as module
from src.caller.control_backend import LiveBackend
from src.caller.transcript import write_json


@pytest.fixture
def backend(tmp_path, configured):
    (tmp_path / ".runtime").mkdir()
    return LiveBackend(tmp_path, configured)


def test_worker_registration_is_required_and_dispatch_is_unique(backend, monkeypatch):
    process = SimpleNamespace(pid=1234, returncode=None, send_signal=Mock(), wait=AsyncMock())

    async def spawn(*args, **kwargs):
        assert args[-1] == "src.caller.managed_worker"
        assert kwargs["start_new_session"] is True
        env = kwargs["env"]
        assert env["PYTHONFAULTHANDLER"] == "1"
        assert env["PATIENT_SIM_AGENT_NAME"] == backend.agent_name
        write_json(
            backend.root / ".runtime/call-fixture-worker.json",
            {
                "nonce": env["PATIENT_SIM_WORKER_NONCE"],
                "pid": process.pid,
            },
        )
        return process

    monkeypatch.setattr(module.asyncio, "create_subprocess_exec", spawn)

    async def run():
        assert not backend.exited()
        await backend.prepare("call-fixture")
        assert not backend.exited()
        await backend.close()
        process.send_signal.assert_called_once_with(signal.SIGTERM)
        assert backend.log is None
        assert (backend.root / ".runtime/call-fixture-stopped.json").exists()
        process.returncode = 0
        assert backend.exited()
        await backend.close()

    asyncio.run(run())


def test_cancellation_during_process_creation_retains_ownership(backend, monkeypatch):
    process = SimpleNamespace(pid=1234, returncode=None, send_signal=Mock(), wait=AsyncMock())

    async def run():
        started = asyncio.Event()
        release = asyncio.Event()

        async def spawn(*args, **kwargs):
            started.set()
            await release.wait()
            return process

        monkeypatch.setattr(module.asyncio, "create_subprocess_exec", spawn)
        task = asyncio.create_task(backend.prepare("call-cancel"))
        await started.wait()
        task.cancel()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        await backend.close()
        process.send_signal.assert_called_once()

    asyncio.run(run())


def test_worker_exit_before_registration_fails(backend, monkeypatch):
    monkeypatch.setattr(
        module.asyncio,
        "create_subprocess_exec",
        AsyncMock(return_value=SimpleNamespace(pid=1234, returncode=1)),
    )

    async def run():
        with pytest.raises(RuntimeError, match="worker_exited"):
            await backend.prepare("call-dead")
        await backend.close()

    asyncio.run(run())


def test_registration_does_not_trust_a_stale_receipt(backend, monkeypatch):
    process = SimpleNamespace(pid=1234, returncode=None, send_signal=Mock(), wait=AsyncMock())
    monkeypatch.setattr(module.asyncio, "create_subprocess_exec", AsyncMock(return_value=process))
    write_json(backend.root / ".runtime/call-stale-worker.json", {"nonce": "old", "pid": 1234})

    async def run():
        task = asyncio.create_task(backend.prepare("call-stale"))
        await asyncio.sleep(0.02)
        assert not task.done()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        await backend.close()

    asyncio.run(run())


def test_owned_hung_worker_is_killed_without_signalling_unowned_pids(backend, monkeypatch):
    process = SimpleNamespace(pid=1234, returncode=None, send_signal=Mock(), wait=AsyncMock())
    backend.process = process
    killed = Mock()
    monkeypatch.setattr(module.os, "killpg", killed)

    async def timeout(coro, seconds):
        coro.close()
        raise TimeoutError

    monkeypatch.setattr(module.asyncio, "wait_for", timeout)
    asyncio.run(backend.close())
    killed.assert_called_once_with(1234, signal.SIGKILL)


def test_recovery_waits_for_matching_worker_shutdown_receipt(backend, monkeypatch):
    backend.call_id = "call-recover"
    directory = backend.root / ".runtime"
    write_json(directory / "call-recover-intent.json", {"nonce": "current"})
    write_json(directory / "call-recover-stopped.json", {"nonce": "old", "stopped": True})
    killed = Mock()
    monkeypatch.setattr(module.os, "killpg", killed)

    async def run():
        task = asyncio.create_task(backend.close())
        await asyncio.sleep(0.02)
        assert not task.done()
        write_json(directory / "call-recover-stopped.json", {"nonce": "current", "stopped": True})
        await task

    asyncio.run(run())
    killed.assert_not_called()


@pytest.mark.parametrize(
    "delete_error,remaining,fails",
    [
        (None, [], False),
        (api.TwirpError("not_found", "Gone", status=404), [], False),
        (api.TwirpError("unavailable", "private-provider-detail", status=503), [], True),
        (None, [SimpleNamespace(name="call-api")], True),
    ],
)
def test_provider_requests_and_room_absence_verification(
    backend, monkeypatch, delete_error, remaining, fails
):
    room = SimpleNamespace(
        delete_room=AsyncMock(side_effect=delete_error),
        list_rooms=AsyncMock(return_value=SimpleNamespace(rooms=remaining)),
    )
    dispatch = AsyncMock(return_value=SimpleNamespace(id="dispatch-fixture"))
    client = SimpleNamespace(room=room, agent_dispatch=SimpleNamespace(create_dispatch=dispatch))

    class Client:
        async def __aenter__(self):
            return client

        async def __aexit__(self, *args):
            pass

    factory = Mock(return_value=Client())
    monkeypatch.setattr(module.api, "LiveKitAPI", factory)

    async def run():
        assert await backend.dispatch("call-api", "smoke") == "dispatch-fixture"
        request = dispatch.await_args.args[0]
        assert request.agent_name == backend.agent_name
        assert request.room == "call-api"
        assert json.loads(request.metadata) == {"call_id": "call-api", "scenario": "smoke"}
        if fails:
            with pytest.raises((api.TwirpError, RuntimeError)):
                await backend.hangup("call-api")
        else:
            await backend.hangup("call-api")
        assert room.delete_room.await_args.args[0].room == "call-api"
        if not delete_error or delete_error.code == "not_found":
            assert list(room.list_rooms.await_args.args[0].names) == ["call-api"]

    asyncio.run(run())


@pytest.mark.parametrize(
    "change",
    [{}, {"nonce": "stale"}, {"parent_pid": 999}, {"call_id": "call-other"}, {"reason": "unknown"}],
)
def test_child_failure_receipt_requires_current_worker(backend, change):
    backend.call_id = "call-fixture"
    backend.nonce = "current-nonce"
    backend.process = SimpleNamespace(pid=1234, returncode=None)
    receipt = {
        "call_id": "call-fixture",
        "nonce": "current-nonce",
        "parent_pid": 1234,
        "reason": "child_exit",
        "child_pid": 4567,
        "job_id": "job-fixture",
        "exit_code": -11,
        "observed_at": 1.0,
    }
    receipt.update(change)
    write_json(backend.root / ".runtime/call-fixture-failure.json", receipt)
    result = backend.failure()
    if change:
        assert result is None
    else:
        assert result["exit_code"] == -11
        assert result["child_pid"] == 4567
        assert "nonce" not in result
    assert not backend.exited()  # The receipt works independently of parent exit.


@pytest.mark.parametrize("content", [None, "{broken", "[]"])
def test_missing_or_malformed_failure_receipt_is_not_trusted(backend, content):
    assert backend.failure() is None
    backend.call_id, backend.nonce = "call-fixture", "current"
    backend.process = SimpleNamespace(pid=1234, returncode=None)
    if content is not None:
        (backend.root / ".runtime/call-fixture-failure.json").write_text(content)
    assert backend.failure() is None
