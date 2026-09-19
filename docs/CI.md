# CI and artifact delivery

GitHub Actions runs on pull requests (including drafts), pushes to `main`, and manual
runs. Main/manual triggers and Dependabot configuration activate after merge. PRs test
GitHub's proposed merge commit, which can differ from the branch head.

Three independent jobs run in parallel. The required **Verify and package** job checks
that all three succeeded before building or uploading packages. Failure, cancellation,
or skipping an upstream job fails this final gate rather than allowing a skipped build
to satisfy branch protection.

| Job | Required checks |
| --- | --- |
| Lint, types, and workflow checks | Ruff lint/format; Pyright standard mode on application and Python tooling; actionlint; ShellCheck on all shell scripts |
| Tests and branch coverage | pytest with TCP/UDP sockets disabled, synthetic/mocked providers, real ffmpeg decode, and a 90% combined statement/branch coverage floor |
| Secrets and dependency audit | Gitleaks on full available Git history and tracked/unignored working files; pip-audit on hashed exports of locked runtime and development dependencies |
| Verify and package | All preceding jobs must succeed; build wheel/sdist with the locked backend; install wheel with locked production dependencies and check its CLI outside the checkout |

The measured baseline was 70% coverage with 41 tests. Targeted dispatch, finalization,
and worker-failure tests raised this to 93.3% with 59 tests. Coverage measures exercised
code, not voice quality or live telephony correctness. Tests do not dial the assessment
line. Unix sockets remain allowed for the local asyncio event loop.

## Local equivalent

Requires Python 3.12, uv, Git, curl, tar, and ffmpeg/ffprobe on PATH. Run:

```sh
./scripts/verify.sh
```

The same scripts power CI. `./scripts/check.sh quality`, `tests`, or `security` runs an
individual gate; `./scripts/build.sh` runs packaging alone and is not full verification.
Checks write reports to ignored `reports/` (override with `REPORT_DIR`). Packages go to
a fresh temporary directory, or an optional empty directory passed to `verify.sh`.

The native tools are pinned in `scripts/ci-tools.json` and installed from official
GitHub releases only after verifying their archive SHA-256 hashes. Their ignored cache
is `.ci-tools/`. Pinned binaries cover macOS Apple Silicon and Linux x86-64, the current
development and CI targets. Other platforms need reviewed manifest entries. Python tools
and the build backend are locked in `uv.lock`; Pyright's Python wrapper uses Node.js and
can download it when no usable Node is installed. First runs and security audits need
network access; the pytest suite disables IP sockets and `.env` loading.

## Reports and packages

Successful runs provide `patient-sim-<version>-<tested commit>-<attempt>` artifacts with
a wheel, source distribution, `build.json` provenance, and `SHA256SUMS`, retained for
30 days. Test/coverage and redacted security reports are retained for 14 days, including
when their check fails. Download them from the run's **Artifacts** section.

Packages contain explicitly selected source, tests, lockfile, and documentation; raw
calls and local credentials are excluded. Actual calling uses a Git checkout shared by
the dispatcher and worker. Passing package smoke tests does not establish successful
SIP connection or a coherent conversation.

## Maintenance and boundaries

Workflow permissions are read-only; no telephony secrets are provided. Actions are pinned
to commit SHAs, checkout does not persist credentials, and untrusted PRs run under
`pull_request`. Secret findings are redacted. Scanners can miss issues; a clean audit is
not a security guarantee. Fix confirmed findings rather than hiding failures; any future
exception needs a narrow scope, documented rationale, and review date.

Dependabot proposes weekly Python and Actions updates without auto-merge. Development
tools are grouped; the contract-pinned LiveKit Agents version requires an explicit manual
decision. Review runtime/provider changes before collecting more experimental evidence.
Native tool versions/checksums are reviewed manually.

`main` requires an up-to-date **Verify and package** check from GitHub Actions and a pull
request, including for administrators. Force-pushes and branch deletion are blocked.
No additional reviewer is required for this personal repository.

Artifact delivery is the current delivery boundary. This assessment does not require
cloud deployment, a production service, or automatic calls. Finish the first real-call
milestone before considering additional infrastructure.
