#!/usr/bin/env bash
# Reproduce evolution with a live model backend (requires API keys).
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ -z "${OPENAI_API_KEY:-}" && -z "${ANTHROPIC_API_KEY:-}" ]]; then
  echo "Set OPENAI_API_KEY or ANTHROPIC_API_KEY before running." >&2
  exit 1
fi

if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
  export SRH_BACKEND=anthropic
else
  export SRH_BACKEND=openai
fi

unset SRH_PROPOSER_NOISE
python3 -m runtime.cli evolve --all --generations "${GENERATIONS:-6}"
python3 scripts/plot_results.py
echo "Results written under results/ (live backend — not MOCK)"
