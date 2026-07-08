#!/usr/bin/env bash
set -euo pipefail

cd /opt/apps/autotask-ai

SESSION_NAME="autotask-ai-sync"
LOG_DIR="data/logs/sync"
STATUS_DIR="data/status"
STATUS_JSON="${STATUS_DIR}/raw-sync-status.json"
STATUS_TEXT="${STATUS_DIR}/raw-sync-status.txt"
STOP_FILE="${STATUS_DIR}/STOP_RAW_SYNC"
RUN_ID="$(date -u +%Y%m%d-%H%M%S)"
LOG_FILE="${LOG_DIR}/raw-sync-${RUN_ID}.log"

mkdir -p "${LOG_DIR}" "${STATUS_DIR}"

RAW_SYNC_TICKET_BATCH_SIZE="${RAW_SYNC_TICKET_BATCH_SIZE:-5000}"
RAW_SYNC_NOTE_BATCH_SIZE="${RAW_SYNC_NOTE_BATCH_SIZE:-5000}"
RAW_SYNC_COMPANY_BATCH_SIZE="${RAW_SYNC_COMPANY_BATCH_SIZE:-1000}"
RAW_SYNC_MAX_CYCLES="${RAW_SYNC_MAX_CYCLES:-12}"
RAW_SYNC_SLEEP_SECONDS="${RAW_SYNC_SLEEP_SECONDS:-60}"
RAW_SYNC_MIN_FREE_GB="${RAW_SYNC_MIN_FREE_GB:-50}"
RAW_SYNC_STOP_AT_THRESHOLD_REMAINING="${RAW_SYNC_STOP_AT_THRESHOLD_REMAINING:-500}"

STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
LAST_TICKET_SYNC="{}"
LAST_TICKET_NOTE_SYNC="{}"
LAST_COMPANY_SYNC="{}"
LAST_ERROR="null"

log() {
  printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "${LOG_FILE}"
}

json_string() {
  python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().strip()))'
}

collect_counts_json() {
  docker compose exec -T postgres psql -U autotask_ai -d autotask_ai -At -F $'\t' -c "
SELECT 'companies', COUNT(*) FROM autotask_companies
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
" 2>/dev/null | python3 -c '
import json, sys
out = {"companies": 0, "tickets": 0, "ticket_notes": 0, "documents": 0, "active_chunks": 0, "embeddings": 0}
for line in sys.stdin:
    if not line.strip():
        continue
    key, value = line.rstrip("\n").split("\t", 1)
    out[key] = int(value)
print(json.dumps(out))
' || printf '{"companies":0,"tickets":0,"ticket_notes":0,"documents":0,"active_chunks":0,"embeddings":0}'
}

collect_backlog_json() {
  docker compose exec -T postgres psql -U autotask_ai -d autotask_ai -At -F $'\t' -c "
SELECT
  COUNT(*) FILTER (WHERE dc.is_active = true) AS active_chunks,
  COUNT(*) FILTER (WHERE dc.is_active = true AND de.id IS NOT NULL) AS active_embedded,
  COUNT(*) FILTER (WHERE dc.is_active = true AND de.id IS NULL) AS active_missing_embeddings
FROM document_chunks dc
LEFT JOIN document_embeddings de ON de.chunk_id = dc.id;
" 2>/dev/null | python3 -c '
import json, sys
line = sys.stdin.read().strip()
if not line:
    print(json.dumps({"active_chunks": 0, "active_embedded": 0, "active_missing_embeddings": 0}))
else:
    values = line.split("\t")
    print(json.dumps({"active_chunks": int(values[0]), "active_embedded": int(values[1]), "active_missing_embeddings": int(values[2])}))
' || printf '{"active_chunks":0,"active_embedded":0,"active_missing_embeddings":0}'
}

free_gb() {
  df -BG . | awk 'NR==2 {gsub("G","",$4); print $4}'
}

