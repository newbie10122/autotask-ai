from __future__ import annotations

import json
from hashlib import sha256
from typing import Any

from fastapi.encoders import jsonable_encoder

from .config import settings

try:
    import redis
except ImportError:  # pragma: no cover - optional runtime dependency
    redis = None


_client: Any | None = None


def _redis_client() -> Any | None:
    global _client
    if not settings.redis_url or redis is None:
        return None
    if _client is None:
        _client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    return _client


def cache_key(namespace: str, payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    digest = sha256(encoded.encode("utf-8")).hexdigest()
    return f"autotask-ai:{namespace}:{digest}"


def scoped_cache_key(
    namespace: str,
    payload: dict[str, Any],
    *,
    authority_class: str,
    roles: list[str],
    scope: dict[str, Any],
    version: int,
    model_name: str | None = None,
    config: dict[str, Any] | None = None,
) -> str:
    if not authority_class:
        raise ValueError("Scoped cache keys require an authority class.")
    if not roles:
        raise ValueError("Scoped cache keys require at least one role.")
    if not scope:
        raise ValueError("Scoped cache keys require an explicit scope.")
    if version < 1:
        raise ValueError("Scoped cache keys require a positive version.")
    scoped_payload = {
        "payload": payload,
        "scope_contract": {
            "authority_class": authority_class,
            "roles": sorted(roles),
            "scope": scope,
            "version": version,
            "model_name": model_name,
            "config": config or {},
        },
    }
    return cache_key(namespace, scoped_payload)


def cache_get_json(key: str) -> dict[str, Any] | None:
    client = _redis_client()
    if client is None:
        return None
    try:
        value = client.get(key)
    except Exception:
        return None
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def cache_set_json(key: str, value: dict[str, Any], ttl_seconds: int) -> None:
    if ttl_seconds <= 0:
        return
    client = _redis_client()
    if client is None:
        return
    try:
        client.setex(key, ttl_seconds, json.dumps(jsonable_encoder(value), sort_keys=True))
    except Exception:
        return


def cache_delete(key: str) -> None:
    client = _redis_client()
    if client is None:
        return
    try:
        client.delete(key)
    except Exception:
        return


def cache_delete_pattern(pattern: str) -> int:
    client = _redis_client()
    if client is None:
        return 0
    deleted = 0
    try:
        for key in client.scan_iter(match=pattern, count=100):
            deleted += int(client.delete(key) or 0)
    except Exception:
        return deleted
    return deleted


def cache_delete_namespace(namespace: str) -> int:
    return cache_delete_pattern(f"autotask-ai:{namespace}:*")


def invalidate_dashboard_caches() -> dict[str, int]:
    return {
        "ticket_health_summary": cache_delete_namespace("ticket-health-summary"),
        "customer_success_summary": cache_delete_namespace("customer-success-summary"),
        "operations_status": cache_delete_namespace("operations-status"),
    }


def cache_status() -> dict[str, Any]:
    client = _redis_client()
    if client is None:
        return {"enabled": False, "connected": False}
    try:
        return {"enabled": True, "connected": bool(client.ping())}
    except Exception:
        return {"enabled": True, "connected": False}
