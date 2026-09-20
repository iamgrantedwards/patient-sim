"""Launch local call review; outbound controls require --enable-calls."""

import argparse
from pathlib import Path

import uvicorn

from .server import create_app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--calls-dir", type=Path, default=Path.cwd() / "calls")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--enable-calls",
        action="store_true",
        help="Enable explicitly confirmed calls to the fixed assessment line",
    )
    parser.add_argument(
        "--enable-reviews",
        action="store_true",
        help="Enable saving local listening reviews without enabling calls",
    )
    parser.add_argument(
        "--enable-assessments",
        action="store_true",
        help="Enable paid transcript assessments through LiveKit Inference",
    )
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("port must be between 1024 and 65535")
    controls = configuration = None
    if args.enable_calls:
        from ..caller.config import PROJECT_ROOT
        from .control_routes import production_manager

        if args.calls_dir.resolve() != (PROJECT_ROOT / "calls").resolve():
            parser.error("Calling requires the project's own calls directory.")
        controls, configuration = production_manager(PROJECT_ROOT)
    judge = None
    if args.enable_assessments:
        import os

        from dotenv import load_dotenv

        from ..analysis.assessment import LiveKitJudge
        from ..caller.config import PROJECT_ROOT

        load_dotenv(PROJECT_ROOT / ".env")
        if not (os.getenv("LIVEKIT_API_KEY") and os.getenv("LIVEKIT_API_SECRET")):
            parser.error("AI assessments require LiveKit credentials in the local environment.")
        model = os.getenv("JUDGE_MODEL", "gpt-4.1")
        judge = LiveKitJudge(model if "/" in model else f"openai/{model}")
    uvicorn.run(
        create_app(
            args.calls_dir,
            controls=controls,
            configuration=configuration,
            enable_reviews=args.enable_reviews,
            judge=judge,
        ),
        host="127.0.0.1",
        port=args.port,
        access_log=False,
    )


if __name__ == "__main__":
    main()
