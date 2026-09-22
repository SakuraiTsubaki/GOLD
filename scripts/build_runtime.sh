#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="${GOLD_RUNTIME_DIR:-$ROOT_DIR/build/pokeemerald-expansion}"
JOBS="${JOBS:-2}"

"$ROOT_DIR/scripts/prepare_runtime.sh"
make -C "$RUNTIME_DIR" -j"$JOBS" -O all
