#!/usr/bin/env bash
# Simulate inputs, run the bridge, and rebuild the interactive page.
set -euo pipefail
SEED="${1:-2026}"
python bridge/bridge.py --seed "$SEED" --out results
python bridge/build_page.py results/bridge_results.json
