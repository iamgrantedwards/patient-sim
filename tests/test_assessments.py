import json
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.analysis.assessment import DIMENSIONS, Assessment, CallAssessment, score, validate_evidence
from src.review.server import create_app
from tests.test_review import evidence as evidence_fixture

evidence = evidence_fixture


def report():
    return CallAssessment.model_validate(
        {
            "summary": "Synthetic fixture assessment, not a call finding.",
            "dimensions": [
                {
                    "dimension": d,
                    "score": 2,
                    "rationale": "Fixture rationale.",
                    "evidence": [{"turn": 0, "quote": "<img src=x onerror=alert(1)>"}],
                }
                for d in DIMENSIONS
            ],
            "call_quality": [
                {
                    "topic": topic,
                    "result": "not_assessable" if topic == "turn_taking" else "concern",
                    "rationale": "Fixture concern; audio has not been reviewed.",
                    "evidence": []
                    if topic == "turn_taking"
                    else [{"turn": 1, "quote": "Thank you"}],
                    "attribution": "unknown",
                    "next_step": "Listen to the final exchange.",
                }
                for topic in ("patient", "turn_taking", "ending")
            ],
            "observations": [
                {
                    "title": "Fixture candidate",
                    "expected_behavior": "Clarify request",
                    "basis_for_expectation": "Conversation context",
                    "attribution": "unknown",
                    "uncertainty": "Needs listening",
                    "recommended_improvement": "Clarify",
                    "next_test": "Repeat with a correction",
                    "evidence": [{"turn": 1, "quote": "Thank you"}],
                }
            ],
        }
    )


@pytest.fixture
def setup(evidence):
    root, call, meta, transcript = evidence
    transcript["turns"][1]["status"] = "completed"
    (call / "transcript.json").write_text(json.dumps(transcript))
    judge = AsyncMock(return_value=report())
    judge.model = "fixture-model"
    with TestClient(create_app(root, judge=judge), base_url="http://127.0.0.1") as client:
        client.headers["x-assessment-token"] = client.get(
            f"/api/calls/{call.name}/assessment"
        ).json()["token"]
        yield client, call, judge


def post(client, call, **kwargs):
    headers = {
        "origin": "http://127.0.0.1",
        "x-assessment-token": client.headers["x-assessment-token"],
    }
    headers.update(kwargs.pop("headers", {}))
    return client.post(f"/api/calls/{call.name}/assessment", headers=headers, **kwargs)


def test_assessment_persists_caches_and_never_changes_originals_or_human_review(setup, evidence):
    client, call, judge = setup
    originals = {p.name: p.read_bytes() for p in call.iterdir()}
    r = post(client, call)
    assert r.status_code == 200, r.text
    assert r.json()["score"] == {"percent": 100, "assessed": 5, "total": 5}
    assert post(client, call).status_code == 200
    assert judge.await_count == 1
    assert {n: (call / n).read_bytes() for n in originals} == originals
    assert not (call / "review.json").exists()
    sent = judge.call_args.args[0]
    assert set(sent) == {"scenario", "turns", "capture"}
    assert sent["capture"]["ended_by"] == "remote_hangup"
    assert "recording" not in sent and "patient_record" not in sent
    checks = r.json()["quality_checks"]
    assert len(checks) == 7
    assert {c["topic"] for c in checks if c["result"] == "needs_audio"} == {
        "transcript",
        "pacing",
        "audio",
    }
    assert "private-dob" not in json.dumps(sent)
    with TestClient(create_app(evidence[0]), base_url="http://127.0.0.1") as reader:
        saved = reader.get(f"/api/calls/{call.name}/assessment").json()
        assert saved["status"] == "saved" and not saved["enabled"]
        assert reader.post(f"/api/calls/{call.name}/assessment").status_code == 405
        assert not reader.get(f"/api/calls/{call.name}").json()["review"]["usable"]


@pytest.mark.parametrize("change", ["transcript", "model"])
def test_staleness_and_revision_history(setup, change):
    client, call, judge = setup
    assert post(client, call).status_code == 200
    if change == "transcript":
        with (call / "transcript.json").open("a") as stream:
            stream.write(" ")
    else:
        judge.model = "new-fixture-model"
    state = client.get(f"/api/calls/{call.name}/assessment").json()
    assert state["status"] == "stale" and state["score"] is None
    assert post(client, call).status_code == 200
    assert len(json.loads((call / "assessment.json").read_text())["revisions"]) == 2


