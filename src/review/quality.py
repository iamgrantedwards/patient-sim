"""Call-review coverage: local facts, AI text checks and explicit listening gaps."""


def capture_context(detail):
    return {
        "status": detail["status"],
        "ended_by": detail["ended_by"],
        "duration_seconds": detail["duration_seconds"],
        "recording_available": detail["recording"]["available"],
        "decode_status": detail["recording"]["decode_status"],
        "partial_turns": detail["partial_turns"],
        "uncommitted_transcriptions": detail["uncommitted_transcriptions"],
        **detail["termination"],
    }


def quality_checks(detail, result=None):
    complete = (
        detail["recording"]["available"]
        and detail["transcript_available"]
        and detail["status"] == "ended"
        and detail["recording"]["decode_status"] == "decoded"
        and {t["role"] for t in detail["turns"]} == {"patient", "remote"}
        and detail["uncommitted_transcriptions"] == 0
    )
    checks = [
        {
            "topic": "completeness",
            "source": "Local files",
            "result": "files_present" if complete else "attention",
            "rationale": "Recording decoded and transcript contains both speakers. This does not establish a complete audible conversation."
            if complete
            else "Capture checks are incomplete: check file availability, decode status, both speakers and pending speech.",
            "next_step": "Listen for both voices and a complete ending before marking the call usable.",
            "evidence": [],
        }
    ]
    text_checks = {c.topic: c.model_dump() for c in result.call_quality or []} if result else {}
    listening = {
        "transcript": (
            "Transcription accuracy needs comparison with the recording.",
            "Compare names, dates and important instructions with what is audible.",
        ),
        "pacing": (
            "No audio-aligned pause or response measurements are available.",
            "Listen for long gaps or rushed replies; transcript arrival times are not speech timing.",
        ),
        "audio": (
            "A decodable recording does not establish intelligibility or freedom from clipping.",
            "Listen for both voices, distortion, dropouts and clipped speech.",
        ),
    }
    for topic in ("transcript", "patient", "turn_taking", "pacing", "audio", "ending"):
        if topic in listening:
            rationale, action = listening[topic]
            check = {
                "topic": topic,
                "source": "Audio needed",
                "result": "needs_audio",
                "rationale": rationale,
                "next_step": action,
                "evidence": [],
            }
        elif topic in text_checks:
            check = {**text_checks[topic], "source": "AI · transcript"}
        else:
            check = {
                "topic": topic,
                "source": "AI · transcript",
                "result": "not_assessed",
                "rationale": "Request a current AI assessment to include this check.",
                "next_step": "Assess the transcript, then confirm concerns against the recording.",
                "evidence": [],
            }
        if topic == "ending":
            reason = {
                "end_call_tool": "Our caller requested hangup",
                "remote_hangup": "The other participant hung up",
                "failsafe": "A safety limit ended the call",
            }.get(detail["ended_by"]) or (
                "Recorded ending: " + detail["ended_by"].replace("_", " ")
            )
            context = reason + ". This does not verify a clean audible ending."
            if detail["turns"]:
                last = detail["turns"][-1]
                if (
                    last["status"] == "partial"
                    or last["interrupted"]
                    or last["text"].rstrip().endswith(("...", "…"))
                ):
                    context += (
                        " The final transcript turn contains incomplete speech; possible cutoff."
                    )
            if detail["termination"]["duration_limit_may_have_fired"]:
                context += " The provider duration limit may have fired."
            check["context"] = context
        checks.append(check)
    return checks
