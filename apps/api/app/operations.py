from __future__ import annotations

import os
import shutil
import socket
import time
from datetime import UTC, datetime, time as clock_time
from math import ceil
from typing import Any, Callable

import httpx
from fastapi.encoders import jsonable_encoder
from psycopg.types.json import Jsonb

from .autotask import AutotaskReadOnlyClient
from .cache import cache_get_json, cache_set_json, invalidate_dashboard_caches, scoped_cache_key
from .config import settings as app_settings
from .customer_success import capture_customer_success_score_snapshot, cleanup_customer_success_score_snapshots
from .db import db_connection, init_schema
from .documents import create_documents_from_tickets, noise_report, reclassify_chunks
from .embeddings import run_embedding_batch
from .sync import (
    sync_companies,
    sync_open_ticket_history_gaps,
    sync_open_ticket_time_entry_gaps,
    sync_recent,
    sync_status_sample_ticket_history,
    sync_ticket_history,
    sync_ticket_history_gaps,
    sync_ticket_time_entry_gaps,
    sync_ticket_note_gaps,
    sync_ticket_notes,
    sync_tickets,
    sync_time_entries,
    sync_waiting_ticket_history,
)
from .ticket_analytics import classify_tickets, sync_reference_data


DEFAULT_SETTINGS: dict[str, Any] = {
    "sync_enabled": True,
    "recent_sync_enabled": True,
    "recent_sync_interval_minutes": 15,
    "raw_backfill_enabled": False,
    "raw_backfill_batch_tickets": 5000,
    "raw_backfill_batch_notes": 5000,
    "ticket_note_gap_batch_size": 25,
    "raw_backfill_batch_time_entries": 5000,
    "ticket_time_entry_gap_batch_size": 100,
    "open_ticket_time_entry_gap_batch_size": 25,
    "open_ticket_time_entry_gaps_enabled": True,
    "raw_backfill_batch_ticket_history": 250,
    "targeted_waiting_ticket_history_batch_size": 25,
    "status_sample_ticket_history_batch_size": 25,
    "ticket_history_gap_batch_size": 100,
    "open_ticket_history_gap_batch_size": 25,
    "open_ticket_history_gaps_enabled": True,
    "ticket_time_entry_gaps_enabled": True,
    "ticket_history_gaps_enabled": True,
    "related_data_work_plan_enabled": False,
    "raw_backfill_max_cycles_per_run": 4,
    "document_build_enabled": False,
    "document_build_batch_size": 5000,
    "ticket_classification_enabled": True,
    "ticket_classification_batch_size": 10000,
    "chunk_reclassification_enabled": True,
    "chunk_reclassification_batch_size": 10000,
    "embedding_enabled": False,
    "embedding_batch_size": 500,
    "embedding_quiet_hours_only": True,
    "embedding_quiet_hours_start": "19:00",
    "embedding_quiet_hours_end": "06:00",
    "embedding_max_cpu_note": "CPU-only Ollama; keep batches small",
    "nightly_pipeline_enabled": True,
    "nightly_pipeline_time": "02:00",
    "customer_success_snapshot_enabled": True,
    "customer_success_snapshot_batch_size": 100,
    "customer_success_snapshot_retention_days": 180,
    "autotask_threshold_min_remaining": 500,
    "min_free_disk_gb": 50,
    "global_pause": False,
}

SETTING_LIMITS: dict[str, tuple[int, int]] = {
    "recent_sync_interval_minutes": (1, 1440),
    "raw_backfill_batch_tickets": (1, 5000),
    "raw_backfill_batch_notes": (1, 5000),
    "ticket_note_gap_batch_size": (1, 100),
    "raw_backfill_batch_time_entries": (1, 5000),
    "ticket_time_entry_gap_batch_size": (1, 100),
    "open_ticket_time_entry_gap_batch_size": (1, 100),
    "raw_backfill_batch_ticket_history": (1, 500),
    "targeted_waiting_ticket_history_batch_size": (1, 100),
    "status_sample_ticket_history_batch_size": (1, 100),
    "ticket_history_gap_batch_size": (1, 100),
    "open_ticket_history_gap_batch_size": (1, 100),
    "raw_backfill_max_cycles_per_run": (1, 10),
    "document_build_batch_size": (1, 5000),
    "ticket_classification_batch_size": (1, 10000),
    "chunk_reclassification_batch_size": (1, 10000),
    "embedding_batch_size": (1, 500),
    "customer_success_snapshot_batch_size": (1, 500),
    "customer_success_snapshot_retention_days": (1, 730),
    "autotask_threshold_min_remaining": (0, 100000),
    "min_free_disk_gb": (0, 100000),
}

DEFAULT_JOBS: dict[str, dict[str, Any]] = {
    "recent_sync": {"enabled": True, "cadence_seconds": 15 * 60, "schedule": "every 15 minutes"},
    "raw_backfill_tickets": {"enabled": False, "cadence_seconds": 60 * 60, "schedule": "hourly when enabled"},
    "raw_backfill_ticket_notes": {"enabled": False, "cadence_seconds": 60 * 60, "schedule": "hourly when enabled"},
    "ticket_note_gaps": {
        "enabled": False,
        "cadence_seconds": 60 * 60,
        "schedule": "manual bounded ticket-note gap pull",
    },
    "raw_backfill_time_entries": {"enabled": False, "cadence_seconds": 60 * 60, "schedule": "hourly when enabled"},
    "ticket_time_entry_gaps": {
        "enabled": True,
        "cadence_seconds": 60 * 60,
        "schedule": "hourly bounded estate TimeEntries gap pull",
    },
    "open_ticket_time_entry_gaps": {
        "enabled": True,
        "cadence_seconds": 15 * 60,
        "schedule": "every 15 minutes bounded open-ticket TimeEntries gap pull",
    },
    "raw_backfill_ticket_history": {"enabled": False, "cadence_seconds": 60 * 60, "schedule": "hourly when enabled"},
    "targeted_waiting_ticket_history": {
        "enabled": False,
        "cadence_seconds": 60 * 60,
        "schedule": "manual bounded waiting-status TicketHistory pull",
    },
    "status_sample_ticket_history": {
        "enabled": False,
        "cadence_seconds": 60 * 60,
        "schedule": "manual bounded per-status TicketHistory sample pull",
    },
    "ticket_history_gaps": {
        "enabled": True,
        "cadence_seconds": 60 * 60,
        "schedule": "hourly bounded estate TicketHistory gap pull",
    },
    "open_ticket_history_gaps": {
        "enabled": True,
        "cadence_seconds": 15 * 60,
        "schedule": "every 15 minutes bounded open-ticket TicketHistory gap pull",
    },
    "related_data_work_plan": {
        "enabled": False,
        "cadence_seconds": 60 * 60,
        "schedule": "manual bounded related-data work-plan wrapper",
    },
    "raw_backfill_companies": {"enabled": False, "cadence_seconds": 60 * 60, "schedule": "hourly when enabled"},
    "sync_reference_data": {"enabled": True, "cadence_seconds": 6 * 60 * 60, "schedule": "every 6 hours"},
    "classify_tickets": {"enabled": True, "cadence_seconds": 30 * 60, "schedule": "every 30 minutes"},
    "build_documents": {"enabled": False, "cadence_seconds": 30 * 60, "schedule": "every 30 minutes when enabled"},
    "reclassify_chunks": {"enabled": True, "cadence_seconds": 60 * 60, "schedule": "hourly"},
    "run_embeddings": {"enabled": False, "cadence_seconds": 30 * 60, "schedule": "quiet-hours batches when enabled"},
    "nightly_pipeline": {"enabled": True, "cadence_seconds": 24 * 60 * 60, "schedule": "daily 02:00"},
    "customer_success_score_snapshot": {"enabled": True, "cadence_seconds": 24 * 60 * 60, "schedule": "daily local score snapshot"},
}

AUTOTASK_JOBS = {
    "recent_sync",
    "raw_backfill_tickets",
    "raw_backfill_ticket_notes",
    "ticket_note_gaps",
    "raw_backfill_time_entries",
    "ticket_time_entry_gaps",
    "open_ticket_time_entry_gaps",
    "raw_backfill_ticket_history",
    "targeted_waiting_ticket_history",
    "status_sample_ticket_history",
    "ticket_history_gaps",
    "open_ticket_history_gaps",
    "related_data_work_plan",
    "raw_backfill_companies",
}
RAW_BACKFILL_JOBS = {
    "raw_backfill_tickets",
    "raw_backfill_ticket_notes",
    "raw_backfill_time_entries",
    "raw_backfill_ticket_history",
    "raw_backfill_companies",
}
MUTATES_CHUNKS = {"build_documents", "reclassify_chunks"}
OPERATIONS_STATUS_CACHE_VERSION = 6
SYNC_RECOVERY_REQUIRED_JOBS: tuple[str, ...] = (
    "recent_sync",
    "open_ticket_time_entry_gaps",
    "open_ticket_history_gaps",
    "ticket_time_entry_gaps",
    "ticket_history_gaps",
    "sync_reference_data",
    "classify_tickets",
    "reclassify_chunks",
    "nightly_pipeline",
)


