"""Bounded, allowlisted projections of local evidence; original files are never changed."""

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, StrictBool, StrictInt, StrictStr, ValidationError

CALL_ID = re.compile(r"[a-z0-9][a-z0-9-]{1,79}\Z")
MAX_JSON = 2 * 1024 * 1024
MAX_AUDIO = 64 * 1024 * 1024
MAX_CALLS = 1000


class ArtifactError(ValueError):
    """Safe message for a missing, malformed, or unsafe evidence file."""


class Turn(BaseModel):
    idx: StrictInt
    role: Literal["patient", "remote"]
    text: StrictStr
    status: Literal["completed", "partial"]
    interrupted: StrictBool = False
    audio_start_ms: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    audio_end_ms: float | None = Field(default=None, ge=0, allow_inf_nan=False)


class Transcript(BaseModel):
    call_id: StrictStr
    turns: list[Turn] = Field(max_length=1000)
    claimed_state: dict | str | None = None
    consistency: dict | str | None = None
    verified_state: dict | str | None = None


def obj(value) -> dict:
    return value if isinstance(value, dict) else {}


def string(value, default="Unknown") -> str:
    return value if isinstance(value, str) and value else default


def number(value) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
        return result if math.isfinite(result) and result >= 0 else None
    except (ValueError, TypeError, OverflowError):
        return None


def reject_nonfinite(_constant: str):
    raise ArtifactError("Artifact cannot contain non-finite JSON numbers.")


