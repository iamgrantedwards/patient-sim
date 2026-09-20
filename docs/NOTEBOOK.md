# Build notebook

The [debugging journal](DEBUGGING.md) records the first two actual attempts and
separates observations, prior fixes and unresolved hypotheses. Its starting account
was written retrospectively on 2026-09-19 for #48; the debugging video is still pending.

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


## 2026-09-19 — compact workspace and product-facing copy (#47)

- Grant requested a tighter layout and icon-oriented controls after reviewing the actual
  console. Opened #47 before implementation. Consolidated the sidebar and repeated
  header rows; kept governance in its evidence tab with a quiet footer entry.
- Learn, Guide and Refresh use named icon controls. The scenario picker supports
  arrows, Home/End, type-ahead, Enter, Escape, pointer selection and disabled state;
  selection still feeds the existing explicit call-confirmation flow.
- Removed the in-app verification-note link and Build & decisions navigation. Public
  technical evidence remains in the repository; the app offers View Cloud snapshot.
- Browser inspection of the same actual call at 1440px: the evidence panel begins at
  about 499px instead of 715px; metrics shrink from 79px to 53px. Checked 390px layout
  without horizontal overflow. No real call or caller/prompt/evidence-model change.
- Full local verification passed: 198 Python tests (95.6% combined coverage), 48 browser
  tests across desktop/mobile Chromium and WebKit, accessibility, quality/security gates
  and installed-package checks. The two-call debugging journal is separately tracked by
  #48; the unresolved crash in #46 is reserved for genuine debugging work.


## 2026-09-19 — call rail, compact search and concrete controls (#50)

- Grant requested cards as the default, the existing list as an alternate, and a search
  icon beside the call count. Opened #50 before implementation; expanded its acceptance
  when he asked to relocate the metrics/finished-operation details and replace the
  generic governance page.
- Added a horizontal card rail with local view preference, honest file availability,
  selected-state depth and reduced-motion-aware hover/press feedback. Search and filters
  open on demand; active filters remain indicated when the menu is closed.
- Moved evidence counts and the latest finished-operation receipt into Calls. The call
  controls retain active progress, failures and recovery; raw saved metadata is unchanged.
- Controls & data now shows the current mode, enforced call restrictions, local storage
  and external processing. Broad governance recommendations remain in the repository.
- Initial checks caught ambiguous test selectors after adding a search-menu label, and
  Safari moving focus to the document during a pointer press, dismissing the menu before
  Clear filters could run. Scoped the selectors and restricted focus-leave dismissal to
  keyboard navigation. All 54 browser cases now pass, including view persistence,
  keyboard selection, search/reset, reduced motion and accessibility.
- Visually inspected actual calls at 1440px and 390px, including search and Controls &
  data. No real call, caller/prompt change, listening approval or fix for #46. Full local
  verification passed: 198 Python tests (95.6% combined coverage), 54 browser cases,
  quality/security checks and installed-package validation. Hosted CI is the next gate.

- Follow-up user review rejected the first card typography and clarified that List
  means full-width rows in the same Calls container, not the previous sidebar layout.
  Held #52 as a draft. Fresh Chromium/WebKit probes showed the toggle already switched
  at 390–1440px; Grant confirmed it worked. Do not claim a functional toggle repair.
- Removed CALL RECORD lettering and visible IDs from the compact cards, strengthened
  the active view icon, and changed List to raised full-width rows with details below.
  New assertions check actual horizontal/vertical geometry, row width, toolbar alignment
  and details position, in addition to state/persistence. All 54 browser cases passed;
  inspected both actual-call views at desktop, 620px and 390px with no overflow.
- Grant then requested destination/caller chips in the module heading. Moved the actual
  configured numbers above the scenario row, with responsive wrapping and the original
  call-confirmation path intact. Full verification passed after the row redesign;
  reran UI checks and Python tests for this final layout-only refinement.
- A further visual pass replaced loose checkmarks/dashes with consistent headphone,
  document and clock badges. Missing files stay amber and explicit; available files
  use a separate treatment. Selection uses the card/row highlight, not a checkmark.
  Accessible call names now include file availability and whether duration is known.
- Grant confirmed the badge treatment, then identified a responsive list gap: duration
  remained inside the flexible title cell and floated away from the outcome at wider
  sizes. Duration and outcome now share a compact status group at wider sizes; the
  existing narrow-phone arrangement is preserved.

