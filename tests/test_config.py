import pytest

from src.caller.config import PERMITTED_TARGET, NotPermittedError, load


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


@pytest.mark.parametrize(
    "name,value",
    [
        ("CALLER_ID", "+1"),
        ("MAX_CALL_SECONDS", "999"),
        ("MAX_TURNS", "0"),
        ("TTS_VOICE", ""),
        ("ENDPOINTING_MIN_DELAY", "9"),
        ("LIVEKIT_URL", "https://example.com"),
        ("SIP_OUTBOUND_TRUNK_ID", "ST_"),
    ],
)
def test_invalid_settings_fail_before_dialing(monkeypatch, configured, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError):
        load()


def test_public_provenance_and_repr_do_not_contain_credentials(configured):
    assert "fixture-secret" not in repr(configured)
    assert "fixture-key" not in str(configured.pipeline)
