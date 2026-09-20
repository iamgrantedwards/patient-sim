# Final submission checklist

Reconciled September 20, 2026. Application code is frozen. The public evidence PR is
tracked by #18/#26; recorded reviews, not earlier candidate counts, define this package.

## Deliverables

- Public repository: https://github.com/iamgrantedwards/patient-sim
- [Application demo](https://www.loom.com/share/0db55c95dd894cd388593a33c5d9a2b1)
- [AI-assisted debugging](https://www.loom.com/share/12245c3a689549f69ff08590087fc83e)
- Caller DID: **+19062567632** (not the destination number).
- [Primary ten reviewed calls and all 47 records](../calls/README.md): 46 original OGG
  recordings with transcripts, plus one failed attempt without audio/transcript.
- [Findings](../BUGS.md), [architecture](../ARCHITECTURE.md), [setup](SETUP.md),
  [evaluation boundaries](EVALUATION.md), [checksums](../calls/manifest.json).

## Remaining actions before the form

1. Grant confirmed both replacement video links work after checking them on September 20. Their share
   pages and oEmbed metadata return HTTP 200 anonymously. The demo is 178.821 seconds
   (2:59), within the three-minute limit; debug is 225.876 seconds (3:46). This check
   verifies access metadata and length, not independent viewing of the entire videos.
2. Confirm the final evidence PR is merged and green and the public archive matches
   its manifest. The index distinguishes the primary ten from additional attempts.
3. Include receipts if requesting reimbursement (brief maximum $20).
4. Grant submits the required Pretty Good AI AI Engineer submission form with the public
   repository, both videos and exact DID. **Do not email, message or contact the team
   directly about the assessment.** No account or credential transfer is needed.

## Evidence and acceptance

The final inventory contains 47 records / 46 original recordings and transcripts.
Fifteen saved reviews confirm listening: fourteen usable and one needs recheck. The selected
ten usable calls cover each scenario once and form the primary set. Reviews marked usable
can still contain quality issues, especially endings; the package does not claim flawless
conversations or independent verification of backend transactions. Saved fingerprints
match original files. All 46 OGG recordings fully decode; no audio has been altered.

Published files are explicitly allowlisted. Local event journals, runtime logs, locks,
dispatch internals and real .env credentials stay private. Original metadata, raw
transcripts, OGG recordings and available human/AI review revisions are included. One
historical MP3 playback conversion is a duplicate, not an extra conversation.

The issue closeout distinguishes completed delivery, explicitly deferred experiments,
and unresolved known limitations. #12's ending diagnosis and the native SIGSEGV cause
are not claimed fixed. Optional configuration comparison and audio-aligned turn timing
were not performed. #26 remains open for actual form submission; its parent #5 remains open until that acceptance is met.

## Copy into the submission form

Patient Sim is a Python/LiveKit pipeline caller with a local review console. The public
repository includes ten human-reviewed conversations across scheduling, changes,
refills, office information and edge cases, plus the full development-call archive.
Recordings, transcripts, saved observations and configuration provenance remain linked.
The findings report distinguishes observed office behavior, caller defects and uncertainty.
Setup uses the reviewer's own credentials only for new calls; published evidence and
the read-only viewer need no provider access. Architecture and both video links are in
README. Single assessment caller number: +19062567632.