def operations_status_cache_key(
    *,
    authority_class: str = "outer-auth",
    roles: list[str] | None = None,
    scope: dict[str, Any] | None = None,
) -> str:
    return scoped_cache_key(
        "operations-status",
        {"view": "operations-status"},
        authority_class=authority_class,
        roles=roles or ["OuterAuth"],
        scope=scope or {"global": True, "app_route_auth_required": False},
        version=OPERATIONS_STATUS_CACHE_VERSION,
        config={"ttl_seconds": app_settings.operations_status_cache_ttl_seconds},
    )


def invalidate_operations_status_cache() -> None:
    invalidate_dashboard_caches()["operations_status"]


def _coverage_percent(covered: int, total: int) -> float:
    return round((covered / total) * 100, 2) if total else 100.0


def _operations_coverage(row: dict[str, Any]) -> dict[str, Any]:
    open_tickets = int(row.get("open_tickets") or 0)
    with_time = int(row.get("open_tickets_with_time_entries") or 0)
    with_history = int(row.get("open_tickets_with_history") or 0)
    return {
        "open_tickets": open_tickets,
        "labor": {
            "with_time_entries": with_time,
            "without_time_entries": int(row.get("open_tickets_without_time_entries") or 0),
            "checked": int(row.get("open_tickets_checked_for_time_entries") or 0),
            "checked_empty": int(row.get("open_tickets_checked_empty_time_entries") or 0),
            "unchecked": int(row.get("open_tickets_unchecked_time_entries") or 0),
            "time_entry_rows": int(row.get("open_ticket_time_entry_rows") or 0),
            "labor_hours": round(float(row.get("open_ticket_labor_hours") or 0), 2),
            "coverage_percent": _coverage_percent(with_time, open_tickets),
        },
        "ticket_history": {
            "with_history": with_history,
            "without_history": int(row.get("open_tickets_without_history") or 0),
            "checked": int(row.get("open_tickets_checked_for_history") or 0),
            "checked_empty": int(row.get("open_tickets_checked_empty_history") or 0),
            "unchecked": int(row.get("open_tickets_unchecked_history") or 0),
            "history_rows": int(row.get("open_ticket_history_rows") or 0),
            "coverage_percent": _coverage_percent(with_history, open_tickets),
        },
    }


def _operations_estate_coverage(
    row: dict[str, Any],
    *,
    estate_labor_targets: list[dict[str, Any]] | None = None,
    estate_history_targets: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    total_tickets = int(row.get("total_tickets") or 0)
    with_notes = int(row.get("tickets_with_notes") or 0)
    with_time = int(row.get("tickets_with_time_entries") or 0)
    with_history = int(row.get("tickets_with_history") or 0)
    notes_without = max(total_tickets - with_notes, 0)
    time_without = max(total_tickets - with_time, 0)
    history_without = max(total_tickets - with_history, 0)
    assigned_resources = int(row.get("assigned_resource_ids") or 0)
    assigned_resources_with_reference = int(row.get("assigned_resource_ids_with_reference") or 0)
    return {
        "tickets": {
            "total": total_tickets,
            "with_autotask_updated_at": int(row.get("tickets_with_autotask_updated_at") or 0),
            "oldest_autotask_update": row.get("oldest_autotask_update"),
            "newest_autotask_update": row.get("newest_autotask_update"),
        },
        "related_data": {
            "notes": {
                "tickets_with_data": with_notes,
                "tickets_without_data": notes_without,
                "backlog_tickets": notes_without,
                "checked": int(row.get("tickets_checked_for_notes") or 0),
                "checked_empty": int(row.get("tickets_checked_empty_notes") or 0),
                "unchecked": int(row.get("tickets_unchecked_notes") or 0),
                "rows": int(row.get("ticket_note_rows") or 0),
                "coverage_percent": _coverage_percent(with_notes, total_tickets),
            },
            "time_entries": {
                "tickets_with_data": with_time,
                "tickets_without_data": time_without,
                "backlog_tickets": time_without,
                "checked": int(row.get("tickets_checked_for_time_entries") or 0),
                "checked_empty": int(row.get("tickets_checked_empty_time_entries") or 0),
                "unchecked": int(row.get("tickets_unchecked_time_entries") or 0),
                "next_targets": estate_labor_targets or [],
                "rows": int(row.get("time_entry_rows") or 0),
                "coverage_percent": _coverage_percent(with_time, total_tickets),
            },
            "ticket_history": {
                "tickets_with_data": with_history,
                "tickets_without_data": history_without,
                "backlog_tickets": history_without,
                "checked": int(row.get("tickets_checked_for_history") or 0),
                "checked_empty": int(row.get("tickets_checked_empty_history") or 0),
                "unchecked": int(row.get("tickets_unchecked_history") or 0),
                "check_sources": ["ticket_history_gaps", "open_ticket_history_gaps", "status_sample_ticket_history"],
                "next_targets": estate_history_targets or [],
                "rows": int(row.get("ticket_history_rows") or 0),
                "coverage_percent": _coverage_percent(with_history, total_tickets),
            },
        },
        "related_data_backlog": {
            "notes": notes_without,
            "time_entries": time_without,
            "ticket_history": history_without,
            "interpretation": "All local tickets can be refreshed independently from related notes, TimeEntries, and TicketHistory; these backlog counts show tickets still missing each related-data type.",
        },
        "resource_labels": {
            "assigned_resource_ids": assigned_resources,
            "with_reference_labels": assigned_resources_with_reference,
            "without_reference_labels": max(assigned_resources - assigned_resources_with_reference, 0),
            "reference_label_rows": int(row.get("resource_reference_rows") or 0),
            "coverage_percent": _coverage_percent(assigned_resources_with_reference, assigned_resources),
        },
    }


def _related_data_work_plan(
    estate: dict[str, Any],
    settings: dict[str, Any],
    *,
    threshold_remaining: int | None,
    global_pause: bool,
) -> dict[str, Any]:
    related = estate.get("related_data", {})
    minimum_remaining = int(settings.get("autotask_threshold_min_remaining") or 0)
    blocked_reasons: list[str] = []
    if global_pause:
        blocked_reasons.append("global_pause")
    if threshold_remaining is not None and threshold_remaining < minimum_remaining:
        blocked_reasons.append(f"autotask_threshold_low:{threshold_remaining}")

    job_specs = [
        (
            "ticket_time_entry_gaps",
            "Estate labor gaps",
            "/api/sync/time-entries/ticket-gaps/start",
            "ticket_time_entry_gap_batch_size",
            related.get("time_entries", {}),
            "Expands labor coverage with bounded per-ticket TimeEntries reads.",
        ),
        (
            "ticket_history_gaps",
            "Estate history gaps",
            "/api/sync/ticket-history/ticket-gaps/start",
            "ticket_history_gap_batch_size",
            related.get("ticket_history", {}),
            "Expands TicketHistory coverage with bounded per-ticket reads; status-duration remains source-limited until status-change events appear.",
        ),
        (
            "ticket_note_gaps",
            "Ticket note gaps",
            "/api/sync/ticket-notes/gaps/start",
            "ticket_note_gap_batch_size",
            related.get("notes", {}),
            "Fills the small remaining note backlog with bounded per-ticket note reads.",
        ),
    ]
    items: list[dict[str, Any]] = []
    for job_name, label, endpoint, setting_key, coverage, reason in job_specs:
        backlog = int(coverage.get("backlog_tickets") or coverage.get("tickets_without_data") or 0)
        unchecked = int(coverage.get("unchecked") or 0)
        checked_empty = int(coverage.get("checked_empty") or 0)
        batch_limit = int(settings.get(setting_key) or DEFAULT_SETTINGS[setting_key])
        estimated_runs = ceil(unchecked / batch_limit) if unchecked > 0 and batch_limit > 0 else 0
        items.append(
            {
                "job_name": job_name,
                "label": label,
                "endpoint": endpoint,
                "recommended_limit": batch_limit,
                "estimated_runs_to_check": estimated_runs,
                "backlog_tickets": backlog,
                "unchecked": unchecked,
                "checked_empty": checked_empty,
                "coverage_percent": coverage.get("coverage_percent", 0),
                "next_targets": list(coverage.get("next_targets") or [])[:3],
                "ready": not blocked_reasons and unchecked > 0,
                "reason": reason if unchecked > 0 else "No unchecked local targets currently need this bounded job.",
            }
        )
    recommended = next((item for item in items if item["ready"]), None)
    if blocked_reasons:
        recommendation = "hold"
        summary = "Bounded related-data jobs are paused by local Operations safeguards."
    elif recommended:
        recommendation = recommended["job_name"]
        summary = f"Run {recommended['label']} next with limit {recommended['recommended_limit']}."
    else:
        recommendation = "none"
        summary = "No unchecked related-data targets are currently available."
    return {
        "recommendation": recommendation,
        "summary": summary,
        "blocked_reasons": blocked_reasons,
        "items": items,
    }


def default_operations_settings() -> dict[str, Any]:
    return dict(DEFAULT_SETTINGS)


def ensure_operations_defaults() -> None:
    init_schema()
    with db_connection() as conn:
        for key, value in DEFAULT_SETTINGS.items():
            conn.execute(
                """
                INSERT INTO system_settings(key, value)
                VALUES (%s, %s)
                ON CONFLICT (key) DO NOTHING
                """,
                (key, Jsonb(value)),
            )
        for key in ("ticket_time_entry_gap_batch_size", "ticket_history_gap_batch_size"):
            conn.execute(
                """
                UPDATE system_settings
                SET value=%s, updated_at=now()
                WHERE key=%s AND value=%s
                """,
                (Jsonb(DEFAULT_SETTINGS[key]), key, Jsonb(25)),
            )
        for job_name, job in DEFAULT_JOBS.items():
            conn.execute(
                """
                INSERT INTO scheduled_jobs(job_name, enabled, cadence_seconds, schedule)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (job_name) DO NOTHING
                """,
                (job_name, job["enabled"], job["cadence_seconds"], job["schedule"]),
            )
            conn.execute(
                """
                UPDATE scheduled_jobs
                SET cadence_seconds=%s,
                    schedule=%s,
                    enabled=CASE
                        WHEN job_name IN (
                            'ticket_time_entry_gaps',
                            'open_ticket_time_entry_gaps',
                            'ticket_history_gaps',
                            'open_ticket_history_gaps'
                        )
                          AND schedule LIKE 'manual bounded %%'
                        THEN %s
                        ELSE enabled
                    END,
                    updated_at=now()
                WHERE job_name=%s
                  AND (cadence_seconds IS DISTINCT FROM %s OR schedule IS DISTINCT FROM %s OR schedule LIKE 'manual bounded %%')
                """,
                (job["cadence_seconds"], job["schedule"], job["enabled"], job_name, job["cadence_seconds"], job["schedule"]),
            )


def operations_settings() -> dict[str, Any]:
    ensure_operations_defaults()
    with db_connection() as conn:
        rows = conn.execute("SELECT key, value FROM system_settings ORDER BY key").fetchall()
    merged = default_operations_settings()
    for row in rows:
        key = row["key"]
        if key in DEFAULT_SETTINGS:
            merged[key] = normalize_operations_setting(key, row["value"])
    return merged


def normalize_operations_setting(key: str, value: Any) -> Any:
    default = DEFAULT_SETTINGS[key]
    if key in SETTING_LIMITS:
        minimum, maximum = SETTING_LIMITS[key]
        try:
            numeric = int(value)
        except (TypeError, ValueError):
            numeric = int(default)
        return min(max(numeric, minimum), maximum)
    if isinstance(default, bool):
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "1", "yes", "on"}:
                return True
            if lowered in {"false", "0", "no", "off"}:
                return False
        return bool(value)
    return value if value is not None else default


