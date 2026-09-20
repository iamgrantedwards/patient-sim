# Collection results and freeze inventory

These are capture and transcript inspections, not completed human listening reviews.
Raw recordings, journals and transcripts are unchanged. Provider/model configuration
and source revision are recorded separately for every call. No backend access exists;
spoken transaction confirmations and cross-call consistency are not verified writes.

## Original ten-candidate set — 2026-09-19 Pacific

Ten candidates total 20.59 minutes. All original stereo recordings fully decode, both channels contain audio, and transcripts contain both participants. These checks establish capture integrity, not conversation quality. No app listening/Usable decisions are saved for this set at the freeze audit. This is
a saved-state observation, not a claim that Grant has never listened to the audio.

| Scenario | Call ID | Audio | Turns | Human acceptance |
| --- | --- | --- | --- | --- |
| Office information | `call-20260920-011714-108d161e` | 1:30 | 10 | Pending |
| Appointment scheduling | `call-20260920-011949-1416594f` | 2:11 | 12 | Pending |
| Rescheduling | `call-20260920-012229-385cbddd` | 2:31 | 16 | Pending |
| Cancellation | `call-20260920-012551-68c384cc` | 1:39 | 13 | Pending |
| Medication refill — retest | `call-20260920-014805-936b2fa6` | 2:10 | 15 | Pending |
| Missing refill details | `call-20260920-013308-e844b113` | 1:50 | 12 | Pending |
| Insurance questions | `call-20260920-013605-748acbe7` | 2:36 | 17 | Pending |
| Availability correction | `call-20260920-013929-89116fae` | 2:20 | 20 | Pending |
| Unclear request | `call-20260920-014248-53504de4` | 2:26 | 18 | Pending |
| Third-party request | `call-20260920-014604-0566403f` | 1:17 | 8 | Pending |

The local candidate bundle preserves original file hashes and source revisions. Synthetic inputs were checked against the recorded source revision, recordings were decoded, and a secret scan passed. The bundle remains private while the recordings are reviewed. It does not include fabricated review records.

Earlier diagnostic attempts remain separate: the original callback/crash attempts, an operator-stopped call, the onboarding refusal and the pre-fix transfer acceptance are not in this candidate set.

## Later retests and application freeze — 2026-09-20 UTC

The local index contains **19 attempts and 18 audio/transcript file pairs**. This
includes diagnostic/short/incomplete attempts and is not an accepted-conversation count.
The four later records below are available alternatives; they have not silently replaced
rows in the original candidate bundle or been approved for public release.

| Scenario | Call ID | Duration shown by the app | Turns | Saved human acceptance |
| --- | --- | --- | --- | --- |
| Office Information | `call-20260920-034355-fa5b226a` | 1:33 | 13 | Pending |
| Unclear Request | `call-20260920-042404-94899755` | 2:01 | 12 | Pending |
| Availability Correction | `call-20260920-043854-fd9ce1a5` | 2:21 | 17 | Pending |
| Refill Missing Information | `call-20260920-050215-67ac848f` | 2:05 | 13 | Pending |

These durations/turn counts come from saved metadata and the local index; this audit
has not newly listened to or decoded these four recordings. AI assessment state may
change as Grant assesses calls; its scores are not human listening acceptance. The
latest seven-topic checklist distinguishes text-supported ending concerns from audio
checks that still need listening. Suspected end-tool cutoffs remain in #12.

Grant has frozen application development and further call collection. Select the
minimum ten complete conversations from existing evidence and document any remaining
limitations. A private bundle is not a public deliverable; no raw call files are yet
tracked in GitHub. Publication remains a deliberate reviewed handoff step.

## Iteration boundary

- The original first call preserved a conversation despite a callback exception.
- The original second attempt lost its child worker with SIGSEGV; native cause remains
  unresolved. PR #58 detects child failure and blocks repeated assignment safely.
- An operator-stopped retest preserved a short recording and confirmed cleanup; excluded.
- Smoke v2 completed but ignored generic onboarding instructions. Smoke v3 put accepting
  the offered demo profile first. The next call obtained hours and location successfully.
- Transaction collection uses the synthetic identity assigned by the demo office.

## State sequence

| Scenario | Claimed state | Consistency | Independently verified |
| --- | --- | --- | --- |
| Scheduling | Appointment confirmed | First observation | Unknown |
| Rescheduling | Prior appointment retrieved; replacement confirmed | Prior slot matched the scheduling transcript | Unknown |
| Cancellation | Replacement appointment found and cancellation confirmed | Date matched the replacement claim | Unknown |

Re-verifying identity is expected and not a defect. The provider name has several raw
STT spellings; do not assert the office changed providers without listening to the audio.

## Deferred work

- Human listening and suitability/publication review for each candidate pair; detailed checklist rows are optional.
- Audio-aligned turn timing (#15); SDK speech metrics are available, but callback event
  arrival timestamps are not speech boundaries and are not substituted for measurements.
- Controlled interruption has not been implemented or demonstrated.
- Three-configuration comparison (#13) is deferred; no best-model claim is made.
- The native segmentation fault has not recurred in this collection; its precise
  root cause remains unresolved. An absence of recurrence does not prove a native fix.

## Listening priorities

Start with the successful office-information onboarding call, then compare the two
onboarding runs. Check the final 15 seconds of each recording for clipping, silence,
or a missing spoken farewell; end_call_tool proves termination, not naturalness.
For the availability-correction call, listen around the partial “Actually” before the
completed afternoon correction. Its interrupted flag alone does not establish audible
overlap or a controlled barge-in experiment. Check provider-name spellings against the
audio before proposing any correction to the separate review notes.

Use the existing Review panel to save your outcome, useful notes and explicit listening
confirmation. The Usable outcome also requires Complete evidence: OK; other detailed
checks can remain not assessed. None of these inspection notes automatically mark a recording usable.

## Remaining submission work

- #18: listen to every selected pair, record suitability and listening, select an existing alternative for any unusable conversation where possible, then publish the reviewed set. No further calling is planned.
- #12: verify natural endings by listening, especially the last 15 seconds.
- #24: confirm the call/review workflow in use; automated checks alone do not finish human acceptance.
- #46: retain the unresolved native-crash limitation separately from the repaired lifecycle behavior.
- #25: verify logged-out playback and required content of the linked debugging video.
- #26: record the final walkthrough (maximum three minutes) and verify all submission links.

The review UI's Usable indicator follows an explicit saved judgment. Capture selection
and a green CI run never substitute for that judgment.