### 2026-09-19 — Worker explanation and recording preparation

- Before filming, traced the local application -> managed agent server -> child call
  job hierarchy in our code and pinned LiveKit Agents 1.8.2. Confirmed the controller's
  exit check observes the managed process, not the child job; these lifecycle files
  are unchanged from the second attempt's revision. No failure regression or fix yet.
- Development mode has zero idle job processes by default in the pinned SDK, so the
  no-warmed-process message alone is not a crash diagnosis. Original -11 cause and
  subsequent initialization mechanism remain unknown.
- Updated the debugging journal and added DEBUGGING-SCRIPT.md with easy speaking cues,
  actual investigation prompts and a follow-up outline. Labels all prior inspection
  as preparation; does not claim a video, live retest or successful fix occurred.

### 2026-09-19 — Per-call review and learning workflow

- Grant asked to connect model/worker learning to practical testing, changes, videos
  and handoff while keeping the app product-oriented. Added CALL-REVIEW.md and a blank
  manual review sheet, linked from the README, recording runbook and script.
- Confirmed the current viewer reads recording.listened_by_human from original metadata
  and has no structured review-save action. #54 tracks a compact, separate review record
  and selected-call control after #46; no new UI/API was implemented here. Manual notes
  do not update UI counters. Full listening and submission suitability remain distinct.
- No calls were reviewed, scored, accepted, modified or placed by this preparation.
  Remote-agent defects can be useful complete conversations; incomplete attempts do
  not count toward ten. Model choices remain hypotheses until compared with call evidence.


## 2026-09-19 — saved listening reviews (#54)

Grant moved the compact review feature ahead of the caller investigation to finish the
review workflow. Added a separately enabled, providerless write path and folded Review
panel beside each recording. Reviews preserve revisions separately from raw artifacts;
evidence fingerprints invalidate stale judgments. Legacy flags are shown as provenance,
not silently promoted to acceptance. The seven checks distinguish listening completion
from a usable conversation. No real call was placed or reviewed during this work.
Initial offline verification: 223 Python tests passed, including reload, revisions, stale
evidence, protected writes and unchanged original bytes. Browser verification is underway.

Grant's screenshot caught a layout regression that the first accessibility checks did
not catch: a global select margin shifted checklist dropdowns into note fields. Reset
field margins/heights and added row-geometry assertions on desktop/mobile/WebKit.
The local server's older asset allowlist also caused a temporary module 404 during
development; restarting it restored both original call records.

Final focused browser checks pass in Chromium desktop/mobile and WebKit, including
row alignment/no overlap, keyboard operation, accessibility, saving and amendments.
The expanded panel was inspected in the in-app browser after the correction. Local
secret/dependency scans and package installation checks passed. No genuine listening
completion or suitability judgment was saved on either real call.

Grant requested the same picker styling as the call scenario. Review status and result
menus now share the scenario menu's styling, selected checkmark and hover state, with
arrow/Home/End/typeahead navigation, Enter selection and Escape dismissal. Review and
scenario browser checks cover these interactions without dialing; the review controls
remain compact and aligned.


## 2026-09-19 — #46 investigation before a production fix

- Grant started the planned offline investigation of the second call's native crash,
  later initialization, and stale Dialing state. Issue #46 is assigned and in progress.
- Found a matching local macOS crash report: child PID 20955, parent PID 20951 matching
  the worker receipt, SIGSEGV / invalid null address in `liblivekit_ffi.dylib`. This
  narrows the crash location but does not identify the triggering operation or root cause.
- Added a passing regression proving a repeated call identity preserves original
  fixture evidence and fails before connection or SIP dialing.
- Reproduced the controller gap with the actual managed wrapper and SDK failure
  mapping across mocked external boundaries: child failure is reported, parent stays
  alive, controller still returns Dialing. The before-fix run is 1 failed / 13 passed.
- Kept the one known failure explicitly marked strict xfail, with `--runxfail` documented
  for demonstration. This is a test/evidence checkpoint, not a failure-handling fix.
- The original warning-only worker log cannot settle the exact reassignment mechanism.
  Next change should deliver child failure to cleanup and capture assignment identity.
  No calls, dependency changes, production fixes, or original evidence edits occurred.


