import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.review import __main__, server, store


@pytest.fixture
def evidence(tmp_path):
    root = tmp_path / "calls"
    call = root / "call-review-test"
    call.mkdir(parents=True)
    meta = {
        "call_id": call.name,
        "scenario_id": "smoke",
        "started_at": 1000,
        "status": "ended",
        "ended_by": "remote_hangup",
        "git_dirty": False,
        "private_credential": "do-not-return-this",
        "patient_record": {"dob": "private-dob"},
        "recording": {
            "status": "decoded",
            "listened_by_human": False,
            "probe": {"format": {"duration": "70.25"}},
            "file": "../../.env",
        },
        "pipeline": {"stt": "fixture-stt", "api_key": "do-not-return-this"},
    }
    transcript = {
        "call_id": call.name,
        "turns": [
            {
                "idx": 0,
                "role": "remote",
                "text": "<img src=x onerror=alert(1)>",
                "status": "completed",
            },
            {
                "idx": 1,
                "role": "patient",
                "text": "Thank you",
                "status": "partial",
                "interrupted": True,
            },
        ],
    }
    (call / "meta.json").write_text(json.dumps(meta))
    (call / "transcript.json").write_text(json.dumps(transcript))
    (call / "recording.ogg").write_bytes(b"OggS-audio-fixture")
    return root, call, meta, transcript


@pytest.fixture
def client(evidence):
    with TestClient(server.create_app(evidence[0]), base_url="http://127.0.0.1") as client:
        yield client


def test_projection_preserves_uncertainty_and_excludes_private_fields(client, evidence):
    _, call, _, _ = evidence
    before = {p.name: p.read_bytes() for p in call.iterdir()}
    listed = client.get("/api/calls").json()
    assert listed["read_only"] and not listed["truncated"]
    detail = client.get(f"/api/calls/{call.name}").json()
    assert detail["ended_by"] == "remote_hangup"
    assert detail["partial_turns"] == 1
    assert detail["duration_seconds"] == 70.25
    assert detail["recording"]["listened_by_human"] is False
    assert detail["recording"]["sha256"] == hashlib.sha256(before["recording.ogg"]).hexdigest()
    assert detail["turns"][0]["audio_start_ms"] is None
    assert detail["claims"]["verified_state"] is None
    assert "do-not-return-this" not in json.dumps(detail)
    assert "private-dob" not in json.dumps(listed)
    assert "patient_record" not in detail
    assert {p.name: p.read_bytes() for p in call.iterdir()} == before


def test_audio_supports_seeking_head_and_unsatisfiable_range(client, evidence):
    url = f"/api/calls/{evidence[1].name}/audio"
    response = client.get(url, headers={"Range": "bytes=0-3"})
    assert response.status_code == 206
    assert response.content == b"OggS"
    assert response.headers["content-range"].startswith("bytes 0-3/")
    assert client.head(url).content == b""
    assert client.get(url, headers={"Range": "bytes=999999-"}).status_code == 416
    assert client.get(url).headers["content-type"] == "audio/ogg"


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/assets/app.js",
        "/assets/style.css",
        "/assets/theme.css",
        "/assets/theme.js",
        "/assets/favicon.svg",
        "/api/calls",
        "/not-a-route",
    ],
)
def test_browser_security_headers(client, path):
    response = client.get(path)
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert "unsafe-inline" not in response.headers["content-security-policy"]
    assert response.headers["permissions-policy"] == "camera=(), microphone=(), geolocation=()"
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize(
    "headers,status",
    [
        ({"Host": "evil.example"}, 400),
        ({"Origin": "https://evil.example"}, 403),
        ({"Origin": "null"}, 403),
        ({"Origin": "http://[malformed"}, 403),
        ({"Origin": "http://127.0.0.1:9999"}, 403),
        ({"Origin": "https://127.0.0.1"}, 403),
        ({"Sec-Fetch-Site": "cross-site"}, 403),
        ({"Origin": "http://127.0.0.1"}, 200),
    ],
)
def test_local_request_boundary(client, headers, status):
    assert client.get("/api/calls", headers=headers).status_code == status


