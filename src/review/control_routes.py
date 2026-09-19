"""Opt-in mutation routes with per-process token, exact Origin, and strict bodies."""

import secrets
from pathlib import Path

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictBool, ValidationError

from ..caller.control import ControlError


class StartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    scenario: str = Field(min_length=1, max_length=40)
    start_token: str = Field(min_length=20, max_length=100)
    request_id: str = Field(pattern=r"^[a-zA-Z0-9-]{16,64}$")
    confirmed: StrictBool


class StopRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    call_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,79}$")


def install(app, manager, configuration):
    token = secrets.token_urlsafe(32)

    @app.exception_handler(ControlError)
    async def control_error(_request, error):
        return JSONResponse({"error": str(error)}, status_code=error.status)

    @app.get("/api/console")
    async def state():
        from ..caller.scenarios import SCENARIOS

        return {
            "enabled": True,
            "csrf_token": token,
            "configuration": configuration(),
            "scenarios": [
                {"id": key, "label": item.kind.replace("_", " "), "objective": item.objective}
                for key, item in SCENARIOS.items()
                if key != "calibration"
            ],
            "operation": manager.snapshot(),
        }

    async def body(request, model):
        if not secrets.compare_digest(request.headers.get("x-console-token", ""), token):
            raise ControlError("The console session changed. Refresh before trying again.", 403)
        if request.headers.get("origin") != f"http://{request.headers.get('host')}":
            raise ControlError("An exact local Origin is required.", 403)
        if request.headers.get("content-type", "").split(";")[0] != "application/json":
            raise ControlError("Use an application/json request.", 415)
        raw = bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw) > 4096:
                raise ControlError("Request is too large.", 413)
        try:
            return model.model_validate_json(raw)
        except ValidationError:
            raise ControlError("Invalid call request. Refresh and confirm again.", 422) from None

    @app.post("/api/console/start", status_code=202)
    async def start(request: Request):
        data = await body(request, StartRequest)
        if data.confirmed is not True:
            raise ControlError("Explicit call confirmation is required.", 422)
        return await manager.start(data.scenario, data.start_token, data.request_id)

    @app.post("/api/console/stop", status_code=202)
    async def stop(request: Request):
        data = await body(request, StopRequest)
        return await manager.stop(data.call_id)


def production_manager(root: Path):
    from ..caller.config import PERMITTED_TARGET, load
    from ..caller.control import CallManager
    from ..caller.control_backend import LiveBackend

    def configuration():
        try:
            cfg = load()
            return {
                "ready": True,
                "destination": PERMITTED_TARGET,
                "caller_id": cfg.caller_id,
                "max_seconds": cfg.max_call_seconds,
            }
        except Exception:
            return {
                "ready": False,
                "destination": PERMITTED_TARGET,
                "message": "Complete .env using .env.example. Confirm LiveKit, SIP trunk, caller ID, and voice settings.",
            }

    def backend():
        return LiveBackend(root, load())

    return CallManager(root, backend), configuration
