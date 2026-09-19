"""One OS-locked call slot with a durable record for crash recovery."""

import fcntl
import json
from pathlib import Path

from .transcript import write_json


class CallBusy(RuntimeError):
    pass


class CallSlot:
    def __init__(self, root: Path):
        self.directory = root / ".runtime"
        self.path = self.directory / "active-call.json"
        self.handle = None

    def read(self) -> dict | None:
        if not self.path.exists():
            return None
        try:
            if self.path.stat().st_size > 32768:
                raise ValueError
            data = json.loads(self.path.read_text())
            if not isinstance(data, dict) or not isinstance(data.get("phase"), str):
                raise ValueError
            return data
        except (ValueError, OSError):
            # Fail closed: an unreadable record does not establish an empty call slot.
            return {"phase": "recovery_required", "error": "unreadable_operation"}

    def acquire(self):
        self.directory.mkdir(mode=0o700, exist_ok=True)
        handle = (self.directory / "call.lock").open("a+")
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            handle.close()
            raise CallBusy("Another console or CLI process owns the call slot.") from None
        self.handle = handle

    def save(self, record: dict):
        if self.handle is None:
            raise RuntimeError("Call slot must be locked before writing")
        write_json(self.path, record)
        self.path.chmod(0o600)

    def release(self):
        if self.handle is not None:
            fcntl.flock(self.handle, fcntl.LOCK_UN)
            self.handle.close()
            self.handle = None
