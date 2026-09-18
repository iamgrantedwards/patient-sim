# Build notebook

## 2026-09-18 — repository setup

- Adopted the reviewed Revision 3 contract before starting the caller implementation.
- Existing scaffold has no working dialer, scenarios module, or captured calls yet.
- GitHub identity is iamgrantedwards; CLI login is isolated from other projects.
- LiveKit Cloud and Twilio accounts/trunk are not configured yet (confirmed by Grant).
- Found that bootstrap-github.sh would duplicate issues on rerun and hide milestone
  API errors. Changed it to check existing titles and surface errors.
- Inspected the installed LiveKit Agents 1.8.2 signatures. Session recording exposes
  a local OGG path in the session report; finalization/copying still needs verification.

## Open environment questions

- Does the athena test account share data with the assessment line?
- What cross-call state, if any, persists? Caller-ID recognition is not assumed.
- Does the test environment reset? Are offered appointments simulated?
- Does the assessment line answer directly or use an IVR?

No findings have been confirmed. No calls have been placed.


## 2026-09-18 — first caller implementation

- GitHub CLI login confirmed as iamgrantedwards, account ID 331040136. The repository
  uses its noreply commit address and a repository-local credential helper.
- Built a read-only smoke scenario and explicit patient facts. Evaluation fields never
  enter the patient prompt. The broader scenario set remains future work.
- Found in installed SDK source that ivr_detection=True generates replies after silence
  and exposes DTMF, rather than simply classifying voicemail. Disabled it for initial
  observation and corrected the contract. No real-line behavior has been observed.
- SDK recording is a local stereo OGG. Its public session report exposes the file path;
  preserve it in on_session_end after closure and before temporary-directory cleanup.
- Noise cancellation was already disabled. Also explicitly disabled automatic gain
  control after discovering RoomIO enables it by default without noise cancellation.
- Journaled transcripts can be recovered after a crash. Guaranteed audio export after
  an abrupt kill and audio-derived response timing remain unverified/unimplemented.
- Public publication is awaiting Grant's explicit approval after automatic approval
  review rejected the first attempt. No repository or issues were created by that attempt.

- Offline verification passed 34 tests before the subsequent disconnect-cause refinement.
  ffmpeg decoded a generated stereo OGG fixture; that is not telephone audio evidence.

- Final local check for this checkpoint: 41 tests passed, including mocked outbound
  ordering/limits, disconnect attribution, secret-free provenance, prompt separation,
  event recovery, and a full generated-OGG decode. CLI help and the no-network dry run
  also succeeded. No live call has been made.

## 2026-09-18 — publication approved and completed

- Grant approved public publication. Created iamgrantedwards/patient-sim and pushed
  the initial scaffold to main and the first-call implementation to codex/first-call.
- Created seven milestones, nine project labels, and nineteen issues (five epics and
  fourteen tasks). These are planned work, not claims of completed live verification.
- Opened draft PR #20 with the completed review template, offline test evidence, and
  an explicit statement that real calls and listening are still pending.
- The earlier publication approval blocker is resolved. LiveKit Cloud and Twilio setup
  remain the prerequisites for the first real-call milestone.

## 2026-09-18 — CI and artifact delivery

- Added one verification path for local runs and GitHub Actions: locked dependencies,
  unit tests, credential-free CLI checks, package builds, and installed-wheel smoke tests.
- CI installs ffmpeg explicitly so the generated-recording test runs on Linux too.
- Restricted source-distribution contents to code, tests, lockfile, and documentation;
  call evidence and local credentials are not build inputs.
- The worker and dispatcher currently share a local calls directory. Cloud deployment
  therefore needs both account setup and a remote handoff design; uploading a wheel does
  not make the current caller remotely deployable.
- GitHub CLI requires an additional workflow scope to publish Actions definitions.
  Live-call verification remains separate from all automated checks.

