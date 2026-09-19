import asyncio
from unittest.mock import AsyncMock

import pytest

from src.caller import dial


@pytest.mark.parametrize("phase", ["ended", "failed"])
def test_cli_uses_shared_one_call_manager(monkeypatch, configured, phase, capsys):
    state = {"phase": phase, "call_id": "call-cli-fixture", "message": "fixture failure"}
    instances = []

    class Manager:
        start_token = "token"
        task = None

        def __init__(self, *args, **kwargs):
            instances.append(self)

        async def start(self, scenario, token, request_id):
            assert scenario == "smoke" and token == "token" and request_id
            self.task = asyncio.create_task(asyncio.sleep(0))
            return state

        def snapshot(self):
            return state

    monkeypatch.setattr("src.caller.control.CallManager", Manager)
    if phase == "failed":
        with pytest.raises(RuntimeError, match="fixture failure"):
            asyncio.run(dial.dispatch("smoke"))
    else:
        asyncio.run(dial.dispatch("smoke"))
        assert "Call ended" in capsys.readouterr().out
    assert len(instances) == 1


def test_unknown_scenario_fails_before_provider_configuration():
    with pytest.raises(ValueError, match="Unknown scenario"):
        asyncio.run(dial.dispatch("unknown"))


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


def test_cli_interrupt_waits_for_controller_cleanup(monkeypatch, configured):
    instances = []

    class Manager:
        start_token = "token"
        task = None

        def __init__(self, *args, **kwargs):
            self.shutdown = AsyncMock(side_effect=self.cleanup)
            instances.append(self)

        async def start(self, *args):
            self.task = asyncio.create_task(asyncio.Event().wait())
            return {"call_id": "call-interrupted"}

        async def cleanup(self):
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)

    monkeypatch.setattr("src.caller.control.CallManager", Manager)

    async def run():
        task = asyncio.create_task(dial.dispatch("smoke"))
        while not instances or instances[0].task is None:
            await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        instances[0].shutdown.assert_awaited_once()
        assert instances[0].task.done()

    asyncio.run(run())
