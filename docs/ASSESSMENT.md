# Assessment compliance review

Reviewed against Grant's original AI Engineering Challenge brief on 2026-09-18.
The mandatory implementation choices are followed; the submission is not complete.

| Brief requirement | Current evidence/status |
| --- | --- |
| Python + LiveKit Agents, separate STT/LLM/TTS | Implemented in `src/caller/agent.py`; no realtime models or prohibited hosted voice-agent platforms |
| Call only +1-805-439-8008 | Destination enforced before dispatch and in configuration validation; rejection tests pass |
| One caller number throughout, submitted in E.164 | Owned DID configured and used for the first call; keep the same number for all calls and final submission |
| Athena test account; never call its confirmation-screen number | Completed per Grant’s firsthand report on 2026-09-19; demo callback/booking experienced, calendar/SMS recollected but not independently checked; assessment-line state sharing unknown |
| Natural, coherent conversations | Unverified until real calls are listened to; mocks and coverage do not establish this |
| At least 10 full conversations, each with both-sided audio and transcript | Ten candidate pairs (20.59 minutes) are captured with decoded recordings and both-sided transcripts; see COLLECTION.md. Human listening acceptance remains pending; captured files are not accepted pairs |
| Variety: scheduling, changes/cancellation, refills, information, edge cases | Ten scenario definitions implemented in PR #60; appointment state sequence and broader workflows now exercised; controlled interruption remains untested |
| Bug report with evidence | BUGS.md separates observed caller defects from office behavior; no office-agent bug is confirmed, and listening remains pending |
| Public GitHub repository | Verified public: iamgrantedwards/patient-sim. Worker recovery, scenario catalog, journal recovery and transfer boundary are merged; selected call artifacts await publication review |
| Setup/run README and .env.example; no committed secrets | Present; one-command console or explicit CLI now manages its worker. Secret scans are part of the required verification gate; no provider keys reach the UI |
| Architecture explanation in 1–2 paragraphs | Condensed to two paragraphs. Provider and latency choices remain hypotheses pending call-based comparison |
| Public walkthrough video, maximum 3 minutes | Pending; Grant's own voice and webcam required |
| Second public video showing AI-assisted debugging | Recorded per Grant's 2026-09-19 report; public URL and logged-out playback still need verification (#25) |
| Submission form with public links and exact caller DID | Pending; check access while logged out before submitting |

## Scope and priorities

The brief's first gate remains voice interaction quality. The local console and worker
fixes are merged, and live collection now exercises the scenario catalog. The remaining
submission path is to listen and record review acceptance, publish the selected pairs,
finish evidence-backed findings and add the two public video links. The debug recording
is already complete per Grant's report. See COLLECTION.md for actual collection status.

Ten complete call pairs are mandatory. Twelve calls, eight scenario kinds, and the
specific safety/privacy mix in our contract are internal planning targets, not additional
employer requirements. Six hours is an expected effort, not a stated hard deadline.
Keep receipts; the brief offers reimbursement up to $20, not unlimited spending.

CI is supporting work. Preserve the existing gates and extend them only for actual
new UI code. Grant's requested local call console is in scope; production deployment,
analytics dashboards, fancy diagrams, and an automated judge remain unnecessary.
Keep model/settings changes traceable between experiments. Do not contact the employer
or its team outside the stated submission process.
