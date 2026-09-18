import json

import pytest

from src.caller.transcript import CallArtifacts, finalize, read_events, reconcile


def event(kind, data):
    return {"type": kind, "received_at": 1000, "data": data}


def message(item_id, role, text, interrupted=False):
    return event(
        "conversation_item_added",
        {
            "item": {
                "id": item_id,
                "type": "message",
                "role": role,
                "content": [text],
                "interrupted": interrupted,
            }
        },
    )


def test_interim_and_final_stt_do_not_duplicate_committed_turns():
    events = [
        event("user_input_transcribed", {"transcript": "We close", "is_final": False}),
        event("user_input_transcribed", {"transcript": "We close at five", "is_final": True}),
        message("remote-1", "user", "We close at five"),
        message("remote-1", "user", "We close at five"),
        message("patient-1", "assistant", "Thank you"),
    ]
    turns, pending = reconcile(events)
    assert [t["text"] for t in turns] == ["We close at five", "Thank you"]
    assert pending == []
    assert all(t["our_response_ms"] is None for t in turns)


def test_repeated_words_in_distinct_turns_are_not_deduplicated():
    turns, _ = reconcile([message("one", "user", "Hello"), message("two", "user", "Hello")])
    assert len(turns) == 2


def test_partial_output_and_uncommitted_input_survive_recovery(tmp_path):
    artifacts = CallArtifacts(tmp_path, {"call_id": "fixture", "scenario_id": "smoke"})
    artifacts.append(
        "conversation_item_added", message("one", "assistant", "I would like", True)["data"]
    )
    artifacts.append("user_input_transcribed", {"transcript": "Could you", "is_final": False})
    # Simulate an interrupted append; prior events are already flushed to disk.
    with (tmp_path / "events.jsonl").open("a") as stream:
        stream.write('{"type":')
    result = finalize(tmp_path)
    assert result["status"] == "recovered_partial"
    assert result["turns"][0]["status"] == "partial"
    assert result["uncommitted_transcriptions"][0]["transcript"] == "Could you"
    assert result["verified_state"] is None
    artifacts.events.close()


def test_specific_termination_is_not_overwritten(tmp_path):
    artifacts = CallArtifacts(tmp_path, {"call_id": "fixture", "scenario_id": "smoke"})
    artifacts.end("failsafe")
    artifacts.end("remote_hangup")
    assert json.loads((tmp_path / "meta.json").read_text())["ended_by"] == "failsafe"
    artifacts.events.close()


def test_corrupted_middle_event_is_not_silently_discarded(tmp_path):
    path = tmp_path / "events.jsonl"
    path.write_text("not-json\n{}\n")
    with pytest.raises(ValueError):
        read_events(path)
