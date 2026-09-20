# Delivery status and GitHub workflow

Application freeze reconciled 2026-09-20 UTC (2026-09-19 Pacific), #90 after #75. GitHub issues track acceptance;
[SUBMISSION.md](SUBMISSION.md) is the current closeout order. Earlier plans and actual
iteration remain in NOTEBOOK.md, DEBUGGING.md, issue comments and merged PR history.

## Current scope

The caller, ten-scenario catalog, evidence capture, local console, optional AI
assessment and compact reviews are merged. Ten candidate recording/transcript pairs
are captured. Remaining work is listening/selection, useful verified findings, public
artifact delivery, video checks and submission. Grant explicitly froze application
scope: complete the already-open #88 fixes and #90 documentation, then only the final
links/evidence handoff. Grant will make one final presentation call. Do not restart UI,
infrastructure or scenario development; publish all records with incomplete attempts
clearly distinguished from the minimum ten complete conversations.
The original candidate set is distinct from the later 20-attempt / 19-file-pair inventory.

| Category | Issues | Next action |
| --- | --- | --- |
| Audio and workflow acceptance | #12, #18, #24 | Listen to selected evidence, document ending/quality decisions and publish reviewed pairs. |
| Findings | #4 | Verify candidate observations against audio; keep our defects distinct from office-agent findings. |
| Videos and handoff | #25, #26 | Link and check the debug video, finish the <=3-minute walkthrough, verify public deliverables and submit. |
| Deferred experiments | #13, #15 | Keep in backlog; neither is an employer-mandated implementation gate. No comparative or measured-latency claims. |
| Parent rollups | #1, #2, #3, #5, #22 | Update from child evidence; don't treat each epic as a new build. |

#46's lifecycle fix is separate from the unresolved native SIGSEGV cause. PR #58
and later connected retests establish failure propagation/duplicate-admission work;
no native-library root-cause fix is claimed. #21 callback handling and #8 product
exploration are complete. The debugging recording is captured, not a new task to stage.

## Issue-led delivery

1. Choose/create a task before implementation. Assign the owner, set one status label,
   record acceptance and post a short plan.
2. Open a focused draft PR on the first commit using the repository template. Link the
   issue in the PR and the PR in an issue comment. Document actual discoveries/results.
3. Run `uv run pytest` before commits and `./scripts/verify.sh` before pushing.
   Required GitHub checks must pass on the final PR revision before merging.
4. Use `Closes #N` only when all acceptance is satisfied. Otherwise use `Related: #N`
   and name the remaining check. Remove obsolete status labels when closing.
5. Update epic checkboxes and milestone state from actual acceptance. Retrospective
   reconciliation is dated as such, never presented as earlier planning.

## Labels, protection and evidence

Every PR, including drafts and dependency updates, has exactly one delivery type:
`type:task` or `type:docs`, plus a recognized area label: analysis, ci, evidence,
process, simulator, telephony or ui. `bug` and `accessibility` are additional context;
`type:finding` is reserved for justified office-agent evaluation issues.

PR draft/open/merged state tracks code delivery. `status:` labels belong on issues:
ready, in-progress, in-review, blocked or backlog. A merged task awaiting human
listening is blocked by that named acceptance, not still awaiting code review.

Protected main requires up-to-date Verify and package and PR labels checks, including
for administrators; force-pushes and deletion are disabled. Use labeled PRs, never
bypass checks to meet recording timing. CI has no telephony credentials and places
no assessment calls. See [CI.md](CI.md).

Review call artifacts before explicitly committing selected evidence. Never publish
`.env`, worker logs or the unreviewed calls directory in a broad add. Automated grades,
decode checks and saved filenames are not human approvals or backend verification.
