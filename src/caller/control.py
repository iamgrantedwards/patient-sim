"""Explicit one-call orchestration; no dial/redial from reads or reconnection."""

import asyncio
import secrets
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..review.store import CALL_ID, EvidenceStore
from .call_slot import CallBusy, CallSlot
from .scenarios import SCENARIOS, get_scenario
from .transcript import read_events, reconcile, write_json

TERMINAL = {"ended", "failed"}
MESSAGES = {
    "configuration": "Configuration is not ready. Check the required values in .env and the README.",
    "worker_start": "The dedicated worker did not register. Check .runtime worker logs and LiveKit connectivity; no automatic retry.",
    "dispatch": "Dispatch failed or timed out. Review the outcome before trying another call.",
    "worker_exit": "The worker exited. Available evidence is preserved; review it before another call.",
    "deadline": "The controller deadline expired. Stop was requested and available evidence was preserved.",
    "cleanup": "Call termination could not be confirmed. Use Stop / recover again; new calls are blocked.",
    "unreadable_operation": "The saved operation is unreadable. Inspect .runtime/active-call.json; new calls are blocked.",
}


class ControlError(RuntimeError):
    def __init__(self, message: str, status=409):
        self.status = status
        super().__init__(message)


class CallManager:
    def __init__(self, root: Path, backend_factory, *, max_seconds=240, poll=0.5):
        self.root = root
        self.slot = CallSlot(root)
        self.factory = backend_factory
        self.max_seconds = max_seconds
        self.poll = poll
        self.start_token = secrets.token_urlsafe(32)
        self.lock = asyncio.Lock()
        self.task: asyncio.Task | None = None
        self.backend: Any = None
        self.stop_event = asyncio.Event()
        self.operation: dict | None = None
        self.closing = False

    def save(self, **changes):
        assert self.operation is not None
        self.operation.update(changes, updated_at=time.time())
        self.slot.save(self.operation)

    def metadata(self, call_id):
        try:
            return EvidenceStore(self.root / "calls").read(call_id, "meta.json")
        except (ValueError, OSError):
            return {}

    def snapshot(self):
        source = self.operation if self.task and not self.task.done() else self.slot.read()
        record: dict[str, Any] = dict(source or {"phase": "idle"})
        if record["phase"] not in TERMINAL | {"idle", "recovery_required"} and not (
            self.task and not self.task.done()
        ):
            record["phase"] = "recovery_required"
        record["message"] = MESSAGES.get(record.get("error") or "", "")
        record["start_token"] = self.start_token
        record["live_turns"] = []
        call_id = record.get("call_id")
        if isinstance(call_id, str) and CALL_ID.fullmatch(call_id):
            try:
                path = EvidenceStore(self.root / "calls").file(call_id, "events.jsonl")
                # The caller's reconciler preserves committed item IDs and partial speech.
                turns, _ = reconcile(read_events(path))
                record["live_turns"] = [
                    {key: turn[key] for key in ("idx", "role", "text", "status")}
                    for turn in turns[-100:]
                ]
            except (ValueError, OSError, KeyError, TypeError):
                record["live_warning"] = (
                    "Live transcript unavailable; saved raw evidence remains on disk."
                )
        return record

    async def start(self, scenario: str, start_token: str, request_id: str):
        async with self.lock:
            if self.closing:
                raise ControlError("The console is shutting down.")
            prior = self.slot.read()
            if prior and prior.get("request_id") == request_id:
                if prior.get("scenario") != scenario:
                    raise ControlError("An existing request ID cannot change scenario.", 422)
                return self.snapshot()  # An uncertain HTTP response must never cause a redial.
            if not secrets.compare_digest(start_token, self.start_token):
                raise ControlError(
                    "This confirmation expired. Review the latest state and confirm again."
                )
            if scenario not in SCENARIOS:
                raise ControlError("Unknown scenario.", 422)
            get_scenario(scenario)
            try:
                self.slot.acquire()
            except CallBusy as error:
                raise ControlError(str(error)) from None
            try:
                prior = self.slot.read()
                if prior and prior.get("phase") not in TERMINAL:
                    raise ControlError("An unresolved call needs Stop / recover before a new call.")
                try:
                    self.backend = self.factory()
                except Exception:
                    raise ControlError(MESSAGES["configuration"], 503) from None
                call_id = datetime.now(UTC).strftime("call-%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8]
                (self.root / "calls" / call_id).mkdir(parents=True, exist_ok=False)
                self.operation = {
                    "call_id": call_id,
                    "scenario": scenario,
                    "request_id": request_id,
                    "phase": "preparing_worker",
                    "requested_at": time.time(),
                    "error": None,
                    "stop_requested": False,
                    "cleanup_confirmed": False,
                }
                self.save()
                self.start_token = secrets.token_urlsafe(32)
                self.stop_event = asyncio.Event()
                self.task = asyncio.create_task(self.run())
                return self.snapshot()
            except BaseException:
                self.slot.release()
                raise

    async def until_stopped(self, awaitable):
        action = asyncio.create_task(awaitable)
        stop = asyncio.create_task(self.stop_event.wait())
        try:
            done, _ = await asyncio.wait([action, stop], return_when=asyncio.FIRST_COMPLETED)
            if stop in done:
                action.cancel()
                await asyncio.gather(action, return_exceptions=True)
                return False, None
            return True, await action
        finally:
            action.cancel()
            stop.cancel()
            await asyncio.gather(action, stop, return_exceptions=True)

    async def run(self):
        assert self.operation is not None
        call_id = self.operation["call_id"]
        error = None
        stage = "worker_start"
        try:
            prepared, _ = await self.until_stopped(self.backend.prepare(call_id))
            if prepared and not self.stop_event.is_set():
                self.save(phase="dispatching")
                stage = "dispatch"
                dispatched, dispatch_id = await self.until_stopped(
                    self.backend.dispatch(call_id, self.operation["scenario"])
                )
                if dispatched:
                    self.save(phase="waiting_for_worker", dispatch_id=dispatch_id)
                    deadline = time.monotonic() + self.max_seconds + 90
                    while not self.stop_event.is_set():
                        meta = self.metadata(call_id)
                        if meta.get("status") == "ended":
                            self.save(ended_by=meta.get("ended_by"), phase="finalizing")
                            break
                        if self.backend.exited():
                            error = "worker_exit"
                            break
                        if time.monotonic() > deadline:
                            error = "deadline"
                            break
                        phase = "waiting_for_worker"
                        if meta.get("ended_by"):
                            phase = "finalizing"
                        elif meta.get("sip", {}).get("status") == "answered":
                            phase = "connected"
                        elif meta.get("sip", {}).get("status") == "dialing":
                            phase = "dialing"
                        elif meta:
                            phase = "preparing_audio"
                        if phase != self.operation["phase"]:
                            self.save(phase=phase)
                        await asyncio.sleep(self.poll)
        except Exception:
            error = stage
        finally:
            try:
                self.save(phase="finalizing", error=error)
            finally:
                await self.finish(call_id, error)

    async def finish(self, call_id, error=None):
        # Stop the room promptly; retain the worker long enough to finalize available audio.
        confirmed = False
        try:
            try:
                await self.backend.hangup(call_id)
            except Exception:
                pass
            await self.backend.close()
            # Check again after the worker has stopped and cannot issue another SIP request.
            await self.backend.hangup(call_id)
            confirmed = True
        except Exception:
            error = "cleanup"
        finally:
            meta = self.metadata(call_id)
            try:
                self.save(
                    phase=("failed" if error else "ended") if confirmed else "recovery_required",
                    error=error,
                    cleanup_confirmed=confirmed,
                    ended_by=meta.get("ended_by")
                    or (self.operation or {}).get("stop_reason")
                    or "unknown",
                    evidence_status="finalized"
                    if meta.get("status") == "ended"
                    else "partial_or_unavailable",
                )
            finally:
                self.slot.release()

    async def stop(self, call_id: str, reason="operator_stop"):
        async with self.lock:
            owned = self.task is not None and not self.task.done()
            record = self.operation if owned else self.slot.read()
            if not record or record.get("call_id") != call_id or not CALL_ID.fullmatch(call_id):
                raise ControlError("That call is no longer the active operation.")
            if record["phase"] in TERMINAL:
                return self.snapshot()
            if not owned:
                try:
                    self.slot.acquire()
                except CallBusy as error:
                    raise ControlError(str(error)) from None
                self.operation = record
                try:
                    self.backend = self.factory()
                except Exception:
                    self.slot.release()
                    raise ControlError(MESSAGES["configuration"], 503) from None
            try:
                self.save(stop_requested=True, stop_reason=reason, phase="stopping")
                write_json(
                    self.root / "calls" / call_id / "operator-stop.json",
                    {"reason": reason, "requested_at": time.time()},
                )
            except OSError:
                raise ControlError(
                    "Stop was requested, but recovery evidence could not be saved. Keep the console running and inspect local storage.",
                    503,
                ) from None
            finally:
                self.stop_event.set()
                if self.task is None or self.task.done():
                    self.task = asyncio.create_task(self.finish(call_id))
            return self.snapshot()

    async def shutdown(self):
        self.closing = True
        if self.task and not self.task.done() and self.operation:
            try:
                await self.stop(self.operation["call_id"], "controller_shutdown")
            finally:
                await self.task
