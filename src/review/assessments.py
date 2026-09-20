"""Explicit local assessment requests; immutable originals and separate human reviews."""

import asyncio
import fcntl
import hashlib
import json
import os
import secrets
import tempfile
from datetime import UTC, datetime

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import Field

from src.analysis.assessment import (
    PROMPT,
    RUBRIC_VERSION,
    Assessment,
    StrictModel,
    score,
    validate_evidence,
)

from .reviews import fingerprints

PROMPT_SHA = hashlib.sha256(PROMPT.encode()).hexdigest()


class SavedAssessment(StrictModel):
    call_id: str
    created_at: str
    model: str
    rubric: str
    prompt_sha256: str
    fingerprints: dict[str, str | None]
    result: Assessment


class History(StrictModel):
    revisions: list[SavedAssessment] = Field(min_length=1, max_length=10)


def load(store, call_id):
    path = store.directory(call_id) / "assessment.json"
    if not path.exists() and not path.is_symlink():
        return []
    records = History.model_validate(store.read(call_id, "assessment.json")).revisions
    if any(r.call_id != call_id for r in records):
        raise ValueError("Assessment call mismatch.")
    return records


def eligible(detail):
    return (
        detail["status"] == "ended"
        and detail["ended_by"] in ("end_call_tool", "remote_hangup")
        and detail["recording"]["available"]
        and {t["role"] for t in detail["turns"] if t["status"] == "completed"}
        == {"patient", "remote"}
    )


def install(app, store, judge=None):
    token = secrets.token_urlsafe(32)
    busy = asyncio.Lock()

    def state(call_id):
        detail = store.detail(call_id)
        try:
            records = load(store, call_id)
        except ValueError:
            return {"status": "unavailable", "enabled": False, "eligible": False}
        latest = records[-1] if records else None
        current = fingerprints(store, call_id)
        stale = bool(
            latest
            and (
                latest.fingerprints != current
                or latest.rubric != RUBRIC_VERSION
                or latest.prompt_sha256 != PROMPT_SHA
                or (judge is not None and latest.model != judge.model)
            )
        )
        return {
            "status": "stale" if stale else "saved" if latest else "pending",
            "enabled": judge is not None,
            "token": token if judge is not None else None,
            "eligible": eligible(detail),
            "latest": latest.model_dump() if latest else None,
            "score": score(latest.result) if latest and not stale else None,
        }

    @app.get("/api/calls/{call_id}/assessment")
    def get_assessment(call_id: str):
        return state(call_id)

    @app.post("/api/calls/{call_id}/assessment")
    async def assess(call_id: str, request: Request):
        def error(message, status):
            return JSONResponse({"error": message}, status_code=status)

        if judge is None:
            return error("AI assessment is disabled.", 405)
        if request.headers.get(
            "origin"
        ) != f"http://{request.headers.get('host')}" or not secrets.compare_digest(
            request.headers.get("x-assessment-token", ""), token
        ):
            return error("Refresh before requesting an assessment.", 403)
        # No client-supplied transcript, model, prompt, path or large request body.
        async for chunk in request.stream():
            if chunk:
                return error("Assessment requests do not accept a body.", 400)
        if busy.locked():
            return error("An assessment is running. Try again when it finishes.", 409)
        async with busy:
            directory = store.directory(call_id)
            fd = os.open(
                directory / ".assessment.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600
            )
            with os.fdopen(fd, "w") as lock:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    return error("An assessment is already running for this call.", 409)
                current = state(call_id)
                if current["status"] == "unavailable":
                    return error(
                        "Saved assessment cannot be read. Original files are preserved.", 409
                    )
                if current["status"] == "saved":
                    return current
                if not current["eligible"]:
                    return error(
                        "Insufficient evidence: a finished conversation, both speakers and recording are required.",
                        422,
                    )
                records = load(store, call_id)
                if len(records) >= 10:
                    return error("Assessment revision limit reached.", 409)
                before = fingerprints(store, call_id)
                detail = store.detail(call_id)
                evidence = {"scenario": detail["scenario"], "turns": detail["turns"]}
                if len(json.dumps(evidence)) > 60000:
                    return error("Transcript exceeds the assessment size limit.", 422)
                try:
                    result = await asyncio.wait_for(judge(evidence), timeout=90)
                    validate_evidence(result, detail["turns"])
                except Exception:
                    # Provider exceptions may include credentials or transcript content.
                    return error(
                        "Assessment failed or returned unsupported evidence. Nothing was saved; retry when ready.",
                        502,
                    )
                if fingerprints(store, call_id) != before:
                    return error("Evidence changed during assessment. Refresh and retry.", 409)
                records.append(
                    SavedAssessment(
                        call_id=call_id,
                        created_at=datetime.now(UTC).isoformat(),
                        model=judge.model,
                        rubric=RUBRIC_VERSION,
                        prompt_sha256=PROMPT_SHA,
                        fingerprints=before,
                        result=result,
                    )
                )
                fd, name = tempfile.mkstemp(prefix=".assessment-", dir=directory)
                try:
                    with os.fdopen(fd, "w") as output:
                        output.write(History(revisions=records).model_dump_json(indent=2) + "\n")
                        output.flush()
                        os.fsync(output.fileno())
                    os.replace(name, directory / "assessment.json")
                finally:
                    if os.path.exists(name):
                        os.unlink(name)
                return state(call_id)
