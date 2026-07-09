from __future__ import annotations

import os
import shutil
import socket
import time
from datetime import UTC, datetime, time as clock_time
from typing import Any, Callable

import httpx
from psycopg.types.json import Jsonb

from .autotask import AutotaskReadOnlyClient
from .config import settings as app_settings
from .db import db_connection, init_schema
from .documents import create_documents_from_tickets, noise_report, reclassify_chunks
from .embeddings import run_embedding_batch
from .sync import sync_companies, sync_recent, sync_ticket_notes, sync_tickets
from .ticket_analytics import classify_tickets, sync_reference_data


DEFAULT_SETTINGS: dict[str, Any] = {
    "sync_enabled": True,
    "recent_sync_enabled": True,
    "recent_sync_interval_minutes": 15,
    "raw_backfill_enabled": False,
    "raw_backfill_batch_tickets": 5000,
    "raw_backfill_batch_notes": 5000,
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
    "autotask_threshold_min_remaining": 500,
    "min_free_disk_gb": 50,
    "global_pause": False,
}

DEFAULT_JOBS: dict[str, dict[str, Any]] = {
    "recent_sync": {"enabled": True, "cadence_seconds": 15 * 60, "schedule": "every 15 minutes"},
    "raw_backfill_tickets": {"enabled": False, "cadence_seconds": 60 * 60, "schedule": "hourly when enabled"},
    "raw_backfill_ticket_notes": {"enabled": False, "cadence_seconds": 60 * 60, "schedule": "hourly when enabled"},
    "raw_backfill_companies": {"enabled": False, "cadence_seconds": 60 * 60, "schedule": "hourly when enabled"},
    "sync_reference_data": {"enabled": True, "cadence_seconds": 6 * 60 * 60, "schedule": "every 6 hours"},
    "classify_tickets": {"enabled": True, "cadence_seconds": 30 * 60, "schedule": "every 30 minutes"},
    "build_documents": {"enabled": False, "cadence_seconds": 30 * 60, "schedule": "every 30 minutes when enabled"},
    "reclassify_chunks": {"enabled": True, "cadence_seconds": 60 * 60, "schedule": "hourly"},
    "run_embeddings": {"enabled": False, "cadence_seconds": 30 * 60, "schedule": "quiet-hours batches when enabled"},
    "nightly_pipeline": {"enabled": True, "cadence_seconds": 24 * 60 * 60, "schedule": "daily 02:00"},
}

AUTOTASK_JOBS = {"recent_sync", "raw_backfill_tickets", "raw_backfill_ticket_notes", "raw_backfill_companies"}
RAW_BACKFILL_JOBS = {"raw_backfill_tickets", "raw_backfill_ticket_notes", "raw_backfill_companies"}
MUTATES_CHUNKS = {"build_documents", "reclassify_chunks"}


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
        for job_name, job in DEFAULT_JOBS.items():
            conn.execute(
                """
                INSERT INTO scheduled_jobs(job_name, enabled, cadence_seconds, schedule)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (job_name) DO NOTHING
                """,
                (job_name, job["enabled"], job["cadence_seconds"], job["schedule"]),
            )


def operations_settings() -> dict[str, Any]:
    ensure_operations_defaults()
    with db_connection() as conn:
        rows = conn.execute("SELECT key, value FROM system_settings ORDER BY key").fetchall()
    merged = default_operations_settings()
    for row in rows:
        merged[row["key"]] = row["value"]
    return merged


def update_operations_settings(changes: dict[str, Any]) -> dict[str, Any]:
    ensure_operations_defaults()
    allowed = set(DEFAULT_SETTINGS)
    with db_connection() as conn:
        for key, value in changes.items():
            if key not in allowed:
                continue
            conn.execute(
                """
                INSERT INTO system_settings(key, value, updated_at)
                VALUES (%s, %s, now())
                ON CONFLICT (key) DO UPDATE
                SET value=EXCLUDED.value, updated_at=now()
                """,
                (key, Jsonb(value)),
            )
    _sync_job_enabled_from_settings()
    return operations_settings()


