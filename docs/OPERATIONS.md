# Local call operations

The default viewer is read-only. Calling is an explicit mode for a trusted local operator,
with the existing sole assessment destination and the same owned caller number.

## Start and review

1. From this checkout, run `uv sync --locked`, then
   `uv run python -m src.review --enable-calls`.
2. Open `http://127.0.0.1:8765`. A readiness message validates local configuration, not
   provider availability. Keys stay server-side; no `.env` values should be filmed.
3. Choose the supported scenario and **Review & call**. Check the fixed number, caller
   ID and duration cap. The confirmation checkbox and **Place one call** initiate one
   operation. Closing the dialog makes no call.
4. The console shows registration, dispatch, worker preparation, dialing, connection,
   and finalization from actual worker/provider acknowledgements and saved metadata.
   A phase can be brief or skipped between polls. The live transcript contains committed
   text only; it has no invented word/audio timing and is not a live audio monitor.
5. Once ended, **Open saved evidence** loads the available original recording and
   transcript. Listen to them together. Cleanup and file existence do not establish
   a complete conversation or a successful patient request.

Use the default read-only viewer to inspect a different `--calls-dir`. Calling requires
this project's calls directory. The CLI alternative is
`uv run python -m src.caller.dial --scenario smoke --call`; it uses the same lock and
worker lifecycle, and no manually started worker is needed. Its default remains dry-run.

## Stop, disconnect, or recovery

- **Stop call** marks an operator stop, requests room deletion, and lets the worker save
  available evidence before checking the room again. The UI may show Finalizing while
  this completes. Ctrl-C on the console/CLI records `controller_shutdown`.
- Browser refresh/tab closure does not dial or redial, and does not itself end an
  existing call. Reopen the local console and use Stop if needed. The provider duration
  limit remains in effect.
- If the console loses connection, do not assume the call ended. Restore the local
  service and inspect its saved operation. Never click repeatedly to retry a start.
- An unresolved operation offers **Stop / recover** and disables new calls. A dedicated
  worker notices parent-process loss, drains, closes, and writes a nonce-bound stopped
  receipt. Recovery requires that receipt (or confirmation that the owned process
  exited) plus an absent room. If either cannot be confirmed, recovery stays blocked.
- `.runtime/active-call.json`, worker logs, and lifecycle receipts are private local
  diagnostics. Do not remove them merely to unblock another call. A forcibly killed
  orphan may require checking the LiveKit room/dispatch and local process state manually;
  the controller intentionally does not kill a PID it did not create.
- Provider errors are summarized safely in the UI. Detailed worker logs remain local
  and may contain evidence or provider identifiers; review before sharing.

The concurrency guard covers this project's UI and CLI. It does not govern someone
manually dispatching work through the LiveKit dashboard or running an older checkout.
Run only this checkout during evidence collection. Do not expose the console through a
public tunnel. No recurring/batch calling or automatic retries are implemented.

## Acceptance still required

Offline tests cover lifecycle, confirmation, request boundaries, duplicate starts, stop
while preparing/dispatching, failed cleanup, and crash recovery. Browser tests use
explicitly synthetic responses. A real call initiated through this console, matching
original audio/transcript, human listening, and a natural ending remain required. The
existing closing issue (#12) must not be called fixed solely because control tests pass.
