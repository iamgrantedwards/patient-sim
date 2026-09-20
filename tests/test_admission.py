import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.caller import admission
from src.caller.admission import SingleCallAdmission


def request(*, job_id="job-one", metadata='{"call_id":"call-fixture"}', room="call-fixture"):
    return SimpleNamespace(
        job=SimpleNamespace(
            id=job_id,
            dispatch_id="dispatch-fixture",
            metadata=metadata,
            room=SimpleNamespace(name=room),
        ),
        accept=AsyncMock(),
        reject=AsyncMock(),
    )


@pytest.fixture
def guard(tmp_path):
    (tmp_path / ".runtime").mkdir()
    return SingleCallAdmission(tmp_path, "call-fixture")


def test_concurrent_assignments_accept_only_once_and_record_identity(guard):
    first, second = request(), request(job_id="job-two")

    async def run():
        gate = asyncio.Event()
        first.accept.side_effect = gate.wait
        task = asyncio.create_task(guard(first))
        await asyncio.sleep(0)
        await guard(second)
        second.reject.assert_awaited_once()
        second.accept.assert_not_awaited()
        gate.set()
        await task

    asyncio.run(run())
    first.accept.assert_awaited_once()
    entries = [
        json.loads(line)
        for line in (guard.root / ".runtime/call-fixture-jobs.jsonl").read_text().splitlines()
    ]
    assert [e["decision"] for e in entries] == ["accepting", "rejected_duplicate"]
    assert [e["job_id"] for e in entries] == ["job-one", "job-two"]
    assert all(e["dispatch_id"] == "dispatch-fixture" for e in entries)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"metadata": "{bad"},
        {"metadata": "[]"},
        {"metadata": '{"call_id":"call-other"}'},
        {"room": "call-other"},
    ],
)
def test_wrong_assignment_identity_is_rejected_without_consuming_slot(guard, kwargs):
    offered = request(**kwargs)
    asyncio.run(guard(offered))
    offered.reject.assert_awaited_once()
    offered.accept.assert_not_awaited()
    assert not guard.accepted


def test_existing_evidence_rejected_before_entrypoint(guard):
    directory = guard.root / "calls/call-fixture"
    directory.mkdir(parents=True)
    original = b"original journal\n"
    (directory / "events.jsonl").write_bytes(original)
    offered = request()
    asyncio.run(guard(offered))
    offered.accept.assert_not_awaited()
    offered.reject.assert_awaited_once()
    assert (directory / "events.jsonl").read_bytes() == original


def test_uncertain_acceptance_never_retries(guard):
    first, second = request(), request(job_id="job-two")
    first.accept.side_effect = TimeoutError("unknown remote acceptance")
    with pytest.raises(TimeoutError):
        asyncio.run(guard(first))
    asyncio.run(guard(second))
    second.accept.assert_not_awaited()
    second.reject.assert_awaited_once()


def test_diagnostic_write_failure_rejects_without_accepting(guard, monkeypatch):
    def fail(*args):
        raise OSError("fixture disk full")

    monkeypatch.setattr(guard, "record", fail)
    offered = request()
    with pytest.raises(OSError):
        asyncio.run(guard(offered))
    offered.accept.assert_not_awaited()
    offered.reject.assert_awaited_once()
    assert guard.accepted  # An uncertain attempt stays consumed.


def test_managed_callback_uses_guard_and_legacy_keeps_explicit_dispatch(tmp_path, monkeypatch):
    monkeypatch.setattr(admission, "_admission", None)
    monkeypatch.setattr(admission, "PROJECT_ROOT", tmp_path)
    monkeypatch.delenv("PATIENT_SIM_CALL_ID", raising=False)
    legacy = request()
    asyncio.run(admission.accept_job(legacy))
    legacy.accept.assert_awaited_once()
    (tmp_path / ".runtime").mkdir()
    monkeypatch.setenv("PATIENT_SIM_CALL_ID", "call-fixture")
    first, second = request(), request(job_id="job-two")
    asyncio.run(admission.accept_job(first))
    asyncio.run(admission.accept_job(second))
    first.accept.assert_awaited_once()
    second.reject.assert_awaited_once()
    with pytest.raises(ValueError):
        SingleCallAdmission(tmp_path, "../escape")
