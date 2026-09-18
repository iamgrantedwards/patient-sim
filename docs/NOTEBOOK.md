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
