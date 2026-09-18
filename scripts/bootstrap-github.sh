#!/usr/bin/env bash
# Creates labels, milestones, epics and issues for patient-sim.
# Run once, after: gh auth login  (as iamgrantedwards)
#                  gh repo create iamgrantedwards/patient-sim --public --source=. --remote=origin
set -euo pipefail
export GH_CONFIG_DIR="${PATIENT_SIM_GH_CONFIG_DIR:-$HOME/.config/gh-patient-sim}"

REPO="${1:-iamgrantedwards/patient-sim}"
[[ "$REPO" == "iamgrantedwards/patient-sim" ]] || { echo "Unexpected repository" >&2; exit 1; }
[[ "$(gh api user --jq .login)" == "iamgrantedwards" ]] || { echo "Sign in as iamgrantedwards first" >&2; exit 1; }
echo "Bootstrapping $REPO"

label() { gh label create "$1" --repo "$REPO" --color "$2" --description "$3" --force >/dev/null; }

label "epic"              "5319E7" "A phase of work, tracked by child issues"
label "type:task"         "1D76DB" "A unit of work one PR can close"
label "type:finding"      "D93F0B" "A defect observed in the agent under test"
label "type:docs"         "0E8A16" "README, architecture, contract"
label "blocked:external"  "B60205" "Waiting on a third-party account or credential"
label "area:telephony"    "C2E0C6" "SIP, trunk, dispatch, call lifecycle"
label "area:simulator"    "C2E0C6" "Persona, scenarios, turn-taking"
label "area:evidence"     "C2E0C6" "Transcripts, recordings, timing, provenance"
label "area:analysis"     "C2E0C6" "Findings, verification, reporting"

existing_milestones=$(gh api --paginate "repos/$REPO/milestones?state=all&per_page=100" --jq '.[].title')
ms() {
  if ! rg --fixed-strings --line-regexp --quiet -- "$1" <<< "$existing_milestones"; then
    gh api -X POST "repos/$REPO/milestones" -f title="$1" -f description="$2" >/dev/null
  fi
}

ms "M0 Accounts and trunk"   "Twilio DID, Elastic SIP Trunk, LiveKit project, redaction off"
ms "M1 First good call"      "One natural conversation, clean ending, matching recording"
ms "M2 Calibration screen"   "Three configurations on a read-only scenario"
ms "M3 Evidence pipeline"    "Incremental events, reconciled turns, audio-based timing"
ms "M4 Call collection"      "Twelve calls across the scenario set"
ms "M5 Findings"             "Hand-written findings with basis and uncertainty"
ms "M6 Submission"           "README, architecture doc, Looms, public repo"

existing_issues=$(gh issue list --repo "$REPO" --state all --limit 1000 --json title --jq '.[].title')
iss() { # title, body, milestone, labels
  if rg --fixed-strings --line-regexp --quiet -- "$1" <<< "$existing_issues"; then
    echo "  = $1"
    return
  fi
  gh issue create --repo "$REPO" --title "$1" --body "$2" --milestone "$3" --label "$4" >/dev/null
  echo "  + $1"
}

# ---- Epics -----------------------------------------------------------------
iss "Epic: Call infrastructure" \
"Everything required to place a real outbound call and know what happened to it.

Children: trunk registration, dispatch, agent-placed SIP call, lifecycle failure modes.

Done when a call can be placed, its outcome classified, and its failure modes handled
explicitly rather than by timeout." \
"M1 First good call" "epic,area:telephony"

iss "Epic: The patient simulator" \
"The persona, its synthetic record, the scenario set, and turn-taking behaviour.

This is the highest-leverage part of the project: the assessment's first gate is whether
the bot holds a coherent voice conversation." \
"M1 First good call" "epic,area:simulator"

iss "Epic: Evidence pipeline" \
"Transcripts, recordings, timing and provenance — everything a finding is later argued
from.

Design constraint: claims are not outcomes. What the agent said and what actually
happened are recorded separately." \
"M3 Evidence pipeline" "epic,area:evidence"

iss "Epic: Findings and analysis" \
"Turning calls into defensible findings.

Every finding carries an expected behaviour, the basis for expecting it, attribution,
and remaining uncertainty. The optional judge proposes candidates; it never declares a
finding." \
"M5 Findings" "epic,area:analysis"

iss "Epic: Submission" \
"README, architecture doc, bug report, two Looms, public repo." \
"M6 Submission" "epic,type:docs"

# ---- M0 --------------------------------------------------------------------
iss "Buy one Twilio DID and create an Elastic SIP Trunk" \
"One number for every test call; it goes on the submission form in E.164.

Acceptance:
- [ ] DID purchased
- [ ] Elastic SIP Trunk created
- [ ] Trunk registered with LiveKit as an outbound trunk, SIP_OUTBOUND_TRUNK_ID recorded" \
"M0 Accounts and trunk" "type:task,area:telephony,blocked:external"

iss "Confirm recording redaction is OFF at the LiveKit project level" \
"RecordingOptions.redaction defaults to false locally, but a project-level setting
overrides a local false. If redaction is on, the privacy-boundary evidence arrives
scrubbed and those calls are wasted.

Acceptance:
- [ ] Project redaction setting inspected in the console and confirmed off" \
"M0 Accounts and trunk" "type:task,area:evidence,blocked:external"

iss "Create the pgai.us/athena test account and write up what patients are meant to experience" \
"Research, not paperwork. Establishes what correct behaviour looks like, which is the
basis_for_expectation on most findings.

