# patient-sim

Read docs/CONTRACT.md before changing the caller or evidence model.
This is a standalone personal assessment repository.
Use Python 3.12, uv, and LiveKit Agents 1.8.2 in STT / LLM / TTS pipeline mode.
Only dial the allowlisted assessment number; use synthetic patient facts.
Keep credentials in ignored .env files. Never print or commit them.
Keep evaluator expectations and traps out of the patient prompt.
Preserve raw evidence; label corrected text and unverified claims explicitly.
Run uv run pytest before commits. A local test is not a verified phone call.
Use scripts/gh-personal for this account; never change global GitHub identity.
Use feature branches and the PR template after the initial scaffold.
Review call artifacts before adding them explicitly to the public repository.
Update docs/NOTEBOOK.md with discoveries as they happen. Never invent results.
