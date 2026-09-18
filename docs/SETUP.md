# Personal account setup

GitHub CLI is authenticated as `iamgrantedwards` using a separate configuration profile.
Run `./scripts/gh-personal auth status` to inspect that profile. Git commit identity is
set only in this checkout, using the account's GitHub noreply address.

## Needed before the first real call

1. Create a personal [LiveKit Cloud](https://cloud.livekit.io/) account and project.
   Keep its project URL, API key and API secret in the local `.env` file only.
2. Create a personal [Twilio](https://www.twilio.com/) account. Review any payment or
   trial restrictions before buying one voice-capable US number or adding credit.
   Retain this same caller ID for the submission.
3. Follow LiveKit's [Twilio Elastic SIP Trunk setup](https://docs.livekit.io/telephony/start/providers/twilio/).
   Configure outbound termination credentials and register the outbound trunk with
   LiveKit. Put its `ST_...` ID in `.env` along with the purchased caller number.
4. Choose one Cartesia voice supported by LiveKit Inference and put its voice ID in
   `TTS_VOICE`. Hold the voice fixed during calibration.
5. Inspect project recording/redaction settings before using synthetic test data.
   A local `redaction=False` does not override a project-level redaction requirement.
6. Confirm available balances and current usage rates in both accounts. Do not treat
   the early planning estimate as a verified price or authorize an ongoing paid plan.

No OpenAI API key is needed for the call path. LiveKit Inference handles its LLM.
The optional judge is not implemented or needed for the first milestone.

Create the ignored file without exposing keys in chat or shell history:

```sh
cp .env.example .env
```

Edit `.env` locally. Do not paste its contents into chat. Only report which setup step
is complete. The assessment line is the sole allowed destination.