@pytest.mark.parametrize("method", ["post", "put", "delete", "patch", "options"])
def test_review_cannot_mutate_or_dispatch(client, method):
    assert getattr(client, method)("/api/calls").status_code == 405


@pytest.mark.parametrize(
    "path",
    [
        "/.env",
        "/assets/.env",
        "/assets/server.py",
        "/docs",
        "/openapi.json",
        "/api/calls/call-review-test/meta.json",
        "/api/calls/not-there",
    ],
)
def test_unlisted_paths_are_not_served(client, path):
    assert client.get(path).status_code == 404


def test_safe_transcript_download(client, evidence):
    response = client.get(f"/api/calls/{evidence[1].name}/transcript")
    assert response.headers["content-type"].startswith("text/plain")
    assert "attachment;" in response.headers["content-disposition"]
    assert "patient [partial]: Thank you" in response.text
    assert "<img src=x onerror=alert(1)>" in response.text  # Literal evidence, not executable HTML.


@pytest.mark.parametrize(
    "bad", ["{", "[]", '"text"', '{"call_id":"mismatch"}', b"\xff", '{"call_id": NaN}']
)
def test_bad_metadata_remains_visible_as_unavailable(client, evidence, bad):
    path = evidence[1] / "meta.json"
    path.write_bytes(bad if isinstance(bad, bytes) else bad.encode())
    assert client.get("/api/calls").json()["calls"][0]["status"] == "unavailable"
    assert client.get(f"/api/calls/{evidence[1].name}").status_code == 404


@pytest.mark.parametrize(
    "changes",
    [
        {"call_id": "wrong"},
        {"turns": "wrong"},
        {"claimed_state": {"value": float("nan")}},
        {"turns": [{"idx": 0, "role": "tool", "text": "x", "status": "completed"}]},
    ],
)
def test_bad_transcript_cannot_be_counted_as_pair(client, evidence, changes):
    _, call, _, transcript = evidence
    transcript.update(changes)
    (call / "transcript.json").write_text(json.dumps(transcript))
    detail = client.get(f"/api/calls/{call.name}").json()
    assert not detail["transcript_available"] and not detail["turns"]
    assert client.get(f"/api/calls/{call.name}/transcript").status_code == 404


def test_missing_audio_and_transcript_are_explicit(client, evidence):
    _, call, meta, _ = evidence
    (call / "recording.ogg").unlink()
    (call / "transcript.json").unlink()
    meta["recording"]["listened_by_human"] = "true"
    (call / "meta.json").write_text(json.dumps(meta))
    detail = client.get(f"/api/calls/{call.name}").json()
    assert detail["recording"]["available"] is False
    assert detail["recording"]["listened_by_human"] is None
    assert detail["duration_seconds"] is None
    assert client.get(f"/api/calls/{call.name}/audio").status_code == 404


def test_mp3_fallback_ignores_zero_byte_ogg(client, evidence):
    call = evidence[1]
    (call / "recording.ogg").write_bytes(b"")
    (call / "recording.mp3").write_bytes(b"ID3fixture")
    assert client.get(f"/api/calls/{call.name}/audio").headers["content-type"] == "audio/mpeg"


def test_symlinks_and_path_traversal_cannot_expose_files(client, evidence, tmp_path):
    root, call, _, _ = evidence
    secret = tmp_path / "private.json"
    secret.write_text('{"secret":"outside-evidence-root"}')
    (call / "recording.ogg").unlink()
    (call / "recording.ogg").symlink_to(secret)
    assert client.get(f"/api/calls/{call.name}/audio").status_code == 404
    (call / "meta.json").unlink()
    (call / "meta.json").symlink_to(secret)
    assert client.get(f"/api/calls/{call.name}").status_code == 404
    (root / "call-linked").symlink_to(call, target_is_directory=True)
    assert len(client.get("/api/calls").json()["calls"]) == 1
    for invalid in ("../private", "/tmp/private", "..", "CALL-UPPER", "a" * 81):
        with pytest.raises(store.ArtifactError):
            store.EvidenceStore(root).directory(invalid)
    with pytest.raises(store.ArtifactError):
        store.EvidenceStore(root).directory("call-linked")


