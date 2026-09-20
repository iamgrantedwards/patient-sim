"""One accepted job per managed call, with private assignment diagnostics."""

import json
import os
import re
import time
from pathlib import Path

from livekit.agents import JobRequest

from .config import PROJECT_ROOT


class SingleCallAdmission:
    def __init__(self, root: Path, call_id: str):
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,79}", call_id):
            raise ValueError("Invalid managed call identifier")
        self.root = root
        self.call_id = call_id
        self.accepted = False

    def record(self, request: JobRequest, decision: str):
        entry = {
            "at": time.time(),
            "call_id": self.call_id,
            "job_id": request.job.id,
            "dispatch_id": request.job.dispatch_id,
            "room": request.job.room.name,
            "decision": decision,
        }
        path = self.root / ".runtime" / f"{self.call_id}-jobs.jsonl"
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, "w") as output:
            output.write(json.dumps(entry) + "\n")

    async def __call__(self, request: JobRequest):
        try:
            metadata = json.loads(request.job.metadata or "{}")
        except ValueError:
            metadata = None
        if (
            not isinstance(metadata, dict)
            or metadata.get("call_id") != self.call_id
            or request.job.room.name != self.call_id
        ):
            decision = "rejected_identity"
        elif self.accepted:
            decision = "rejected_duplicate"
        elif (self.root / "calls" / self.call_id / "events.jsonl").exists():
            decision = "rejected_existing_evidence"
        else:
            decision = "accepting"
            # Latch before any await: simultaneous offers and uncertain accepts cannot retry.
            self.accepted = True
        try:
            self.record(request, decision)
        except OSError:
            await request.reject()
            raise
        if decision != "accepting":
            await request.reject()
            return
        try:
            await request.accept()
        except Exception:
            self.record(request, "accept_failed")
            raise


_admission: SingleCallAdmission | None = None


async def accept_job(request: JobRequest):
    global _admission
    managed_call = os.environ.get("PATIENT_SIM_CALL_ID")
    if not managed_call:
        # Legacy explicitly launched agent: evidence creation still protects each call ID.
        await request.accept()
        return
    if _admission is None:
        _admission = SingleCallAdmission(PROJECT_ROOT, managed_call)
    await _admission(request)
