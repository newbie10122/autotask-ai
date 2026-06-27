#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
backup="${1:-}"
test -n "$backup" || { echo "Usage: scripts/restore-db.sh data/backups/file.sql"; exit 1; }
test -f "$backup" || { echo "Backup not found: $backup"; exit 1; }
docker compose exec -T postgres psql -U "${POSTGRES_USER:-autotask_ai}" "${POSTGRES_DB:-autotask_ai}" < "$backup"