## 2026-09-19 — #46 first fix: child failure reaches the controller

- Added a failure receipt from the pinned SDK process-closed notification. It records
  call/worker identity, child PID, job ID, and exit code, then drains the dedicated
  server. The controller accepts only a receipt matching its current call, nonce,
  and parent PID; it records the failure separately from original call evidence.
- The prior stuck-Dialing regression now passes with its xfail marker removed.
  It retains the original metadata and records exit -11 while cleanup completes.
  Cleanup failure instead leaves recovery_required and blocks a new call.
- Native crash symbolication checked the installed binary UUID against the report:
  they match, but the native frames still lack names beyond livekit_ffi_request.
  This change handles that failure; it does not repair the native memory access.


## 2026-09-19 — #46 second fix and native investigation

- Added a one-job admission guard on the SDK's public request callback. Concurrent
  offers, acceptance uncertainty, mismatched identity, and existing evidence are
  covered by offline tests. The original exclusive-create evidence guard remains.
- Added private assignment identity diagnostics and enabled structured worker logging
  plus inherited Python fault-handler output for the parent and spawned children.
- Ran five isolated local native probes, 20 audio initialization/capture/teardown
  cycles each, against the unchanged LiveKit 1.1.18 binary. All exited 0. This did not
  reproduce the connected-call crash; its triggering operation remains unknown.
- Native crash prevention is still unverified. The implemented correction makes the
  child failure observable and bounded, with cleanup uncertainty blocking a new call.
  No live test call was placed, no provider/model configuration changed, and the
  first two calls' original evidence remains untouched.

- Full local verification passed after the admission/diagnostic changes: 246 Python
  tests, 60 browser/accessibility tests, 96.1% coverage, lint/types, dependency and
  secret checks, and package build/install checks. A final SDK review identified
  that unassigned processes have no job status; the failure handler now reads the
  nonzero exit first, with assigned/unassigned regression cases added.

- Final affected checks after that guard: 248 Python tests passed, no xfails, 96.1%
  coverage, and types clean. The native probe did not reproduce the crash; there is
  still no claim that the segmentation fault's root cause has been fixed.

## 2026-09-19 — ten-call strategy before filming

Grant asked how the simulator will test the office agent, document results and improve
against the minimum ten-call requirement. Re-read the team's original brief and inspected
the actual scenario registry: only office information exists. Prepared TEST-STRATEGY.md
with ten coverage slots, state dependencies and honest fallbacks, review checkpoints,
separate attribution, and matched retests. A prompt does not prove barge-in occurred;
that behavior needs implementation and audio verification. Existing generic refill facts
also need product-context review before treating a request as a supported happy path.
No scenarios were executed, no calls were approved, and no findings were invented.


## 2026-09-19 — Athena product exploration, reported by Grant (#8)

Grant confirms that he already created the Athena test account and experienced the
demo himself. He recalls accepting an offer to call his phone, receiving that call,
and having an appointment-booking conversation. He believes the flow also arranged
a date/calendar entry and sent a text about the appointment. This is Grant's firsthand
report recorded today, not an independently inspected recording, calendar or SMS.
The exact appointment outcome and message contents remain unverified.

This satisfies the setup/exploration step and establishes appointment booking as an
observed demo workflow. It does not establish office policies, refill support, or
whether Athena and the assessment line share patient/appointment state. Do not reuse
Grant's personal appointment details as synthetic test facts. Our caller should follow
legitimate demo onboarding when needed. All automated test calls still use only the
allowlisted assessment line; this personal demo is not one of our ten submitted calls.
Earlier entries correctly describe what was unverified at that time; they are not
rewritten to imply we had this report earlier.

## 2026-09-19 — actual killed-process journal recovery (#14)

An isolated Python subprocess wrote two committed turns with CallArtifacts and
acknowledged the durable writes. The test sent SIGKILL (exit -9), then recovered the
journal: both turns survived once, unmatched STT was empty, and original journal bytes
were unchanged. Recovery is labeled recovered_partial; no audio or successful call is
claimed. This tests abrupt process death, not a reproduced native SIGSEGV.


## 2026-09-19 — scenario implementation after the debug recording

