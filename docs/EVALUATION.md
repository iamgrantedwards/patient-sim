# Evaluation: strategy, AI assessment and listening

Implementation audit: 2026-09-20 UTC, #77; call-quality extension #85. This document
describes `transcript-v2`. Existing assessments are preserved; another explicit
assessment request is required to generate the new checks.

## Three different kinds of evaluation

| Layer | Purpose | Authoritative implementation / evidence |
| --- | --- | --- |
| Call strategy | Choose varied patient goals and decide what to investigate. | [TEST-STRATEGY.md](TEST-STRATEGY.md), [scenario registry](../src/caller/scenarios.py); [COLLECTION.md](COLLECTION.md) records execution. |
| AI transcript assessment | Suggest text-supported quality grades and observations for one office-agent conversation. | [Rubric, schema and judge](../src/analysis/assessment.py), [assessment API](../src/review/assessments.py). |
| Offline software tests | Verify our implementation, validation, lifecycle and UI with fixtures/mocks. | [CI.md](CI.md), [Python assessment tests](../tests/test_assessments.py), [browser assessment tests](../tests/browser/assessments.spec.js). |

`TEST-STRATEGY.md` is a human planning document, not a runtime prompt or test harness.
Its principles overlap with the judge: legitimate refusals can be correct, quotes
need evidence, attribution may be unknown, and claims are not backend outcomes.
There is no automatic synchronization between that Markdown, scenario success
criteria and the five-dimension judge. Editing the strategy alone changes no scores.

## What a per-call assessment actually does

1. The operator starts the console with `--enable-assessments` and explicitly selects
   **Assess transcript** on a saved call. No assessment runs automatically at call end.
   Read-only mode can display existing results without provider credentials.
2. Local eligibility requires ended status, end-call-tool or remote-hangup outcome,
   an available recording and at least one completed turn from each speaker. This
   excludes incomplete attempts; it does not prove audio quality or a natural ending.
3. The server builds JSON with exactly `scenario` (saved scenario ID), `turns`
   (raw transcript projection: IDs, speaker, text and status) and `capture`
   (status, termination reason, duration, recording availability/decode status, partial
   and pending speech counts, and explicit safety-limit indicators). Metadata is not
   audio timing. The system prompt and structured schema come from Python code.
   Raw audio, review notes, patient configuration, prior calls, external policy facts,
   scenario objective/success criteria/traps and Markdown docs are not sent.
4. `LiveKitJudge` sends a separate request through LiveKit Inference. The default
   `JUDGE_MODEL=gpt-4.1` becomes `openai/gpt-4.1`; it is independent of the caller's
   GPT-4.1-mini conversation model. Existing LiveKit credentials are used; no direct
   OpenAI key is required. A new request incurs LiveKit usage; opening saved results does not.
5. Code validates the schema and quotes, calculates the aggregate and atomically saves
   `calls/<call-id>/assessment.json`. Original audio/transcripts and human reviews remain
   unchanged. There is no automatic prompt tuning, code fix, redial or recursive learning.

## The five rubric dimensions

| Dimension | Question | Not established by a passing grade |
| --- | --- | --- |
| `request_handling` | Did the office address the request or explain a legitimate limit? | Fulfillment in a real system or every scenario-specific objective. |
| `consistency` | Do comparable names, dates or instructions agree within this call? | Cross-call consistency, correct pronunciation or independently true facts. |
| `clarification` | Did it resolve ambiguity and retain corrections actually presented? | Audio interruption handling or clarity when no ambiguity was exercised. |
| `supported_claims` | Can a claim be checked against facts elsewhere in the supplied conversation? | Actual chart contents, policy, booking or prescription state. |
| `next_steps` | Is the stated outcome or next action clear? | A natural audible farewell, completed transfer, follow-up or calendar update. |

Grades are 2 (no material issue observed in available text), 1 (specific minor gap),
0 (specific substantial failure), or null (not assessable/not exercised). The code
requires all five distinct dimensions. Every numeric grade must cite exact nonempty
raw transcript text and include at least one remote-agent turn. Quote validation
establishes textual support, not that the rationale is correct or STT heard accurately.

The aggregate is `round(100 × sum(grades) / (2 × number_assessed))`. Null grades are
excluded, and the aggregate is withheld below 3/5 assessed dimensions. It is a
provisional rubric score, not a calibrated probability, pass certificate or benchmark.
Zero candidate observations is valid. Each proposed concern needs an expected behavior,
a basis, citations, attribution, uncertainty, suggested improvement and focused next test.

## How this maps to the review checklist

