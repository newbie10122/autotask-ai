#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

runs="${ANSWER_SAFETY_STREAK_RUNS:-3}"
if ! [[ "$runs" =~ ^[1-9][0-9]*$ ]]; then
  echo "ANSWER_SAFETY_STREAK_RUNS must be a positive integer." >&2
  exit 1
fi

for run in $(seq 1 "$runs"); do
  echo "== answer-safety quality streak run ${run}/${runs} =="
  docker compose run --rm -T --no-deps \
    -v "$PWD":/workspace \
    -w /workspace \
    api pytest -q \
      apps/api/tests/test_guardrails.py \
      apps/api/tests/test_ingestion_rag.py \
      -k "answer or source or injection or secret or verifier or generated_answer or redaction_preserves"
done

echo "answer-safety quality streak complete: ${runs}/${runs} runs passed"
