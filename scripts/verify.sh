#!/usr/bin/env bash
# The same offline verification path is used locally and by GitHub Actions.
set -euo pipefail
cd "$(dirname "$0")/.."

# Tests must never load a developer's telephony credentials from .env.
export PYTHON_DOTENV_DISABLED=1
command -v ffmpeg >/dev/null
command -v ffprobe >/dev/null

build_dir="${1:-$(mktemp -d "${TMPDIR:-/tmp}/patient-sim-build.XXXXXX")}"
mkdir -p "$build_dir"
build_dir="$(cd "$build_dir" && pwd)"
if [[ -n "$(ls -A "$build_dir")" ]]; then
  echo "Build output directory must be empty: $build_dir" >&2
  exit 1
fi

uv sync --locked --dev
if [[ -n "${JUNIT_XML:-}" ]]; then
  mkdir -p "$(dirname "$JUNIT_XML")"
  uv run --locked pytest "--junitxml=$JUNIT_XML"
else
  uv run --locked pytest
fi
uv run --locked python -m src.caller.dial --scenario smoke --dry-run
uv run --locked python -m src.caller.agent --help
uv build --out-dir "$build_dir"

# Install the wheel into a fresh environment with locked production dependencies.
# -I and a different working directory prevent imports from this source checkout.
smoke_dir="$(mktemp -d "${TMPDIR:-/tmp}/patient-sim-smoke.XXXXXX")"
trap 'rm -rf "$smoke_dir"' EXIT
UV_PROJECT_ENVIRONMENT="$smoke_dir/venv" uv sync --locked --no-dev --no-install-project
uv pip install --python "$smoke_dir/venv/bin/python" --no-deps "$build_dir"/*.whl
(
  cd "$smoke_dir"
  ./venv/bin/python -I -m src.caller.dial --scenario smoke --dry-run
  ./venv/bin/python -I -m src.caller.agent --help
)
printf '\nVerified packages: %s\n' "$build_dir"
