# Build order and GitHub workflow

Updated 2026-09-18 after Grant requested a usable UI before recording the debugging
video. GitHub issues are the task status source; this document defines the sequence
and review rules. No additional call is needed to start the UI.

## Next work

| Order | Deliverable | Tracking | Acceptance |
| --- | --- | --- | --- |
| 1 | Call review UI | [#23](https://github.com/iamgrantedwards/patient-sim/issues/23) | Show the real existing call, audio player, patient/remote transcript, partial turns, outcome, and review status; browser-verified |
| 2 | Call controls and live status | [#24](https://github.com/iamgrantedwards/patient-sim/issues/24) | Explicit one-call start/stop, actual progress and dialogue, duplicate-start protection, actionable errors, fixed assessment destination |
| 3 | Genuine recorded debugging | [#25](https://github.com/iamgrantedwards/patient-sim/issues/25), [#21](https://github.com/iamgrantedwards/patient-sim/issues/21), [#12](https://github.com/iamgrantedwards/patient-sim/issues/12) | UI exists first; show Grant's prompts and real diagnosis, code change, and verification with his webcam and voice |
| 4 | Close first-call quality gate | [M1](https://github.com/iamgrantedwards/patient-sim/milestone/2) | Natural ending plus a matching recording listened to end to end; no unresolved callback exception |
| 5 | Calibrate and collect evidence | [#13](https://github.com/iamgrantedwards/patient-sim/issues/13), [#15](https://github.com/iamgrantedwards/patient-sim/issues/15), [#18](https://github.com/iamgrantedwards/patient-sim/issues/18) | Traceable settings, audio-based timing, at least ten complete reviewed recording/transcript pairs across varied scenarios |
| 6 | Findings and final submission | [#19](https://github.com/iamgrantedwards/patient-sim/issues/19), [#26](https://github.com/iamgrantedwards/patient-sim/issues/26) | Evidence-backed BUGS.md, docs, final walkthrough of at most three minutes, public repository/video links |

Required product exploration [#8](https://github.com/iamgrantedwards/patient-sim/issues/8)
remains unverified. It can proceed alongside UI work. The Athena confirmation number
must never be dialed.

The [UI epic #22](https://github.com/iamgrantedwards/patient-sim/issues/22) and
[UI milestone](https://github.com/iamgrantedwards/patient-sim/milestone/8) track the two
UI deliveries. This is Grant's requested scope, not an employer-mandated frontend.
Keep the interface local and focused on actual calls. No public hosting, user-account
system, simulated incoming-call screen, or analytics platform is needed.

## Pull requests

- [PR #20](https://github.com/iamgrantedwards/patient-sim/pull/20) owns the caller/CI
  foundation. Its CI is green at `338e7f8`; M1 and defects #21/#12 still block readiness.
  A later commit must pass its own checks. Do not append UI implementation to it.
- Use `codex/call-review-ui` for #23 and `codex/call-controls` for #24. Open a draft PR
  on the first implementation commit; each PR links its issue and fills the repository
  template with actual verification and risks.
- While the foundation is unmerged, the first UI PR targets `codex/first-call` so its
  diff contains only UI changes. Clearly state that dependency. The controls PR can
  depend on the review UI. Retarget/rebase in order after the foundation lands; never
  merge a dependent PR into the foundation branch merely to combine the work.
- Fixes discovered while building get issues with observed evidence. Reuse existing
  issues when they already describe the failure; use `bug` for our code and
  `type:finding` only for justified findings about the assessment agent.
- Before pushing code, run the relevant checks and the CI-equivalent verification.
  Run `uv run pytest` before every commit as required by AGENTS.md. Browser behavior
  needs browser verification as well as automated tests. Add checks for new UI code
  in the UI PR; keep Ruff/Pyright for Python and use Biome if standalone JS is added.
- Keep `main` protected. Required CI passing is necessary but does not establish live
  voice quality. Merge only when that PR's acceptance criteria and review are complete.
- Use `Closes #...` for fully implemented issue scope when merging to `main`. Code
  remains open/in-review while only on a draft branch. Completed external setup tasks
  may close once their evidence is recorded.
- Review raw recordings before explicitly adding selected submission evidence. Never
  include `.env`, credentials, or the unreviewed calls directory in a broad `git add`.

## Issue states

Every active task has one `status:` label and an owner. `backlog` is later work;
`ready` is defined and unblocked; `in-progress` means actual work is underway;
`in-review` means implemented on a PR but not landed; `blocked` identifies an unmet
dependency or acceptance gate. Completion is a closed issue with evidence, not a
second status label. Epics use linked task lists; milestones group deliverables.

The UI-ready recording preference must not block building the UI. If a bug is fixed
before filming, use another real issue for the debugging video rather than reenacting
the fix as live work.
