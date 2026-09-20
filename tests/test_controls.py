import asyncio
import json

import pytest

from src.caller.call_slot import CallSlot
from src.caller.control import CallManager, ControlError
from src.caller.transcript import write_json


class Backend:
    def __init__(self, root, mode="normal"):
        self.root = root
        self.mode = mode
        self.actions = []
        self.call_id = None
        self.gate = asyncio.Event()

    async def prepare(self, call_id):
        self.call_id = call_id
        self.actions.append("prepare")
        if self.mode == "prepare_error":
            raise RuntimeError("private-provider-key")
        if self.mode == "slow_prepare":
            await self.gate.wait()

    async def dispatch(self, call_id, scenario):
        self.call_id = call_id
        self.actions.append("dispatch")
        if self.mode == "dispatch_error":
            raise TimeoutError("private-provider-key")
        if self.mode == "slow_dispatch":
            await self.gate.wait()
        write_json(
            self.root / "calls" / call_id / "meta.json",
            {
                "call_id": call_id,
                "scenario_id": scenario,
                "status": "ended" if self.mode == "normal" else "connected",
                "ended_by": "end_call_tool" if self.mode == "normal" else None,
                "sip": {"status": "answered"},
            },
        )
        return "dispatch-fixture"

    def failure(self):
        return None

    def exited(self):
        return self.mode == "worker_exit"

    async def hangup(self, call_id):
        self.actions.append("hangup")
        if self.mode == "cleanup_error":
            raise RuntimeError("private-provider-key")
        directory = self.root / "calls" / call_id
        if (directory / "meta.json").exists():
            meta = json.loads((directory / "meta.json").read_text())
            stop = directory / "operator-stop.json"
            meta.update(
                status="ended",
                ended_by=json.loads(stop.read_text())["reason"]
                if stop.exists()
                else meta.get("ended_by") or "remote_hangup",
            )
            write_json(directory / "meta.json", meta)

    async def close(self):
        self.actions.append("close")


async def wait_phase(manager, phase):
    for _ in range(500):
        if manager.snapshot()["phase"] == phase:
            return
        await asyncio.sleep(0.001)
    raise AssertionError(manager.snapshot())


def test_real_lifecycle_and_idempotency_never_redial(tmp_path):
    async def run():
        backend = Backend(tmp_path)
        manager = CallManager(tmp_path, lambda: backend, poll=0.001)
        initial = manager.start_token
        request_id = "request-id-one-123"
        result = await manager.start("smoke", initial, request_id)
        repeated = await manager.start("smoke", initial, request_id)
        assert result["call_id"] == repeated["call_id"]
        with pytest.raises(ControlError, match="cannot change scenario"):
            await manager.start("calibration", initial, request_id)
        await manager.task
        assert manager.snapshot()["phase"] == "ended"
        assert manager.snapshot()["cleanup_confirmed"]
        assert manager.snapshot()["ended_by"] == "end_call_tool"
        assert backend.actions == ["prepare", "dispatch", "hangup", "close", "hangup"]
        # Retrying a completed operation remains a read; an older confirmation cannot start again.
        await manager.start("smoke", initial, request_id)
        with pytest.raises(ControlError, match="expired"):
            await manager.start("smoke", initial, "request-id-two-123")
        assert backend.actions.count("dispatch") == 1
        assert (await manager.stop(result["call_id"]))["phase"] == "ended"
        await manager.shutdown()

    asyncio.run(run())


@pytest.mark.parametrize(
    "mode,stage",
    [
        ("prepare_error", "worker_start"),
        ("dispatch_error", "dispatch"),
        ("worker_exit", "worker_exit"),
    ],
)
def test_failures_preserve_private_errors_and_close_room(tmp_path, mode, stage):
    async def run():
        backend = Backend(tmp_path, mode)
        manager = CallManager(tmp_path, lambda: backend, poll=0.001)
        await manager.start("smoke", manager.start_token, "failure-request-123")
        await manager.task
        result = manager.snapshot()
        assert result["phase"] == "failed" and result["error"] == stage
        assert result["cleanup_confirmed"]
        assert "private-provider-key" not in json.dumps(result) + manager.slot.path.read_text()
        assert backend.actions.count("dispatch") <= 1

    asyncio.run(run())


