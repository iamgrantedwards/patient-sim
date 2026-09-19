"""A dedicated, registered worker for one explicitly confirmed console/CLI call."""

import asyncio
import os
import signal

from .agent import server
from .config import PROJECT_ROOT
from .transcript import write_json


async def run():
    call_id = os.environ["PATIENT_SIM_CALL_ID"]
    from ..review.store import CALL_ID

    if not CALL_ID.fullmatch(call_id):
        raise ValueError("Invalid managed call identifier")
    nonce = os.environ["PATIENT_SIM_WORKER_NONCE"]
    parent = int(os.environ["PATIENT_SIM_PARENT_PID"])
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    @server.on("worker_registered")
    def registered(_worker_id, _server_info):
        write_json(
            PROJECT_ROOT / ".runtime" / f"{call_id}-worker.json",
            {
                "nonce": nonce,
                "pid": os.getpid(),
                "registered": True,
            },
        )

    async def parent_watch():
        while not stop.is_set():
            if os.getppid() != parent:
                try:
                    write_json(
                        PROJECT_ROOT / "calls" / call_id / "operator-stop.json",
                        {"reason": "controller_shutdown"},
                    )
                finally:
                    stop.set()
                return
            await asyncio.sleep(1)

    runner = asyncio.create_task(server.run(devmode=True))
    watcher = asyncio.create_task(parent_watch())
    waiter = asyncio.create_task(stop.wait())
    try:
        await asyncio.wait([runner, waiter], return_when=asyncio.FIRST_COMPLETED)
        if runner.done():
            await runner
        else:
            await server.drain(timeout=20)
    finally:
        await server.aclose()
        watcher.cancel()
        waiter.cancel()
        await asyncio.gather(watcher, waiter, runner, return_exceptions=True)
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.remove_signal_handler(sig)
        write_json(
            PROJECT_ROOT / ".runtime" / f"{call_id}-stopped.json",
            {"nonce": nonce, "stopped": True},
        )


if __name__ == "__main__":
    asyncio.run(run())
