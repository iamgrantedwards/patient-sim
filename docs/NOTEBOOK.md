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
  request to pause immediately for Loom. Next is real-call review UI #23, then explicit
  outbound call controls/live status #24, then genuine recorded debugging #25.
- Audited the repository: completed external setup tasks were still open and PR #20
  still claimed no call had occurred. Closed setup #6/#7 with evidence, marked code
  work #9/#10/#11/#16 as in review pending merge, and kept unverified Athena context
  #8 and first-good-call acceptance open. No completed history was invented.
- Opened actual simulator bug #21 from the captured AgentHandoff error; updated #12
  with the partial ending and attribution uncertainty rather than duplicating it.
- Created UI epic #22 and its milestone; added owners, workflow labels, linked epic
  task lists, and separate video/submission issues #25/#26. PR #20 now states the real
  call evidence and remaining blockers. Main protection was verified unchanged.
- Added ROADMAP.md with focused branches/PRs and dependency handling. UI code will
  have its own PR rather than expanding the foundation PR. Existing 59-test hosted
  CI passed at checkpoint 338e7f8 (run 35405543960); code and acceptance remain distinct.
- No caller/provider settings changed and no additional call was made in this
  planning/management update. Original recordings remain local and unreviewed.

## 2026-09-18 — real-evidence review UI and AI governance (#23)

- Built a separate Python-served, read-only review interface. The actual local first
  call displays seven committed turns, its original 70.289583-second OGG, remote
  hangup, and the incomplete final patient sentence. The browser loaded original
  media metadata without autoplay. Human listening remains pending.
- Added model/code/prompt provenance and SHA-256 of served audio, preserving the
  distinction between a fingerprint, a claim, consistency, and independent evidence.
  Unknown audio offsets remain unknown; only recorded offsets enable turn seeking.
- Added visible AI governance controls and `AI-GOVERNANCE.md`: intended use, owner,
  NIST AI RMF mapping, prompt-injection boundaries, publication review, provider/data
  lifecycle questions, and residual risks. No compliance certification is claimed.
- The first browser pass caught low-contrast secondary text and an empty-state tab
  issue. Increased text sizes, corrected contrast, and disabled call-only tabs when
  no call is loaded. Host/origin checks, bounded JSON reads, non-finite and overflowing JSON number handling,
  safe text rendering, missing artifacts, and range requests have regression coverage.
- Full local verification passed: 116 Python tests, 95.1% combined statement/branch
  coverage, 18 Playwright tests across desktop/mobile Chromium and desktop WebKit,
  axe checks, Biome, Ruff, types, workflow/shell checks, secret/dependency scans, and
  isolated wheel installation with packaged UI assets. Two upstream test-client
  deprecation warnings remain visible. Automated accessibility checks are partial
  evidence, not a complete conformance assessment.
- Browser-checked actual local evidence at 1440px and 390px; audio duration and no
  horizontal overflow were verified. PR screenshots under `docs/images/review-synthetic-*`
  intentionally use generated fixtures; no actual recording/transcript is published.
- Added a fourth required CI job for UI/a11y/browser checks and npm audit, preserving
  the existing gate before package delivery. Node is a development dependency only;
  running the review UI needs Python. Draft PR targets the foundation branch for a
  focused diff; main retargeting follows foundation acceptance.
- No caller/provider settings changed, patient state mutated, or new call placed.
  #21/#12 and M1 are still open. Live calling controls remain the separate #24 task.

- Final navigation review caught that the sidebar's Call review link only scrolled
  while leaving AI governance selected. It now restores Conversation, or the empty
  review state when no call is selected; browser regression checks cover both paths.
- Hosted CI run 35408568707 found Linux WebKit displaying the transcript inline even
  though the response supplied `Content-Disposition: attachment`. Its trace showed a
  successful 200 response followed by navigation away from review. Added an explicit
  same-origin `download` filename to the link; the browser test still requires an actual
  download and now also checks that the review screen remains available. No test was
  skipped and the required gate correctly blocked package delivery on the failed run.

## 2026-09-18 — explicit call console and worker ownership (#24)

