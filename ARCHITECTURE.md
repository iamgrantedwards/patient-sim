# Architecture

`dial.py` validates local settings and dispatches a uniquely named room to the local
`AgentServer`. The worker validates dispatch metadata, connects to that room, prepares
`AgentSession` with recording, and creates the SIP participant itself. Twilio provides
the outbound PSTN leg. The caller waits for the remote greeting. The model path is
explicitly STT → text LLM → TTS; no realtime or speech-to-speech model is used.

The initial configuration is Deepgram Flux endpointing, GPT-4.1-mini, and Cartesia
Sonic 3.6 with an explicitly selected voice. This is a starting hypothesis, not a
measured winner. Calibration is still pending and uses the same read-only office
information scenario. The alternate `default` detector option pins LiveKit's
`v1-mini` audio turn model for reproducibility. Interruption handling uses VAD;
preemptive generation, noise cancellation, and automatic gain control are off initially.

The worker journals raw events immediately. Committed message IDs determine dialogue
turns; STT partials never create duplicate committed turns. The session-end hook runs
after SDK session closure, copies the SDK's stereo OGG before temporary cleanup, and
verifies container and decoding with ffmpeg tools. Speech timing metrics remain null
until measured against that audio timeline. An abrupt process kill preserves journaled
events but does not yet guarantee an exported recording.

The built-in end-call tool has no generated closing instruction; the patient prompt
handles the farewell. Refusal/unavailability can end normally. Server call duration,
ring timeout, a local watchdog, and a committed-turn cap bound failures. Initial SDK
source inspection showed `ivr_detection=True` proactively generates replies after
silence and exposes DTMF; it is not a standalone voicemail classifier. It remains off
until the actual assessment line is inspected.

## Verification limits

Offline tests exercise config rejection, prompt separation, event recovery and
reconciliation, recording decode, and mocked lifecycle ordering/limits. No test result
in this repository currently establishes successful SIP connection, natural pacing,
correct voice selection, or a real conversation. Those require the first live call.
