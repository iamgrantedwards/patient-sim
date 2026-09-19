import json

import pytest
from fastapi.testclient import TestClient

from src.review.reviews import CRITERIA
from src.review.server import create_app
from tests.test_review import evidence as evidence_fixture

evidence = evidence_fixture


@pytest.fixture
def session(evidence):
    with TestClient(
        create_app(evidence[0], enable_reviews=True), base_url="http://127.0.0.1"
    ) as client:
        yield client


def payload(client, call):
    state = client.get(f"/api/calls/{call.name}").json()["review"]
    return {
        "reviewer": "Fixture reviewer",
        "listened": False,
        "suitability": "needs_recheck",
        "checks": {key: {"result": "not_assessed", "note": ""} for key in CRITERIA},
        "summary": "Synthetic test only",
        "base_revision": state["revision"],
        "fingerprints": state["fingerprints"],
    }


def save(client, call, data, **kwargs):
    headers = {
        "origin": "http://127.0.0.1",
        "x-review-token": client.get("/api/reviews").json()["token"],
    }
    headers.update(kwargs.pop("headers", {}))
    return client.post(f"/api/calls/{call.name}/review", json=data, headers=headers, **kwargs)


def test_reviews_survive_reload_preserve_originals_and_amendments(session, evidence):
    root, call, _, _ = evidence
    originals = {p.name: p.read_bytes() for p in call.iterdir()}
    data = payload(session, call)
    data.update(listened=True, suitability="usable")
    data["checks"]["completeness"]["result"] = "ok"
    assert save(session, call, data).status_code == 200
    assert save(session, call, data).status_code == 409
    with TestClient(create_app(root), base_url="http://127.0.0.1") as reader:
        state = reader.get(f"/api/calls/{call.name}").json()["review"]
        assert state["listened"] and state["usable"] and state["revision"] == 1
        assert reader.get("/api/reviews").json() == {"enabled": False, "token": None}
        assert reader.post(f"/api/calls/{call.name}/review", json=data).status_code == 405
    updated = payload(session, call)
    updated["summary"] = "After another listen, incomplete."
    updated["suitability"] = "incomplete"
    assert save(session, call, updated).status_code == 200
    state = session.get(f"/api/calls/{call.name}").json()["review"]
    assert state["revision"] == 2 and not state["usable"]
    assert state["history"][0]["review"] == data
    assert state["history"][1]["saved_at"] >= state["history"][0]["saved_at"]
    assert {name: (call / name).read_bytes() for name in originals} == originals


@pytest.mark.parametrize("filename", ["meta.json", "transcript.json", "recording.ogg"])
def test_changed_evidence_requires_recheck(session, evidence, filename):
    call = evidence[1]
    data = payload(session, call)
    data.update(listened=True, suitability="usable")
    data["checks"]["completeness"]["result"] = "ok"
    assert save(session, call, data).status_code == 200
    stale_payload = payload(session, call)
    with (call / filename).open("ab") as stream:
        stream.write(b" ")
    state = session.get(f"/api/calls/{call.name}").json()["review"]
    assert state["status"] == "stale" and not state["usable"] and not state["listened"]
    assert save(session, call, stale_payload).status_code == 409
    assert session.get("/api/calls").json()["calls"][0]["review"]["status"] == "stale"


@pytest.mark.parametrize(
    "patch",
    [
        {"reviewer": " "},
        {"reviewer": "x" * 101},
        {"listened": "true"},
        {"extra": 1},
        {"suitability": "usable"},
        {"checks": {}},
        {"base_revision": -1},
        {"summary": "x" * 2001},
    ],
)
def test_invalid_fields(session, evidence, patch):
    data = payload(session, evidence[1])
    data.update(patch)
    assert save(session, evidence[1], data).status_code == 422
    assert not (evidence[1] / "review.json").exists()


def test_issue_notes_missing_evidence_and_one_sided_transcript(session, evidence):
    call = evidence[1]
    data = payload(session, call)
    data["checks"]["ending"]["result"] = "issue"
    assert save(session, call, data).status_code == 422
    data["checks"]["ending"]["note"] = "00:42 — clipped farewell"
    assert save(session, call, data).status_code == 200
    (call / "recording.ogg").unlink()
    data = payload(session, call)
    data["listened"] = True
    assert save(session, call, data).status_code == 422
    data["listened"] = False
    data["suitability"] = "incomplete"
    assert save(session, call, data).status_code == 200
    (call / "recording.ogg").write_bytes(b"OggS")
    transcript = evidence[3]
    transcript["turns"] = transcript["turns"][:1]
    (call / "transcript.json").write_text(json.dumps(transcript))
    data = payload(session, call)
    data.update(listened=True, suitability="usable")
    data["checks"]["completeness"]["result"] = "ok"
    assert save(session, call, data).status_code == 422


@pytest.mark.parametrize(
    "headers,status",
    [
        ({"origin": "http://evil.example"}, 403),
        ({"origin": ""}, 403),
        ({"x-review-token": "wrong"}, 403),
        ({"content-type": "text/plain"}, 415),
        ({"sec-fetch-site": "cross-site"}, 403),
    ],
)
def test_write_boundary(session, evidence, headers, status):
    assert (
        save(session, evidence[1], payload(session, evidence[1]), headers=headers).status_code
        == status
    )


def test_oversized_and_malformed_requests(session, evidence):
    data = payload(session, evidence[1])
    data["summary"] = "x" * 17000
    assert save(session, evidence[1], data).status_code == 413
    assert save(session, evidence[1], "invalid").status_code == 422


@pytest.mark.parametrize(
    "content",
    [
        "broken",
        "{}",
        '{"call_id":"wrong","revisions":[{}]}',
        '{"call_id":"call-review-test","revisions":[{}]}',
    ],
)
def test_corrupt_history_is_not_overwritten(session, evidence, content):
    call = evidence[1]
    data = payload(session, call)
    (call / "review.json").write_text(content)
    assert session.get(f"/api/calls/{call.name}").json()["review"]["status"] == "unavailable"
    assert save(session, call, data).status_code == 409
    assert (call / "review.json").read_text() == content


def test_review_symlink_is_not_followed(session, evidence, tmp_path):
    call = evidence[1]
    data = payload(session, call)
    external = tmp_path / "external.json"
    external.write_text("{}")
    (call / "review.json").symlink_to(external)
    assert save(session, call, data).status_code == 409
    assert external.read_text() == "{}"


def test_legacy_flag_never_becomes_acceptance(session, evidence):
    _, call, meta, _ = evidence
    meta["recording"]["listened_by_human"] = True
    (call / "meta.json").write_text(json.dumps(meta))
    data = session.get(f"/api/calls/{call.name}").json()
    assert data["recording"]["listened_by_human"] is True
    assert not data["review"]["usable"] and not data["review"]["listened"]