| Manual review item | Automated help | Remaining human judgment |
| --- | --- | --- |
| Complete evidence | Local file, decode, both-speaker and pending-speech checks | Files present does not mean a complete audible conversation. |
| Transcript accuracy | Explicit Needs listening status; exact quote-to-text validation | Compare important words to audio; preserve raw STT and label corrections. |
| Patient behavior | Dedicated AI text check with patient-turn citations | Realism in audio and fair pursuit of the objective; hidden patient facts are not supplied. |
| Turn-taking | AI can flag text-supported concerns; cannot clear the check from text | Listen for overlap/interruptions; no automatic audio-aligned timing. |
| Pacing | Explicit Needs listening status | Listen or measure from audio offsets, never callback arrival timestamps. |
| Audio clarity | Explicit Needs listening status | Decoding alone cannot establish intelligibility, clipping or dropouts. |
| Ending | Dedicated AI check of final exchange plus termination metadata; expanded by default | Listen to the final 10–15 seconds. A committed transcript item or caller hangup does not prove completed playback. |

These seven rows appear in **Call quality**, separate from the unchanged five-dimension
0–100 office-agent score. The model returns exactly three text checks: patient behavior,
turn-taking and ending. Each uses Concern, No issue in text, or Not assessable, with a
rationale, provisional attribution and next step. Assessed checks require exact quotes;
patient checks require a patient citation and ending checks a citation from the final
two turns. Code rejects a clear ending when the last turn is partial, interrupted or
ends in an ellipsis, and rejects any text-only clearance of turn-taking. A grammatically
unfinished sentence without those markers remains a model judgment, not a deterministic
language rule. These checks do not automatically mark any manual review item complete.

### Ending diagnosis and the time limit

`Caller ended` means our simulator invoked its end-call tool. It does not mean the
conversation ended well. The default and maximum call duration is 240 seconds, with
additional turn and cleanup bounds to limit stuck calls and usage. Recent suspected
cutoffs ended via the tool well before 240 seconds; the recorded limit indicators did
not identify a timeout. The pinned SDK waits for the patient's current speech handle,
then shuts down the session; it does not explicitly wait for another office-agent
closing turn. Early tool invocation is a hypothesis to investigate, not a confirmed
root cause. This review extension changes no call timing or hangup behavior. See
[DEBUGGING.md](DEBUGGING.md) and the still-open ending investigation #12.

The optional **Add AI summary** action copies a fresh saved model summary into draft
review notes. It preserves existing notes and changes no checklist result, listening
confirmation or submission outcome. Saving review notes does not silently approve a call.

## What is validated and what is still a model instruction

Deterministic checks enforce schema, distinct dimensions, grade range, quote presence,
remote-speaker evidence, aggregate arithmetic, eligibility, request boundaries and
persistence. Tests also cover staleness, concurrency, revision limits, provider errors,
invalid/oversized output and preservation of originals. Provider calls in these tests
are mocked; CI does not listen to or assess our real recordings.

The prompt instructs the model to treat input as untrusted evidence, ignore embedded
instructions, use null for inapplicable dimensions, avoid invented policies, and
avoid audio/backend claims. Those semantic instructions are **not proven by JSON or
quote validation**. The judge has no tools or automatic authority to act on its output.

One authored office-hours provider fixture exposed overgrading of unexercised dimensions;
the prompt was tightened and a fixture retest withheld the aggregate at 2/5 coverage.
This is narrow calibration evidence, not a labeled evaluation set or accuracy measure.
The saved refill assessment still treats repetition/lack of contradiction as sufficient
support for a chart claim. That does not meet the intended grounding rule: review this
judgment before citing it. The result has not been rewritten or automatically rerun.
No score should be presented as verification of the office's backend.

## Provenance and future changes

Saved results record model, rubric version, prompt SHA-256, evidence fingerprints and
generation time, with up to ten revisions. Changed fingerprints, rubric or prompt mark
results stale; a configured judge's model change also does so. A fresh result is reused,
and rerunning stale evidence requires another explicit request. Existing call recordings
are not invalidated by a new rubric, but scores from different rubric revisions should
not be treated as a controlled comparison.

If changing the evaluation later, use a focused issue/PR: update the prompt/schema and
rubric version as appropriate, add meaningful applicability and adversarial fixtures,
record what changed, and explicitly assess again only when wanted. Scenario-specific
assertions, cross-call analysis, audio scoring and automatic learning are future scope,
not features demonstrated in this submission. Human-confirmed findings belong in
[BUGS.md](../BUGS.md); current remaining work is in [SUBMISSION.md](SUBMISSION.md).
