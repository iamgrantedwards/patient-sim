import json
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.caller.control import CallManager
from src.review.control_routes import production_manager
from src.review.server import create_app
from tests.test_controls import Backend


@pytest.fixture
def console(tmp_path):
    backend = Backend(tmp_path, "slow_prepare")
    manager = CallManager(tmp_path, lambda: backend, poll=0.001)
    app = create_app(
        tmp_path / "calls",
        controls=manager,
        configuration=lambda: {
            "ready": True,
            "destination": "+18054398008",
            "caller_id": "+12025550123",
            "max_seconds": 240,
        },
    )
    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        state = client.get("/api/console").json()
        headers = {"Origin": "http://127.0.0.1:8765", "X-Console-Token": state["csrf_token"]}
        payload = {
            "scenario": "smoke",
            "start_token": state["operation"]["start_token"],
            "request_id": "fixture-request-123",
            "confirmed": True,
        }
        yield client, manager, backend, headers, payload
    assert manager.closing


def test_readonly_default_cannot_start_or_stop(tmp_path):
    with TestClient(create_app(tmp_path), base_url="http://localhost") as client:
        assert client.get("/api/console").json() == {"enabled": False}
        for route in ("start", "stop"):
            assert client.post(f"/api/console/{route}", json={}).status_code == 405


def test_explicit_start_duplicate_stop_and_shutdown(console):
    client, manager, backend, headers, payload = console
    assert backend.actions == []
    result = client.post("/api/console/start", json=payload, headers=headers)
    assert result.status_code == 202
    call_id = result.json()["call_id"]
    again = client.post("/api/console/start", json=payload, headers=headers)
    assert again.status_code == 202 and again.json()["call_id"] == call_id
    for _ in range(3):
        assert client.get("/api/console").status_code == 200
    assert backend.actions.count("prepare") == 1
    assert "dispatch" not in backend.actions
    assert (
        client.post("/api/console/stop", json={"call_id": call_id}, headers=headers).status_code
        == 202
    )


@pytest.mark.parametrize(
    "change,status",
    [
        ({"confirmed": False}, 422),
        ({"confirmed": "true"}, 422),
        ({"destination": "+12025550199"}, 422),
        ({"scenario": "unknown"}, 422),
        ({"request_id": "short"}, 422),
        ({"start_token": "x" * 32}, 409),
    ],
)
def test_unconfirmed_or_tampered_requests_never_call(console, change, status):
    client, _, backend, headers, payload = console
    payload.update(change)
    response = client.post("/api/console/start", json=payload, headers=headers)
    assert response.status_code == status
    assert backend.actions == []


@pytest.mark.parametrize(
    "header,value,status",
    [
        ("X-Console-Token", "wrong", 403),
        ("Origin", "", 403),
        ("Origin", "http://localhost:8765", 403),
        ("Origin", "https://evil.example", 403),
        ("Host", "evil.example", 403),
        ("Content-Type", "text/plain", 415),
    ],
)
def test_cross_site_and_session_boundaries(console, header, value, status):
    client, _, backend, headers, payload = console
    headers[header] = value
    response = client.post(
        "/api/console/start",
        content=json.dumps(payload),
        headers={"Content-Type": "application/json", **headers},
    )
    assert response.status_code == status
    assert backend.actions == []


def test_size_limit_invalid_json_and_unknown_stop(console):
    client, _, backend, headers, _ = console
    headers["Content-Type"] = "application/json"
    assert client.post("/api/console/start", content="x" * 4097, headers=headers).status_code == 413
    assert client.post("/api/console/start", content="{broken", headers=headers).status_code == 422
    assert (
        client.post("/api/console/stop", json={"call_id": "../escape"}, headers=headers).status_code
        == 422
    )
    assert (
        client.post(
            "/api/console/stop", json={"call_id": "call-no-longer"}, headers=headers
        ).status_code
        == 409
    )
    assert backend.actions == []


def test_preflight_projection_never_discloses_configuration_secrets(
    tmp_path, configured, monkeypatch
):
    from src.caller import config

    manager, configuration = production_manager(tmp_path)
    result = configuration()
    assert result["ready"] and result["destination"] == configured.target_number
    assert "fixture-secret" not in json.dumps(result)
    backend = manager.factory()
    assert backend.config == configured
    monkeypatch.setattr(config, "load", lambda: None)
    # The closure captures load; force validation to fail through the environment instead.
    monkeypatch.setenv("TARGET_NUMBER", "+12025550111")
    result = configuration()
    assert not result["ready"]
    assert "+12025550111" not in json.dumps(result)


def test_launcher_enables_only_project_calls(monkeypatch, tmp_path):
    from src.caller import config
    from src.review import __main__ as entry
    from src.review import control_routes

    monkeypatch.setattr(config, "PROJECT_ROOT", tmp_path)
    manager = type("Manager", (), {"shutdown": AsyncMock()})()
    monkeypatch.setattr(control_routes, "production_manager", lambda root: (manager, lambda: {}))
    calls = []
    monkeypatch.setattr(entry.uvicorn, "run", lambda app, **kwargs: calls.append(kwargs))
    monkeypatch.setattr(
        "sys.argv", ["review", "--enable-calls", "--calls-dir", str(tmp_path / "calls")]
    )
    entry.main()
    assert calls == [{"host": "127.0.0.1", "port": 8765, "access_log": False}]
    monkeypatch.setattr(
        "sys.argv", ["review", "--enable-calls", "--calls-dir", str(tmp_path / "other")]
    )
    with pytest.raises(SystemExit):
        entry.main()
