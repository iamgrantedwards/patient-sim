"""Pure outcome rules, shared by runtime and fixture tests."""


def sip_failure(status_code: int | None) -> str:
    if status_code in (408, 480):
        return 'no_answer'
    if status_code in (486, 603):
        return 'rejected'
    return 'sip_error'


def session_end(reason: str, prior: str | None = None) -> str:
    if prior:
        return prior
    if reason == 'participant_disconnected':
        return 'remote_hangup'
    if reason == 'error':
        return 'worker_error'
    return 'worker_shutdown'


def disconnect_end(reason: str) -> str:
    return {
        'CLIENT_INITIATED': 'remote_hangup',
        'USER_UNAVAILABLE': 'no_answer',
        'USER_REJECTED': 'rejected',
        'SIP_TRUNK_FAILURE': 'sip_error',
        'MEDIA_FAILURE': 'telephony_error',
        'CONNECTION_TIMEOUT': 'telephony_error',
    }.get(reason, 'unknown_disconnect')