threshold_json() {
  curl -fsS http://127.0.0.1:5110/api/autotask/threshold 2>/dev/null | python3 -c '
import json, sys
try:
    payload = json.load(sys.stdin).get("threshold", {})
    total = payload.get("externalRequestThreshold")
    used = payload.get("currentTimeframeRequestCount")
    remaining = total - used if isinstance(total, int) and isinstance(used, int) else None
    print(json.dumps({
        "externalRequestThreshold": total,
        "requestThresholdTimeframe": payload.get("requestThresholdTimeframe"),
        "currentTimeframeRequestCount": used,
        "remaining": remaining,
    }))
except Exception:
    print(json.dumps({
        "externalRequestThreshold": None,
        "requestThresholdTimeframe": None,
        "currentTimeframeRequestCount": None,
        "remaining": None,
    }))
'
}

write_status() {
  local status="$1"
  local cycle="$2"
  local step="$3"
  local error_value="${4:-null}"
  local counts backlog free threshold
  counts="$(collect_counts_json)"
  backlog="$(collect_backlog_json)"
  free="$(free_gb)"
  threshold="$(threshold_json)"
  python3 - "$STATUS_JSON" "$STATUS_TEXT" <<PY
import json, sys
status_path, text_path = sys.argv[1], sys.argv[2]
payload = {
    "started_at": "${STARTED_AT}",
    "updated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "session": "${SESSION_NAME}",
    "status": "${status}",
    "cycle": int("${cycle}"),
    "max_cycles": int("${RAW_SYNC_MAX_CYCLES}"),
    "current_step": "${step}",
    "last_error": json.loads("""${error_value}"""),
    "last_ticket_sync": json.loads("""${LAST_TICKET_SYNC}"""),
    "last_ticket_note_sync": json.loads("""${LAST_TICKET_NOTE_SYNC}"""),
    "last_company_sync": json.loads("""${LAST_COMPANY_SYNC}"""),
    "local_counts": json.loads("""${counts}"""),
    "embedding_backlog": json.loads("""${backlog}"""),
    "disk": {"free_gb": int("${free}"), "min_free_gb": int("${RAW_SYNC_MIN_FREE_GB}")},
    "autotask_threshold": json.loads("""${threshold}"""),
}
with open(status_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2, sort_keys=True)
    f.write("\n")
with open(text_path, "w", encoding="utf-8") as f:
    f.write(f"status: {payload['status']}\n")
    f.write(f"updated_at: {payload['updated_at']}\n")
    f.write(f"cycle: {payload['cycle']} / {payload['max_cycles']}\n")
    f.write(f"current_step: {payload['current_step']}\n")
    f.write(f"last_error: {payload['last_error']}\n")
    f.write(f"counts: {payload['local_counts']}\n")
    f.write(f"embedding_backlog: {payload['embedding_backlog']}\n")
    f.write(f"disk_free_gb: {payload['disk']['free_gb']}\n")
    f.write(f"threshold_remaining: {payload['autotask_threshold'].get('remaining')}\n")
PY
}

run_step() {
  local label="$1"
  shift
  write_status "running" "${cycle}" "${label}"
  log "Starting ${label}: $*"
  local output
  if ! output="$("$@" 2>&1 | tee -a "${LOG_FILE}")"; then
    LAST_ERROR="$(printf '%s' "${output}" | tail -20 | json_string)"
    write_status "failed" "${cycle}" "${label}" "${LAST_ERROR}"
    log "Failed ${label}"
    exit 1
  fi
  log "Completed ${label}"
  local parsed
  parsed="$(printf '%s' "${output}" | python3 -c 'import json,sys; text=sys.stdin.read(); start=text.find("{"); end=text.rfind("}"); print(json.dumps({}) if start < 0 or end < start else json.dumps(json.loads(text[start:end+1])))' 2>/dev/null || printf '{}')"
  case "${label}" in
    tickets*) LAST_TICKET_SYNC="${parsed}" ;;
    ticket-notes*) LAST_TICKET_NOTE_SYNC="${parsed}" ;;
    companies*) LAST_COMPANY_SYNC="${parsed}" ;;
  esac
  write_status "running" "${cycle}" "${label}"
}

