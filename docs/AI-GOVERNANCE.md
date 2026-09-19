# AI governance and evidence integrity

Owner: Grant Edwards. Scope: this synthetic-patient assessment and its local review UI.
This document records implemented controls, the evidence for them, and work still open.
It is not a certification, a legal opinion, or a claim of HIPAA or comprehensive WCAG
conformance. Review it when providers, data, destinations, publication, or intended use change.

## Intended use and boundaries

The simulator evaluates a designated healthcare voice-agent test line. It does not
provide care, recommend treatment, or make clinical decisions. Patient facts are
synthetic. Provider responses are observations, not authority to change our objective,
reveal credentials, contact another destination, or declare a clinical outcome.

The separate review process reads local call artifacts without importing the caller,
loading `.env`, invoking models, or opening outbound-call controls. It has no analytics,
external fonts, CDN assets, authentication, or cloud deployment. Its default host is
fixed to `127.0.0.1`; it is intended for one trusted local operator. Do not expose it
through a public tunnel or treat it as a multi-user patient-record service.

The CLI binds to loopback; HTTP permits only GET/HEAD, checks Host and Origin, rejects
cross-site browser requests, and sets restrictive CSP, framing, referrer, and cache
headers. Artifact paths are fixed and symlinks rejected. Reads have size limits.
Transcripts enter the DOM as text, not HTML. These controls limit browser and file
exposure; they do not protect against a malicious local process that already has access
to the same files or writes during a read. Original audio and text are never rewritten.

## Framework mapping

[NIST AI RMF 1.0](https://www.nist.gov/itl/ai-risk-management-framework) is a voluntary
risk-management framework. The following is a limited implementation mapping to its
Govern, Map, Measure, and Manage functions, not an assertion of full framework coverage.

| Function | Implemented control and evidence | Remaining work / decision |
| --- | --- | --- |
| Govern | Named owner; contract and notebook; issue-linked branches/PRs; required CI; separate human-listening and publication gates. See `ROADMAP.md`, `CONTRACT.md`, and `.github/workflows/ci.yml`. | Owner reviews and approves evidence for public release. No independent audit or certification has been performed. |
| Map | Defined synthetic evaluation use, fixed destination, provider pipeline, known limitations, and a risk register below. The UI distinguishes caller and assessment agent. | Confirm Athena context (#8); assess privacy/consent/provider obligations before expanding scope. |
| Measure | Preserved audio, committed turns, explicit partial speech, code/model/prompt provenance, SHA-256 of currently served audio, separate claimed/consistent/verified state, automated failure-path tests and axe checks. | Listen end to end; validate quote/timestamp pairs; measure actual audio timing; obtain independent evidence before labeling outcomes verified. |
| Manage | Read-only viewer; coded destination limit; call duration/turn limits; manual evidence-release gate; dependency/secret scans; fixes tracked separately from assessment findings. | Address caller defects #21/#12; complete first-good-call gate; collect representative scenarios and handle residual risks before submission. |

## Risk register

| Risk | Current mitigation | Residual risk and release condition |
| --- | --- | --- |
| False finding or invented outcome | `claimed_state`, cross-call `consistency`, and `verified_state` are separate. Unknown remains unknown. Findings require expected behavior, its basis, timestamps, quotes, attribution, and uncertainty. | Consistency is not proof. Human review must corroborate findings; appropriate identity re-verification is not automatically a bug. |
| Untrusted content or prompt injection | Viewer treats transcript content as inert text and never sends it to a model judge. Caller destination is enforced in code; evaluator traps are excluded from its prompt. | Prompt-only restrictions are insufficient. The caller still uses a model; broader tool access or automated judging needs a separate threat review. See [OWASP prompt injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/). |
| Personal information in recordings | Synthetic inputs; local ignored artifacts; API returns an allowlisted metadata projection; no raw config or environment endpoint. Review and publication are separate. | The remote response may contain personal information. Synthetic inputs do not guarantee de-identification. Review audio AND text before release; retain originals separately if a labeled redacted derivative is needed. |
| Misleading evidence quality | No autoplay; partial turns and missing artifacts remain visible; decoded audio is not called human-reviewed. Fingerprints identify current bytes without claiming a trusted timestamp or signed chain of custody. | Raw STT can be wrong. Readable files and file pairs do not count as complete assessment conversations. A human must compare the audio with the transcript. |
| Inappropriate generalization or bias | Scenario provenance and explicit limits keep findings tied to observed calls. | The small synthetic set cannot establish fairness across accents, languages, disability, or patient populations. Do not claim representative performance. |
| Accidental calling, state changes, or spending | This UI has no write or dispatch endpoints. Existing CLI restricts destination and bounds duration/turns. | Live-call controls are a separate task (#24) and need explicit confirmation, duplicate-call protection, and reliable stop behavior before enabling. |
| Loss or unintended retention of evidence | Originals remain local; packaging excludes calls; CI uses generated fixtures only. | Abrupt worker termination can lose unfinished audio. There is no automated retention/deletion policy or backup guarantee. Owner must decide retention after submission and review provider-side storage separately. |

## Human review and public release

1. Confirm the call ID, scenario, code/model configuration, and original audio match.
2. Listen end to end. Check audibility, speaker attribution, turn-taking, transcript
   accuracy, and the ending. The read-only UI cannot mark a call reviewed; playback
   does not silently change `listened_by_human` or any other evidence field.
3. Inspect audio and text for personal information, secrets, and unrelated content.
   If editing is necessary, retain original evidence privately and label the derivative,
   edit rationale, and missing context. Do not silently clean up the evaluator's words.
4. Support each finding with a quote, measured timestamp, expected behavior and its
   basis, attribution, uncertainty, and any corroborating evidence. Keep simulator bugs
   separate from findings about the assessment agent.
5. Add only reviewed submission artifacts explicitly. Public Git history is difficult
   to retract; `calls/` is ignored and never uploaded by CI. Review the final diff.

This workflow is specified, not asserted complete. The first captured call's listening
review is still pending. No finding against the assessment agent has been confirmed.

## Privacy, providers, and accessibility

The real voice pipeline processes data through Twilio, LiveKit, and inference providers.
A local viewer does not make that pipeline local-only. Provider terms, retention,
training use, consent requirements, deletion mechanisms, and agreements have not been
fully assessed. No BAA or authorization for production PHI is asserted. Before any
real-patient use, determine applicable obligations and appropriate agreements, access
controls, retention, and incident handling. [HHS de-identification guidance](https://www.hhs.gov/hipaa/for-professionals/special-topics/de-identification/index.html)
explains methods and their conditions; using fictional prompts is not itself one of them.

The UI includes semantic controls, keyboard tab navigation, visible focus, responsive
layouts, contrast checks, reduced-motion support, and an adjacent raw transcript.
Playwright and axe exercise desktop/mobile Chromium and desktop WebKit with synthetic
fixtures. Automated checks cannot establish complete accessibility. The transcript is
not yet human-corrected or complete with non-speech sound annotations, and unmeasured
audio offsets cannot truthfully become synchronized captions. Manual assistive-technology
review and validated audio alternatives remain necessary before claiming conformance.
