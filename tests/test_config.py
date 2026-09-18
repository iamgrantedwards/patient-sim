import pytest

from src.caller.config import NotPermittedError, PERMITTED_TARGET, load


@pytest.mark.parametrize("target", ["+18005550100", "18054398008", "", "+18054398008;other"])
def test_disallowed_destination_rejected_before_credentials(monkeypatch, target):
    monkeypatch.setenv("TARGET_NUMBER", target)
    with pytest.raises(NotPermittedError):
        load()


def test_missing_credentials_fail_locally(monkeypatch):
    monkeypatch.setenv("TARGET_NUMBER", PERMITTED_TARGET)
    monkeypatch.delenv("LIVEKIT_URL", raising=False)
    with pytest.raises(RuntimeError, match="LIVEKIT_URL is not set"):
        load()
