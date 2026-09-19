"""Preview a scenario or explicitly dispatch one real assessment call."""

import argparse
import asyncio
import uuid

from .config import PERMITTED_TARGET, PROJECT_ROOT, load
from .patient import DEFAULT_PATIENT, build_instructions
from .scenarios import SCENARIOS, get_scenario


async def dispatch(scenario: str) -> None:
    from .control import CallManager
    from .control_backend import LiveBackend

    get_scenario(scenario)
    cfg = load()
    manager = CallManager(
        PROJECT_ROOT, lambda: LiveBackend(PROJECT_ROOT, cfg), max_seconds=cfg.max_call_seconds
    )
    result = await manager.start(scenario, manager.start_token, uuid.uuid4().hex)
    print(f"Call requested: {result['call_id']}. No automatic retry.")
    try:
        if manager.task is not None:
            await asyncio.shield(manager.task)
    except asyncio.CancelledError:
        await asyncio.shield(manager.shutdown())
        raise
    result = manager.snapshot()
    if result["phase"] != "ended":
        raise RuntimeError(
            result["message"]
            or "Call did not complete. Review the saved operation before retrying."
        )
    print(
        f"Call ended: {result['call_id']}. Artifacts: {PROJECT_ROOT / 'calls' / result['call_id']}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), default="smoke")
    action = parser.add_mutually_exclusive_group()
    action.add_argument(
        "--call",
        action="store_true",
        help="Start a dedicated worker and place one real assessment call",
    )
    action.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the patient prompt without network calls (default)",
    )
    args = parser.parse_args()
    if args.call:
        asyncio.run(dispatch(args.scenario))
    else:
        print(f"DRY RUN — permitted destination: {PERMITTED_TARGET}; no call placed.\n")
        print(build_instructions(DEFAULT_PATIENT, get_scenario(args.scenario)))


if __name__ == "__main__":
    main()