Grant reports the debugging recording is finished and authorizes sequential remaining
assessment calls. #59 implements the #18 catalog. The first transcript identifies
Pivot Point Orthopedics and offers demo onboarding; the patient now accepts that offer
using synthetic facts. New appointment objectives use a nonurgent knee consultation.
Reschedule/cancel ask for lookup and do not assert an unverified prior booking.
The third-party request is an additional edge case; controlled barge-in remains untested.
The optional three-configuration screen is deferred to prioritize required coverage;
provider choices remain engineering rationale, not measured comparative superiority.

The first fresh attempt (call-20260920-011336-9e2e5e9b) was stopped by the operator
after connecting; Grant confirmed this was accidental and authorized continuing. The
next attempt (call-20260920-011456-fe6d34a0) held a multi-turn conversation without a
worker crash, but still declined onboarding. The generic rule lost to the office-info
opening posture. Smoke v3 makes onboarding the first action explicitly. This is our
prompt defect, not evidence against the office; the original transcript is preserved.

Smoke v3 call-20260920-011714-108d161e accepted onboarding, obtained weekday hours,
address and insurance-card guidance, and ended through end_call_tool. Ten dialogue
turns and 90.92 seconds of decoded stereo OGG were saved. Listening remains pending.
The office explicitly assigned July 4, 2000 as the demo DOB. Subsequent synthetic
patient facts use that assigned demo DOB, rather than silently conflicting with it;
the original March 4 facts and both recordings remain unchanged. The reason for visit
is aligned with the nonurgent knee scenario before transaction collection.


## 2026-09-19 — refill transfer boundary (#62)

call-20260920-012849-8a9bc2d4 declined a refill absent from the chart, then the patient
accepted the offered support transfer. The old rule only prohibited requesting a
transfer to another number. Tightened it to decline all offered transfers and staff
callbacks, ask general next steps and end. The call ended through end_call_tool and
controller cleanup was confirmed. No conversation with staff is established by the
saved transcript; the remote statement of transfer is not independently verified.


## 2026-09-19 — live dialogue follow and record separation (#65)

During collection Grant observed new dialogue below the visible scroll position and
requested clearer speaker styling and a distinct lower detail area. Added a bounded
live viewport that follows new turns, preserves manual scrollback and offers a Latest
turns control. Patient and office backgrounds differ; selected-call details have a
separate dark header and inset surface. No call lifecycle or evidence changes.

Follow-up feedback: moved the large review introduction into a compact logo tagline;
scenario cards now share the dropdown's display names and include a one-line purpose.
A Usable marker/filter reflects saved review state only; no candidate is automatically
marked listened or usable. Browser fixtures cover that distinction.

Verification: 252 Python tests and 63 browser cases passed across desktop Chromium,
mobile Chromium and desktop WebKit. Browser checks include accessibility, live follow /
manual scrollback, review-driven usable filtering, and no unintended call requests.
Inspected desktop and 390px mobile screenshots; kept card descriptions short to fit.

## 2026-09-19 — charcoal theme and recording-first review (#67)

Grant requested an icon-based charcoal theme, stronger light-mode surfaces, a more
separate selected record and a closed-by-default transcript. Added persisted explicit
theme choice (light default, storage-failure fallback), a stronger inset details surface
and a native transcript disclosure with a styled download link. Changing the selected
call closes its transcript; refreshing the same record preserves an open disclosure.

The first contrast run caught small library labels on the stronger light fill and
footer/help/search labels in charcoal. Adjusted those rather than weakening the gate.
All 69 browser cases passed; the final neutral-charcoal adjustment and live-dialogue
checks passed another six focused cases across the three browser projects. Python:
254 tests passed. Inspected light, charcoal and mobile fixture screenshots. No real
calls or review judgments were changed by this UI work.

## 2026-09-19 — collection report reconciliation (#17, #18, #19)

Ten candidate pairs are captured and validated for file integrity; the collection
ledger lists their IDs, durations and remaining listening decisions. Human acceptance
remains pending. Kept office claims separate from backend verification, and recorded
the reported provider-name variation as an unattributed candidate needing audio review.
Three quoted caller/office turns match raw transcripts byte-for-byte; that validates
quotation, not STT accuracy. Raw recordings, journals and the private candidate bundle
are not part of this documentation PR. Updated stale assessment and README status.