def test_bounded_artifact_reads_and_listing(client, evidence, monkeypatch):
    root, call, _, _ = evidence
    monkeypatch.setattr(store, "MAX_JSON", 10)
    assert client.get(f"/api/calls/{call.name}").status_code == 404
    with pytest.raises(store.ArtifactError):
        store.EvidenceStore(root).file(call.name, "meta.json", limit=5)
    monkeypatch.setattr(store, "MAX_CALLS", 0)
    assert client.get("/api/calls").json() == {"calls": [], "truncated": True, "read_only": True}


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, None),
        (True, None),
        (-1, None),
        ("nan", None),
        (float("inf"), None),
        ({}, None),
        ("4.5", 4.5),
        (0, 0.0),
    ],
)
def test_unknown_measurements_never_become_zero(value, expected):
    assert store.number(value) == expected


def test_missing_root_is_empty_but_unreadable_root_is_error(tmp_path, monkeypatch):
    assert store.EvidenceStore(tmp_path / "missing").listing()["calls"] == []
    monkeypatch.setattr(
        Path, "iterdir", lambda _: (_ for _ in ()).throw(PermissionError("private path"))
    )
    with pytest.raises(store.ArtifactError, match="calls directory cannot be read"):
        store.EvidenceStore(tmp_path).listing()


def test_filesystem_error_does_not_leak_paths(client, monkeypatch):
    monkeypatch.setattr(
        store.EvidenceStore, "listing", lambda _: (_ for _ in ()).throw(OSError("private path"))
    )
    response = client.get("/api/calls")
    assert response.status_code == 503 and "private path" not in response.text


