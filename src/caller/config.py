"""Environment configuration, with one safety rule that is not negotiable."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, cast
from urllib.parse import urlsplit

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

# The assessment permits exactly one destination. The athena signup flow shows a
# different number on its confirmation screen and the brief explicitly says not to
# call it, so the allowlist is enforced in code rather than left to discipline.
PERMITTED_TARGET = "+18054398008"


class NotPermittedError(RuntimeError):
    pass


def _req(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is not set. Copy .env.example to .env and fill it in.")
    return value


def _f(name: str, default: float) -> float:
    return float(os.getenv(name, "") or default)


def _i(name: str, default: int) -> int:
    return int(os.getenv(name, "") or default)


@dataclass(frozen=True)
class Config:
    livekit_url: str
    livekit_api_key: str = field(repr=False)
    livekit_api_secret: str = field(repr=False)
    sip_trunk_id: str
    target_number: str
    caller_id: str

    stt_model: str
    stt_language: str
    llm_model: str
    tts_model: str
    tts_voice: str

    turn_detection: Literal["stt", "vad", "default"]
    endpointing_mode: Literal["fixed", "dynamic"]
    endpointing_min_delay: float
    endpointing_max_delay: float

    max_call_seconds: int
    max_turns: int
    ringing_timeout_seconds: int

    judge_model: str

    def __post_init__(self):
        if self.target_number != PERMITTED_TARGET:
            raise NotPermittedError("Only the assessment destination is permitted")
        if not re.fullmatch(r"\+[1-9][0-9]{7,14}", self.caller_id):
            raise ValueError("CALLER_ID must be the owned Twilio DID in E.164")
        url = urlsplit(self.livekit_url)
        if url.scheme != "wss" or not (url.hostname or "").endswith(".livekit.cloud"):
            raise ValueError("LIVEKIT_URL must be a LiveKit Cloud wss URL")
        if not self.sip_trunk_id.startswith("ST_") or len(self.sip_trunk_id) < 6:
            raise ValueError("SIP_OUTBOUND_TRUNK_ID is incomplete")
        if not self.tts_voice:
            raise ValueError("TTS_VOICE must name an explicitly selected Cartesia voice")
        if self.turn_detection not in ("stt", "vad", "default"):
            raise ValueError("TURN_DETECTION must be stt, vad, or default")
        if self.endpointing_mode not in ("fixed", "dynamic"):
            raise ValueError("ENDPOINTING_MODE must be fixed or dynamic")
        if not 0 <= self.endpointing_min_delay <= self.endpointing_max_delay <= 10:
            raise ValueError("Endpointing delays must be ordered within 0..10 seconds")
        if not 1 <= self.max_call_seconds <= 240 or not 1 <= self.max_turns <= 40:
            raise ValueError("Call limits cannot exceed 240 seconds or 40 turns")
        if not 5 <= self.ringing_timeout_seconds <= 60:
            raise ValueError("Ringing timeout must be 5..60 seconds")

    @property
    def pipeline(self) -> dict:
        """Explicit public provenance: never serialize credentials."""
        return {
            "stt": self.stt_model,
            "stt_language": self.stt_language,
            "llm": self.llm_model,
            "llm_temperature": 0.4,
            "tts": self.tts_model,
            "tts_voice": self.tts_voice,
            "turn_detection": self.turn_detection,
            "turn_detector_version": "v1-mini" if self.turn_detection == "default" else None,
            "endpointing": {
                "mode": self.endpointing_mode,
                "min_delay": self.endpointing_min_delay,
                "max_delay": self.endpointing_max_delay,
            },
            "interruption": {"mode": "vad"},
            "preemptive_generation": False,
            "ivr_detection": False,
            "noise_cancellation": False,
            "auto_gain_control": False,
        }


def load() -> Config:
    target = os.getenv("TARGET_NUMBER", PERMITTED_TARGET).strip()
    if target != PERMITTED_TARGET:
        raise NotPermittedError(
            f"TARGET_NUMBER is {target!r}. This bot may only dial {PERMITTED_TARGET}."
        )

    return Config(
        livekit_url=_req("LIVEKIT_URL"),
        livekit_api_key=_req("LIVEKIT_API_KEY"),
        livekit_api_secret=_req("LIVEKIT_API_SECRET"),
        sip_trunk_id=_req("SIP_OUTBOUND_TRUNK_ID"),
        target_number=target,
        caller_id=_req("CALLER_ID"),
        stt_model=os.getenv("STT_MODEL", "deepgram/flux-general-en"),
        stt_language=os.getenv("STT_LANGUAGE", "en"),
        llm_model=os.getenv("LLM_MODEL", "openai/gpt-4.1-mini"),
        tts_model=os.getenv("TTS_MODEL", "cartesia/sonic-3.6"),
        tts_voice=os.getenv("TTS_VOICE", ""),
        # Config.__post_init__ validates these narrowed environment values.
        turn_detection=cast(Literal["stt", "vad", "default"], os.getenv("TURN_DETECTION", "stt")),
        endpointing_mode=cast(
            Literal["fixed", "dynamic"], os.getenv("ENDPOINTING_MODE", "dynamic")
        ),
        endpointing_min_delay=_f("ENDPOINTING_MIN_DELAY", 0.4),
        endpointing_max_delay=_f("ENDPOINTING_MAX_DELAY", 6.0),
        max_call_seconds=_i("MAX_CALL_SECONDS", 240),
        max_turns=_i("MAX_TURNS", 40),
        ringing_timeout_seconds=_i("RINGING_TIMEOUT_SECONDS", 30),
        judge_model=os.getenv("JUDGE_MODEL", "gpt-4.1"),
    )
