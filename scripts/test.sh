#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT/core/framework/modules/ess-core/src:$ROOT/core/framework/modules/harness-core/src:$ROOT/core/framework/modules/ekg-core/src:$ROOT/core/framework/modules/query-engine/src:$ROOT/core/framework/modules/sdk-consumption/src:$ROOT/core/framework/modules/conformance-core/src:$ROOT/core/framework/modules/supply-chain-core/src:$ROOT/core/framework/extensions/sdd-adapter/src:$ROOT/core/framework/extensions/memory-adapter/src"

python3 -m unittest discover -s "$ROOT/core/framework/tests" -v
python3 "$ROOT/tools/validation/day_zero_demo_check.py" "$ROOT"