Acceptance:
- [ ] Account created
- [ ] docs/NOTEBOOK.md records what the product claims to do, and what remains unknown
      (does the athena record share state with the assessment line?)" \
"M0 Accounts and trunk" "type:task,blocked:external"

# ---- M1 --------------------------------------------------------------------
iss "Agent places its own SIP call from inside the session" \
"Dispatch preceding SIP does not prove the worker is ready. The agent joins the room,
then calls ctx.api.sip.create_sip_participant with ringing_timeout and max_call_duration.

Acceptance:
- [ ] Dispatch carries the scenario id in metadata
- [ ] Call placed from inside the entrypoint
- [ ] Worker start command documented in the README" \
"M1 First good call" "type:task,area:telephony"

iss "Classify every way a call can end" \
"ended_by in {end_call_tool, failsafe, remote_hangup, dispatch_error, no_answer}, plus
IVR/voicemail detection via AgentSession(ivr_detection=True).

Acceptance:
- [ ] Each outcome produces a record rather than an exception
- [ ] Fixture test covers termination classification" \
"M1 First good call" "type:task,area:telephony"

iss "Patient record: synthetic facts each scenario needs" \
"An underspecified persona improvises differently every call, which destroys the state
sequence and manufactures bugs when the agent correctly balks at inconsistent data.

Acceptance:
- [ ] Medication, pharmacy, prescriber, insurance, availability, reason-for-visit defined
- [ ] Explicit rule for unknowns: say you do not have it handy, never invent
- [ ] Test asserting known_traps and success_criteria never reach the prompt" \
"M1 First good call" "type:task,area:simulator"

iss "EndCallTool with end_instructions=None and graceful negative-outcome closing" \
"EndCallTool already generates a farewell; combined with a patient who has said goodbye
this produces a double goodbye. Refusal and unavailability are valid endings — the
patient must close normally rather than persisting until a failsafe.

Acceptance:
- [ ] end_instructions=None
- [ ] A refused request produces a clean close, verified on a real call" \
"M1 First good call" "type:task,area:simulator"

# ---- M2 --------------------------------------------------------------------
iss "Calibration screen: three configurations on a read-only scenario" \
"Not three STT models — C varies STT and turn detection together, and the default turn
detection is already a trained audio model. This is a screen, not a proof.

MUST use a read-only scenario (hours/location/insurance). Booking during calibration
would populate the patient record before the state sequence starts.

Acceptance:
- [ ] Voice, TTS, LLM, scenario and patient facts held fixed
- [ ] Overlap count, our response delay, their response delay recorded per config
- [ ] One chosen, reason written into ARCHITECTURE.md" \
"M2 Calibration screen" "type:task,area:simulator"

# ---- M3 --------------------------------------------------------------------
iss "Incremental event capture with reconciliation" \
"conversation_item_added already covers both participants; user_input_transcribed is
interim-only and must be reconciled or every remote turn is double-counted. Events
append to events.jsonl as they arrive and finalize on shutdown, so a crash does not
lose the most interesting call.

Acceptance:
- [ ] No duplicated turns, covered by a fixture test
- [ ] A killed process still leaves usable evidence" \
"M3 Evidence pipeline" "type:task,area:evidence"

iss "Timing from audio offsets, in both directions" \
"our_response_ms, their_response_ms and overlap_ms, derived from audio timestamps against
a common recording offset — not from when a callback fired.

Acceptance:
- [ ] Three separate measurements per turn
- [ ] Spot-checked against a recording by ear" \
"M3 Evidence pipeline" "type:task,area:evidence"

iss "Per-call provenance in meta.json" \
"git revision, scenario version, resolved model ids, voice id, turn-handling settings,
caller id, SIP status. Without this, a calibration result cannot be tied to the stack
that produced it.

Acceptance:
- [ ] meta.json written for every call
- [ ] uv.lock committed" \
"M3 Evidence pipeline" "type:task,area:evidence"

iss "Claimed state, consistency, and verified state kept separate" \
"An agent saying 'your appointment is booked' proves a confirmation was spoken. It does
not prove an appointment exists. verified_state is null unless independently confirmed.

Acceptance:
- [ ] Three fields, never collapsed
- [ ] BUGS.md language reflects the distinction" \
"M3 Evidence pipeline" "type:task,area:evidence"

# ---- M4 --------------------------------------------------------------------
iss "Scenario set: 12 calls, with the state sequence as calls 01-06" \
"Baseline transactions, grounding, constraint handling, conversational repair, plus the
two boundary scenarios that matter most in healthcare: medication advice and a request
for another person's information.

Acceptance:
- [ ] >=8 distinct kinds, >=1 safety, >=1 privacy (non-vacuity test)
- [ ] Verification calls ride inside a real errand, not a probe-and-hangup
- [ ] Fallback to independent scenarios documented if cross-call state is unsupported" \
"M4 Call collection" "type:task,area:simulator"

# ---- M5 --------------------------------------------------------------------
iss "Write the first findings by hand, before building any judge" \
"The judge is optional throughout and proposes candidates only. Findings are written by
hand from the first useful calls.

Acceptance:
- [ ] Each finding carries expected_behavior and basis_for_expectation
- [ ] attribution includes unknown and mixed where honest
- [ ] Quote verification passes byte-exact against raw transcripts" \
"M5 Findings" "type:task,area:analysis"

echo "Done."
