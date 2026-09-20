# Local call operations

The default viewer is read-only. Calling is an explicit mode for a trusted local operator,
with the existing sole assessment destination and the same owned caller number.

## Start and review

1. From this checkout, run `uv sync --locked`, then
   `uv run python -m src.review --enable-calls --enable-reviews`.
2. Open `http://127.0.0.1:8765`. A readiness message validates local configuration, not
   provider availability. Keys stay server-side; no `.env` values should be filmed.
3. Choose the supported scenario and **Review & call**. Check the fixed number, caller
   ID and duration cap. The confirmation checkbox and **Place one call** initiate one
   operation. Closing the dialog makes no call.
4. The console shows registration, dispatch, worker preparation, dialing, connection,
   and finalization from actual worker/provider acknowledgements and saved metadata.
   A phase can be brief or skipped between polls. The live transcript contains committed
   dialogue only, with partial speech labeled. It opens automatically for a new call,
   shows connection/waiting progress before the first turn, and closes when the call
   ends. Manual collapse is preserved during that call. The bounded transcript follows new turns
   unless you scroll back; return to the latest turn to resume following. It is not a
   live audio monitor, and callback times are not audio boundaries.
5. Once ended, select the resulting call in **Calls** to open its saved details. The
   recording is primary; expand Conversation to read the transcript. Review saves an
   outcome and useful notes; detailed checks are optional. Usable requires listening
   confirmation and Complete evidence: OK. Cleanup/file existence alone do not establish
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

## Optional transcript assessment

Add `--enable-assessments` to enable **Assess transcript** on eligible saved calls.
This is a paid, explicit LiveKit Inference request using the scenario ID, transcript
and allowlisted capture/termination metadata,
not a phone call or an audio review. Saved results remain viewable without that flag.
**Add AI summary** in Review copies a fresh saved summary into draft notes without
changing grades or listening approval. Call cards show current scores or historical
scores marked prior; Notes saved is distinct from Human reviewed and Usable. The
separate Call quality section highlights ending concerns without claiming an audio
review. See [EVALUATION.md](EVALUATION.md).

## Local browser access

Use the same `http://127.0.0.1:8765` origin throughout the session. The app allows a
top-level link to its home page but rejects cross-site API/asset requests and foreign
write origins. If an old page reports an origin/token error after a server restart,
reload the address and reopen the call before retrying an explicit action. Do not add
permissive CORS or expose the server publicly to bypass the local boundary.

## Acceptance still required

Offline tests cover lifecycle, confirmation, request boundaries, duplicate starts, stop
while preparing/dispatching, failed cleanup, and crash recovery. Browser tests use
explicitly synthetic responses. Real connected calls and artifact finalization have
also been exercised; [COLLECTION.md](COLLECTION.md) records ten candidates. Human
listening, coherent conversation quality and natural endings remain unverified. The
existing closing issue (#12) must not be called fixed solely because control tests pass.
