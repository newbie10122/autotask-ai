#!/usr/bin/env bash
set -euo pipefail

cd /opt/apps/autotask-ai

SESSION_NAME="autotask-ai-sync"

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is required but was not found in PATH." >&2
  exit 1
fi

if tmux has-session -t "${SESSION_NAME}" 2>/dev/null; then
  echo "tmux session '${SESSION_NAME}' already exists. Refusing to start a second raw sync."
  echo "Attach with: tmux attach -t ${SESSION_NAME}"
  exit 1
fi

mkdir -p data/logs/sync data/status
rm -f data/status/STOP_RAW_SYNC

tmux new-session -d -s "${SESSION_NAME}" "cd /opt/apps/autotask-ai && ./scripts/raw-sync-loop.sh"

echo "Started tmux session: ${SESSION_NAME}"
echo "Attach with: tmux attach -t ${SESSION_NAME}"
echo "Detach from tmux with: Ctrl+b, then d"
echo "Check status with: ./scripts/raw-sync-status.sh"
echo "Stop gracefully with: ./scripts/stop-raw-sync.sh"
