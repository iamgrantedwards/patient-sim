import pytest


@pytest.fixture
def configured(monkeypatch):
    from src.caller.config import load
    values = {
        'LIVEKIT_URL': 'wss://fixture.livekit.cloud',
        'LIVEKIT_API_KEY': 'fixture-key', 'LIVEKIT_API_SECRET': 'fixture-secret',
        'SIP_OUTBOUND_TRUNK_ID': 'ST_fixture', 'CALLER_ID': '+12025550123',
        'TARGET_NUMBER': '+18054398008', 'TTS_VOICE': 'fixture-voice',
        'MAX_CALL_SECONDS': '240', 'MAX_TURNS': '40', 'RINGING_TIMEOUT_SECONDS': '30',
        'TURN_DETECTION': 'stt', 'ENDPOINTING_MODE': 'dynamic',
        'ENDPOINTING_MIN_DELAY': '0.4', 'ENDPOINTING_MAX_DELAY': '6',
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)
    return load()
