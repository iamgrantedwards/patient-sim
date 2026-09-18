# Assessment compliance review

Reviewed against Grant's original AI Engineering Challenge brief on 2026-09-18.
The mandatory implementation choices are followed; the submission is not complete.

| Brief requirement | Current evidence/status |
| --- | --- |
| Python + LiveKit Agents, separate STT/LLM/TTS | Implemented in `src/caller/agent.py`; no realtime models or prohibited hosted voice-agent platforms |
| Call only +1-805-439-8008 | Destination enforced before dispatch and in configuration validation; rejection tests pass |
| One caller number throughout, submitted in E.164 | Configuration and provenance support this; an owned DID is not configured yet. Hold it fixed once chosen |
| Athena test account; never call its confirmation-screen number | Account creation/product exploration not yet verified; permitted destination stays fixed |
| Natural, coherent conversations | Unverified until real calls are listened to; mocks and coverage do not establish this |
| At least 10 full conversations, each with both-sided audio and transcript | Zero real-call pairs collected. OGG preservation and transcription implemented and tested with fixtures only |
| Variety: scheduling, changes/cancellation, refills, information, edge cases | Only the read-only office-information smoke scenario exists; expand after the first good call |
| Bug report with evidence | No findings confirmed; `BUGS.md` remains to be written from actual calls |
| Public GitHub repository | Verified public: iamgrantedwards/patient-sim. Working implementation remains on draft PR #20; merge before submission |
| Setup/run README and .env.example; no committed secrets | Present; two terminals currently required. Full-history/working-tree secret scans pass. A single-command caller is an optional usability improvement |
| Architecture explanation in 1–2 paragraphs | Condensed to two paragraphs. Provider and latency choices remain hypotheses pending call-based comparison |
| Public walkthrough video, maximum 3 minutes | Pending; Grant's own voice and webcam required |
| Second public video showing AI-assisted debugging | Pending; record a genuine upcoming debugging session, including Grant's prompts, own voice and webcam. Do not recreate past work as if live |
| Submission form with public links and exact caller DID | Pending; check access while logged out before submitting |

## Scope and priorities

The brief's first gate is voice interaction quality. The next milestone is personal
LiveKit/Twilio setup and one full conversation with a clean ending and matching audio
and transcript. Start recording a genuine debugging session before fixing issues found
during those calls, so the second video is real process evidence.

Ten complete call pairs are mandatory. Twelve calls, eight scenario kinds, and the
specific safety/privacy mix in our contract are internal planning targets, not additional
employer requirements. Six hours is an expected effort, not a stated hard deadline.
Keep receipts; the brief offers reimbursement up to $20, not unlimited spending.

CI is supporting work. The current quality checks are sufficient; do not add deployment
platforms, dashboards, diagrams, or an automated judge before useful call evidence.
Keep model/settings changes traceable between experiments. Do not contact the employer
or its team outside the stated submission process.
