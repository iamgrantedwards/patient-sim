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
