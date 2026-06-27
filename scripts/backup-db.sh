#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p data/backups
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
docker compose exec -T postgres pg_dump -U "${POSTGRES_USER:-autotask_ai}" "${POSTGRES_DB:-autotask_ai}" > "data/backups/autotask_ai_${stamp}.sql"
echo "Wrote data/backups/autotask_ai_${stamp}.sql"

