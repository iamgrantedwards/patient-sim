"""Preview a scenario or explicitly dispatch one real assessment call."""

import argparse
import asyncio
import json
import uuid
from datetime import UTC, datetime

from .config import PERMITTED_TARGET, PROJECT_ROOT, load
from .patient import DEFAULT_PATIENT, build_instructions
from .scenarios import SCENARIOS, get_scenario
from .transcript import write_json


async def dispatch(scenario: str) -> None:
    from livekit import api

    cfg = load()  # Fail before creating a dispatch if local settings are incomplete.
    call_id = datetime.now(UTC).strftime("call-%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8]
    directory = PROJECT_ROOT / "calls" / call_id
    directory.mkdir(parents=True, exist_ok=False)
    record = {"call_id": call_id, "scenario": scenario, "status": "dispatching"}
    write_json(directory / "dispatch.json", record)
    async with api.LiveKitAPI(
        cfg.livekit_url, cfg.livekit_api_key, cfg.livekit_api_secret
    ) as client:
        try:
            created = await client.agent_dispatch.create_dispatch(
                api.CreateAgentDispatchRequest(
                    agent_name="patient-sim",
                    room=call_id,
                    metadata=json.dumps({"scenario": scenario, "call_id": call_id}),
                )
            )
            record.update(status="dispatched", dispatch_id=created.id)
            write_json(directory / "dispatch.json", record)
            # Local worker and dispatcher share calls/. Never automatically redial.
            for _ in range(60):
                if (directory / "meta.json").exists():
                    print(f"Worker accepted {call_id}. Artifacts: {directory}")
                    return
                await asyncio.sleep(0.5)
            raise TimeoutError("Worker did not accept the dispatch within 30 seconds")
        except Exception as error:
            record.update(status="dispatch_error", error_type=type(error).__name__)
            try:
                await client.room.delete_room(api.DeleteRoomRequest(room=call_id))
                record["cleanup"] = "room_deleted"
            except Exception as cleanup_error:
                record["cleanup"] = type(cleanup_error).__name__
            write_json(directory / "dispatch.json", record)
            raise RuntimeError(
                f"Dispatch failed ({type(error).__name__}); inspect {directory}/dispatch.json. No automatic retry."
            ) from None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), default="smoke")
    action = parser.add_mutually_exclusive_group()
    action.add_argument(
        "--call", action="store_true", help="Place one real call; requires a running worker"
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
