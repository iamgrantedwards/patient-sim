# Account and environment setup

The maintainer uses `scripts/gh-personal` with an isolated GitHub CLI profile and
repository-local commit identity. A new reviewer does not inherit that authentication
and does not need it to clone the public repository or inspect published evidence.
Use your own provider accounts for new calls or model assessments. No credentials
are included or transferred with the repository.

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
   `TTS_VOICE`. Keep the voice fixed for comparable calls; configuration comparison is deferred.
5. Inspect project recording/redaction settings before using synthetic test data.
   A local `redaction=False` does not override a project-level redaction requirement.
6. Confirm available balances and current usage rates in both accounts. Do not treat
   the early planning estimate as a verified price or authorize an ongoing paid plan.

No direct OpenAI API key is required for either the caller or optional AI assessment:
both use LiveKit Inference. The caller defaults to `openai/gpt-4.1-mini`; the separate
transcript judge defaults to `JUDGE_MODEL=gpt-4.1` (`openai/gpt-4.1`). LiveKit usage and
Twilio telephony charges are separate. Check their dashboards for current balances;
this repository makes no remaining-credit guarantee.

Viewing local evidence and saving human reviews need no provider credentials.
`--enable-assessments` loads LiveKit credentials from the environment/project `.env`
and enables explicitly requested transcript analysis. It does not require the SIP
trunk or place a phone call. `--enable-calls` requires the full caller configuration.
See [EVALUATION.md](EVALUATION.md) for exactly what is sent to the judge.

Create the ignored file without exposing keys in chat or shell history:

```sh
# Only when creating the file for the first time; do not overwrite existing credentials.
cp -n .env.example .env
```

Edit `.env` locally. Do not paste its contents into chat. Only report which setup step
is complete. The assessment line is the sole allowed destination.

Use the README's locked installation and dry run before a real call. For review with
optional AI analysis, run `uv run python -m src.review --enable-reviews --enable-assessments`.
Add `--enable-calls` only when you want the explicitly confirmed outbound controls.
A fresh reviewer must also obtain the published call artifacts; ignored local `calls/`
files do not arrive through a clone until selected evidence is deliberately committed.