def update_operations_settings(changes: dict[str, Any]) -> dict[str, Any]:
    ensure_operations_defaults()
    allowed = set(DEFAULT_SETTINGS)
    with db_connection() as conn:
        for key, value in changes.items():
            if key not in allowed:
                continue
            normalized_value = normalize_operations_setting(key, value)
            conn.execute(
                """
                INSERT INTO system_settings(key, value, updated_at)
                VALUES (%s, %s, now())
                ON CONFLICT (key) DO UPDATE
                SET value=EXCLUDED.value, updated_at=now()
                """,
                (key, Jsonb(normalized_value)),
            )
    _sync_job_enabled_from_settings()
    invalidate_operations_status_cache()
    return operations_settings()


def _sync_job_enabled_from_settings() -> None:
    settings = operations_settings()
    mapping = {
        "recent_sync": bool(settings["sync_enabled"] and settings["recent_sync_enabled"]),
        "raw_backfill_tickets": bool(settings["raw_backfill_enabled"]),
        "raw_backfill_ticket_notes": bool(settings["raw_backfill_enabled"]),
        "raw_backfill_time_entries": bool(settings["raw_backfill_enabled"]),
        "raw_backfill_ticket_history": bool(settings["raw_backfill_enabled"]),
        "raw_backfill_companies": bool(settings["raw_backfill_enabled"]),
        "build_documents": bool(settings["document_build_enabled"]),
        "classify_tickets": bool(settings["ticket_classification_enabled"]),
        "reclassify_chunks": bool(settings["chunk_reclassification_enabled"]),
        "run_embeddings": bool(settings["embedding_enabled"]),
        "nightly_pipeline": bool(settings["nightly_pipeline_enabled"]),
        "customer_success_score_snapshot": bool(settings["customer_success_snapshot_enabled"]),
        "related_data_work_plan": bool(settings["related_data_work_plan_enabled"]),
        "ticket_time_entry_gaps": bool(settings["sync_enabled"] and settings["ticket_time_entry_gaps_enabled"]),
        "open_ticket_time_entry_gaps": bool(settings["sync_enabled"] and settings["open_ticket_time_entry_gaps_enabled"]),
        "ticket_history_gaps": bool(settings["sync_enabled"] and settings["ticket_history_gaps_enabled"]),
        "open_ticket_history_gaps": bool(settings["sync_enabled"] and settings["open_ticket_history_gaps_enabled"]),
    }
    with db_connection() as conn:
        for job_name, enabled in mapping.items():
            conn.execute(
                "UPDATE scheduled_jobs SET enabled=%s, updated_at=now() WHERE job_name=%s",
                (enabled, job_name),
            )


def _bool(settings: dict[str, Any], key: str) -> bool:
    return bool(settings.get(key))


def _int(settings: dict[str, Any], key: str) -> int:
    return int(settings.get(key) or 0)


def _parse_hhmm(value: str) -> clock_time:
    hour, minute = str(value).split(":", 1)
    return clock_time(int(hour), int(minute))


def is_quiet_hours(now: datetime | None, start: str, end: str) -> bool:
    current = (now or datetime.now()).time()
    start_time = _parse_hhmm(start)
    end_time = _parse_hhmm(end)
    if start_time <= end_time:
        return start_time <= current <= end_time
    return current >= start_time or current <= end_time


def disk_free_gb(path: str = "/") -> float:
    usage = shutil.disk_usage(path)
    return usage.free / (1024**3)


def extract_threshold_remaining(payload: dict[str, Any]) -> int | None:
    for key in ("remaining", "requestsRemaining", "RequestCountRemaining", "thresholdRemaining", "currentTimeFrameRequestsAvailable"):
        value = payload.get(key)
        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                pass
    for value in payload.values():
        if isinstance(value, dict):
            remaining = extract_threshold_remaining(value)
            if remaining is not None:
                return remaining
    return None


def autotask_threshold_remaining() -> int | None:
    payload = AutotaskReadOnlyClient(delay_seconds=0).threshold_information()
    return extract_threshold_remaining(payload)


def ollama_available() -> bool:
    try:
        response = httpx.get(f"{app_settings.ollama_base_url.rstrip('/')}/api/tags", timeout=5)
        return response.status_code < 500
    except Exception:
        return False


def _running_job_names(conn: Any) -> set[str]:
    rows = conn.execute("SELECT job_name FROM job_runs WHERE status='running'").fetchall()
    return {row["job_name"] for row in rows}


def conflicting_jobs(job_name: str, running: set[str]) -> set[str]:
    if job_name in AUTOTASK_JOBS:
        return running & AUTOTASK_JOBS
    if job_name == "recent_sync":
        return running & RAW_BACKFILL_JOBS
    if job_name in RAW_BACKFILL_JOBS:
        return running & (RAW_BACKFILL_JOBS | {"recent_sync"})
    if job_name == "build_documents":
        return running & {"reclassify_chunks", "run_embeddings"}
    if job_name == "reclassify_chunks":
        return running & {"build_documents"}
    if job_name == "run_embeddings":
        return running & {"build_documents"}
    return set()


def record_scheduler_heartbeat(
    worker_name: str,
    *,
    interval_seconds: int,
    status: str = "running",
    last_error: str | None = None,
    tick_started_at: datetime | None = None,
    tick_finished_at: datetime | None = None,
) -> None:
    init_schema()
    with db_connection() as conn:
        conn.execute(
            """
            INSERT INTO scheduler_heartbeats(
                worker_name, heartbeat_at, interval_seconds, status, last_error,
                last_tick_started_at, last_tick_finished_at, updated_at
            )
            VALUES (%s, now(), %s, %s, %s, %s, %s, now())
            ON CONFLICT (worker_name) DO UPDATE SET
                heartbeat_at=EXCLUDED.heartbeat_at,
                interval_seconds=EXCLUDED.interval_seconds,
                status=EXCLUDED.status,
                last_error=EXCLUDED.last_error,
                last_tick_started_at=COALESCE(EXCLUDED.last_tick_started_at, scheduler_heartbeats.last_tick_started_at),
                last_tick_finished_at=COALESCE(EXCLUDED.last_tick_finished_at, scheduler_heartbeats.last_tick_finished_at),
                updated_at=now()
            """,
            (
                worker_name,
                interval_seconds,
                status,
                (last_error or "")[:1000] if last_error else None,
                tick_started_at,
                tick_finished_at,
            ),
        )
    invalidate_operations_status_cache()


