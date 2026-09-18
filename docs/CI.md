# CI and artifact delivery

GitHub Actions runs **CI / Verify and package** for every pull request (including
drafts), pushes to `main`, and manual runs. Main and manual triggers become available
when the workflow is merged. Pull requests test GitHub's proposed merge commit, so
the artifact's commit SHA can differ from the feature branch's head SHA.

The job uses Python 3.12 and uv 0.12.17, installs the dependencies from `uv.lock`, and:

1. Requires ffmpeg and ffprobe so the recording test cannot silently skip for missing tools.
2. Runs the test suite, the no-network patient dry run, and the worker's CLI help.
3. Builds a wheel and source distribution.
4. Installs the wheel in a fresh environment using the locked production dependencies,
   then repeats the CLI checks outside the source checkout.
5. Uploads the verified packages, `build.json` provenance, and `SHA256SUMS` in an artifact
   named `patient-sim-<version>-<tested commit>`, retained for 30 days. JUnit test reports
   are retained for 14 days, including after a test failure.

Find a successful run in the repository's **Actions** tab and download its build artifact.
The source distribution includes the code, lockfile, tests, and operating documentation.
The wheel smoke test proves packaging/imports; actual calling still uses a shared checkout
for the dispatcher and worker as described in the README.

## Local equivalent

Install uv, Python 3.12, and ffmpeg, then run:

```sh
./scripts/verify.sh
```

This writes packages to a new temporary directory and prints its location. An optional
first argument chooses an empty output directory; `JUNIT_XML` enables a test report.
The script disables `.env` loading. It never starts a worker or passes `--call`.

## Permissions and delivery boundary

The workflow has read-only repository permissions and needs no repository secrets.
Third-party actions are pinned to reviewed commit SHAs; checkout does not persist Git
credentials. It uses `pull_request`, so untrusted pull requests receive no privileged
deployment context.

For now, continuous delivery means tested, downloadable build artifacts. Cloud deployment
is pending personal LiveKit/Twilio setup and a change to the current local-filesystem
handoff between dispatcher and worker. There is no deployment job or automatic dial.
No release tag or successful CI run is evidence that a real call has been verified.

`main` requires a pull request and the **Verify and package** check from GitHub Actions,
with the branch up to date. These protections include administrators; force-pushes and
branch deletion are blocked. No additional reviewer is required for this personal repo.
The first-call PR remains a draft until its separate live-call milestone is met.
