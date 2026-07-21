#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing environment file: $ENV_FILE" >&2
  exit 1
fi

read_env_value() {
  local key="$1"
  local line
  line="$(grep -E "^[[:space:]]*${key}=" "$ENV_FILE" | tail -n 1 || true)"
  if [[ -z "$line" ]]; then
    return 0
  fi
  local value="${line#*=}"
  value="${value%\"}"
  value="${value#\"}"
  value="${value%\'}"
  value="${value#\'}"
  printf '%s' "$value"
}

is_true() {
  case "$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')" in
    true | 1 | yes | y | on) return 0 ;;
    *) return 1 ;;
  esac
}

app_env="$(read_env_value APP_ENV)"
if [[ "$app_env" != "production" ]]; then
  echo "Production auth preflight skipped for APP_ENV=${app_env:-unset}."
  exit 0
fi

app_route_auth_required="$(read_env_value APP_ROUTE_AUTH_REQUIRED)"
if is_true "$app_route_auth_required"; then
  echo "Production auth preflight passed: app-route authentication is required."
  exit 0
fi

external_auth_confirmed="$(read_env_value EXTERNAL_AUTH_CONFIRMED)"
external_auth_description="$(read_env_value EXTERNAL_AUTH_DESCRIPTION)"
if is_true "$external_auth_confirmed" && [[ -n "$external_auth_description" ]]; then
  echo "Production auth preflight passed: external auth boundary is explicitly documented."
  exit 0
fi

cat >&2 <<'EOF'
Production auth preflight failed.

For APP_ENV=production, set APP_ROUTE_AUTH_REQUIRED=true before deployment, or explicitly document the approved external authentication boundary with:

  EXTERNAL_AUTH_CONFIRMED=true
  EXTERNAL_AUTH_DESCRIPTION="Nginx Basic Auth, SSO proxy, or equivalent reviewed boundary"

EOF
exit 1
