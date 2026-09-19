# Next working session

The local UI exists before filming. Do not record tool installation or reenact a past
fix as if it were new work. Keep the existing raw call private until listening/release review.

## First: confirm the working surface

From the patient-sim checkout:

```sh
uv run python -m src.review --enable-calls
```

Open `http://127.0.0.1:8765`. If that port already has the prepared console running,
use it rather than starting a second copy. The page must show **Run a test call** and
the real prior call in the library. A UI page load makes no call. See OPERATIONS.md for
status, confirmation, and recovery behavior. Keep the owned caller ID unchanged.

## Genuine debugging recording

Record the actual next working session with your own voice and webcam. Show the UI,
relevant code/issue, your prompts, and the resulting verification. Keep account settings,
`.env`, provider credentials and private desktop content out of the capture.

The original call's closing behavior (#12) is still unresolved: the remote side said
goodbye and disconnected as the patient started another question. Start by listening to
that ending and inspecting the transcript/prompt/events. Form a hypothesis, reproduce
only as needed, make the smallest justified change, and verify it. If another real bug
appears first, document and debug that honestly. The AgentHandoff handler fix (#21)
happened before filming and should be described as prior work, not staged as discovery.

The first console call is also a real acceptance check for #24. Use the read-only smoke
scenario and explicit confirmation. Observe registration, dispatch, connection, and
ending; then compare the saved recording and transcript. Stop is available if needed,
but an operator-stopped call does not pass the natural-ending gate. Capture the call ID,
commit, settings and result. No automatic retry or background call schedule exists.

## After the first good call

- Listen end to end and record the actual review result. Playback alone never marks a
  call reviewed. M1 needs a clean natural ending and matching usable evidence.
- Verify Athena product exploration (#8); never dial its confirmation-screen number.
- Complete the read-only configuration screen (#13), then freeze the chosen settings
  and expand scenarios. Hold caller ID, synthetic patient facts and voice fixed.
- Collect at least ten complete, human-reviewed audio/transcript pairs across the
  assessment's required variety. The current incomplete first attempt is not counted.
- Write findings only from evidence, with expected behavior, basis, measured timestamp,
  verbatim quote, attribution, uncertainty and corroboration where available. Keep our
  caller bugs separate. No confirmed assessment-agent bug currently exists.
- Record the final walkthrough (maximum three minutes) once the evidence/findings are
  ready. Check both video links and repository access while logged out before submitting.

## GitHub review and landing

Foundation #20, review UI #27 and controls #28 are merged. The added learning work
is issue-led: #29 / PR #32, #30 / PR #33 and #31 / PR #35. Each dependent PR targets
its predecessor until that predecessor lands. #34 tracks npm audit availability;
#36 / PR #37 fixes an incompatible Dependabot update proposal.

Choose the issue before the next change, post the plan, then link the draft PR and
actual verification back to that issue. For the next recorded session, use #12/#25;
record the call ID and results on #24/#21 as well. See ROADMAP.md for current ordering.
Required CI and actual voice acceptance are separate: green CI does not pass M1.
Main stays protected; unreviewed recordings and secrets stay out of commits.
