#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export SRH_BACKEND=mock
unset SRH_PROPOSER_NOISE
python3 -m runtime.cli evolve --all --generations 8
python3 scripts/plot_results.py
