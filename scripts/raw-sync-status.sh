#!/usr/bin/env bash
set -euo pipefail

cd /opt/apps/autotask-ai

SESSION_NAME="autotask-ai-sync"
STATUS_DIR="data/status"
STATUS_JSON="${STATUS_DIR}/raw-sync-status.json"
STATUS_TEXT="${STATUS_DIR}/raw-sync-status.txt"

echo "== Raw Sync Status =="
date -Is
echo

if command -v tmux >/dev/null 2>&1 && tmux has-session -t "${SESSION_NAME}" 2>/dev/null; then
  echo "tmux: running (${SESSION_NAME})"
else
  echo "tmux: not running (${SESSION_NAME})"
fi
echo

echo "== Status JSON =="
if [[ -f "${STATUS_JSON}" ]]; then
  cat "${STATUS_JSON}"
else
  echo "No ${STATUS_JSON} found."
fi
echo
echo

echo "== Status Text =="
if [[ -f "${STATUS_TEXT}" ]]; then
  cat "${STATUS_TEXT}"
else
  echo "No ${STATUS_TEXT} found."
fi
echo

echo "== Local DB Counts =="
if docker compose ps postgres >/dev/null 2>&1; then
  docker compose exec -T postgres psql -U autotask_ai -d autotask_ai -c "
SELECT 'companies' AS table_name, COUNT(*) FROM autotask_companies
UNION ALL
SELECT 'tickets', COUNT(*) FROM autotask_tickets
UNION ALL
SELECT 'ticket_notes', COUNT(*) FROM autotask_ticket_notes
UNION ALL
SELECT 'documents', COUNT(*) FROM documents
UNION ALL
SELECT 'active_chunks', COUNT(*) FROM document_chunks WHERE is_active = true
UNION ALL
SELECT 'embeddings', COUNT(*) FROM document_embeddings;
" || true
else
  echo "Postgres service is not available."
fi
echo

echo "== Embedding Backlog =="
docker compose exec -T postgres psql -U autotask_ai -d autotask_ai -c "
SELECT
  COUNT(*) FILTER (WHERE dc.is_active = true) AS active_chunks,
  COUNT(*) FILTER (WHERE dc.is_active = true AND de.id IS NOT NULL) AS active_embedded,
  COUNT(*) FILTER (WHERE dc.is_active = true AND de.id IS NULL) AS active_missing_embeddings
FROM document_chunks dc
LEFT JOIN document_embeddings de ON de.chunk_id = dc.id;
" || true
echo

echo "== Recent Sync Runs =="
docker compose exec -T postgres psql -U autotask_ai -d autotask_ai -c "
SELECT id, sync_type, status, pulled_count, inserted_count, updated_count, failed_count,
       started_at, finished_at, checkpoint
FROM autotask_sync_runs
ORDER BY id DESC
LIMIT 15;
" || true
echo

echo "== Disk Usage =="
df -h .
echo
if [[ -d data ]]; then
  du -h -d 2 data 2>/dev/null | sort -h | tail -30 || true
else
  echo "No data directory found."
fi
echo

echo "== Docker Compose =="
docker compose ps || true
echo

echo "== Autotask Threshold =="
if curl -fsS http://127.0.0.1:5110/health >/dev/null 2>&1; then
  curl -fsS http://127.0.0.1:5110/api/autotask/threshold 2>/dev/null | python3 -c '
import json, sys
try:
    threshold = json.load(sys.stdin).get("threshold", {})
    total = threshold.get("externalRequestThreshold")
    used = threshold.get("currentTimeframeRequestCount")
    remaining = total - used if isinstance(total, int) and isinstance(used, int) else None
    print(json.dumps({
        "externalRequestThreshold": total,
        "requestThresholdTimeframe": threshold.get("requestThresholdTimeframe"),
        "currentTimeframeRequestCount": used,
        "remaining": remaining,
    }, indent=2))
except Exception as exc:
    print(f"Unable to read threshold: {exc}")
' || true
  echo
else
  echo "API is not reachable on http://127.0.0.1:5110."
fi
