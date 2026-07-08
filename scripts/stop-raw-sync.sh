#!/usr/bin/env bash
set -euo pipefail

cd /opt/apps/autotask-ai
mkdir -p data/status
touch data/status/STOP_RAW_SYNC

echo "Created data/status/STOP_RAW_SYNC."
echo "The raw sync loop will stop after the current batch finishes."
echo "Optional force stop: tmux kill-session -t autotask-ai-sync"
