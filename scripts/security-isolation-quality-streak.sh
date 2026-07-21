#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

runs="${SECURITY_ISOLATION_STREAK_RUNS:-3}"
if ! [[ "$runs" =~ ^[1-9][0-9]*$ ]]; then
  echo "SECURITY_ISOLATION_STREAK_RUNS must be a positive integer." >&2
  exit 1
fi

for run in $(seq 1 "$runs"); do
  echo "== security-isolation quality streak run ${run}/${runs} =="
  docker compose run --rm -T --no-deps \
    -v "$PWD":/workspace \
    -w /workspace \
    api pytest -q \
      apps/api/tests/test_api.py \
      apps/api/tests/test_ingestion_rag.py \
      apps/api/tests/test_guardrails.py \
      -k "auth or scope or audit or route or rbac or scoped_cache or cache_consumers or export_routes or feedback or verifier or source_sufficiency or realtime or local_capability or production_auth"
done

echo "security-isolation quality streak complete: ${runs}/${runs} runs passed"
