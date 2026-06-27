#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
docker compose ps
curl -fsS http://127.0.0.1:${API_PORT:-5110}/health && echo

