"""Provider/process adapter. Imported only by explicit calling entry points."""

import asyncio
import json
import os
import signal
import sys
import uuid
from pathlib import Path

from livekit import api

from .config import Config
from .transcript import write_json


class LiveBackend:
    def __init__(self, root: Path, config: Config):
        self.root = root
        self.config = config
        self.process = None
        self.log = None
        self.call_id: str | None = None
        self.nonce: str | None = None
        self.agent_name = "patient-sim-console-" + uuid.uuid4().hex[:12]

    async def prepare(self, call_id: str):
        ready = self.root / ".runtime" / f"{call_id}-worker.json"
        nonce = self.nonce = uuid.uuid4().hex
        self.call_id = call_id
        write_json(self.root / ".runtime" / f"{call_id}-intent.json", {"nonce": nonce})
        env = dict(os.environ)
        env.update(
            PATIENT_SIM_AGENT_NAME=self.agent_name,
            PATIENT_SIM_CALL_ID=call_id,
            PATIENT_SIM_WORKER_NONCE=nonce,
            PATIENT_SIM_PARENT_PID=str(os.getpid()),
        )
        log_path = self.root / ".runtime" / f"{call_id}-worker.log"
        descriptor = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        self.log = os.fdopen(descriptor, "wb")
        creation = asyncio.create_task(
            asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "src.caller.managed_worker",
                cwd=self.root,
                env=env,
                stdout=self.log,
                stderr=self.log,
                start_new_session=True,
            )
        )
        try:
            self.process = await asyncio.shield(creation)
        except asyncio.CancelledError:
            # Retain ownership even if Stop arrives while the OS is creating the worker.
            self.process = await creation
            raise
        async with asyncio.timeout(60):
            while True:
                if self.process.returncode is not None:
                    raise RuntimeError("worker_exited")
                if ready.exists():
                    data = json.loads(ready.read_text())
                    if data.get("nonce") == nonce and data.get("pid") == self.process.pid:
                        return
                await asyncio.sleep(0.1)

    def client(self):
        cfg = self.config
        return api.LiveKitAPI(cfg.livekit_url, cfg.livekit_api_key, cfg.livekit_api_secret)

    async def dispatch(self, call_id: str, scenario: str):
        async with self.client() as client:
            async with asyncio.timeout(20):
                result = await client.agent_dispatch.create_dispatch(
                    api.CreateAgentDispatchRequest(
                        agent_name=self.agent_name,
                        room=call_id,
                        metadata=json.dumps({"scenario": scenario, "call_id": call_id}),
                    )
                )
                return result.id

    async def hangup(self, call_id: str):
        self.call_id = call_id
        async with self.client() as client:
            async with asyncio.timeout(15):
                try:
                    await client.room.delete_room(api.DeleteRoomRequest(room=call_id))
                except api.TwirpError as error:
                    if error.code != "not_found":
                        raise
                # A deletion acknowledgement alone must not become a successful conversation.
                rooms = await client.room.list_rooms(api.ListRoomsRequest(names=[call_id]))
                if rooms.rooms:
                    raise RuntimeError("room_still_present")

    def exited(self):
        return self.process is not None and self.process.returncode is not None

    async def close(self):
        try:
            if self.process is not None and self.process.returncode is None:
                try:
                    self.process.send_signal(signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    await asyncio.wait_for(self.process.wait(), 35)
                except TimeoutError:
                    # Only signal the process group that this adapter itself created.
                    try:
                        os.killpg(self.process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    await self.process.wait()
            if self.call_id:
                intent = self.root / ".runtime" / f"{self.call_id}-intent.json"
                stopped = self.root / ".runtime" / f"{self.call_id}-stopped.json"
                if self.process is not None or self.nonce is not None:
                    # Owned process is confirmed exited, or creation failed before it existed.
                    write_json(stopped, {"nonce": self.nonce, "stopped": True})
                elif intent.exists():
                    # Recovery cannot kill a PID it did not create. The orphan worker watches
                    # its parent and writes this receipt only after draining and closing.
                    expected = json.loads(intent.read_text())["nonce"]
                    async with asyncio.timeout(40):
                        while True:
                            if stopped.exists():
                                receipt = json.loads(stopped.read_text())
                                if (
                                    receipt.get("nonce") == expected
                                    and receipt.get("stopped") is True
                                ):
                                    break
                            await asyncio.sleep(0.1)
        finally:
            if self.log is not None:
                self.log.close()
                self.log = None