def finite_float(value: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ArtifactError("Artifact cannot contain non-finite JSON numbers.")
    return result


class EvidenceStore:
    def __init__(self, root: Path):
        self.root = root.resolve()

    def directory(self, call_id: str) -> Path:
        if not CALL_ID.fullmatch(call_id):
            raise ArtifactError("Invalid call identifier.")
        directory = self.root / call_id
        if (
            directory.is_symlink()
            or not directory.is_dir()
            or directory.resolve().parent != self.root
        ):
            raise ArtifactError("Call not found.")
        return directory

    def file(self, call_id: str, name: str, limit=MAX_JSON) -> Path:
        directory = self.directory(call_id)
        path = directory / name
        if path.is_symlink() or not path.is_file() or path.resolve().parent != directory:
            raise ArtifactError("Artifact is unavailable.")
        if path.stat().st_size > limit:
            raise ArtifactError("Artifact exceeds the local review size limit.")
        return path

    def read(self, call_id: str, name: str) -> dict:
        try:
            # Read a bounded amount even if a local writer grows the file after stat.
            with self.file(call_id, name).open("rb") as stream:
                raw = stream.read(MAX_JSON + 1)
            if len(raw) > MAX_JSON:
                raise ArtifactError("Artifact exceeds the local review size limit.")
            data = json.loads(raw, parse_constant=reject_nonfinite, parse_float=finite_float)
            if not isinstance(data, dict):
                raise ArtifactError("Artifact must contain a JSON object.")
            return data
        except (OSError, UnicodeError, ValueError, RecursionError) as error:
            raise ArtifactError("Artifact cannot be read as valid JSON.") from error

    def audio(self, call_id: str) -> Path:
        # Ignore file paths supplied by metadata. Prefer the preserved original recording.
        for name in ("recording.ogg", "recording.mp3"):
            try:
                path = self.file(call_id, name, MAX_AUDIO)
                if path.stat().st_size > 0:
                    return path
            except ArtifactError:
                continue
        raise ArtifactError("No supported original recording is available.")

    def detail(self, call_id: str, *, fingerprint=False) -> dict:
        meta = self.read(call_id, "meta.json")
        if meta.get("call_id") != call_id:
            raise ArtifactError("Call identifier does not match its metadata.")
        warnings = []
        transcript = None
        try:
            transcript = Transcript.model_validate(self.read(call_id, "transcript.json"))
            if transcript.call_id != call_id:
                raise ArtifactError("Call identifier does not match its transcript.")
        except (ArtifactError, ValidationError):
            warnings.append(
                "Transcript unavailable or invalid. Original files have been preserved."
            )
            transcript = None
        audio = None
        try:
            audio = self.audio(call_id)
        except ArtifactError:
            warnings.append("Recording unavailable. This call is not an audio/transcript pair.")
        recording = obj(meta.get("recording"))
        pipeline = obj(meta.get("pipeline"))
        turns = [turn.model_dump(mode="json") for turn in transcript.turns] if transcript else []
        partial_count = sum(turn["status"] == "partial" or turn["interrupted"] for turn in turns)
        if partial_count:
            warnings.append("Incomplete speech is present. Listen before drawing a conclusion.")
        listened = recording.get("listened_by_human")
        listened = listened if isinstance(listened, bool) else None
        duration = number(obj(obj(recording.get("probe")).get("format")).get("duration"))
        if not audio:
            duration = None
        digest = None
        if audio and fingerprint:
            with audio.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
        endpoints = obj(pipeline.get("endpointing"))
        result = {
            "call_id": call_id,
            "scenario": string(meta.get("scenario_id")),
            "started_at": number(meta.get("started_at")),
            "status": string(meta.get("status")),
            "ended_by": string(meta.get("ended_by"), "Not recorded"),
            "duration_seconds": duration,
            "turn_count": len(turns),
            "partial_turns": partial_count,
            "transcript_available": transcript is not None,
            "recording": {
                "available": audio is not None,
                "url": f"/api/calls/{call_id}/audio" if audio else None,
                "format": audio.suffix[1:].upper() if audio else None,
                "decode_status": string(recording.get("status"), "Not recorded"),
                "listened_by_human": listened,
                "sha256": digest,
            },
            "pipeline": {
                **{
                    key: string(pipeline.get(key))
                    for key in ("stt", "llm", "tts", "tts_voice", "turn_detection")
                },
                "endpointing_mode": string(endpoints.get("mode")),
                "min_delay": number(endpoints.get("min_delay")),
                "max_delay": number(endpoints.get("max_delay")),
            },
            "provenance": {
                "git_revision": string(meta.get("git_revision")),
                "git_dirty": meta.get("git_dirty")
                if isinstance(meta.get("git_dirty"), bool)
                else None,
                "scenario_version": str(meta["scenario_version"])
                if type(meta.get("scenario_version")) in (str, int)
                else "Unknown",
                "sdk_version": string(meta.get("sdk_version")),
                "prompt_sha256": string(meta.get("prompt_sha256")),
            },
            "claims": {
                key: getattr(transcript, key) if transcript else None
                for key in ("claimed_state", "consistency", "verified_state")
            },
            "turns": turns,
            "warnings": warnings,
        }
        return result

    def listing(self) -> dict:
        try:
            entries = (
                sorted(self.root.iterdir(), key=lambda path: path.name, reverse=True)
                if self.root.exists()
                else []
            )
        except OSError as error:
            raise ArtifactError("The calls directory cannot be read.") from error
        eligible = [
            p for p in entries if CALL_ID.fullmatch(p.name) and p.is_dir() and not p.is_symlink()
        ]
        calls = []
        for entry in eligible[:MAX_CALLS]:
            try:
                detail = self.detail(entry.name)
                calls.append(
                    {
                        key: detail[key]
                        for key in (
                            "call_id",
                            "scenario",
                            "started_at",
                            "status",
                            "ended_by",
                            "duration_seconds",
                            "turn_count",
                            "partial_turns",
                            "recording",
                            "transcript_available",
                            "warnings",
                        )
                    }
                )
            except (ArtifactError, OSError):
                calls.append(
                    {
                        "call_id": entry.name,
                        "scenario": "Unreadable artifacts",
                        "status": "unavailable",
                        "ended_by": "Unknown",
                        "started_at": None,
                        "duration_seconds": None,
                        "turn_count": 0,
                        "partial_turns": 0,
                        "recording": {"available": False, "listened_by_human": None},
                        "transcript_available": False,
                        "warnings": [
                            "Call artifacts could not be read. Original files have been preserved."
                        ],
                    }
                )
        return {"calls": calls, "truncated": len(eligible) > MAX_CALLS, "read_only": True}
