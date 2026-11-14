#!/bin/bash
# Overnight batch (29-30 Oct 2026): repeat runs for repeatability + probe repeats.
# Settings identical to the first runs; expectations and keys unchanged.
cd "$(dirname "$0")"
source ../dpp-prep-mcp/.venv/bin/activate
export DPP_PREP="$PWD/../dpp-prep-mcp/vendor/dpp-prep-08d5840"
LOG="$PWD/out/overnight_$(date +%Y%m%d-%H%M%S).log"
echo "log: $LOG"
{
  echo "=== $(date) START"
  # 1) agent probe repeats (different seeds), qwen3.5:9b
  cd ../dpp-prep-mcp
  for seed in 1 2; do
    echo "=== $(date) probe qwen3.5:9b seed $seed"
    python probe/agent_probe.py --model qwen3.5:9b --seed $seed
  done
  cd ../dpp-real
  # 2) real documents, second execution (same settings: checks repeatability)
  for m in qwen3.5:4b gemma4:12b qwen3.5:9b; do
    echo "=== $(date) real documents, second execution: $m"
    python run_real.py --extractor ollama --model "$m"
  done
  echo "=== $(date) ALL DONE"
} >> "$LOG" 2>&1