@pytest.mark.parametrize("mode", ["slow_prepare", "slow_dispatch", "active"])
def test_stop_at_each_boundary_never_retries_and_preserves_operator_reason(tmp_path, mode):
    async def run():
        backend = Backend(tmp_path, mode)
        manager = CallManager(tmp_path, lambda: backend, poll=0.001)
        result = await manager.start("smoke", manager.start_token, "stop-request-1234")
        await wait_phase(
            manager,
            {
                "slow_prepare": "preparing_worker",
                "slow_dispatch": "dispatching",
                "active": "connected",
            }[mode],
        )
        await manager.stop(result["call_id"])
        await manager.task
        assert manager.snapshot()["ended_by"] == "operator_stop"
        assert manager.snapshot()["cleanup_confirmed"]
        assert backend.actions.count("dispatch") == (0 if mode == "slow_prepare" else 1)
        assert (
            json.loads((tmp_path / "calls" / result["call_id"] / "operator-stop.json").read_text())[
                "reason"
            ]
            == "operator_stop"
        )

    asyncio.run(run())


def test_duplicate_start_is_blocked_across_manager_instances(tmp_path):
    async def run():
        first = CallManager(tmp_path, lambda: Backend(tmp_path, "active"), poll=0.001)
        second = CallManager(tmp_path, lambda: Backend(tmp_path))
        result = await first.start("smoke", first.start_token, "first-request-1234")
        with pytest.raises(ControlError, match="owns the call slot"):
            await second.start("smoke", second.start_token, "second-request-123")
        with pytest.raises(ControlError, match="owns the call slot"):
            await second.stop(result["call_id"])
        with pytest.raises(ControlError, match="no longer"):
            await first.stop("call-wrong")
        await first.shutdown()
        assert first.snapshot()["ended_by"] == "controller_shutdown"

    asyncio.run(run())


def test_cleanup_uncertainty_blocks_new_calls_until_explicit_recovery(tmp_path):
    async def run():
        backend = Backend(tmp_path, "cleanup_error")
        manager = CallManager(tmp_path, lambda: backend, max_seconds=-100, poll=0.001)
        result = await manager.start("smoke", manager.start_token, "uncertain-request-1")
        await manager.task
        assert manager.snapshot()["phase"] == "recovery_required"
        with pytest.raises(ControlError, match="unresolved"):
            await manager.start("smoke", manager.start_token, "uncertain-request-2")
        restored = CallManager(tmp_path, lambda: Backend(tmp_path))
        await restored.stop(result["call_id"])
        await restored.task
        assert restored.snapshot()["cleanup_confirmed"]
        assert restored.backend.actions == ["hangup", "close", "hangup"]

    asyncio.run(run())


def test_controller_deadline_stops_without_claiming_natural_completion(tmp_path):
    async def run():
        manager = CallManager(
            tmp_path, lambda: Backend(tmp_path, "active"), max_seconds=-100, poll=0.001
        )
        await manager.start("smoke", manager.start_token, "deadline-request-1")
        await manager.task
        assert manager.snapshot()["phase"] == "failed"
        assert manager.snapshot()["error"] == "deadline"

    asyncio.run(run())


def test_unreadable_journal_and_interrupted_operation_fail_closed(tmp_path):
    slot = CallSlot(tmp_path)
    assert slot.read() is None
    slot.acquire()
    slot.path.write_text("{broken")
    assert slot.read()["phase"] == "recovery_required"
    slot.path.write_text("[]")
    assert slot.read()["error"] == "unreadable_operation"
    slot.path.write_text("x" * 32769)
    assert slot.read()["error"] == "unreadable_operation"
    slot.save({"phase": "connected", "call_id": "call-interrupted"})
    slot.release()
    manager = CallManager(tmp_path, lambda: None)
    assert manager.snapshot()["phase"] == "recovery_required"
    with pytest.raises(RuntimeError, match="locked"):
        slot.save({})
    slot.release()