load_env() {
  set -a
  # shellcheck disable=SC1091
  [[ -f .env ]] && source .env
  set +a
  if [[ -z "${AUTOTASK_INTEGRATION_CODE:-}" && -n "${AUTOTASK_API_INTEGRATION_CODE:-}" ]]; then
    AUTOTASK_INTEGRATION_CODE="${AUTOTASK_API_INTEGRATION_CODE}"
    export AUTOTASK_INTEGRATION_CODE
  fi
}

validate_env() {
  local missing=()
  for name in AUTOTASK_BASE_URL AUTOTASK_USERNAME AUTOTASK_SECRET AUTOTASK_INTEGRATION_CODE; do
    if [[ -z "${!name:-}" ]]; then
      missing+=("${name}")
    fi
  done
  if (( ${#missing[@]} > 0 )); then
    log "Missing required Autotask environment variables: ${missing[*]}"
    LAST_ERROR="$(printf 'Missing required Autotask environment variables: %s' "${missing[*]}" | json_string)"
    write_status "failed" 0 "validate-env" "${LAST_ERROR}"
    exit 1
  fi
}

validate_runtime() {
  docker compose ps --status running | grep -q "autotask-ai-api" || {
    LAST_ERROR="$(printf 'Docker Compose API service is not running.' | json_string)"
    write_status "failed" 0 "validate-docker" "${LAST_ERROR}"
    exit 1
  }
  curl -fsS http://127.0.0.1:5110/health >/dev/null
  curl -fsS http://127.0.0.1:5110/api/autotask/threshold >/dev/null
}

should_stop_for_threshold() {
  local remaining
  remaining="$(threshold_json | python3 -c 'import json,sys; value=json.load(sys.stdin).get("remaining"); print("" if value is None else value)' 2>/dev/null || true)"
  [[ -n "${remaining}" && "${remaining}" != "None" && "${remaining}" -lt "${RAW_SYNC_STOP_AT_THRESHOLD_REMAINING}" ]]
}

log "Raw sync loop starting. Log: ${LOG_FILE}"
write_status "running" 0 "starting"
load_env
validate_env
validate_runtime

for ((cycle=1; cycle<=RAW_SYNC_MAX_CYCLES; cycle++)); do
  write_status "running" "${cycle}" "cycle-start"
  log "Cycle ${cycle}/${RAW_SYNC_MAX_CYCLES} starting"

  if [[ -f "${STOP_FILE}" ]]; then
    log "Stop file detected before cycle ${cycle}."
    write_status "stopped" "${cycle}" "stop-file"
    exit 0
  fi

  if (( "$(free_gb)" < RAW_SYNC_MIN_FREE_GB )); then
    log "Stopping because free disk is below ${RAW_SYNC_MIN_FREE_GB} GB."
    write_status "stopped" "${cycle}" "disk-threshold"
    exit 0
  fi

  if should_stop_for_threshold; then
    log "Stopping because Autotask threshold remaining is below ${RAW_SYNC_STOP_AT_THRESHOLD_REMAINING}."
    write_status "stopped" "${cycle}" "autotask-threshold"
    exit 0
  fi

  run_step "tickets" ./scripts/sync-tickets.sh --limit "${RAW_SYNC_TICKET_BATCH_SIZE}"
  [[ -f "${STOP_FILE}" ]] && { write_status "stopped" "${cycle}" "stop-file"; exit 0; }

  run_step "ticket-notes" ./scripts/sync-ticket-notes.sh --limit "${RAW_SYNC_NOTE_BATCH_SIZE}"
  [[ -f "${STOP_FILE}" ]] && { write_status "stopped" "${cycle}" "stop-file"; exit 0; }

  run_step "companies" ./scripts/sync-companies.sh --limit "${RAW_SYNC_COMPANY_BATCH_SIZE}"

  log "Cycle ${cycle}/${RAW_SYNC_MAX_CYCLES} complete"
  write_status "running" "${cycle}" "sleeping"
  if (( cycle < RAW_SYNC_MAX_CYCLES )); then
    sleep "${RAW_SYNC_SLEEP_SECONDS}"
  fi
done

log "Raw sync loop completed after ${RAW_SYNC_MAX_CYCLES} cycles."
write_status "completed" "${RAW_SYNC_MAX_CYCLES}" "completed"
