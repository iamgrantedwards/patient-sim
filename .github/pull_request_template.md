## What changed

<!-- One or two sentences. What a reviewer would say this PR does. -->

<!-- Required PR labels: exactly one type:task / type:docs, plus at least one area:
analysis, ci, evidence, process, simulator, telephony, or ui. Add these when opening
this PR; bug/accessibility are supplementary. PR labels is a required CI check. -->

## Why

<!-- Link the task issue and explain the problem. If it came out of a call, link its ID.
Use "Closes #N" only when every acceptance item is met; repeat "Closes" for each issue.
Otherwise use "Related: #N" and state the remaining acceptance. Name any parent PR. -->

## How it was verified

<!-- Pick what applies. Delete the rest. Be honest about what was NOT checked. -->

- [ ] `./scripts/verify.sh` (lint, types, tests/coverage, security, packaging)
- [ ] `uv run pytest`
- [ ] Made a real call — call id(s):
- [ ] Listened to the recording end to end
- [ ] Not verified by a call (explain why):

## Evidence

<!-- Link the issue progress comment, checks, and relevant call IDs/quotes when applicable.
Before requesting review, post the PR link, actual results, and next action on the issue. -->

## Risk / what could break

<!-- Especially: does this change the pipeline mid-experiment? Does it mutate
     patient state? Does it invalidate calls already collected? -->
