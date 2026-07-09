#!/usr/bin/env bash
set -euo pipefail

tmpfile="$(mktemp)"
cleanup() {
  rm -f "$tmpfile"
}
trap cleanup EXIT

docker compose config >"$tmpfile"

python3 - "$tmpfile" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

secret_keys = {
    "AUTOTASK_SECRET",
    "AUTOTASK_INTEGRATION_CODE",
    "AUTOTASK_API_INTEGRATION_CODE",
    "POSTGRES_PASSWORD",
    "DATABASE_URL",
    "APP_SESSION_SECRET",
}
secret_fragments = ("SECRET", "PASSWORD", "TOKEN", "KEY", "CODE")


def is_secret_key(key: str) -> bool:
    normalized = key.strip().upper()
    return (
        normalized in secret_keys
        or normalized == "DATABASE_URL"
        or any(fragment in normalized for fragment in secret_fragments)
    )


def redact_line(line: str) -> str:
    yaml_match = re.match(r"^(\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:\s*)(.*)$", line)
    if yaml_match and is_secret_key(yaml_match.group(2)):
        return f"{yaml_match.group(1)}{yaml_match.group(2)}{yaml_match.group(3)}REDACTED"

    list_match = re.match(r"^(\s*-\s*)([A-Za-z_][A-Za-z0-9_]*)(=)(.*)$", line)
    if list_match and is_secret_key(list_match.group(2)):
        return f"{list_match.group(1)}{list_match.group(2)}=REDACTED"

    return line


for raw_line in Path(sys.argv[1]).read_text().splitlines():
    print(redact_line(raw_line))
PY
