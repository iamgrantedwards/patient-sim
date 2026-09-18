import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from livekit import api

from src.caller import dial


@pytest.fixture
def dispatcher(monkeypatch, tmp_path, configured):
    create = AsyncMock(return_value=SimpleNamespace(id="dispatch-fixture"))
    delete = AsyncMock()
    client = SimpleNamespace(
        agent_dispatch=SimpleNamespace(create_dispatch=create),
        room=SimpleNamespace(delete_room=delete),
    )

    class API:
        def __init__(self, *args):
            pass

        async def __aenter__(self):
            return client

        async def __aexit__(self, *args):
            pass

    monkeypatch.setattr(api, "LiveKitAPI", API)
    monkeypatch.setattr(dial, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(dial, "load", lambda: configured)
    monkeypatch.setattr(dial.asyncio, "sleep", AsyncMock())
    return client, tmp_path


@pytest.mark.parametrize("failure", ["timeout", "provider", "cleanup"])
def test_dispatch_failure_is_recorded_and_never_retried(dispatcher, failure):
    client, root = dispatcher
    if failure == "provider":
        client.agent_dispatch.create_dispatch.side_effect = RuntimeError("private-provider-detail")
    if failure == "cleanup":
        client.room.delete_room.side_effect = OSError("private-cleanup-detail")
    with pytest.raises(RuntimeError, match="No automatic retry") as error:
        asyncio.run(dial.dispatch("smoke"))
    client.agent_dispatch.create_dispatch.assert_awaited_once()
    client.room.delete_room.assert_awaited_once()
    record_path = next(root.glob("calls/*/dispatch.json"))
    record = json.loads(record_path.read_text())
    assert record["status"] == "dispatch_error"
    assert record["error_type"] == ("RuntimeError" if failure == "provider" else "TimeoutError")
    assert record["cleanup"] == ("OSError" if failure == "cleanup" else "room_deleted")
    assert client.room.delete_room.call_args.args[0].room == record["call_id"]
    assert "private-" not in record_path.read_text() + str(error.value)


def test_worker_acceptance_returns_without_cleanup_or_retry(dispatcher, capsys):
    client, root = dispatcher

    async def accept(request):
        metadata = json.loads(request.metadata)
        assert request.agent_name == "patient-sim"
        assert metadata["scenario"] == "smoke"
        assert request.room == metadata["call_id"]
        (root / "calls" / request.room / "meta.json").write_text("{}")
        return SimpleNamespace(id="dispatch-fixture")

    client.agent_dispatch.create_dispatch.side_effect = accept
    asyncio.run(dial.dispatch("smoke"))
    client.agent_dispatch.create_dispatch.assert_awaited_once()
    client.room.delete_room.assert_not_awaited()
    assert "Worker accepted" in capsys.readouterr().out


def test_default_cli_cannot_dispatch(monkeypatch, capsys):
    dispatch = AsyncMock()
    monkeypatch.setattr(dial, "dispatch", dispatch)
    monkeypatch.setattr("sys.argv", ["patient-sim"])
    dial.main()
    dispatch.assert_not_called()
    assert "no call placed" in capsys.readouterr().out


def test_cli_requires_explicit_call_flag(monkeypatch):
    dispatch = AsyncMock()
    monkeypatch.setattr(dial, "dispatch", dispatch)
    monkeypatch.setattr("sys.argv", ["patient-sim", "--scenario", "smoke", "--call"])
    dial.main()
    dispatch.assert_awaited_once_with("smoke")