- Local CI-equivalent verification passed all 41 tests, both CLI checks, both package
  builds, and installed-wheel smoke checks outside the checkout. Archive inspection
  confirmed no call evidence or credentials were packaged. Actionlint validation passed
  after correcting runner-context use in job environment setup.
- Automatic approval review blocked the device-code submission for the new workflow
  scope. The prepared pipeline is awaiting Grant's approval of that access expansion.

## 2026-09-18 — hosted CI verified

- Grant completed workflow authorization; the earlier access blocker is resolved.
- Pushed CI commit 23007c7 to PR #20. GitHub Actions run 35395971856 passed on Linux:
  all 41 tests, zero skipped, source/installed-wheel CLI checks, builds, and artifact upload.
- Downloaded both artifacts and checked their package hashes against build.json. The
  packages contain no local credentials or collected call evidence. The manifest names
  the tested PR merge commit ef6ced7ad62880f1c787a1f0d4ffd60a04af3b2c, not the branch head.
- Protected main: pull requests and an up-to-date GitHub Actions Verify and package check
  are required, including for administrators. Force-pushes/deletion are blocked. There is
  no reviewer-count requirement because this is a personal repository.
- PR #20 remains a draft for the live-call milestone. Main/manual workflow triggers will
  become available after merge; PR verification and artifact delivery are active now.

## 2026-09-18 — quality gates and original-brief review

- Measured the original 41-test baseline at roughly 70% coverage. Added dispatch timeout,
  provider rejection, cleanup failure, finalization failure, media disconnect, and duration
  watchdog regression tests. All 59 tests pass at 93.3% combined statement/branch coverage;
  the enforced floor is 90%. These remain synthetic and mocked tests, not live-call proof.
- Reproduced a real local bug: failing metadata/transcript writes skipped room deletion.
  Nested cleanup now closes the journal and attempts room deletion despite those errors;
  room deletion errors also no longer prevent local shutdown. Regression tests failed on
  the original behavior and pass with the fix.
- Pyright found three SDK boundary mismatches. Narrowed runtime-validated config types
  and passed the end-call tools as the list requested by the SDK. Providers and models
  remain unchanged. Ruff standardized formatting/imports across the small Python codebase.
- Added pinned lint, type, coverage, workflow, shell, secret, and dependency checks. Native
  tool archives are SHA-256 verified. Full Git history and unignored working files passed
  secret scanning; the locked dependency audit found no known vulnerabilities. Existing
  runtime dependency versions did not change when development tools were added.
- Compared code and deliverables with Grant's original challenge brief. Mandatory stack
  and destination restrictions are met in code; live voice quality, ten complete call
  pairs, varied scenarios, findings, the fixed owned DID, and two public webcam/voice
  videos remain outstanding. Condensed the architecture explanation to two paragraphs.
- Corrected the distinction between our 12-call/8-kind internal targets and the employer's
  minimum of ten complete pairs. Further cloud infrastructure is unnecessary; finish this
  CI pass and prioritize account setup, genuine recorded debugging, and the first call.

- Expanded hosted CI run 35398379043 passed all four jobs. Downloaded reports confirm
  59 tests, zero skips, 93.3% combined coverage, clean secret/dependency scans, and matching
  package checksums. The first parallel run showed harmless cache-write contention;
  limited cache saving to the quality job while all jobs can restore the same cache.


## 2026-09-18 — account setup and pre-call verification

- Authorized the personal LiveKit project and saved credentials only in the ignored local
  `.env` with permissions 0600. Authenticated read-only room/trunk API requests succeed.
- Grant funded Twilio and purchased one US voice number, then created its Elastic SIP
  trunk, credential list, and number association. The LiveKit outbound trunk has the
  matching caller number, Twilio termination hostname, and TCP transport.
- Read-only verification caught missing authentication fields after initial trunk creation.
  The dashboard placed these under collapsed Optional settings. After entering them,
  the API confirms the expected SIP username and a nonempty password. This proves saved
  configuration, not that Twilio accepts the credentials; a real call must establish that.
