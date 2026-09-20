#!/usr/bin/env bash
# Package only after the quality gates have passed.
set -euo pipefail
cd "$(dirname "$0")/.."

# Tests must never load a developer's telephony credentials from .env.
export PYTHON_DOTENV_DISABLED=1

build_dir="${1:-$(mktemp -d "${TMPDIR:-/tmp}/patient-sim-build.XXXXXX")}"
mkdir -p "$build_dir"
build_dir="$(cd "$build_dir" && pwd)"
if [[ -n "$(ls -A "$build_dir")" ]]; then
  echo "Build output directory must be empty: $build_dir" >&2
  exit 1
fi

uv sync --locked --dev
uv run --locked python -m src.caller.dial --scenario smoke --dry-run
uv run --locked python -m src.caller.agent --help
uv build --no-build-isolation --python .venv/bin/python --out-dir "$build_dir"

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
  ./venv/bin/python -I -m src.review --help
  ./venv/bin/python -I - <<'PYSMOKE'
from src.review.server import ASSETS, create_app
from src.review.store import CLOUD_EVIDENCE, CloudVerification
assert all((ASSETS / name).is_file() for name in ("index.html", "app.js", "console.js", "learning.js", "reviews.js", "theme.js", "style.css", "theme.css", "favicon.svg"))
assert create_app().openapi_url is None
for record_path in CLOUD_EVIDENCE.glob("*/verification.json"):
    record = CloudVerification.model_validate_json(record_path.read_text())
    assert record.call_id == record.room_name == record_path.parent.name
    assert (record_path.parent / "cloud.png").is_file()
    assert (record_path.parent / "verification.md").is_file()
assert any(CLOUD_EVIDENCE.glob("*/verification.json")), "Cloud evidence missing from wheel"
print("Installed review server, assets and Cloud evidence verified.")
PYSMOKE
)
printf '\nVerified packages: %s\n' "$build_dir"
