import pytest

from src.caller.lifecycle import session_end, sip_failure


@pytest.mark.parametrize(
    "code,expected",
    [
        (408, "no_answer"),
        (480, "no_answer"),
        (486, "rejected"),
        (603, "rejected"),
        (500, "sip_error"),
        (None, "sip_error"),
    ],
)
def test_sip_failures(code, expected):
    assert sip_failure(code) == expected


@pytest.mark.parametrize(
    "reason,prior,expected",
    [
        ("participant_disconnected", None, "remote_hangup"),
        ("error", None, "worker_error"),
        ("job_shutdown", None, "worker_shutdown"),
        ("participant_disconnected", "failsafe", "failsafe"),
        ("user_initiated", "end_call_tool", "end_call_tool"),
    ],
)
def test_session_end_preserves_attribution(reason, prior, expected):
    assert session_end(reason, prior) == expected


@pytest.mark.parametrize(
    "reason,expected",
    [
        ("MEDIA_FAILURE", "telephony_error"),
        ("CONNECTION_TIMEOUT", "telephony_error"),
        ("SIP_TRUNK_FAILURE", "sip_error"),
        ("USER_UNAVAILABLE", "no_answer"),
        ("USER_REJECTED", "rejected"),
        ("CLIENT_INITIATED", "remote_hangup"),
        ("SERVER_SHUTDOWN", "unknown_disconnect"),
    ],
)
def test_network_disconnects_are_not_all_remote_hangups(reason, expected):
    from src.caller.lifecycle import disconnect_end

    assert disconnect_end(reason) == expected