def _scheduler_status(conn: Any, now: datetime) -> dict[str, Any]:
    heartbeat = conn.execute(
        "SELECT * FROM scheduler_heartbeats WHERE worker_name='worker-scheduler'"
    ).fetchone()
    next_due = conn.execute(
        """
        SELECT job_name, enabled, cadence_seconds, last_finished_at,
               CASE
                 WHEN NOT enabled THEN NULL
                 WHEN last_finished_at IS NULL THEN now()
                 ELSE last_finished_at + make_interval(secs => cadence_seconds)
               END AS due_at
        FROM scheduled_jobs
        WHERE enabled
        ORDER BY due_at NULLS LAST, job_name
        LIMIT 1
        """
    ).fetchone()
    last_completed = conn.execute(
        """
        SELECT id, job_name, status, started_at, finished_at, last_error
        FROM job_runs
        WHERE status IN ('completed', 'failed', 'skipped')
        ORDER BY finished_at DESC NULLS LAST, id DESC
        LIMIT 1
        """
    ).fetchone()
    if heartbeat and heartbeat.get("heartbeat_at"):
        interval = int(heartbeat.get("interval_seconds") or 60)
        heartbeat_age = max((now - heartbeat["heartbeat_at"]).total_seconds(), 0)
        stale_after = max(interval * 3, 180)
        state = "healthy" if heartbeat_age <= stale_after and heartbeat.get("status") != "failed" else "stale"
        if heartbeat.get("status") == "failed":
            state = "blocked"
        heartbeat_data = dict(heartbeat)
    else:
        interval = 60
        heartbeat_age = None
        stale_after = 180
        state = "stopped"
        heartbeat_data = None
    return {
        "worker_name": "worker-scheduler",
        "state": state,
        "heartbeat": heartbeat_data,
        "heartbeat_age_seconds": round(heartbeat_age, 1) if heartbeat_age is not None else None,
        "stale_after_seconds": stale_after,
        "last_completed_run": dict(last_completed) if last_completed else None,
        "next_due_job": dict(next_due) if next_due else None,
    }


def _create_job_run(conn: Any, job_name: str, triggered_by: str, snapshot: dict[str, Any]) -> int:
    row = conn.execute(
        """
        INSERT INTO job_runs(job_name, status, triggered_by, config_snapshot)
        VALUES (%s, 'running', %s, %s)
        RETURNING id
        """,
        (job_name, triggered_by, Jsonb(snapshot)),
    ).fetchone()
    conn.execute(
        """
        UPDATE scheduled_jobs
        SET status='running', current_step='starting', last_started_at=now(), updated_at=now()
        WHERE job_name=%s
        """,
        (job_name,),
    )
    invalidate_operations_status_cache()
    return int(row["id"])


def _acquire_lock(conn: Any, job_name: str, run_id: int) -> bool:
    row = conn.execute(
        """
        INSERT INTO job_locks(job_name, run_id, owner)
        VALUES (%s, %s, %s)
        ON CONFLICT (job_name) DO NOTHING
        RETURNING job_name
        """,
        (job_name, run_id, f"{socket.gethostname()}:{os.getpid()}"),
    ).fetchone()
    return bool(row)