@pytest.mark.parametrize("failure", ["provider", "quote", "turn", "evidence_changed"])
def test_failure_does_not_save_and_retry_works(setup, failure):
    client, call, judge = setup
    if failure == "provider":
        judge.side_effect = RuntimeError("SECRET not to expose")
    elif failure == "quote":
        judge.return_value.dimensions[0].evidence[0].quote = "invented"
    elif failure == "turn":
        judge.return_value.dimensions[0].evidence[0].turn = 999
    else:

        async def mutate(_data):
            with (call / "meta.json").open("a") as stream:
                stream.write(" ")
            return report()

        judge.side_effect = mutate
    r = post(client, call)
    assert r.status_code == (409 if failure == "evidence_changed" else 502)
    assert "SECRET" not in r.text
    assert not (call / "assessment.json").exists()
    judge.side_effect = None
    judge.return_value = report()
    assert post(client, call).status_code == 200


@pytest.mark.parametrize("kind", ["audio", "worker", "partial", "oversize"])
def test_insufficient_evidence_never_calls_provider(setup, evidence, kind):
    client, call, judge = setup
    meta, transcript = evidence[2:]
    if kind == "audio":
        (call / "recording.ogg").unlink()
    elif kind == "worker":
        meta["ended_by"] = "worker_error"
        (call / "meta.json").write_text(json.dumps(meta))
    else:
        if kind == "partial":
            transcript["turns"][1]["status"] = "partial"
        else:
            transcript["turns"][0]["text"] = "a" * 61000
        (call / "transcript.json").write_text(json.dumps(transcript))
    assert post(client, call).status_code == 422
    judge.assert_not_called()


@pytest.mark.parametrize(
    "headers,status",
    [
        ({"origin": "http://evil.example"}, 403),
        ({"origin": ""}, 403),
        ({"x-assessment-token": "bad"}, 403),
    ],
)
def test_write_boundary(setup, headers, status):
    client, call, judge = setup
    assert post(client, call, headers=headers).status_code == status
    judge.assert_not_called()


def test_no_request_body_and_corrupt_saved_data(setup):
    client, call, judge = setup
    assert post(client, call, content=b"{}").status_code == 400
    (call / "assessment.json").write_text("broken")
    assert post(client, call).status_code == 409
    judge.assert_not_called()
    assert (call / "assessment.json").read_text() == "broken"


def test_symlink_and_wrong_call_never_overwritten(setup, tmp_path):
    client, call, judge = setup
    external = tmp_path / "other.json"
    external.write_text("{}")
    (call / "assessment.json").symlink_to(external)
    assert post(client, call).status_code == 409
    assert external.read_text() == "{}"
    (call / "assessment.json").unlink()
    assert post(client, call).status_code == 200
    record = json.loads((call / "assessment.json").read_text())
    record["revisions"][0]["call_id"] = "call-another"
    (call / "assessment.json").write_text(json.dumps(record))
    assert post(client, call).status_code == 409


