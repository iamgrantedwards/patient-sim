"""Environment configuration, with one safety rule that is not negotiable."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

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
    livekit_api_key: str
    livekit_api_secret: str
    sip_trunk_id: str
    target_number: str
    caller_id: str

    stt_model: str
    stt_language: str
    llm_model: str
    tts_model: str
    tts_voice: str

    turn_detection: str
    endpointing_mode: str
    endpointing_min_delay: float
    endpointing_max_delay: float

    max_call_seconds: int
    max_turns: int
    ringing_timeout_seconds: int

    judge_model: str

    @property
    def pipeline(self) -> dict[str, str]:
        """Recorded into every transcript so a call can be tied to its exact stack."""
        return {
            "stt": self.stt_model,
            "llm": self.llm_model,
            "tts": self.tts_model,
            "turn_detection": self.turn_detection,
            "endpointing_mode": self.endpointing_mode,
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
        turn_detection=os.getenv("TURN_DETECTION", "stt"),
        endpointing_mode=os.getenv("ENDPOINTING_MODE", "dynamic"),
        endpointing_min_delay=_f("ENDPOINTING_MIN_DELAY", 0.4),
        endpointing_max_delay=_f("ENDPOINTING_MAX_DELAY", 6.0),
        max_call_seconds=_i("MAX_CALL_SECONDS", 240),
        max_turns=_i("MAX_TURNS", 40),
        ringing_timeout_seconds=_i("RINGING_TIMEOUT_SECONDS", 30),
        judge_model=os.getenv("JUDGE_MODEL", "gpt-4.1"),
    )