def _sync_job_enabled_from_settings() -> None:
    settings = operations_settings()
    mapping = {
        "recent_sync": bool(settings["sync_enabled"] and settings["recent_sync_enabled"]),
        "raw_backfill_tickets": bool(settings["raw_backfill_enabled"]),
        "raw_backfill_ticket_notes": bool(settings["raw_backfill_enabled"]),
        "raw_backfill_companies": bool(settings["raw_backfill_enabled"]),
        "build_documents": bool(settings["document_build_enabled"]),
        "classify_tickets": bool(settings["ticket_classification_enabled"]),
        "reclassify_chunks": bool(settings["chunk_reclassification_enabled"]),
        "run_embeddings": bool(settings["embedding_enabled"]),
        "nightly_pipeline": bool(settings["nightly_pipeline_enabled"]),
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
            Jsonb(stats.get("checkpoint", {})),
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
        (status, Jsonb(stats.get("checkpoint", {})), error[:1000] if error else None, job_name),
    )
    conn.execute("DELETE FROM job_locks WHERE job_name=%s", (job_name,))


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


def _execute_job(job_name: str, settings: dict[str, Any]) -> dict[str, Any]:
    if job_name == "recent_sync":
        return sync_recent(limit=100)
    if job_name == "raw_backfill_companies":
        return sync_companies(limit=_int(settings, "raw_backfill_batch_tickets"))
    if job_name == "raw_backfill_tickets":
        return sync_tickets(limit=_int(settings, "raw_backfill_batch_tickets"))
    if job_name == "raw_backfill_ticket_notes":
        return sync_ticket_notes(limit=_int(settings, "raw_backfill_batch_notes"))
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
    return {"ok": bool(row), "job": row}


def operations_jobs() -> dict[str, Any]:
    ensure_operations_defaults()
    with db_connection() as conn:
        jobs = list(conn.execute("SELECT * FROM scheduled_jobs ORDER BY job_name").fetchall())
        running = list(conn.execute("SELECT * FROM job_runs WHERE status='running' ORDER BY started_at DESC").fetchall())
    return {"ok": True, "jobs": jobs, "running": running}


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
    return {"ok": bool(row), "run": row}


def operations_status() -> dict[str, Any]:
    ensure_operations_defaults()
    settings = operations_settings()
    with db_connection() as conn:
        counts = conn.execute(
            """
            SELECT
              (SELECT count(*) FROM autotask_companies) AS companies,
              (SELECT count(*) FROM autotask_tickets) AS tickets,
              (SELECT count(*) FROM autotask_ticket_notes) AS ticket_notes,
              (SELECT count(*) FROM documents) AS documents,
              (SELECT count(*) FROM document_chunks WHERE is_active) AS active_chunks,
              (SELECT count(*) FROM document_chunks WHERE is_active AND is_noise) AS noise_chunks,
              (SELECT count(*) FROM document_chunks WHERE is_active AND NOT is_noise) AS useful_chunks,
              (SELECT count(*) FROM document_embeddings) AS embeddings
            """
        ).fetchone()
        running = list(conn.execute("SELECT * FROM job_runs WHERE status='running' ORDER BY started_at DESC").fetchall())
    noise = noise_report()
    threshold_remaining: int | None = None
    threshold_error: str | None = None
    try:
        threshold_remaining = autotask_threshold_remaining()
    except Exception as exc:
        threshold_error = str(exc)[:300]
    return {
        "ok": True,
        "api_status": "ok",
        "db_status": "ok",
        "ollama_status": "available" if ollama_available() else "unavailable",
        "autotask_threshold_remaining": threshold_remaining,
        "autotask_threshold_error": threshold_error,
        "disk_free_gb": round(disk_free_gb("/"), 2),
        "global_pause": settings["global_pause"],
        "counts": {**dict(counts), "eligible_missing_embeddings": noise.get("eligible_missing_embeddings", 0)},
        "running_jobs": running,
    }