def test_launcher_is_loopback_only(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(__main__.uvicorn, "run", lambda *a, **kw: calls.append(kw))
    monkeypatch.setattr("sys.argv", ["review", "--calls-dir", str(tmp_path), "--port", "8767"])
    __main__.main()
    assert calls[0]["host"] == "127.0.0.1" and calls[0]["access_log"] is False
    monkeypatch.setattr("sys.argv", ["review", "--port", "80"])
    with pytest.raises(SystemExit):
        __main__.main()


@pytest.mark.parametrize("invalid_number", ["1e9999", "9" * 4400])
def test_unrepresentable_json_numbers_are_unavailable_not_server_errors(
    client, evidence, invalid_number
):
    call = evidence[1]
    (call / "transcript.json").write_text(
        '{"call_id": "'
        + call.name
        + '", "turns": [], "claimed_state": {"count": '
        + invalid_number
        + "}}"
    )
    response = client.get(f"/api/calls/{call.name}")
    assert response.status_code == 200
    assert not response.json()["transcript_available"]


def test_numeric_overflow_is_unknown():
    assert store.number(10**400) is None


@pytest.fixture
def cloud_record(evidence, monkeypatch, tmp_path):
    curated = tmp_path / "curated"
    monkeypatch.setattr(store, "CLOUD_EVIDENCE", curated)
    folder = curated / evidence[1].name
    folder.mkdir(parents=True)
    record = {
        "call_id": evidence[1].name,
        "room_name": evidence[1].name,
        "session_id": "RM_fixture",
        "checked_at": "2026-09-19T19:30:00Z",
        "method": "authenticated_console",
        "player_visible": True,
    }
    (folder / "verification.json").write_text(json.dumps(record))
    (folder / "verification.md").write_text("Fixture note: player visible, listening pending.")
    (folder / "cloud.png").write_bytes(b"\x89PNG\r\n\x1a\nfixture-image")
    return folder, record


def test_cloud_confirmation_keeps_raw_evidence_and_review_separate(client, evidence, cloud_record):
    call = evidence[1]
    before = {p.name: p.read_bytes() for p in call.iterdir()}
    detail = client.get(f"/api/calls/{call.name}").json()
    cloud = detail["cloud"]
    assert cloud["session_id"] == "RM_fixture"
    assert cloud["player_visible"] is True
    assert cloud["checked_at"] == 1789846200
    assert detail["recording"]["listened_by_human"] is False
    assert detail["claims"]["verified_state"] is None
    screenshot = client.get(cloud["screenshot_url"])
    assert screenshot.status_code == 200
    assert screenshot.headers["content-type"] == "image/png"
    assert screenshot.content.startswith(b"\x89PNG")
    note = client.get(cloud["note_url"])
    assert note.status_code == 200
    assert note.headers["content-type"].startswith("text/plain")
    assert "listening pending" in note.text
    assert "no-store" in note.headers["cache-control"]
    assert client.get(f"/api/calls/{call.name}/cloud-evidence/verification.json").status_code == 404
    assert {p.name: p.read_bytes() for p in call.iterdir()} == before


def test_unchecked_calls_cannot_inherit_cloud_confirmation(client, evidence, cloud_record):
    call = evidence[1]
    other = call.parent / "call-another"
    other.mkdir()
    (other / "meta.json").write_text(json.dumps({"call_id": other.name}))
    assert client.get(f"/api/calls/{other.name}").json()["cloud"] is None
    assert client.get(f"/api/calls/{other.name}/cloud-evidence/screenshot").status_code == 404


@pytest.mark.parametrize(
    "change",
    [
        {"call_id": "call-other"},
        {"room_name": "call-other"},
        {"session_id": "<script>bad</script>"},
        {"checked_at": "yesterday"},
        {"checked_at": "2026-09-19T19:30:00"},
        {"player_visible": "true"},
        {"method": "guessed"},
        {"api_key": "do-not-publish"},
    ],
)
def test_invalid_cloud_records_fail_closed(client, evidence, cloud_record, change):
    folder, record = cloud_record
    (folder / "verification.json").write_text(json.dumps(record | change))
    assert client.get(f"/api/calls/{evidence[1].name}").json()["cloud"] is None
    assert client.get(f"/api/calls/{evidence[1].name}/cloud-evidence/note").status_code == 404


@pytest.mark.parametrize("damage", ["missing", "symlink", "oversized", "not-png", "bad-json"])
def test_cloud_evidence_requires_safe_supporting_files(client, evidence, cloud_record, damage):
    folder, _ = cloud_record
    screenshot = folder / "cloud.png"
    if damage == "missing":
        (folder / "verification.md").unlink()
    elif damage == "symlink":
        screenshot.unlink()
        screenshot.symlink_to(evidence[1] / "recording.ogg")
    elif damage == "oversized":
        with screenshot.open("wb") as stream:
            stream.truncate(store.MAX_SCREENSHOT + 1)
    elif damage == "not-png":
        screenshot.write_text("<html>Not a screenshot</html>")
    else:
        (folder / "verification.json").write_text("{bad")
    assert client.get(f"/api/calls/{evidence[1].name}").json()["cloud"] is None
    assert client.get(f"/api/calls/{evidence[1].name}/cloud-evidence/screenshot").status_code == 404


def test_packaged_cloud_evidence_matches_the_documented_call(tmp_path):
    call_id = "call-20260918-231955-765427d8"
    (tmp_path / call_id).mkdir()
    evidence = store.EvidenceStore(tmp_path)
    cloud = evidence.cloud_verification(call_id)
    assert cloud is not None and cloud["session_id"] == "RM_ffrkrFyiT7T3"
    note = evidence.cloud_artifact(call_id, "note").read_text()
    screenshot = evidence.cloud_artifact(call_id, "screenshot")
    assert hashlib.sha256(screenshot.read_bytes()).hexdigest() in note
    assert call_id in note and cloud["session_id"] in note
