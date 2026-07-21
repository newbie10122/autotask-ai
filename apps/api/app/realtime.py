from __future__ import annotations

import json
import time
from datetime import datetime
from typing import Any, Iterable

from fastapi.encoders import jsonable_encoder

from .db import db_connection


def _event_time(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value or "")


def recent_realtime_events(limit: int = 25) -> dict[str, Any]:
    row_limit = min(max(limit, 1), 100)
    per_source_limit = max(row_limit, 10)
    with db_connection() as conn:
        job_rows = list(
            conn.execute(
                """
                SELECT id, job_name, status, started_at, finished_at, current_step,
                       pulled_count, inserted_count, updated_count, failed_count, last_error
                FROM job_runs
                ORDER BY COALESCE(finished_at, started_at) DESC, id DESC
                LIMIT %s
                """,
                (per_source_limit,),
            ).fetchall()
        )
        history_rows = list(
            conn.execute(
                """
                SELECT h.id, h.autotask_ticket_id, h.ticket_id, t.ticket_number, t.title,
                       h.action, h.detail, h.resource_id, h.happened_at, h.synced_at
                FROM autotask_ticket_history h
                LEFT JOIN autotask_tickets t ON t.id = h.ticket_id
                ORDER BY COALESCE(h.happened_at, h.synced_at) DESC, h.id DESC
                LIMIT %s
                """,
                (per_source_limit,),
            ).fetchall()
        )

    events: list[dict[str, Any]] = []
    for row in job_rows:
        timestamp = row["finished_at"] or row["started_at"]
        events.append(
            {
                "id": f"job:{row['id']}",
                "type": "job",
                "label": f"{row['job_name']} {row['status']}",
                "timestamp": _event_time(timestamp),
                "severity": "error" if row["status"] == "failed" or row["failed_count"] else "info",
                "data": dict(row),
            }
        )
    for row in history_rows:
        timestamp = row["happened_at"] or row["synced_at"]
        ticket_label = row["ticket_number"] or row["autotask_ticket_id"]
        events.append(
            {
                "id": f"ticket-history:{row['id']}",
                "type": "ticket_history",
                "label": f"{ticket_label}: {row['action'] or 'Ticket update'}",
                "timestamp": _event_time(timestamp),
                "severity": "info",
                "data": dict(row),
            }
        )

    events.sort(key=lambda event: event["timestamp"], reverse=True)
    return {"ok": True, "events": jsonable_encoder(events[:row_limit])}


def _sse(event: str, payload: dict[str, Any]) -> str:
    encoded = json.dumps(jsonable_encoder(payload), sort_keys=True)
    return f"event: {event}\ndata: {encoded}\n\n"


def realtime_event_stream(poll_seconds: int = 10) -> Iterable[str]:
    seen: set[str] = set()
    yield _sse("heartbeat", {"ok": True, "message": "connected"})
    while True:
        try:
            events = recent_realtime_events(limit=25)["events"]
            fresh = [event for event in reversed(events) if event["id"] not in seen]
            for event in fresh:
                seen.add(event["id"])
                yield _sse("update", event)
        except Exception as exc:
            yield _sse("error", {"ok": False, "message": str(exc)})
        time.sleep(max(poll_seconds, 1))