- Built opt-in call controls after the review UI: fixed assessment destination, one-call
  confirmation, actual registration/dispatch/worker state, committed dialogue, explicit
  stop/recovery and saved-evidence navigation. The default viewer stays read-only.
- UI and CLI now share a dedicated worker and OS call lock. Reads, refresh and reconnect
  cannot dispatch; one-use confirmation tokens and idempotent request IDs prevent a
  repeated browser request from producing another call. No automatic retry exists.
- Recovery review found that deleting a room alone did not prove the old worker could
  no longer dial. Added nonce-bound worker intent/stopped receipts and parent-loss
  shutdown. Recovery blocks if worker exit or room absence cannot be confirmed and
  never signals an unowned PID. Cancellation during process creation retains ownership.
- Tested disk failure during Stop: provider cleanup must still run even when writing
  the local journal fails. The unresolved record continues blocking a new call.
- Reproduced #21 with the pinned SDK's real AgentHandoff before correcting the message-only
  property access. Handoffs and unknown items remain raw evidence; only unique patient/
  remote ChatMessage IDs count toward the turn limit. SDK tool executions have their own
  event type and are journaled separately, not fabricated as dialogue. Regression tests
  cover actual SDK handoff, message, unknown and tool-execution events.
- Full local verification passed: 168 network-isolated Python tests, 95.5% combined
  statement/branch coverage, 27 browser tests across desktop/mobile Chromium and desktop
  WebKit, axe, Biome, Ruff/Pyright, workflow/shell checks, secret/dependency scans and
  isolated installed-package checks. The two existing test-client deprecation warnings
  remain visible. Automated accessibility evidence is not complete conformance.
- The configured dedicated worker registered with LiveKit and stopped cleanly in a
  registration-only check. No job dispatch or SIP request was made. Browser-checked the
  actual console and confirmation/cancel at desktop/mobile sizes: no mutation requests,
  page exceptions or horizontal overflow; configuration ready and one prior call shown.
- Added OPERATIONS.md, MORNING.md and updated AI governance/contract documentation with
  implemented controls and their limits. Grant's own webcam/voice debugging and final
  videos remain his next-session work. #12 is unresolved; #21 needs live confirmation;
  #24 needs a real UI call and listening. No new call, patient-state mutation, or public
  release of original recordings occurred in this implementation session.

## 2026-09-19 — dependency-update compatibility (#36)

- After the green foundation/review/controls PRs were merged at Grant's request, the
  first uv Dependabot run proposed OpenAI 3.14.1. Resolution failed because our pinned
  LiveKit Agents 1.8.2 requires OpenAI >=2,<3. The application's existing lock resolves;
  this failed update proposal is separate from the npm audit maintenance outage #34.
- Added a scoped Dependabot ignore for OpenAI >=3 while this SDK is pinned. Compatible
  2.x proposals remain eligible, and vulnerability audits still inspect the actual
  locked dependencies. Revisit this rule when upgrading LiveKit. No dependency version,
  prompt, runtime behavior, call artifact or assessment claim changed.
- Parsed the YAML and checked its ignored range against the installed SDK metadata:
  OpenAI 3.14.1 is excluded; 2.x remains eligible; installed OpenAI 2.54.0 satisfies
  the SDK requirement. Local quality, 168 Python tests, 95.5% combined coverage,
  secret/Python audits and Biome passed. Full verification remains blocked at the npm
  audit maintenance response. Hosted Dependabot execution requires landing this config
  and a new update run; static validation is not claimed as that end-to-end result.

## 2026-09-19 — status polling during page exit (#40)

- The final guide integration run 35459511934 passed npm audit but failed the WebKit
  no-page-errors assertion during refresh. The synthetic trace locates the error in
  the console status fetch, between reload starting and the new document navigating.
  Prior same-origin reads and call mutations succeeded; this is not an Origin-policy
  rejection or a finding against the assessment agent.
- Opened #40 and posted the trace/plan before implementation. A deterministic regression
  first failed because status polling continued after pagehide. The fix clears the
  scheduled poll, aborts the in-flight read, ignores its stale result, and resumes one
  polling chain on persisted pageshow. It does not issue a stop or redial.