def test_revision_limit_and_process_lock(setup):
    import fcntl

    client, call, judge = setup
    with (call / ".assessment.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert post(client, call).status_code == 409
    assert post(client, call).status_code == 200
    data = json.loads((call / "assessment.json").read_text())
    data["revisions"] *= 10
    (call / "assessment.json").write_text(json.dumps(data))
    judge.model = "another-model"
    assert post(client, call).status_code == 409


def test_rubric_and_score_coverage_and_target_citations(evidence):
    result = report()
    for d in result.dimensions[:3]:
        d.score = None
    assert score(result) == {"percent": None, "assessed": 2, "total": 5}
    result.dimensions[2].score = 0
    assert score(result)["percent"] == 67
    result.dimensions[-1].evidence[0].turn = 1
    result.dimensions[-1].evidence[0].quote = "Thank you"
    with pytest.raises(ValueError, match="Target-agent"):
        validate_evidence(result, evidence[3]["turns"])
    with pytest.raises(ValueError, match="Ambiguous"):
        validate_evidence(result, evidence[3]["turns"] * 2)
    raw = report().model_dump()
    raw["dimensions"][0]["evidence"] = []
    with pytest.raises(ValueError):
        Assessment.model_validate(raw)
    raw = report().model_dump()
    raw["dimensions"][0]["dimension"] = "consistency"
    with pytest.raises(ValueError):
        Assessment.model_validate(raw)


@pytest.mark.parametrize("output", ["valid", "invalid", "oversize", "provider_error"])
def test_judge_sdk_boundary_closes_client_and_rejects_invalid_output(monkeypatch, output):
    import asyncio
    from types import SimpleNamespace

    from livekit.agents import inference

    from src.analysis.assessment import PROMPT, LiveKitJudge

    captured = {}

    class Stream:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        def __aiter__(self):
            return self.generate()

        async def generate(self):
            if output == "provider_error":
                raise RuntimeError("fixture error")
            text = (
                report().model_dump_json()
                if output == "valid"
                else "x" * (33000 if output == "oversize" else 5)
            )
            yield SimpleNamespace(delta=None)
            yield SimpleNamespace(delta=SimpleNamespace(content=text))

    class Model:
        def __init__(self, model, **kwargs):
            captured["model"] = model

        def chat(self, **kwargs):
            captured.update(kwargs)
            return Stream()

        async def aclose(self):
            captured["closed"] = True

    monkeypatch.setattr(inference, "LLM", Model)
    if output == "valid":
        result = asyncio.run(LiveKitJudge()({"scenario": "fixture", "turns": []}))
        assert result == report()
        assert captured["response_format"] is CallAssessment
        assert captured["conn_options"].max_retry == 0
        assert captured["chat_ctx"].items[0].text_content == PROMPT
    else:
        with pytest.raises((ValueError, RuntimeError)):
            asyncio.run(LiveKitJudge()({"turns": []}))
    assert captured["closed"]


def test_v1_history_stays_readable_but_requires_explicit_reassessment(setup):
    client, call, judge = setup
    assert post(client, call).status_code == 200
    path = call / "assessment.json"
    raw = json.loads(path.read_text())
    raw["revisions"][0]["rubric"] = "transcript-v1"
    del raw["revisions"][0]["result"]["call_quality"]
    path.write_text(json.dumps(raw))
    before = path.read_bytes()
    state = client.get(f"/api/calls/{call.name}/assessment").json()
    assert state["status"] == "stale" and state["score"] is None
    assert state["latest"]["result"]["summary"] == report().summary
    assert (
        next(c for c in state["quality_checks"] if c["topic"] == "ending")["result"]
        == "not_assessed"
    )
    assert path.read_bytes() == before and judge.await_count == 1
    assert post(client, call).status_code == 200
    assert judge.await_count == 2
    assert len(json.loads(path.read_text())["revisions"]) == 2


@pytest.mark.parametrize(
    "kind",
    [
        "missing",
        "duplicate",
        "ungrounded",
        "wrong_speaker",
        "old_ending",
        "false_clear",
        "audio_clear",
    ],
)
def test_quality_checks_reject_incomplete_or_unsupported_assessment(kind):
    raw = report().model_dump()
    turns = [
        {"idx": 0, "role": "remote", "text": "<img src=x onerror=alert(1)>"},
        {"idx": 1, "role": "patient", "text": "Thank you", "status": "completed"},
    ]
    if kind == "missing":
        raw.pop("call_quality")
    elif kind == "duplicate":
        raw["call_quality"][0]["topic"] = "ending"
    elif kind == "ungrounded":
        raw["call_quality"][0]["evidence"] = []
    elif kind == "wrong_speaker":
        raw["call_quality"][0]["evidence"] = [{"turn": 0, "quote": "<img src=x onerror=alert(1)>"}]
    elif kind == "old_ending":
        turns.extend(
            [
                {"idx": 2, "role": "remote", "text": "More instructions"},
                {"idx": 3, "role": "patient", "text": "Wait"},
            ]
        )
    elif kind == "false_clear":
        turns[-1]["text"] = "Thank you..."
        raw["call_quality"][2]["result"] = "no_text_issue"
    else:
        raw["call_quality"][1]["result"] = "no_text_issue"
        raw["call_quality"][1]["evidence"] = [{"turn": 1, "quote": "Thank you"}]
    with pytest.raises(ValueError):
        result = CallAssessment.model_validate(raw)
        validate_evidence(result, turns)


def test_local_capture_and_ending_context_do_not_claim_audio_verification(setup, evidence):
    client, call, judge = setup
    meta, transcript = evidence[2:]
    meta.update(ended_by="end_call_tool", sip={"duration_limit_may_have_fired": True})
    transcript["turns"][-1]["text"] = "Please bring your insurance..."
    transcript["uncommitted_transcriptions"] = [{"text": "pending private text"}]
    (call / "meta.json").write_text(json.dumps(meta))
    (call / "transcript.json").write_text(json.dumps(transcript))
    state = client.get(f"/api/calls/{call.name}/assessment").json()
    checks = {c["topic"]: c for c in state["quality_checks"]}
    assert checks["completeness"]["result"] == "attention"
    assert "possible cutoff" in checks["ending"]["context"]
    assert "may have fired" in checks["ending"]["context"]
    assert "does not verify" in checks["ending"]["context"]
    assert "pending private text" not in json.dumps(state)
    judge.assert_not_called()
