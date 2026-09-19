# Assessment compliance review

Reviewed against Grant's original AI Engineering Challenge brief on 2026-09-18.
The mandatory implementation choices are followed; the submission is not complete.

| Brief requirement | Current evidence/status |
| --- | --- |
| Python + LiveKit Agents, separate STT/LLM/TTS | Implemented in `src/caller/agent.py`; no realtime models or prohibited hosted voice-agent platforms |
| Call only +1-805-439-8008 | Destination enforced before dispatch and in configuration validation; rejection tests pass |
| One caller number throughout, submitted in E.164 | Owned DID configured and used for the first call; keep the same number for all calls and final submission |
| Athena test account; never call its confirmation-screen number | Account creation/product exploration not yet verified; permitted destination stays fixed |
| Natural, coherent conversations | Unverified until real calls are listened to; mocks and coverage do not establish this |
| At least 10 full conversations, each with both-sided audio and transcript | One 70-second stereo OGG/transcript pair exists locally; the last patient turn was cut off and listening is pending. Zero pairs accepted toward the ten-call gate so far |
| Variety: scheduling, changes/cancellation, refills, information, edge cases | Only the read-only office-information smoke scenario exists; expand after the first good call |
| Bug report with evidence | No findings confirmed; `BUGS.md` remains to be written from actual calls |
| Public GitHub repository | Verified public: iamgrantedwards/patient-sim. Working implementation remains on a dependent draft PR stack (#20, #27, controls); merge before submission |
| Setup/run README and .env.example; no committed secrets | Present; one-command console or explicit CLI now manages its worker. Secret scans are part of the required verification gate; no provider keys reach the UI |
| Architecture explanation in 1–2 paragraphs | Condensed to two paragraphs. Provider and latency choices remain hypotheses pending call-based comparison |
| Public walkthrough video, maximum 3 minutes | Pending; Grant's own voice and webcam required |
| Second public video showing AI-assisted debugging | Pending until the requested call UI works (#22–#25); include Grant's prompts, own voice and webcam. Do not recreate past work as if live |
| Submission form with public links and exact caller DID | Pending; check access while logged out before submitting |

## Scope and priorities

The brief's first gate remains voice interaction quality. Personal LiveKit/Twilio
setup now works and the first call produced usable files, but M1 has not passed. On
2026-09-18 Grant requested a usable UI before recording. The next build is a local call
review surface (#23), followed by explicit call controls/live status (#24), then genuine
recorded debugging (#25). This changes our build order, not the employer's requirements.
See [the roadmap](ROADMAP.md) for issues, dependencies, and PR ownership.

Ten complete call pairs are mandatory. Twelve calls, eight scenario kinds, and the
specific safety/privacy mix in our contract are internal planning targets, not additional
employer requirements. Six hours is an expected effort, not a stated hard deadline.
Keep receipts; the brief offers reimbursement up to $20, not unlimited spending.

CI is supporting work. Preserve the existing gates and extend them only for actual
new UI code. Grant's requested local call console is in scope; production deployment,
analytics dashboards, fancy diagrams, and an automated judge remain unnecessary.
Keep model/settings changes traceable between experiments. Do not contact the employer
or its team outside the stated submission process.
