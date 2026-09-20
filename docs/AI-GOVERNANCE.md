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

By default, the separate review process reads local call artifacts without importing the caller,
loading `.env`, invoking models, or opening outbound-call controls. It has no analytics,
external fonts, CDN assets, authentication, or cloud deployment. Its default host is
fixed to `127.0.0.1`; it is intended for one trusted local operator. Do not expose it
through a public tunnel or treat it as a multi-user patient-record service.

The CLI binds to loopback; the default HTTP surface permits only GET/HEAD, checks Host and Origin, rejects
cross-site API/subresource requests (allowing top-level GET / document navigation
without an Origin header), and sets restrictive CSP, framing, referrer, and cache
headers. Artifact paths are fixed and symlinks rejected. Reads have size limits.
Transcripts enter the DOM as text, not HTML. These controls limit browser and file
exposure; they do not protect against a malicious local process that already has access
to the same files or writes during a read. Original audio and text are never rewritten.

An explicit `--enable-calls` startup flag adds a separate control API and loads caller
configuration on the server. The browser receives only readiness, the fixed destination,
caller ID, limits, scenario descriptions, and public operation state. Every start needs
an exact local Origin, an unpredictable per-process request token, a one-use confirmation
token, a unique request ID, and an affirmative confirmation. UI and CLI share an OS lock.
Neither status polling nor refresh dispatches work. Stop and controller shutdown are
recorded separately from natural endings. Recovery blocks new calls until a worker-stop
receipt and room absence establish cleanup; it never kills an unowned PID.

## Optional assessment and review writes

`--enable-reviews` enables local atomic, revisioned `review.json` saves with request
tokens, exact Origin checks, per-call locking and evidence fingerprints. A saved
review or model result never changes original call files. Detailed checklist rows
are optional; Usable requires explicit listening and complete-evidence approval.

`--enable-assessments` separately enables an explicit paid request sending a saved
scenario ID, transcript-turn projection and allowlisted capture/termination metadata
through LiveKit Inference. Call-quality checks separate local file facts and model
text judgments from audio-only topics explicitly marked Needs listening. The default
viewer does not invoke models, but it can display previously saved assessments.
The judge receives no raw audio, other calls or manual reviews. It has no tools and
cannot change prompts, call numbers or code. Its instructions treat transcript text
as untrusted, but prompt adherence is not a proven injection defense. Exact quotes,
output schema and bounded request/response sizes are validated; semantic judgments
remain fallible. Assessment writes are token/Origin protected, locked and atomic;
results have model/rubric/prompt fingerprints and at most ten revisions. See
[EVALUATION.md](EVALUATION.md) for the full boundary and known grounding limitation.

## Framework mapping

[NIST AI RMF 1.0](https://www.nist.gov/itl/ai-risk-management-framework) is a voluntary
risk-management framework. The following is a limited implementation mapping to its
Govern, Map, Measure, and Manage functions, not an assertion of full framework coverage.

| Function | Implemented control and evidence | Remaining work / decision |
| --- | --- | --- |
| Govern | Named owner; contract and notebook; issue-linked branches/PRs; required CI; separate human-listening and publication gates. See `ROADMAP.md`, `CONTRACT.md`, and `.github/workflows/ci.yml`. | Owner reviews and approves evidence for public release. No independent audit or certification has been performed. |
| Map | Defined synthetic evaluation use, fixed destination, provider pipeline, known limitations, and a risk register below. The UI distinguishes caller and assessment agent. | Athena context is recorded from Grant’s firsthand report (#8); shared backend state remains unknown. Assess provider/data obligations before expanding scope. |
| Measure | Preserved audio, committed turns, explicit partial speech, code/model/prompt provenance, SHA-256 of currently served audio, separate claimed/consistent/verified state, automated failure-path tests and axe checks. | Listen end to end; validate quote/timestamp pairs; audio timing is deferred (#15); obtain independent evidence before labeling outcomes verified. |
| Manage | Read-only default viewer and opt-in confirmed controls; shared call lock/recovery; coded destination limit; call duration/turn limits; manual evidence-release gate; dependency/secret scans; fixes tracked separately from assessment findings. | Callback #21 and lifecycle #46 are closed on scoped evidence; original ending #12 and human acceptance remain. Native crash cause is unknown; ten varied candidates are captured. |

## Risk register

| Risk | Current mitigation | Residual risk and release condition |
| --- | --- | --- |
| False finding or invented outcome | `claimed_state`, cross-call `consistency`, and `verified_state` are separate. Unknown remains unknown. Findings require expected behavior, its basis, timestamps, quotes, attribution, and uncertainty. | Consistency is not proof. Human review must corroborate findings; appropriate identity re-verification is not automatically a bug. |
| Untrusted content or prompt injection | Viewer renders transcript content as inert text. Opt-in judging sends it as untrusted evidence under a fixed rubric; the judge has no tools. Caller destination is enforced in code and evaluator traps excluded from the patient prompt. | Prompt-only restrictions are insufficient; structured output and exact quotes do not establish resistance to semantic manipulation. No comprehensive adversarial judge evaluation has been performed. See [OWASP prompt injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/). |
| Personal information in recordings | Synthetic inputs; local ignored artifacts; API returns an allowlisted metadata projection; no raw config or environment endpoint. Review and publication are separate. | The remote response may contain personal information. Synthetic inputs do not guarantee de-identification. Review audio AND text before release; retain originals separately if a labeled redacted derivative is needed. |
| Misleading evidence quality | No autoplay; partial turns and missing artifacts remain visible; decoded audio is not called human-reviewed. Fingerprints identify current bytes without claiming a trusted timestamp or signed chain of custody. | Raw STT can be wrong. Readable files and file pairs do not count as complete assessment conversations. A human must compare the audio with the transcript. |
| Inappropriate generalization or bias | Scenario provenance and explicit limits keep findings tied to observed calls. | The small synthetic set cannot establish fairness across accents, languages, disability, or patient populations. Do not claim representative performance. |
| Accidental calling, state changes, or spending | Read-only default; opt-in confirmation, fixed destination, single-call lock, one-use tokens/idempotent requests, stop/recovery, and duration/turn bounds. | Offline tests and connected call/cleanup paths have been exercised. Voice quality and publication review remain. An uncertain provider outcome blocks another call; new judge requests incur separate inference usage. |
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

This workflow is specified, not asserted complete. Ten candidate pairs are captured;
listening/publication decisions remain in #18. No finding against the assessment
agent has been confirmed. Detailed evidence and current obligations are in
[COLLECTION.md](COLLECTION.md) and [SUBMISSION.md](SUBMISSION.md).

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
