#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -z "${BOOTSTRAP_APP_PASSWORD:-}" ]]; then
  echo "Set BOOTSTRAP_APP_PASSWORD to the user's temporary password before running." >&2
  exit 1
fi

docker compose run --rm -T api python -m app.user_admin "$@"