- The lifecycle regression passes in desktop/mobile Chromium and desktop WebKit; the
  original refresh scenario passed 15 consecutive WebKit runs. These are synthetic
  browser checks, not real-call evidence. Required hosted checks remain the merge gate;
  no retries, exception filters, authentication changes, or audit bypasses were added.

## 2026-09-19 — contextual learning mode (#29)

- Grant requested a top-of-screen light bulb, contextual explanations, a manual, less
  wordy interface copy, and more focused PRs. Split the work into #29 learning mode,
  #30 quick guide, and #31 copy cleanup, each with its own dependent branch/PR.
- Added an off-by-default browser-only learning toggle, visible help markers, and
  explanations for calling, scenarios, saved attempts, evidence, provenance and
  governance. Hover, focus and tap show the same help; Escape and outside interaction
  dismiss it. Only the preference is stored locally; blocked storage is supported.
- Browser checks caught mobile layout changes prematurely hiding a hint and WebKit
  not focusing a clicked hint. Hints now reposition as the layout scrolls and explicitly
  retain focus after click. Their native popover layer avoids clipping by call panels.
- Full local verification passed: 168 Python tests, 95.5% combined statement/branch
  coverage, 36 browser tests, axe, lint/type/security checks and installed-package smoke.
  Inspected the actual idle console at 1440px and 390px. No call was placed, transcript
  changed, or recording published. The caller and provider settings are unchanged.


## 2026-09-19 — quick guide and merge follow-through (#30)

- Added a Guide beside the learning light bulb. It opens a keyboard-accessible manual
  with first-test steps, tab meanings, testing sequence, stop/recovery behavior,
  evidence acceptance and privacy/AI limits. It works with learning hints off.
- Browser checks caught focus leaving the last modal control on Tab. Added explicit
  first/last keyboard wrapping, with tests for both directions, Escape, close-button
  dismissal and focus return. All 39 browser cases pass across Chromium desktop/mobile
  and WebKit; actual desktop/mobile layouts were inspected without placing a call.
- Local quality, 168 Python tests (95.5% combined coverage), secret/Python dependency
  scans, Biome and installed-wheel checks passed. Full verification is blocked at npm
  audit: its bulk endpoint returns HTTP 503 and an explicit maintenance response; the
  retired fallback returns HTTP 400. A minimal one-package request reproduces the same
  503. This is not a clean dependency-audit result; the required gate stays enabled.
- Grant requested merging the three green PRs. Merged #20, #27 and #28 into protected
  main in dependency order using merge commits, without bypassing checks or rewriting
  history. Retargeted learning mode #32 to main and reran its failed CI jobs. #21 and
  #24 remain open for live acceptance; #12, human listening and M1 remain unresolved.
- No new call was placed, raw evidence published, or provider/prompt setting changed.


## 2026-09-19 — concise interface copy (#31)

- Shortened console instructions, evidence notices, metric captions and provenance
  text. Scenario details preserve the full objective behind a named disclosure.
  Governance shows a short summary per control, with the complete explanation and
  source still available under Details. Confirmation, unknown outcomes, pending human
  review, partial speech, privacy/publication limits and provider obligations remain.
- Updated existing browser tests to open scenario details without mutation and expand
  privacy details by keyboard. All 39 browser cases pass, including axe. Inspected
  the actual idle console and governance views at 1440px/390px: no horizontal overflow,
  page errors or mutation requests. Caller prompts and original evidence are unchanged.
- Full verification passed quality, 168 Python tests (95.5% combined coverage), secret
  scans, Python dependency audit and Biome before stopping at npm registry maintenance.
  Installed-package smoke passed separately. External blocker #34 also affects new
  checks on main; affected PRs remain draft with the required audit intact.


## 2026-09-19 — issue reconciliation requested by Grant (#38)

- Audited the issue acceptance against source/tests, existing commits and PRs. Earlier
  issue bodies had been edited, but no progress comments had been posted; merged code
  tasks still said to wait for merging. This was a tracking gap, not evidence that the
  required live calls or submission were complete.
