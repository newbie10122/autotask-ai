#!/usr/bin/env bash
set -euo pipefail
docker compose exec api python -m app.cli run-job --job-name classify_tickets "$@"
