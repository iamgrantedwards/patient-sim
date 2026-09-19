"""Loopback-only review server; no imports of providers, dispatch, or environment config."""

from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .store import ArtifactError, EvidenceStore

ASSETS = Path(__file__).parent / "static"
SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; font-src 'self'; connect-src 'self'; media-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


def create_app(calls_dir: Path | None = None) -> FastAPI:
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    store = EvidenceStore(calls_dir if calls_dir is not None else Path.cwd() / "calls")
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])

    @app.middleware("http")
    async def local_boundary(request: Request, call_next):
        origin = request.headers.get("origin")
        try:
            parsed = urlsplit(origin) if origin is not None else None
            foreign_origin = parsed is not None and (
                parsed.netloc != request.headers.get("host") or parsed.scheme != "http"
            )
        except ValueError:
            foreign_origin = True
        if request.headers.get("sec-fetch-site") == "cross-site" or foreign_origin:
            response = PlainTextResponse(
                "Cross-origin requests are not permitted.", status_code=403
            )
        elif request.method not in ("GET", "HEAD"):
            response = PlainTextResponse("This review interface is read-only.", status_code=405)
        else:
            response = await call_next(request)
        response.headers.update(SECURITY_HEADERS)
        return response

    @app.exception_handler(ArtifactError)
    async def artifact_error(_request, error):
        return JSONResponse({"error": str(error)}, status_code=404)

    @app.exception_handler(OSError)
    async def filesystem_error(_request, _error):
        return JSONResponse(
            {"error": "Evidence is temporarily unavailable. Refresh to retry."}, status_code=503
        )

    @app.get("/")
    def index():
        return FileResponse(ASSETS / "index.html")

    @app.get("/assets/{name}")
    def asset(name: str):
        allowed = {
            "app.js": "text/javascript",
            "style.css": "text/css",
            "favicon.svg": "image/svg+xml",
        }
        if name not in allowed:
            raise ArtifactError("Asset not found.")
        return FileResponse(ASSETS / name, media_type=allowed[name])

    @app.get("/api/calls")
    def calls():
        return store.listing()

    @app.get("/api/calls/{call_id}")
    def detail(call_id: str):
        return store.detail(call_id, fingerprint=True)

    @app.api_route("/api/calls/{call_id}/audio", methods=["GET", "HEAD"])
    def audio(call_id: str):
        path = store.audio(call_id)
        return FileResponse(path, media_type="audio/ogg" if path.suffix == ".ogg" else "audio/mpeg")

    @app.get("/api/calls/{call_id}/transcript")
    def transcript(call_id: str):
        data = store.detail(call_id)
        if not data["transcript_available"]:
            raise ArtifactError("Transcript unavailable.")
        lines = [f"Call {call_id}", "Raw committed dialogue. Audio timings may be unmeasured.", ""]
        lines += [f"{t['idx']:03d} {t['role']} [{t['status']}]: {t['text']}" for t in data["turns"]]
        return PlainTextResponse(
            "\n".join(lines) + "\n",
            headers={"Content-Disposition": f'attachment; filename="{call_id}-transcript.txt"'},
        )

    return app