- Selected Cartesia Jacqueline (`9626c31c-bec5-4cca-baa8-f8ba9e84c8bc`) for the synthetic
  patient, keeping the planned Sonic 3.6 model. LiveKit's current documentation lists both
  as supported. The voice remains fixed for calibration; its call quality is untested.
- Read the project's Observability settings: agent observability is On and PII redaction
  is Off. No project recording or privacy setting was changed. Billing reports the Build
  plan and a $0.00 next invoice; that display is not a forecast of test-call costs.
- All required local configuration fields validate. The credential-free smoke dry run
  passes. The local Python 1.8.2 worker registered in LiveKit US West B, then was stopped
  cleanly without dispatching a call. The SDK emitted deprecation notices for the current
  download-files/dev entry points; both commands still completed their intended checks.
- No phone call, provider inference request, or evidence recording has been verified yet.
  The next step is one read-only office-information call during a genuine recorded
  debugging session, followed by end-to-end listening and transcript comparison.


## 2026-09-18 — first real assessment call

- Call `call-20260918-231955-765427d8` ran from clean revision `b1a6cda` using
  the read-only smoke scenario and the configured single caller number. The sole
  permitted assessment destination answered, establishing that outbound SIP works.
- Preserved the original 70.289583-second stereo Opus/OGG recording and seven
  committed transcript items (four remote, three patient). The last patient item is
  partial. Full audio decoding passed; human listening review is still pending.
  An MP3 playback copy was created without replacing the original OGG evidence.
- The event handler raised `AttributeError: 'AgentHandoff' object has no attribute
  'role'` during session startup. The raw handoff event was captured before the
  exception; subsequent dialogue capture and the call continued. This is our code
  defect, not a finding against the assessment agent. It remains unfixed at this
  checkpoint so it can be investigated in the requested debugging recording.
- The transcript shows the remote agent offering a demo patient profile, declining
  to give office hours/address, and saying goodbye. Our caller began asking about
  an insurance card before the remote hung up. This does not establish a defect in
  their agent; we need to assess our caller's handling of a goodbye and listen for
  timing/overlap before attributing the cutoff.
- The call ended as `remote_hangup`, not our `EndCallTool`; the clean-ending M1 gate
  remains open. The room was deleted, verified through the room API, and the local
  worker was stopped. No second call was dispatched.
- Original call artifacts remain ignored and local pending review. No recordings
  or transcripts were added to the public repository.


## 2026-09-18 — UI priority and GitHub reconciliation

- Grant explicitly requested a usable UI before filming. This supersedes the earlier
+  request to pause immediately for Loom. Next is real-call review UI #23, then explicit
+  outbound call controls/live status #24, then genuine recorded debugging #25.
+- Audited the repository: completed external setup tasks were still open and PR #20
+  still claimed no call had occurred. Closed setup #6/#7 with evidence, marked code
+  work #9/#10/#11/#16 as in review pending merge, and kept unverified Athena context
+  #8 and first-good-call acceptance open. No completed history was invented.
+- Opened actual simulator bug #21 from the captured AgentHandoff error; updated #12
+  with the partial ending and attribution uncertainty rather than duplicating it.
+- Created UI epic #22 and its milestone; added owners, workflow labels, linked epic
+  task lists, and separate video/submission issues #25/#26. PR #20 now states the real
+  call evidence and remaining blockers. Main protection was verified unchanged.
+- Added ROADMAP.md with focused branches/PRs and dependency handling. UI code will
+  have its own PR rather than expanding the foundation PR. Existing 59-test hosted
+  CI passed at checkpoint 338e7f8 (run 35405543960); code and acceptance remain distinct.
+- No caller/provider settings changed and no additional call was made in this
+  planning/management update. Original recordings remain local and unreviewed.
+