def _finish_job_run(
    conn: Any,
    run_id: int,
    job_name: str,
    status: str,
    stats: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    stats = stats or {}
    conn.execute(
        """
        UPDATE job_runs
        SET status=%s,
            finished_at=now(),
            duration_ms=(EXTRACT(EPOCH FROM (now() - started_at)) * 1000)::int,
            pulled_count=%s,
            inserted_count=%s,
            updated_count=%s,
            failed_count=%s,
            last_checkpoint=%s,
            last_error=%s,
            current_step=%s
        WHERE id=%s
        """,
        (
            status,
            int(stats.get("pulled", stats.get("processed", 0)) or 0),
            int(stats.get("inserted", stats.get("documents", 0)) or 0),
            int(stats.get("updated", stats.get("chunks", 0)) or 0),
            int(stats.get("failed", 0) or 0),
            Jsonb(_checkpoint_summary(stats)),
            error[:1000] if error else None,
            status,
            run_id,
        ),
    )
    conn.execute(
        """
        UPDATE scheduled_jobs
        SET status=%s,
            current_step=NULL,
            last_checkpoint=%s,
            last_error=%s,
            last_finished_at=now(),
            updated_at=now()
        WHERE job_name=%s
        """,
        (status, Jsonb(_checkpoint_summary(stats)), error[:1000] if error else None, job_name),
    )
    conn.execute("DELETE FROM job_locks WHERE job_name=%s", (job_name,))
    invalidate_operations_status_cache()


def _checkpoint_summary(stats: dict[str, Any]) -> dict[str, Any]:
    checkpoint = dict(stats.get("checkpoint") or {})
    for key in (
        "processed_tickets",
        "pulled",
        "inserted",
        "updated",
        "failed",
        "target",
        "checked_empty",
        "remaining_unchecked",
        "cycle",
    ):
        if key in stats:
            checkpoint[key] = stats[key]
    if "run_id" in stats:
        checkpoint["sync_run_id"] = stats["run_id"]
    checkpoint["last_successful_completion_at"] = datetime.now(UTC).isoformat()
    return checkpoint


def _skip_job(job_name: str, triggered_by: str, reason: str, snapshot: dict[str, Any]) -> dict[str, Any]:
    ensure_operations_defaults()
    with db_connection() as conn:
        run_id = _create_job_run(conn, job_name, triggered_by, snapshot)
        _finish_job_run(conn, run_id, job_name, "skipped", {}, reason)
    return {"ok": False, "job_name": job_name, "status": "skipped", "reason": reason, "run_id": run_id}


def _preflight(job_name: str, settings: dict[str, Any]) -> str | None:
    if _bool(settings, "global_pause"):
        return "global_pause"
    free_gb = disk_free_gb("/")
    if free_gb < float(settings.get("min_free_disk_gb") or 0):
        return f"low_disk_free_gb:{free_gb:.1f}"
    if job_name in AUTOTASK_JOBS:
        remaining = autotask_threshold_remaining()
        if remaining is not None and remaining < _int(settings, "autotask_threshold_min_remaining"):
            return f"autotask_threshold_low:{remaining}"
    if job_name == "run_embeddings":
        if not _bool(settings, "embedding_enabled"):
            return "embedding_disabled"
        if _bool(settings, "embedding_quiet_hours_only") and not is_quiet_hours(
            datetime.now(), str(settings["embedding_quiet_hours_start"]), str(settings["embedding_quiet_hours_end"])
        ):
            return "outside_embedding_quiet_hours"
        if not ollama_available():
            return "ollama_unavailable"
    return None


def _nightly_pipeline(settings: dict[str, Any]) -> dict[str, Any]:
    stats: dict[str, Any] = {"processed": 0, "failed": 0, "steps": {}}
    steps: list[tuple[str, Callable[[], dict[str, Any]]]] = [
        ("sync_reference_data", sync_reference_data),
        ("classify_tickets", lambda: classify_tickets(limit=_int(settings, "ticket_classification_batch_size"))),
    ]
    if _bool(settings, "document_build_enabled"):
        steps.append(("build_documents", lambda: create_documents_from_tickets(limit=_int(settings, "document_build_batch_size"))))
    if _bool(settings, "chunk_reclassification_enabled"):
        steps.append(("reclassify_chunks", lambda: reclassify_chunks(limit=_int(settings, "chunk_reclassification_batch_size"))))
    if _bool(settings, "embedding_enabled") and is_quiet_hours(
        datetime.now(), str(settings["embedding_quiet_hours_start"]), str(settings["embedding_quiet_hours_end"])
    ):
        steps.append(("run_embeddings", lambda: run_embedding_batch(limit=_int(settings, "embedding_batch_size"))))
    for name, step in steps:
        result = step()
        stats["steps"][name] = result
        stats["processed"] += int(result.get("processed", result.get("pulled", 0)) or 0)
        stats["failed"] += int(result.get("failed", 0) or 0)
    return stats


def _execute_related_data_work_plan(settings: dict[str, Any]) -> dict[str, Any]:
    status = operations_status()
    plan = status.get("related_data_work_plan") or {}
    recommendation = plan.get("recommendation")
    allowed_jobs = {
        "ticket_time_entry_gaps",
        "ticket_history_gaps",
        "ticket_note_gaps",
    }
    if recommendation == "hold":
        return {
            "processed": 0,
            "failed": 0,
            "recommendation": "hold",
            "reason": plan.get("summary") or "No bounded related-data work-plan job is ready.",
            "work_plan": plan,
        }

    ready_jobs = [
        str(item.get("job_name"))
        for item in plan.get("items", [])
        if item.get("ready") and item.get("job_name") in allowed_jobs
    ]
    if not ready_jobs:
        return {
            "processed": 0,
            "failed": 0,
            "recommendation": recommendation or "none",
            "reason": plan.get("summary") or "No bounded related-data work-plan job is ready.",
            "work_plan": plan,
        }

    jobs_to_run: list[str] = []
    if "ticket_time_entry_gaps" in ready_jobs:
        jobs_to_run.append("ticket_time_entry_gaps")
    if "ticket_history_gaps" in ready_jobs:
        jobs_to_run.extend(["status_sample_ticket_history", "ticket_history_gaps"])
    if "ticket_note_gaps" in ready_jobs:
        jobs_to_run.append("ticket_note_gaps")

    delegated_results: dict[str, dict[str, Any]] = {}
    totals = {"processed": 0, "pulled": 0, "inserted": 0, "updated": 0, "failed": 0}
    for job_name in jobs_to_run:
        result = _execute_job(job_name, settings)
        delegated_results[job_name] = result
        totals["processed"] += int(result.get("processed_tickets", result.get("processed", result.get("pulled", 0))) or 0)
        totals["pulled"] += int(result.get("pulled", 0) or 0)
        totals["inserted"] += int(result.get("inserted", 0) or 0)
        totals["updated"] += int(result.get("updated", 0) or 0)
        totals["failed"] += int(result.get("failed", 0) or 0)

    return {
        **totals,
        "recommendation": recommendation,
        "delegated_jobs": jobs_to_run,
        "delegated_results": delegated_results,
        "work_plan": plan,
    }


def _execute_job(job_name: str, settings: dict[str, Any]) -> dict[str, Any]:
    if job_name == "recent_sync":
        return sync_recent(limit=100)
    if job_name == "raw_backfill_companies":
        return sync_companies(limit=_int(settings, "raw_backfill_batch_tickets"))
    if job_name == "raw_backfill_tickets":
        return sync_tickets(limit=_int(settings, "raw_backfill_batch_tickets"))
    if job_name == "raw_backfill_ticket_notes":
        return sync_ticket_notes(limit=_int(settings, "raw_backfill_batch_notes"))
    if job_name == "ticket_note_gaps":
        return sync_ticket_note_gaps(limit=_int(settings, "ticket_note_gap_batch_size"))
    if job_name == "raw_backfill_time_entries":
        return sync_time_entries(limit=_int(settings, "raw_backfill_batch_time_entries"))
    if job_name == "ticket_time_entry_gaps":
        return sync_ticket_time_entry_gaps(limit=_int(settings, "ticket_time_entry_gap_batch_size"))
    if job_name == "open_ticket_time_entry_gaps":
        return sync_open_ticket_time_entry_gaps(limit=_int(settings, "open_ticket_time_entry_gap_batch_size"))
    if job_name == "raw_backfill_ticket_history":
        return sync_ticket_history(limit=_int(settings, "raw_backfill_batch_ticket_history"))
    if job_name == "targeted_waiting_ticket_history":
        return sync_waiting_ticket_history(limit=_int(settings, "targeted_waiting_ticket_history_batch_size"))
    if job_name == "status_sample_ticket_history":
        return sync_status_sample_ticket_history(limit=_int(settings, "status_sample_ticket_history_batch_size"))
    if job_name == "ticket_history_gaps":
        return sync_ticket_history_gaps(limit=_int(settings, "ticket_history_gap_batch_size"))
    if job_name == "open_ticket_history_gaps":
        return sync_open_ticket_history_gaps(limit=_int(settings, "open_ticket_history_gap_batch_size"))
    if job_name == "related_data_work_plan":
        return _execute_related_data_work_plan(settings)
    if job_name == "sync_reference_data":
        return sync_reference_data()
    if job_name == "classify_tickets":
        return classify_tickets(limit=_int(settings, "ticket_classification_batch_size"))
    if job_name == "build_documents":
        return create_documents_from_tickets(limit=_int(settings, "document_build_batch_size"))
    if job_name == "reclassify_chunks":
        return reclassify_chunks(limit=_int(settings, "chunk_reclassification_batch_size"))
    if job_name == "run_embeddings":
        return run_embedding_batch(limit=_int(settings, "embedding_batch_size"))
    if job_name == "nightly_pipeline":
        return _nightly_pipeline(settings)
    if job_name == "customer_success_score_snapshot":
        cleanup = cleanup_customer_success_score_snapshots(
            retention_days=_int(settings, "customer_success_snapshot_retention_days")
        )
        capture = capture_customer_success_score_snapshot(
            limit=_int(settings, "customer_success_snapshot_batch_size"),
            recent_days=30,
        )
        return {
            "processed": int(capture.get("snapshot_rows_inserted", 0) or 0),
            "cleanup": cleanup,
            "capture": capture,
        }
    raise ValueError(f"Unknown job: {job_name}")


def run_job(
    job_name: str,
    triggered_by: str = "scheduler",
    force: bool = False,
    setting_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ensure_operations_defaults()
    snapshot = operations_settings()
    if setting_overrides:
        snapshot.update(setting_overrides)
    with db_connection() as conn:
        job = conn.execute("SELECT * FROM scheduled_jobs WHERE job_name=%s", (job_name,)).fetchone()
        if not job:
            return _skip_job(job_name, triggered_by, "unknown_job", snapshot)
        if force and job_name in RAW_BACKFILL_JOBS and not _bool(snapshot, "raw_backfill_enabled"):
            return _skip_job(job_name, triggered_by, "raw_backfill_disabled", snapshot)
        if not force and not job["enabled"]:
            return _skip_job(job_name, triggered_by, "job_disabled", snapshot)
        running = _running_job_names(conn)
        conflicts = conflicting_jobs(job_name, running)
        if conflicts:
            return _skip_job(job_name, triggered_by, f"conflicting_jobs:{','.join(sorted(conflicts))}", snapshot)

    reason = _preflight(job_name, snapshot)
    if reason:
        return _skip_job(job_name, triggered_by, reason, snapshot)

    with db_connection() as conn:
        run_id = _create_job_run(conn, job_name, triggered_by, snapshot)
        if not _acquire_lock(conn, job_name, run_id):
            _finish_job_run(conn, run_id, job_name, "skipped", {}, "job_locked")
            return {"ok": False, "job_name": job_name, "status": "skipped", "reason": "job_locked", "run_id": run_id}

    try:
        result = _execute_job(job_name, snapshot)
        with db_connection() as conn:
            _finish_job_run(conn, run_id, job_name, "completed", result)
        invalidate_dashboard_caches()
        return {"ok": True, "job_name": job_name, "status": "completed", "run_id": run_id, "result": result}
    except Exception as exc:
        with db_connection() as conn:
            _finish_job_run(conn, run_id, job_name, "failed", {}, str(exc))
        return {"ok": False, "job_name": job_name, "status": "failed", "run_id": run_id, "error": str(exc)}


def _job_due(job: dict[str, Any], now: datetime, settings: dict[str, Any]) -> bool:
    if not job["enabled"]:
        return False
    if job["job_name"] == "nightly_pipeline":
        target = _parse_hhmm(str(settings["nightly_pipeline_time"]))
        last_finished = job.get("last_finished_at")
        if now.time() < target:
            return False
        return not last_finished or last_finished.date() < now.date()
    last_finished = job.get("last_finished_at")
    cadence = int(job.get("cadence_seconds") or 0)
    if not last_finished:
        return True
    return (now - last_finished).total_seconds() >= cadence


def run_due_jobs(only: set[str] | None = None) -> list[dict[str, Any]]:
    ensure_operations_defaults()
    settings = operations_settings()
    now = datetime.now(UTC)
    with db_connection() as conn:
        jobs = conn.execute("SELECT * FROM scheduled_jobs ORDER BY job_name").fetchall()
    results = []
    for job in jobs:
        job_name = job["job_name"]
        if only and job_name not in only:
            continue
        if _job_due(job, now, settings):
            results.append(run_job(job_name, triggered_by="scheduler"))
    return results


def set_job_enabled(job_name: str, enabled: bool) -> dict[str, Any]:
    ensure_operations_defaults()
    with db_connection() as conn:
        row = conn.execute(
            """
            UPDATE scheduled_jobs SET enabled=%s, updated_at=now()
            WHERE job_name=%s
            RETURNING job_name, enabled
            """,
            (enabled, job_name),
        ).fetchone()
    invalidate_operations_status_cache()
    return {"ok": bool(row), "job": row}


def operations_jobs() -> dict[str, Any]:
    ensure_operations_defaults()
    with db_connection() as conn:
        jobs = list(conn.execute("SELECT * FROM scheduled_jobs ORDER BY job_name").fetchall())
        running = list(conn.execute("SELECT * FROM job_runs WHERE status='running' ORDER BY started_at DESC").fetchall())
        scheduler = _scheduler_status(conn, datetime.now(UTC))
    return {"ok": True, "jobs": jobs, "running": running, "scheduler": scheduler}


def job_runs(limit: int = 50) -> dict[str, Any]:
    ensure_operations_defaults()
    with db_connection() as conn:
        rows = list(
            conn.execute(
                "SELECT * FROM job_runs ORDER BY started_at DESC LIMIT %s",
                (min(max(limit, 1), 200),),
            ).fetchall()
        )
    return {"ok": True, "runs": rows}


def _job_recovery_status(row: dict[str, Any], now: datetime) -> str:
    if not row.get("enabled"):
        return "partial"
    latest_status = str(row.get("latest_run_status") or "")
    if not latest_status:
        return "missing"
    if latest_status == "failed" or row.get("latest_has_error"):
        return "partial"
    last_finished = row.get("last_finished_at") or row.get("latest_run_finished_at")
    if not last_finished:
        return "partial"
    cadence = int(row.get("cadence_seconds") or 0)
    stale_after = max(cadence * 3, 30 * 60)
    if cadence > 0 and (now - last_finished).total_seconds() > stale_after:
        return "partial"
    return "available"


def _stale_running_provenance(conn: Any, now: datetime, *, limit: int = 10) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        WITH stale AS (
            SELECT
                jr.id,
                jr.job_name,
                jr.started_at,
                jr.triggered_by,
                jr.current_step,
                EXISTS (
                    SELECT 1
                    FROM job_locks jl
                    WHERE jl.run_id=jr.id
                ) AS has_active_lock
            FROM job_runs jr
            WHERE jr.status='running'
              AND jr.started_at < now() - interval '30 minutes'
            ORDER BY jr.started_at ASC, jr.id ASC
            LIMIT %s
        )
        SELECT
            stale.*,
            newer.id AS newer_completed_run_id,
            newer.finished_at AS newer_completed_finished_at
        FROM stale
        LEFT JOIN LATERAL (
            SELECT id, finished_at
            FROM job_runs completed
            WHERE completed.job_name=stale.job_name
              AND completed.status='completed'
              AND completed.finished_at > stale.started_at
            ORDER BY completed.finished_at DESC NULLS LAST, completed.id DESC
            LIMIT 1
        ) newer ON true
        ORDER BY stale.started_at ASC, stale.id ASC
        """,
        (min(max(limit, 1), 50),),
    ).fetchall()
    provenance: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        started_at = item.get("started_at")
        age_seconds = int(max((now - started_at).total_seconds(), 0)) if started_at else None
        newer_completed = bool(item.get("newer_completed_run_id"))
        has_active_lock = bool(item.get("has_active_lock"))
        if newer_completed and not has_active_lock:
            stale_state = "orphaned_running_row_candidate"
        elif newer_completed:
            stale_state = "superseded_running_row_with_lock"
        elif has_active_lock:
            stale_state = "stale_running_with_lock"
        else:
            stale_state = "stale_running_without_lock"
        provenance.append(
            {
                "run_id": item.get("id"),
                "job_name": item.get("job_name"),
                "started_at": started_at,
                "age_seconds": age_seconds,
                "triggered_by": item.get("triggered_by"),
                "current_step": item.get("current_step"),
                "has_active_lock": has_active_lock,
                "newer_completed_run_id": item.get("newer_completed_run_id"),
                "newer_completed_finished_at": item.get("newer_completed_finished_at"),
                "stale_state": stale_state,
            }
        )
    return provenance


def _scheduler_recovery_streak(conn: Any) -> dict[str, Any]:
    required_values = ", ".join(["(%s)"] * len(SYNC_RECOVERY_REQUIRED_JOBS))
    rows = conn.execute(
        f"""
        WITH required(job_name) AS (VALUES {required_values}),
        ranked_runs AS (
            SELECT
                jr.job_name,
                jr.id,
                jr.status,
                jr.started_at,
                jr.finished_at,
                jr.failed_count,
                jr.last_error IS NOT NULL AS has_error,
                row_number() OVER (
                    PARTITION BY jr.job_name
                    ORDER BY jr.started_at DESC, jr.id DESC
                ) AS run_rank
            FROM job_runs jr
            INNER JOIN required r ON r.job_name=jr.job_name
            WHERE jr.triggered_by='scheduler'
        )
        SELECT
            r.job_name,
            count(rr.id) AS inspected_runs,
            count(rr.id) FILTER (
                WHERE rr.status='completed'
                  AND COALESCE(rr.failed_count, 0)=0
                  AND NOT rr.has_error
            ) AS clean_completed_runs,
            count(rr.id) FILTER (
                WHERE rr.status='failed'
                   OR COALESCE(rr.failed_count, 0)>0
                   OR rr.has_error
            ) AS problematic_runs,
            max(rr.finished_at) FILTER (
                WHERE rr.status='completed'
                  AND COALESCE(rr.failed_count, 0)=0
                  AND NOT rr.has_error
            ) AS latest_clean_finished_at
        FROM required r
        LEFT JOIN ranked_runs rr ON rr.job_name=r.job_name AND rr.run_rank <= 3
        GROUP BY r.job_name
        ORDER BY r.job_name
        """,
        tuple(SYNC_RECOVERY_REQUIRED_JOBS),
    ).fetchall()
    jobs = []
    clean_jobs = 0
    for row in rows:
        item = dict(row)
        inspected_runs = int(item.get("inspected_runs") or 0)
        clean_completed_runs = int(item.get("clean_completed_runs") or 0)
        problematic_runs = int(item.get("problematic_runs") or 0)
        status = "available" if inspected_runs >= 3 and clean_completed_runs >= 3 and problematic_runs == 0 else "partial"
        if status == "available":
            clean_jobs += 1
        jobs.append(
            {
                "job_name": item.get("job_name"),
                "inspected_runs": inspected_runs,
                "clean_completed_runs": clean_completed_runs,
                "problematic_runs": problematic_runs,
                "latest_clean_finished_at": item.get("latest_clean_finished_at"),
                "streak_status": status,
            }
        )
    blockers = [job["job_name"] for job in jobs if job["streak_status"] != "available"]
    return {
        "state": "scheduler_recovery_streak_available" if not blockers else "partial_scheduler_recovery_streak",
        "summary": {
            "required_jobs": len(SYNC_RECOVERY_REQUIRED_JOBS),
            "clean_streak_jobs": clean_jobs,
            "partial_streak_jobs": len(blockers),
            "required_clean_runs_per_job": 3,
        },
        "blockers": blockers,
        "jobs": jobs,
        "policy": {
            "read_only": True,
            "runs_jobs": False,
            "autotask_writes_allowed": False,
            "returns_raw_error_text": False,
        },
    }


def scheduler_automation_certification_report() -> dict[str, Any]:
    ensure_operations_defaults()
    now = datetime.now(UTC)
    required_values = ", ".join(["(%s)"] * len(SYNC_RECOVERY_REQUIRED_JOBS))
    with db_connection() as conn:
        scheduler = _scheduler_status(conn, now)
        rows = list(
            conn.execute(
                f"""
                WITH required(job_name) AS (VALUES {required_values}),
                latest AS (
                    SELECT DISTINCT ON (job_name)
                        job_name,
                        status AS latest_run_status,
                        started_at AS latest_run_started_at,
                        finished_at AS latest_run_finished_at,
                        triggered_by AS latest_triggered_by,
                        failed_count AS latest_failed_count,
                        last_error IS NOT NULL AS latest_has_error
                    FROM job_runs
                    ORDER BY job_name, started_at DESC, id DESC
                )
                SELECT
                    r.job_name,
                    COALESCE(sj.enabled, false) AS enabled,
                    sj.cadence_seconds,
                    sj.schedule,
                    sj.status AS scheduled_status,
                    sj.last_started_at,
                    sj.last_finished_at,
                    latest.latest_run_status,
                    latest.latest_run_started_at,
                    latest.latest_run_finished_at,
                    latest.latest_triggered_by,
                    latest.latest_failed_count,
                    COALESCE(latest.latest_has_error, false) AS latest_has_error,
                    count(jr.id) FILTER (
                        WHERE jr.triggered_by='scheduler'
                          AND jr.started_at >= now() - interval '24 hours'
                    ) AS scheduler_runs_24h,
                    count(jr.id) FILTER (
                        WHERE jr.triggered_by='scheduler'
                          AND jr.status='completed'
                          AND jr.started_at >= now() - interval '24 hours'
                    ) AS scheduler_completed_24h,
                    count(jr.id) FILTER (
                        WHERE jr.triggered_by='scheduler'
                          AND jr.status='failed'
                          AND jr.started_at >= now() - interval '24 hours'
                    ) AS scheduler_failed_24h,
                    count(jr.id) FILTER (
                        WHERE jr.triggered_by='scheduler'
                          AND jr.status='skipped'
                          AND jr.started_at >= now() - interval '24 hours'
                    ) AS scheduler_skipped_24h,
                    count(jr.id) FILTER (
                        WHERE jr.triggered_by='scheduler'
                          AND jr.status='completed'
                          AND jr.started_at >= now() - interval '7 days'
                    ) AS scheduler_completed_7d
                FROM required r
                LEFT JOIN scheduled_jobs sj ON sj.job_name=r.job_name
                LEFT JOIN latest ON latest.job_name=r.job_name
                LEFT JOIN job_runs jr ON jr.job_name=r.job_name
                GROUP BY
                    r.job_name,
                    sj.enabled,
                    sj.cadence_seconds,
                    sj.schedule,
                    sj.status,
                    sj.last_started_at,
                    sj.last_finished_at,
                    latest.latest_run_status,
                    latest.latest_run_started_at,
                    latest.latest_run_finished_at,
                    latest.latest_triggered_by,
                    latest.latest_failed_count,
                    latest.latest_has_error
                ORDER BY r.job_name
                """,
                tuple(SYNC_RECOVERY_REQUIRED_JOBS),
            ).fetchall()
        )
        running_summary = conn.execute(
            """
            SELECT
                count(*) AS running_jobs,
                count(*) FILTER (WHERE started_at < now() - interval '30 minutes') AS stale_running_jobs
            FROM job_runs
            WHERE status='running'
            """
        ).fetchone()
        stale_running_provenance = _stale_running_provenance(conn, now)
        recovery_streak = _scheduler_recovery_streak(conn)

    jobs: list[dict[str, Any]] = []
    for row in rows:
        row_dict = dict(row)
        status = _job_recovery_status(row_dict, now)
        jobs.append(
            {
                "job_name": row_dict["job_name"],
                "enabled": bool(row_dict.get("enabled")),
                "cadence_seconds": row_dict.get("cadence_seconds"),
                "schedule": row_dict.get("schedule"),
                "last_started_at": row_dict.get("last_started_at"),
                "last_finished_at": row_dict.get("last_finished_at"),
                "latest_run_status": row_dict.get("latest_run_status"),
                "latest_triggered_by": row_dict.get("latest_triggered_by"),
                "latest_has_error": bool(row_dict.get("latest_has_error")),
                "scheduler_runs_24h": int(row_dict.get("scheduler_runs_24h") or 0),
                "scheduler_completed_24h": int(row_dict.get("scheduler_completed_24h") or 0),
                "scheduler_failed_24h": int(row_dict.get("scheduler_failed_24h") or 0),
                "scheduler_skipped_24h": int(row_dict.get("scheduler_skipped_24h") or 0),
                "scheduler_completed_7d": int(row_dict.get("scheduler_completed_7d") or 0),
                "certification_status": status,
            }
        )

    status_counts: dict[str, int] = {}
    for job in jobs:
        status_counts[job["certification_status"]] = status_counts.get(job["certification_status"], 0) + 1
    blockers = [
        job["job_name"]
        for job in jobs
        if job["certification_status"] in {"missing", "partial"}
    ]
    running_jobs = int(running_summary["running_jobs"] or 0)
    stale_running_jobs = int(running_summary["stale_running_jobs"] or 0)
    if stale_running_jobs:
        blockers.append("stale_running_jobs")
    warnings = []
    if scheduler.get("state") != "healthy":
        warnings.append("Scheduler heartbeat is not currently healthy.")
    if stale_running_jobs:
        warnings.append("One or more job runs have been running longer than 30 minutes.")
    job_blockers = [
        job["job_name"]
        for job in jobs
        if job["certification_status"] in {"missing", "partial"}
    ]
    if job_blockers:
        warnings.append("Some required scheduled jobs lack recent clean scheduler-run evidence.")

    return {
        "ok": True,
        "generated_at": now,
        "certification_state": (
            "scheduler_automation_available"
            if not blockers and scheduler.get("state") == "healthy" and stale_running_jobs == 0
            else "partial_scheduler_automation_evidence"
        ),
        "scheduler_state": scheduler.get("state"),
        "summary": {
            "required_jobs": len(SYNC_RECOVERY_REQUIRED_JOBS),
            "certified_jobs": status_counts.get("available", 0),
            "partial_jobs": status_counts.get("partial", 0),
            "missing_jobs": status_counts.get("missing", 0),
            "running_jobs": running_jobs,
            "stale_running_jobs": stale_running_jobs,
        },
        "blockers": blockers,
        "jobs": jobs,
        "stale_running_provenance": stale_running_provenance,
        "recovery_streak": recovery_streak,
        "policy": {
            "read_only": True,
            "runs_jobs": False,
            "autotask_writes_allowed": False,
            "returns_raw_error_text": False,
            "returns_raw_checkpoint_or_config": False,
            "automatic_model_or_workflow_changes_allowed": False,
        },
        "warnings": warnings,
    }


def request_stop(run_id: int) -> dict[str, Any]:
    ensure_operations_defaults()
    with db_connection() as conn:
        row = conn.execute(
            """
            UPDATE job_runs
            SET current_step='stop_requested'
            WHERE id=%s AND status='running'
            RETURNING id, job_name, current_step
            """,
            (run_id,),
        ).fetchone()
    invalidate_operations_status_cache()
    return {"ok": bool(row), "run": row}


def archive_stale_orphaned_run(run_id: int) -> dict[str, Any]:
    ensure_operations_defaults()
    with db_connection() as conn:
        row = conn.execute(
            """
            UPDATE job_runs jr
            SET status='stale_orphaned',
                finished_at=now(),
                duration_ms=GREATEST((EXTRACT(EPOCH FROM (now() - jr.started_at)) * 1000)::integer, 0),
                current_step='archived_stale_orphaned'
            WHERE jr.id=%s
              AND jr.status='running'
              AND jr.started_at < now() - interval '30 minutes'
              AND NOT EXISTS (
                  SELECT 1
                  FROM job_locks jl
                  WHERE jl.run_id=jr.id
              )
              AND EXISTS (
                  SELECT 1
                  FROM job_runs newer
                  WHERE newer.job_name=jr.job_name
                    AND newer.status='completed'
                    AND newer.finished_at > jr.started_at
              )
            RETURNING id, job_name, status, started_at, finished_at, current_step
            """,
            (run_id,),
        ).fetchone()
    invalidate_operations_status_cache()
    return {
        "ok": bool(row),
        "archived": bool(row),
        "run": dict(row) if row else None,
        "policy": {
            "local_metadata_only": True,
            "requires_stale_running_row": True,
            "requires_no_active_lock": True,
            "requires_newer_completed_run": True,
            "runs_jobs": False,
            "autotask_writes_allowed": False,
        },
    }


def operations_status(cache_context: dict[str, Any] | None = None) -> dict[str, Any]:
    ensure_operations_defaults()
    cache_key = operations_status_cache_key(**(cache_context or {}))
    cached = cache_get_json(cache_key)
    if cached is not None:
        cached["cache"] = {"hit": True, "ttl_seconds": app_settings.operations_status_cache_ttl_seconds, "scoped": True}
        return cached

    settings = operations_settings()
    with db_connection() as conn:
        counts = conn.execute(
            """
            SELECT
              (SELECT count(*) FROM autotask_companies) AS companies,
              (SELECT count(*) FROM autotask_tickets) AS tickets,
              (SELECT count(*) FROM autotask_ticket_notes) AS ticket_notes,
              (SELECT count(*) FROM autotask_time_entries) AS time_entries,
              (SELECT count(*) FROM autotask_ticket_history) AS ticket_history,
              (SELECT count(*) FROM documents) AS documents,
              (SELECT count(*) FROM document_chunks WHERE is_active) AS active_chunks,
              (SELECT count(*) FROM document_chunks WHERE is_active AND is_noise) AS noise_chunks,
              (SELECT count(*) FROM document_chunks WHERE is_active AND NOT is_noise) AS useful_chunks,
              (SELECT count(*) FROM document_embeddings) AS embeddings,
              (SELECT count(*) FROM customer_success_score_snapshots) AS customer_success_score_snapshots
            """
        ).fetchone()
        coverage = conn.execute(
            """
            WITH open_tickets AS (
                SELECT id
                FROM autotask_tickets
                WHERE completed_at_autotask IS NULL
                  AND COALESCE(status, '') <> ALL(%s)
            ),
            labor AS (
                SELECT ticket_id, count(*) AS entry_count, sum(COALESCE(hours, 0)) AS labor_hours
                FROM autotask_time_entries
                GROUP BY ticket_id
            ),
            history AS (
                SELECT ticket_id, count(*) AS history_count
                FROM autotask_ticket_history
                GROUP BY ticket_id
            )
            SELECT
                count(*) AS open_tickets,
                count(*) FILTER (WHERE COALESCE(labor.entry_count, 0) > 0) AS open_tickets_with_time_entries,
                count(*) FILTER (WHERE COALESCE(labor.entry_count, 0) = 0) AS open_tickets_without_time_entries,
                count(*) FILTER (WHERE labor_check.last_checked_at IS NOT NULL) AS open_tickets_checked_for_time_entries,
                count(*) FILTER (
                    WHERE COALESCE(labor.entry_count, 0) = 0
                      AND labor_check.last_checked_at IS NOT NULL
                      AND COALESCE(labor_check.last_result_count, 0) = 0
                ) AS open_tickets_checked_empty_time_entries,
                count(*) FILTER (
                    WHERE COALESCE(labor.entry_count, 0) = 0
                      AND labor_check.last_checked_at IS NULL
                ) AS open_tickets_unchecked_time_entries,
                COALESCE(sum(labor.entry_count), 0) AS open_ticket_time_entry_rows,
                COALESCE(sum(labor.labor_hours), 0) AS open_ticket_labor_hours,
                count(*) FILTER (WHERE COALESCE(history.history_count, 0) > 0) AS open_tickets_with_history,
                count(*) FILTER (WHERE COALESCE(history.history_count, 0) = 0) AS open_tickets_without_history,
                count(*) FILTER (WHERE history_check.last_checked_at IS NOT NULL) AS open_tickets_checked_for_history,
                count(*) FILTER (
                    WHERE COALESCE(history.history_count, 0) = 0
                      AND history_check.last_checked_at IS NOT NULL
                      AND COALESCE(history_check.last_result_count, 0) = 0
                ) AS open_tickets_checked_empty_history,
                count(*) FILTER (
                    WHERE COALESCE(history.history_count, 0) = 0
                      AND history_check.last_checked_at IS NULL
                ) AS open_tickets_unchecked_history,
                COALESCE(sum(history.history_count), 0) AS open_ticket_history_rows
            FROM open_tickets
            LEFT JOIN labor ON labor.ticket_id=open_tickets.id
            LEFT JOIN history ON history.ticket_id=open_tickets.id
            LEFT JOIN ticket_gap_sync_checks labor_check
              ON labor_check.ticket_id=open_tickets.id AND labor_check.sync_type='open_ticket_time_entry_gaps'
            LEFT JOIN ticket_gap_sync_checks history_check
              ON history_check.ticket_id=open_tickets.id AND history_check.sync_type='open_ticket_history_gaps'
            """,
            (["5", "16", "20"],),
        ).fetchone()
        estate = conn.execute(
            """
            WITH note_tickets AS (
                SELECT ticket_id, count(*) AS row_count
                FROM autotask_ticket_notes
                WHERE ticket_id IS NOT NULL
                GROUP BY ticket_id
            ),
            time_tickets AS (
                SELECT ticket_id, count(*) AS row_count
                FROM autotask_time_entries
                WHERE ticket_id IS NOT NULL
                GROUP BY ticket_id
            ),
            history_tickets AS (
                SELECT ticket_id, count(*) AS row_count
                FROM autotask_ticket_history
                WHERE ticket_id IS NOT NULL
                GROUP BY ticket_id
            ),
            history_checks AS (
                SELECT
                    ticket_id,
                    max(last_checked_at) AS last_checked_at,
                    max(last_result_count) AS max_result_count
                FROM ticket_gap_sync_checks
                WHERE sync_type IN ('ticket_history_gaps', 'open_ticket_history_gaps', 'status_sample_ticket_history')
                GROUP BY ticket_id
            ),
            assigned_resources AS (
                SELECT DISTINCT assigned_resource_id
                FROM autotask_tickets
                WHERE assigned_resource_id IS NOT NULL
            )
            SELECT
                count(*) AS total_tickets,
                count(*) FILTER (WHERE t.updated_at_autotask IS NOT NULL) AS tickets_with_autotask_updated_at,
                min(t.updated_at_autotask) AS oldest_autotask_update,
                max(t.updated_at_autotask) AS newest_autotask_update,
                count(*) FILTER (WHERE COALESCE(note_tickets.row_count, 0) > 0) AS tickets_with_notes,
                count(*) FILTER (WHERE note_check.last_checked_at IS NOT NULL) AS tickets_checked_for_notes,
                count(*) FILTER (
                    WHERE COALESCE(note_tickets.row_count, 0) = 0
                      AND note_check.last_checked_at IS NOT NULL
                      AND COALESCE(note_check.last_result_count, 0) = 0
                ) AS tickets_checked_empty_notes,
                count(*) FILTER (
                    WHERE COALESCE(note_tickets.row_count, 0) = 0
                      AND note_check.last_checked_at IS NULL
                ) AS tickets_unchecked_notes,
                count(*) FILTER (WHERE COALESCE(time_tickets.row_count, 0) > 0) AS tickets_with_time_entries,
                count(*) FILTER (WHERE estate_labor_check.last_checked_at IS NOT NULL) AS tickets_checked_for_time_entries,
                count(*) FILTER (
                    WHERE COALESCE(time_tickets.row_count, 0) = 0
                      AND estate_labor_check.last_checked_at IS NOT NULL
                      AND COALESCE(estate_labor_check.last_result_count, 0) = 0
                ) AS tickets_checked_empty_time_entries,
                count(*) FILTER (
                    WHERE COALESCE(time_tickets.row_count, 0) = 0
                      AND estate_labor_check.last_checked_at IS NULL
                ) AS tickets_unchecked_time_entries,
                count(*) FILTER (WHERE COALESCE(history_tickets.row_count, 0) > 0) AS tickets_with_history,
                count(*) FILTER (WHERE history_checks.last_checked_at IS NOT NULL) AS tickets_checked_for_history,
                count(*) FILTER (
                    WHERE COALESCE(history_tickets.row_count, 0) = 0
                      AND history_checks.last_checked_at IS NOT NULL
                      AND COALESCE(history_checks.max_result_count, 0) = 0
                ) AS tickets_checked_empty_history,
                count(*) FILTER (
                    WHERE COALESCE(history_tickets.row_count, 0) = 0
                      AND history_checks.last_checked_at IS NULL
                ) AS tickets_unchecked_history,
                COALESCE(sum(note_tickets.row_count), 0) AS ticket_note_rows,
                COALESCE(sum(time_tickets.row_count), 0) AS time_entry_rows,
                COALESCE(sum(history_tickets.row_count), 0) AS ticket_history_rows,
                (SELECT count(*) FROM assigned_resources) AS assigned_resource_ids,
                (
                    SELECT count(*)
                    FROM assigned_resources ar
                    JOIN autotask_reference_values ref
                      ON ref.field_name='resource' AND ref.value=ar.assigned_resource_id::text
                ) AS assigned_resource_ids_with_reference,
                (SELECT count(*) FROM autotask_reference_values WHERE field_name='resource') AS resource_reference_rows
            FROM autotask_tickets t
            LEFT JOIN note_tickets ON note_tickets.ticket_id=t.id
            LEFT JOIN time_tickets ON time_tickets.ticket_id=t.id
            LEFT JOIN history_tickets ON history_tickets.ticket_id=t.id
            LEFT JOIN history_checks ON history_checks.ticket_id=t.id
            LEFT JOIN ticket_gap_sync_checks note_check
              ON note_check.ticket_id=t.id AND note_check.sync_type='ticket_note_gaps'
            LEFT JOIN ticket_gap_sync_checks estate_labor_check
              ON estate_labor_check.ticket_id=t.id AND estate_labor_check.sync_type='ticket_time_entry_gaps'
            """
        ).fetchone()
        estate_labor_targets = list(
            conn.execute(
                """
                SELECT
                    t.id,
                    t.autotask_id,
                    t.ticket_number,
                    t.status,
                    status_ref.label AS status_label,
                    COALESCE(time_tickets.row_count, 0) AS time_entry_count,
                    estate_labor_check.last_checked_at,
                    estate_labor_check.last_result_count
                FROM autotask_tickets t
                LEFT JOIN (
                    SELECT ticket_id, count(*) AS row_count
                    FROM autotask_time_entries
                    WHERE ticket_id IS NOT NULL
                    GROUP BY ticket_id
                ) time_tickets ON time_tickets.ticket_id=t.id
                LEFT JOIN ticket_gap_sync_checks estate_labor_check
                  ON estate_labor_check.ticket_id=t.id AND estate_labor_check.sync_type='ticket_time_entry_gaps'
                LEFT JOIN autotask_reference_values status_ref
                  ON status_ref.field_name='status' AND status_ref.value=t.status
                WHERE COALESCE(time_tickets.row_count, 0) = 0
                ORDER BY
                    estate_labor_check.last_checked_at NULLS FIRST,
                    t.updated_at_autotask DESC NULLS LAST,
                    t.id
                LIMIT 10
                """
            ).fetchall()
        )
        estate_history_targets = list(
            conn.execute(
                """
                SELECT
                    t.id,
                    t.autotask_id,
                    t.ticket_number,
                    t.status,
                    status_ref.label AS status_label,
                    COALESCE(history_tickets.row_count, 0) AS history_count,
                    history_check.last_checked_at,
                    history_check.last_result_count
                FROM autotask_tickets t
                LEFT JOIN (
                    SELECT ticket_id, count(*) AS row_count
                    FROM autotask_ticket_history
                    WHERE ticket_id IS NOT NULL
                    GROUP BY ticket_id
                ) history_tickets ON history_tickets.ticket_id=t.id
                LEFT JOIN (
                    SELECT
                        ticket_id,
                        max(last_checked_at) AS last_checked_at,
                        max(last_result_count) AS last_result_count
                    FROM ticket_gap_sync_checks
                    WHERE sync_type IN ('ticket_history_gaps', 'open_ticket_history_gaps', 'status_sample_ticket_history')
                    GROUP BY ticket_id
                ) history_check ON history_check.ticket_id=t.id
                LEFT JOIN autotask_reference_values status_ref
                  ON status_ref.field_name='status' AND status_ref.value=t.status
                WHERE COALESCE(history_tickets.row_count, 0) = 0
                ORDER BY
                    history_check.last_checked_at NULLS FIRST,
                    t.updated_at_autotask DESC NULLS LAST,
                    t.id
                LIMIT 10
                """
            ).fetchall()
        )
        running = list(conn.execute("SELECT * FROM job_runs WHERE status='running' ORDER BY started_at DESC").fetchall())
        scheduler = _scheduler_status(conn, datetime.now(UTC))
    noise = noise_report()
    threshold_remaining: int | None = None
    threshold_error: str | None = None
    try:
        threshold_remaining = autotask_threshold_remaining()
    except Exception as exc:
        threshold_error = str(exc)[:300]
    estate_coverage = _operations_estate_coverage(
        dict(estate),
        estate_labor_targets=[dict(row) for row in estate_labor_targets],
        estate_history_targets=[dict(row) for row in estate_history_targets],
    )
    result = {
        "ok": True,
        "cache": {"hit": False, "ttl_seconds": app_settings.operations_status_cache_ttl_seconds, "scoped": True},
        "api_status": "ok",
        "db_status": "ok",
        "ollama_status": "available" if ollama_available() else "unavailable",
        "autotask_threshold_remaining": threshold_remaining,
        "autotask_threshold_error": threshold_error,
        "disk_free_gb": round(disk_free_gb("/"), 2),
        "global_pause": settings["global_pause"],
        "counts": {**dict(counts), "eligible_missing_embeddings": noise.get("eligible_missing_embeddings", 0)},
        "coverage": _operations_coverage(dict(coverage)),
        "estate": estate_coverage,
        "related_data_work_plan": _related_data_work_plan(
            estate_coverage,
            settings,
            threshold_remaining=threshold_remaining,
            global_pause=bool(settings["global_pause"]),
        ),
        "scheduler": scheduler,
        "scheduler_automation": scheduler_automation_certification_report(),
        "running_jobs": running,
    }
    encoded_result = jsonable_encoder(result)
    cache_set_json(cache_key, encoded_result, app_settings.operations_status_cache_ttl_seconds)
    return encoded_result
