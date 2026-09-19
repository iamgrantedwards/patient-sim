#!/usr/bin/env bash
# Full local equivalent of all required CI gates, followed by packaging.
set -euo pipefail
cd "$(dirname "$0")/.."
uv sync --locked --dev
npm ci --ignore-scripts
./scripts/check.sh all
./scripts/build.sh "$@"
