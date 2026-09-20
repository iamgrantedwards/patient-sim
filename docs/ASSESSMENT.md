# Assessment compliance review

Final publication reconciliation — September 20, 2026. Application development is
frozen. Grant supplied both videos and saved the final human reviews. The remaining
steps are public evidence publication and actual form submission. Grant confirmed both replacement video links work after checking them.

| Brief requirement | Current evidence/status |
| --- | --- |
| Python + LiveKit Agents, separate STT/LLM/TTS | Implemented in `src/caller/agent.py`; no realtime models or prohibited hosted voice-agent platforms |
| Call only +1-805-439-8008 | Destination enforced before dispatch and in configuration validation; rejection tests pass |
| One caller number throughout, submitted in E.164 | Owned DID configured and used for the first call; keep the same number for all calls and final submission |
| Athena test account; never call its confirmation-screen number | Completed per Grant’s firsthand report on 2026-09-19; demo callback/booking experienced, calendar/SMS recollected but not independently checked; assessment-line state sharing unknown |
| Natural, coherent conversations | Grant saved listening and usable decisions for the primary ten; reported quality issues remain visible in review.json and BUGS.md |
| At least 10 full conversations, each with both-sided audio and transcript | Primary ten human-reviewed calls span all scenarios. Full archive: 47 records / 46 original audio-transcript pairs, plus saved reviews and assessments. See calls/README.md |
| Variety: scheduling, changes/cancellation, refills, information, edge cases | Ten scenario definitions implemented in PR #60; appointment state sequence and broader workflows now exercised; controlled interruption remains untested |
| Bug report with evidence | BUGS.md includes the intake negation contradiction, human-reported choppy intros, incomplete endings and caller defects. Precise transcript turns are cited; audio alignment and backend verification remain unknown |
| Public GitHub repository | Verified public: iamgrantedwards/patient-sim. Worker recovery, scenario catalog, journal recovery and transfer boundary are merged; explicit publication files have been scanned and indexed with SHA-256; verify PR merge/public access before submitting |
| Setup/run README and .env.example; no committed secrets | Present; one-command console or explicit CLI now manages its worker. Secret scans are part of the required verification gate; no provider keys reach the UI |
| Architecture explanation in 1–2 paragraphs | Condensed to two paragraphs. Provider and latency choices remain hypotheses pending call-based comparison |
| Public walkthrough video, maximum 3 minutes | [Demo supplied](https://www.loom.com/share/0db55c95dd894cd388593a33c5d9a2b1), publicly reachable; 178.821 seconds (2:59), within the limit |
| Second public video showing AI-assisted debugging | Replacement recording of the genuine #92/#93 ending investigation supplied September 20; [link recorded](https://www.loom.com/share/12245c3a689549f69ff08590087fc83e); public share/oEmbed metadata verified; Grant confirmed the replacement links work |
| Submission form with public links and exact caller DID | Pending; Grant confirmed video access; verify the published archive before submitting |

## Scope and priorities

The brief's first gate remains voice interaction quality. The local console and worker
fixes are merged, and live collection now exercises the scenario catalog. Saved human reviews and both replacement video links are complete. The remaining
submission path is to merge and verify the public evidence archive, reconcile GitHub
issues, and submit the required form. See COLLECTION.md for actual collection status.

Ten complete call pairs are mandatory. Twelve calls, eight scenario kinds, and the
specific safety/privacy mix in our contract are internal planning targets, not additional
employer requirements. Six hours is an expected effort, not a stated hard deadline.
Keep receipts; the brief offers reimbursement up to $20, not unlimited spending.

CI is supporting work. Preserve the existing gates and extend them only for actual
new UI code. Grant's requested local call console is in scope; production deployment,
analytics dashboards and fancy diagrams remain unnecessary. The optional transcript
judge is now implemented at Grant's request; it proposes observations and never
substitutes for listening or independent verification.
Keep model/settings changes traceable between experiments. Do not contact the employer
or its team outside the stated submission process.
