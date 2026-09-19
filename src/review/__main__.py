"""Launch the local, read-only call review interface."""

import argparse
from pathlib import Path

import uvicorn

from .server import create_app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--calls-dir", type=Path, default=Path.cwd() / "calls")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("port must be between 1024 and 65535")
    uvicorn.run(create_app(args.calls_dir), host="127.0.0.1", port=args.port, access_log=False)


if __name__ == "__main__":
    main()
