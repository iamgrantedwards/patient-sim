#!/usr/bin/env bash
# Independent gates used by both CI jobs and the local verification entry point.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHON_DOTENV_DISABLED=1
export PATH="$PWD/.ci-tools/bin:$PATH"
reports="${REPORT_DIR:-$PWD/reports}"
mkdir -p "$reports"

case "${1:-all}" in
  quality)
    uv run --locked ruff check src tests scripts
    uv run --locked ruff format --check src tests scripts
    uv run --locked pyright
    uv run --locked python scripts/install-ci-tools.py actionlint shellcheck
    actionlint
    shellcheck scripts/*.sh scripts/gh-personal
    ;;
  tests)
    command -v ffmpeg >/dev/null
    command -v ffprobe >/dev/null
    uv run --locked pytest --cov=src --cov-branch --cov-report=term-missing \
      "--cov-report=xml:$reports/coverage.xml" "--cov-report=json:$reports/coverage.json" \
      "--junitxml=$reports/junit.xml"
    ;;
  security)
    uv run --locked python scripts/install-ci-tools.py gitleaks
    gitleaks git --redact --log-opts=--all --report-format=json \
      --report-path="$reports/gitleaks-history.json" .
    # Include pending local files while respecting .gitignore; CI also scans full history.
    scan_dir="$(mktemp -d "${TMPDIR:-/tmp}/patient-sim-scan.XXXXXX")"
    trap 'rm -rf "$scan_dir"' EXIT
    git ls-files --cached --others --exclude-standard -z | \
      tar --null -T - -cf - | tar -xf - -C "$scan_dir"
    gitleaks dir --redact --report-format=json \
      --report-path="$reports/gitleaks-working-tree.json" "$scan_dir"
    rm -rf "$scan_dir"
    trap - EXIT
    uv export --locked --no-emit-project --format=requirements-txt \
      --output-file="$reports/audit-requirements.txt" >/dev/null
    uv run --locked pip-audit --require-hashes --disable-pip \
      --requirement="$reports/audit-requirements.txt" --format=json \
      --output="$reports/dependency-audit.json"
    ;;
  ui)
    command -v ffmpeg >/dev/null
    npm run lint
    npm audit --audit-level=low --json > "$reports/npm-audit.json"
    npm run test:ui
    ;;
  all)
    "$0" quality
    "$0" tests
    "$0" security
    "$0" ui
    ;;
  *) echo "Usage: $0 [quality|tests|security|ui|all]" >&2; exit 2 ;;
esac
