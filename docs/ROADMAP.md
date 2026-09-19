# Build order and GitHub workflow

Updated 2026-09-19 after the code merges and issue audit requested by Grant. GitHub
issues are the task status source; this document defines the sequence and review
rules. The usable local UI precedes the genuine debugging video.

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
  foundation. It and the separate review UI #27 and call controls #28 were merged on
  2026-09-19 at Grant's request, with required CI green. M1 and live confirmation of
  defects #21/#12 remain open; merging code does not establish call quality.
- The learning work is split into #29 / PR #32 (hints), #30 / PR #33 (guide), and
  #31 / PR #35 (concise copy). The dependent PRs target their predecessor to keep each
  diff focused. Retarget to main in order after landing, and verify the current head.
  Independent fixes, such as #36 / PR #37, target main directly.
- Open a focused draft PR on the first implementation commit; use the repository
  template with actual verification and risks. Each issue links back to its PR.
- Fixes discovered while building get issues with observed evidence. Reuse existing
  issues when they already describe the failure; use `bug` for our code and
  `type:finding` only for justified findings about the assessment agent.
- Before pushing code, run the relevant checks and the CI-equivalent verification.
  Run `uv run pytest` before every commit as required by AGENTS.md. Browser behavior
  needs browser verification as well as automated tests. Add checks for new UI code
  in the UI PR; keep Ruff/Pyright for Python and use Biome if standalone JS is added.
- Keep `main` protected. Required CI passing is necessary but does not establish live
  voice quality. Review the code acceptance before merging. When Grant authorizes a
  code merge ahead of real-call acceptance, retain the unmet live checks in open issues
  and state the distinction in the PR; never close M1 on offline evidence alone.
- Use `Closes #...` for fully implemented issue scope when merging to `main`. Code
  remains open/in-review while only on a draft branch. Completed external setup tasks
  may close once their evidence is recorded. Repeat the closing keyword for each issue
  (`Closes #9. Closes #10.`); a comma-separated list may leave tasks open.
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


## Issue-led delivery

1. **Start from acceptance.** Choose one ready task issue, confirm its scope/dependencies,
   assign an owner, set `status:in-progress`, and post a short plan before implementation.
   A PR is a delivery unit, not a substitute for the issue's acceptance criteria.
2. **Keep the trail live.** Open the draft PR on the first implementation commit. Link
   both directions. Post material discoveries, failed checks, changed hypotheses and
   relevant evidence as they happen. Create a new issue when a distinct defect appears.
3. **Report the boundary.** Before review, comment with the implementation/PR, actual
   local and hosted verification, remaining uncertainty, and the next action. Mark
   `in-review` while awaiting landing; use `blocked` with the specific dependency when
   meaningful progress cannot proceed. A service outage is not a clean audit.
4. **Close acceptance, then refresh parents.** After merge, close completed code tasks
   with evidence. Keep live-call/listening tasks open when unverified. Update epic
   checkboxes and remove obsolete status labels from closed issues. No fabricated
   results, staged debugging, rewritten timestamps, or retroactive claims of planning.

On 2026-09-19, #38 reconciled earlier issue descriptions against the actual commit/PR
history and added explicitly dated review comments. Earlier work was grouped in larger
foundation, UI and controls PRs; the comments do not claim those batches were smaller
or that missing progress updates happened at the time.

## Current execution order

- **Verification:** #34 tracks npm audit maintenance/recovery; #36 / PR #37 corrects
  an incompatible Dependabot proposal. Preserve required checks on every current head.
- **Next working session:** #25 records genuine diagnosis of #12; the confirmed console
  call also supplies the pending acceptance for #24 and live confirmation for #21.
  Required product exploration #8 remains unverified and needs its own evidence.
- **Measurement:** finish killed-process acceptance #14 and audio-offset timing #15,
  then run the read-only configuration screen #13 after the first-good-call gate.
- **Evaluation:** collect the complete reviewed pairs #18 and write findings #19 from
  the first useful calls; verify the claims distinction #17 while writing. Final video,
  logged-out access checks and submission remain #26.


## Required PR labels

Every PR, including drafts and Dependabot updates, needs exactly one delivery type:
`type:task` for implementation/fixes or `type:docs` for documentation-only work. Add
at least one of `area:analysis`, `area:ci`, `area:evidence`, `area:process`,
`area:simulator`, `area:telephony`, or `area:ui`. Multiple areas are allowed. `bug` and
`accessibility` provide additional context; `type:finding` is reserved for evaluation
issues. Set labels with `gh-personal pr create --label ...` when opening the draft.

The required **PR labels** check reads current GitHub metadata on opening, commits,
reopening, readiness, edits (including base changes), and label addition/removal.
API errors and missing/ambiguous labels fail the check. Metadata events do not restart
the separate application CI suite. A stale event rerun still reads current labels.
The workflow has read-only permissions and receives no provider credentials.

PR draft/open/merged state records delivery status. Keep `status:` labels on task
issues, where acceptance can remain open after a code merge. On 2026-09-19, #42 applied
scope labels retrospectively to existing PRs and removed stale PR status labels;
that reconciliation does not claim those labels were present earlier.
