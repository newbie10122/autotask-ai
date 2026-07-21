#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "== redacted compose validation =="
./scripts/compose-config-redacted.sh >/tmp/autotask-ai-compose-redacted.yml

echo "== migration filename ordering =="
python3 - <<'PY'
from __future__ import annotations

import re
from pathlib import Path

migration_dir = Path("apps/api/migrations")
files = sorted(migration_dir.glob("*.sql"))
if not files:
    raise SystemExit("no migrations found")

seen: set[int] = set()
expected = 1
for path in files:
    match = re.match(r"^(\d{3})_.+\.sql$", path.name)
    if not match:
        raise SystemExit(f"migration does not use NNN_name.sql format: {path.name}")
    number = int(match.group(1))
    if number in seen:
        raise SystemExit(f"duplicate migration number: {number:03d}")
    if number != expected:
        raise SystemExit(f"expected migration {expected:03d}, found {path.name}")
    seen.add(number)
    expected += 1

print(f"validated {len(files)} ordered migrations")
PY

echo "== build API test image =="
docker compose build api

echo "== python compile and pytest =="
docker compose run --rm -T --no-deps \
  -v "$ROOT":/workspace \
  -w /workspace \
  api \
  sh -c 'python -m compileall -q apps/api/app workers && pytest -q'

echo "== static web javascript syntax =="
if ! command -v node >/dev/null 2>&1; then
  echo "node is required for static web syntax validation" >&2
  exit 1
fi
tmp_js="$(mktemp --suffix=.js)"
trap 'rm -f "$tmp_js"' EXIT
awk '/<script>/{flag=1; next} /<\/script>/{flag=0} flag {print}' apps/web/index.html >"$tmp_js"
node --check "$tmp_js"

echo "== browser UI RBAC smoke =="
npm ci
npx playwright install --with-deps chromium
npm run test:web

echo "== CI validation complete =="
