# Collection results — 2026-09-19

These are capture and transcript inspections, not completed human listening reviews.
Raw recordings, journals and transcripts are unchanged. Provider/model configuration
and source revision are recorded separately for every call. No backend access exists;
spoken transaction confirmations and cross-call consistency are not verified writes.

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

- Human listening and seven-check review for each candidate pair.
- Audio-aligned turn timing (#15); SDK speech metrics are available, but callback event
  arrival timestamps are not speech boundaries and are not substituted for measurements.
- Controlled interruption has not been implemented or demonstrated.
- Three-configuration comparison (#13) is deferred; no best-model claim is made.
- The native segmentation fault has not recurred in this collection so far; its precise
  root cause remains unresolved. An absence of recurrence does not prove a native fix.
