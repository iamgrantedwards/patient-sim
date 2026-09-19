#!/usr/bin/env bash
# Full local equivalent of all required CI gates, followed by packaging.
set -euo pipefail
cd "$(dirname "$0")/.."
uv sync --locked --dev
./scripts/check.sh all
./scripts/build.sh "$@"
