"""Local human judgments, versioned separately from immutable call evidence."""

import fcntl
import hashlib
import json
import os
import secrets
import tempfile
from datetime import UTC, datetime
from typing import Literal

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from .store import MAX_AUDIO, ArtifactError

CRITERIA = ("completeness", "transcript", "patient", "turn_taking", "pacing", "audio", "ending")


class Check(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    result: Literal["not_assessed", "ok", "issue"]
    note: str = Field(max_length=1200)

    @model_validator(mode="after")
    def explain_issue(self):
        if self.result == "issue" and not self.note.strip():
            raise ValueError("Issues need an observation and timestamp, or timing uncertainty.")
        return self


class Review(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    reviewer: str = Field(min_length=1, max_length=100, pattern=r"\S")
    listened: bool
    suitability: Literal["needs_recheck", "usable", "incomplete"]
    checks: dict[str, Check]
    summary: str = Field(max_length=2000)
    base_revision: int = Field(ge=0, le=100)
    fingerprints: dict[str, str | None]

    @model_validator(mode="after")
    def complete_checks(self):
        if set(self.checks) != set(CRITERIA):
            raise ValueError("All seven checks are required.")
        if self.suitability == "usable" and (
            not self.listened or self.checks["completeness"].result != "ok"
        ):
            raise ValueError("Usable conversations require listening and complete evidence.")
        return self


def fingerprints(store, call_id):
    result = {}
    for name in ("meta.json", "transcript.json", "recording.ogg", "recording.mp3"):
        try:
            path = store.file(call_id, name, MAX_AUDIO)
            with path.open("rb") as stream:
                result[name] = hashlib.file_digest(stream, "sha256").hexdigest()
        except ArtifactError:
            result[name] = None
    return result


def history(store, call_id):
    path = store.directory(call_id) / "review.json"
    if not path.exists() and not path.is_symlink():
        return []
    data = store.read(call_id, "review.json")
    revisions = data.get("revisions")
    if data.get("call_id") != call_id or not isinstance(revisions, list) or not revisions:
        raise ArtifactError("Review history is invalid. Original files are preserved.")
    for index, item in enumerate(revisions):
        try:
            Review.model_validate(item["review"])
            if item["revision"] != index + 1 or not isinstance(item["saved_at"], str):
                raise ValueError
        except (KeyError, TypeError, ValueError):
            raise ArtifactError(
                "Review history is invalid. Original files are preserved."
            ) from None
    return revisions


def project(store, detail):
    """Legacy flags remain visible as provenance, never count as current acceptance."""
    current = fingerprints(store, detail["call_id"])
    try:
        revisions = history(store, detail["call_id"])
    except ArtifactError:
        detail["review"] = {"status": "unavailable", "listened": False, "usable": False}
        return detail
    latest = revisions[-1] if revisions else None
    stale = bool(latest and latest["review"]["fingerprints"] != current)
    paired = detail["recording"]["available"] and detail["transcript_available"]
    listened = bool(latest and not stale and paired and latest["review"]["listened"])
    detail["review"] = {
        "status": "stale" if stale else "saved" if latest else "pending",
        "listened": listened,
        "usable": bool(listened and latest and latest["review"]["suitability"] == "usable"),
        "revision": len(revisions),
        "latest": latest,
        "fingerprints": current,
        "history": revisions,
    }
    return detail


def install(app, store, enabled):
    token = secrets.token_urlsafe(32)

    @app.get("/api/reviews")
    def configuration():
        return {"enabled": enabled, "token": token if enabled else None}

    @app.post("/api/calls/{call_id}/review")
    async def save(call_id: str, request: Request):
        def error(message, status):
            return JSONResponse({"error": message}, status_code=status)

        if not enabled:
            return error("Review saving is disabled.", 405)
        if request.headers.get(
            "origin"
        ) != f"http://{request.headers.get('host')}" or not secrets.compare_digest(
            request.headers.get("x-review-token", ""), token
        ):
            return error("Refresh the local review session before saving.", 403)
        if request.headers.get("content-type", "").split(";")[0] != "application/json":
            return error("Use an application/json request.", 415)
        raw = bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw) > 16000:
                return error("Review is too large.", 413)
        try:
            review = Review.model_validate_json(raw)
        except ValidationError:
            return error(
                "Check the review fields. Issues need notes; usable calls need listening and complete evidence.",
                422,
            )
        directory = store.directory(call_id)
        # Serialize writers across threads/processes without modifying any call artifacts.
        descriptor = os.open(
            directory / ".review.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600
        )
        with os.fdopen(descriptor, "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            detail = project(store, store.detail(call_id))
            state = detail["review"]
            if state["status"] == "unavailable":
                return error("Review history cannot be read. Resolve it before saving.", 409)
            if (
                review.base_revision != state["revision"]
                or review.fingerprints != state["fingerprints"]
            ):
                return error(
                    "Evidence or review changed. Refresh and review again before saving.", 409
                )
            if review.listened and not (
                detail["recording"]["available"] and detail["transcript_available"]
            ):
                return error("Listening completion requires audio and transcript.", 422)
            if review.suitability == "usable" and {t["role"] for t in detail["turns"]} != {
                "patient",
                "remote",
            }:
                return error("A usable conversation requires both participants.", 422)
            revisions = state["history"]
            if len(revisions) >= 100:
                return error("Review revision limit reached.", 409)
            revisions.append(
                {
                    "revision": len(revisions) + 1,
                    "saved_at": datetime.now(UTC).isoformat(),
                    "review": review.model_dump(),
                }
            )
            data = json.dumps({"call_id": call_id, "revisions": revisions}, indent=2) + "\n"
            descriptor, name = tempfile.mkstemp(prefix=".review-", dir=directory)
            try:
                with os.fdopen(descriptor, "w") as output:
                    output.write(data)
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(name, directory / "review.json")
            finally:
                if os.path.exists(name):
                    os.unlink(name)
        return {"revision": len(revisions), "saved_at": revisions[-1]["saved_at"]}
