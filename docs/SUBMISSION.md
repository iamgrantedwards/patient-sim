# Submission checklist

Closeout audit: 2026-09-20 UTC (2026-09-19 Pacific), tracked in #75.
The implementation is on main; the submission is not yet complete. This checklist
tracks the employer's deliverables, not additional production infrastructure.

## Finish in this order

| Step | Owner | Remaining acceptance | Issue |
| --- | --- | --- | --- |
| 1. Select the evidence | Grant | Listen to the ten candidates in COLLECTION.md; confirm full, coherent, two-sided audio and matching transcripts. Note consequential errors and endings. Replace a pair only if it is unusable. | #18, #12, #24 |
| 2. Finalize findings | Grant + Codex | Check candidate observations against the audio; add exact offsets, quotes, expected behavior, impact and attribution to BUGS.md. Do not turn STT spelling differences or unverified backend claims into confirmed office defects. | #4 |
| 3. Publish the call pairs | Codex, after review | Review the selected files for public release, explicitly add OGG/MP3 plus transcripts and an index in a focused labeled PR, verify hashes and public downloads. A local ZIP alone is not submission. | #18, #26 |
| 4. Finish the videos | Grant | Final walkthrough at most three minutes; own voice/webcam. Debugging video already recorded. Verify both videos play without login and include the required content. | #25, #26 |
| 5. Final delivery check | Codex + Grant | Green protected main, fresh-clone setup, ten public playable pairs, final findings, both video links in GitHub, exact caller number and applicable receipts. Grant submits the employer form. | #26 |

The detailed seven-row review is optional. To use the UI's Usable outcome, save
listening confirmation and Complete evidence: OK; other checks may stay not assessed.
AI summary is a draft-notes shortcut, not proof of listening or a confirmed finding.
No new calls are needed merely to make the attempt count larger.

## Links and handoff

- [Public repository](https://github.com/iamgrantedwards/patient-sim)
- [Debugging recording](https://www.loom.com/share/648e67f4f08d4d75af16477e1995304e)
- Final walkthrough: pending Grant's recording/link.
- Single assessment caller number: **+19062567632**. Destination is a different number;
  the submission asks for the caller number.
- [Exact ten candidate IDs and coverage](COLLECTION.md)
- [Findings and caller improvements](../BUGS.md)
- [Two-paragraph architecture](../ARCHITECTURE.md)
- [Strategy, AI assessment and listening boundaries](EVALUATION.md)
- [Setup and required environment variables](SETUP.md); `.env.example` is committed,
  real `.env` files and credentials remain ignored. Reviewers use their own credentials
  to place calls; viewing published evidence should not require provider access.

Original files live in ignored `calls/<call-id>/`. The prepared local bundle is
`.runtime/submission-candidates/` and `.runtime/patient-sim-ten-call-candidates.zip`.
These paths are private working artifacts, not publicly downloadable deliverables.
Publish only reviewed files, retain provenance, and never broadly force-add calls/.

## Verified engineering status

At the start of this audit, main was `af3d57b`; its full
[CI run passed](https://github.com/iamgrantedwards/patient-sim/actions/runs/35486646029).
No PRs were open. All existing PRs had one delivery type and at least one area label.
Main requires an up-to-date Verify and package check plus PR labels, enforces the
rules for administrators, and blocks force-pushes/deletion. No independent reviewer
is required on this personal repository; do not describe it as independent review.

Fresh public clone of main `af3d57b`: `uv sync --locked`, the smoke-scenario
`--dry-run` and review CLI help all passed without a real `.env` or provider credentials.
No call was placed. The closeout branch also passed 276 Python tests, 96 browser cases,
quality/security checks and package verification.

Unauthenticated HTTP requests returned 200 for the repository and the debugging
share page. This checks page access only: video playback, webcam, voice and contents
have not been independently verified. No payment, publication of raw calls or final
form submission was performed by this audit.

## Remaining evidence limits

- Ten captured pairs total 20.59 minutes; none has a saved human review at audit time.
  Capture integrity and a green test suite do not establish coherent audio.
- BUGS.md documents our fixes and office observations. No office-agent defect is yet
  confirmed. Useful audio-backed findings remain a submission priority.
- The native SIGSEGV cause remains unknown. #58 fixed propagation/duplicate admission;
  later connected calls verify recovery-path use, not a native-library cure.
- The saved refill AI assessment grades supported claims positively from repetition
  and lack of contradiction. This does not verify its chart claim. Treat that score
  as an uncalibrated model judgment and check the cited evidence before using it.
- #13 configuration comparison and #15 audio-aligned timing are deferred optional
  experiments. Do not claim measured latency, model superiority or controlled barge-in.

## GitHub closeout policy

A completed fix closes with its PR/tests/retest evidence. Listening, public artifact
and video gates remain open until demonstrated. Deferred experiments stay in backlog,
separate from submission blockers. Epics summarize their remaining child acceptance;
there is no benefit in closing them just to show zero open issues. This audit is dated
now and does not rewrite earlier discovery or implementation history.