- Added explicitly dated acceptance-review comments and bidirectional PR links. Closed
  #10/#11/#16 after verifying their code criteria and merged implementation; removed
  stale statuses from already-closed issues. Kept #12/#14/#15/#17/#21/#24 and required
  account/evidence/video/submission work open. Refreshed parent checklists and next steps.
- Documented issue-first planning, first-commit draft PRs, discovery/verification comments
  and closure on actual acceptance. The existing larger PRs and their timestamps remain
  intact. Real iteration includes CI fixes, the first call and its defects, plus browser
  navigation/download fixes; this review links that evidence without backdating work.
- npm's bulk advisory service subsequently recovered. The unchanged dependency lock
  passed the full audit with zero reported vulnerabilities; reran the blocked hosted
  jobs without modifying or bypassing the required audit gate. Hosted outcomes remain
  tracked in #34 until confirmed. The separate Dependabot incompatibility is #36/#37.
- After registry recovery, full local verification passed: 168 Python tests, 95.5%
  combined coverage, 39 browser tests, all audits/lints/types and installed-package
  smoke checks. The issue audit confirmed every one of the 31 task/epic issues had an
  owner and a dated progress comment, with no duplicate status labels.


## 2026-09-19 — required PR labels (#42)

- Grant identified unlabeled recent PRs. Opened #42 before implementation, classified
  all nine existing PRs by actual scope, and removed obsolete PR status labels.
  Native PR states now carry draft/open/merged status; issue labels retain acceptance.
- Added a separate read-only metadata workflow requiring one task/docs type and a
  recognized area. It reads current GitHub labels, including on label removal or an
  old run's retry, and fails closed on API/data errors. Label-only changes do not rerun
  application/browser CI. Dependabot configuration supplies the same required labels.
- Local tests exercise accepted scopes, missing/removal/ambiguous labels, invalid data,
  and CLI failure status. Hosted missing-label and recovery checks plus branch-protection
  enforcement are still pending; code alone is not proof of the required merge gate.
- Full local verification passed: 182 Python tests, 95.5% combined coverage, 42 browser
  tests, quality/workflow checks, secret/dependency scans and installed-package smoke.
  The merged workflow base has identical file contents to the verified base.

## 2026-09-19 — Cloud evidence in Provenance (#44)

- Grant requested public evidence of the LiveKit Cloud integration. Opened #44 and
  posted the plan before implementation. Rechecked session RM_ffrkrFyiT7T3 in the
  authenticated console: room name matches call-20260918-231955-765427d8, status CLOSED,
  SIP and agent participants, and Agent insights has a player and waveform lanes.
- macOS screen-capture permission was unavailable. Grant supplied the real screenshot;
  visual review found no credentials/contact information/transcript content. It shows
  the public handle and project name. Copied it unchanged, with its SHA-256 in the note.
- Added packaged, call-specific verification evidence and a compact Provenance section.
  Missing/invalid records remain unconfirmed; presence never changes listening review,
  verified patient state or call counts. Original call files remain untouched.
- The Cloud timeline (97.06 seconds) and local OGG duration (70.29 seconds) have not been
  reconciled. The note explicitly does not claim identical audio, completed listening,
  a hosted worker deployment, or permanent Cloud retention. No new call was placed.
- Initial Python checks: 198 passed. Browser/full verification and hosted checks pending.
- The first full run passed 198 Python cases, lint/types/security, and 44/45 browser
  cases. The new native-link Tab assertion failed on macOS WebKit: a direct browser
  probe showed Tab skipping links and Option-Tab focusing the next link. Adjusted
  only the test shortcut for that platform; native anchor behavior stays unchanged.
  Inspected the actual call's new panel at desktop and 390px widths.
- Full local verification now passes: 198 Python tests (95.6% combined coverage),
  45 browser tests across desktop/mobile Chromium and WebKit, axe checks, lint/types,
  secret/dependency scans, and an installed-wheel check that includes the Cloud assets.
  Keyboard activation opened the actual unchanged 4222x2452 screenshot without auth;
  the listening-review counter stayed 0/1. Hosted checks remain the next gate.