def test_start_validation_and_configuration_do_not_dispatch(tmp_path):
    async def run():
        def unavailable():
            raise RuntimeError("private-secret")

        manager = CallManager(tmp_path, unavailable)
        with pytest.raises(ControlError, match="Unknown scenario"):
            await manager.start("unknown", manager.start_token, "invalid-request-12")
        with pytest.raises(ControlError, match="Configuration"):
            await manager.start("smoke", manager.start_token, "invalid-request-12")
        assert manager.slot.handle is None
        manager.closing = True
        with pytest.raises(ControlError, match="shutting down"):
            await manager.start("smoke", manager.start_token, "invalid-request-12")

    asyncio.run(run())


def test_live_committed_dialogue_is_reconciled_and_raw_events_unchanged(tmp_path):
    manager = CallManager(tmp_path, lambda: None)
    call = tmp_path / "calls" / "call-live-fixture"
    call.mkdir(parents=True)
    event = {
        "type": "conversation_item_added",
        "received_at": 123,
        "data": {
            "item": {
                "type": "message",
                "role": "assistant",
                "id": "one",
                "content": ["Hello"],
                "interrupted": True,
            }
        },
    }
    content = json.dumps(event) + "\n" + json.dumps(event) + '\n{"truncated"'
    (call / "events.jsonl").write_text(content)
    manager.slot.acquire()
    manager.slot.save({"phase": "ended", "call_id": call.name})
    manager.slot.release()
    assert manager.snapshot()["live_turns"] == [
        {"idx": 0, "role": "patient", "text": "Hello", "status": "partial"}
    ]
    assert (call / "events.jsonl").read_text() == content


def test_disk_failure_during_stop_cannot_prevent_provider_cleanup(tmp_path, monkeypatch):
    async def run():
        backend = Backend(tmp_path, "active")
        manager = CallManager(tmp_path, lambda: backend, poll=0.001)
        result = await manager.start("smoke", manager.start_token, "disk-failure-request")
        await wait_phase(manager, "connected")

        def unavailable(_record):
            raise OSError("private disk path")

        monkeypatch.setattr(manager.slot, "save", unavailable)
        with pytest.raises(ControlError, match="Stop was requested"):
            await manager.stop(result["call_id"])
        with pytest.raises(OSError):
            await manager.task
        assert backend.actions[-3:] == ["hangup", "close", "hangup"]
        assert manager.slot.handle is None
        assert manager.snapshot()["phase"] == "recovery_required"

    asyncio.run(run())


def test_cancelled_startup_still_closes_owned_resources(tmp_path):
    async def run():
        backend = Backend(tmp_path, "slow_prepare")
        manager = CallManager(tmp_path, lambda: backend)
        await manager.start("smoke", manager.start_token, "cancel-request-123")
        while "prepare" not in backend.actions:
            await asyncio.sleep(0)
        manager.task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await manager.task
        assert backend.actions[-3:] == ["hangup", "close", "hangup"]
        assert manager.slot.handle is None

    asyncio.run(run())


def test_live_startup_waits_for_journal_but_preserves_read_failures(tmp_path):
    async def run():
        manager = CallManager(tmp_path, lambda: None)
        call = tmp_path / "calls" / "call-pending-fixture"
        call.mkdir(parents=True)
        manager.operation = {"phase": "preparing_worker", "call_id": call.name}
        manager.task = asyncio.create_task(asyncio.Event().wait())
        journal = call / "events.jsonl"
        try:
            for phase in (
                "preparing_worker",
                "dispatching",
                "waiting_for_worker",
                "preparing_audio",
                "dialing",
                "connected",
            ):
                manager.operation["phase"] = phase
                snapshot = manager.snapshot()
                assert snapshot["live_turns"] == []
                assert "live_warning" not in snapshot
            journal.write_text("broken JSON\n{}\n")
            assert "live_warning" in manager.snapshot()
            journal.write_text("")
            assert "live_warning" not in manager.snapshot()
            journal.unlink()
            journal.symlink_to(call / "absent.jsonl")
            assert "live_warning" in manager.snapshot()
            journal.unlink()
            for phase in ("stopping", "finalizing", "ended", "failed", "recovery_required"):
                manager.operation["phase"] = phase
                assert "live_warning" in manager.snapshot()
        finally:
            manager.task.cancel()
            await asyncio.gather(manager.task, return_exceptions=True)

    asyncio.run(run())
