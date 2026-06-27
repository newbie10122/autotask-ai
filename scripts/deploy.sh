#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
test -f .env || { echo "Create .env from .env.example before deploying."; exit 1; }
docker compose pull || true
docker compose up -d --build
docker compose ps

