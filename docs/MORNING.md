# Next working session

The local UI exists before filming. Do not record tool installation or reenact a past
fix as if it were new work. Keep the existing raw call private until listening/release review.

## First: confirm the working surface

From the patient-sim checkout:

```sh
uv run python -m src.review --enable-calls --enable-reviews
```

Open `http://127.0.0.1:8765`. If that port already has the prepared console running,
use it rather than starting a second copy. The page must show **Run a test call** and
the real prior call in the library. A UI page load makes no call. See OPERATIONS.md for
status, confirmation, and recovery behavior. Keep the owned caller ID unchanged.

## Genuine debugging recording

Start with the [two-call debugging journal](DEBUGGING.md) and
[copyable Loom speaking notes](DEBUGGING-SCRIPT.md), updated 2026-09-19. The journal
labels the process hierarchy and parent-only exit check as pre-recording inspection. The
second attempt exposed #46: a child-worker crash, repeated initialization failure and
stale Dialing status. That unresolved problem is the first investigation; its native
crash cause remains unknown. Preserve the original files and avoid automatic retries.

Record the actual next working session with your own voice and webcam. Show the UI,
relevant code/issue, your prompts, and the resulting verification. Keep account settings,
`.env`, provider credentials and private desktop content out of the capture.

The original call's closing behavior (#12) is still unresolved: the remote side said
goodbye and disconnected as the patient started another question. After investigating
#46, listen to that ending and inspecting the transcript/prompt/events. Form a hypothesis, reproduce
only as needed, make the smallest justified change, and verify it. If another real bug
appears first, document and debug that honestly. The AgentHandoff handler fix (#21)
happened before filming and should be described as prior work, not staged as discovery.

The second attempt was started and stopped through the console; #24 remains open
until a complete call and listening review. After a supported #46 fix and separate
authorization, use the read-only smoke scenario and explicit confirmation for a retest. Observe registration, dispatch, connection, and
ending; then compare the saved recording and transcript. Stop is available if needed,
but an operator-stopped call does not pass the natural-ending gate. Capture the call ID,
commit, settings and result. No automatic retry or background call schedule exists.

Use the [per-call review workflow](CALL-REVIEW.md) and [blank sheet](CALL-REVIEW-TEMPLATE.md)
after each attempt. Review completion and submission suitability are separate decisions.
Use Review beside the recording to save checks and update the listening badge. Optional manual sheets stay local and are not imported.

## After the first good call

- Listen end to end and record the actual review result. Playback alone never marks a
  call reviewed. M1 needs a clean natural ending and matching usable evidence.
- Verify Athena product exploration (#8); never dial its confirmation-screen number.
- Complete the read-only configuration screen (#13), then freeze the chosen settings
  and expand scenarios. Hold caller ID, synthetic patient facts and voice fixed.
- Collect at least ten complete, human-reviewed audio/transcript pairs across the
  assessment's required variety. Neither existing attempt establishes an accepted conversation.
- Write findings only from evidence, with expected behavior, basis, measured timestamp,
  verbatim quote, attribution, uncertainty and corroboration where available. Keep our
  caller bugs separate. No confirmed assessment-agent bug currently exists.
- Record the final walkthrough (maximum three minutes) once the evidence/findings are
  ready. Check both video links and repository access while logged out before submitting.

## GitHub review and landing

Foundation #20, review UI #27, controls #28, learning/guide/copy #32/#33/#35,
compact layout #49 and debugging journal #51 are merged. Follow current issue and PR
states on GitHub; old notebook entries describe the state at the time they were written.

Choose the issue before the next change, post the plan, then link the draft PR and
actual verification back to that issue. For the next recorded session, use #46/#25, followed by #12;
record the call ID and results on #24/#21 as well. See ROADMAP.md for current ordering.
Required CI and actual voice acceptance are separate: green CI does not pass M1.
Main stays protected; unreviewed recordings and secrets stay out of commits.
