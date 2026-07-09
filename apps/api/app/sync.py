from __future__ import annotations

from datetime import datetime
from typing import Any

from psycopg.types.json import Jsonb

from .autotask import AutotaskReadOnlyClient
from .config import settings
from .db import db_connection, init_schema
from .ticket_classifier import classify_ticket


def _field(record: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in record and record[name] is not None:
            return record[name]
    return None


def _parse_dt(value: Any) -> Any:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _create_run(sync_type: str) -> int:
    init_schema()
    with db_connection() as conn:
        row = conn.execute(
            "INSERT INTO autotask_sync_runs(sync_type, status) VALUES (%s, 'running') RETURNING id",
            (sync_type,),
        ).fetchone()
        return int(row["id"])


def _finish_run(run_id: int, status: str, stats: dict[str, Any], error: str | None = None) -> None:
    with db_connection() as conn:
        conn.execute(
            """
            UPDATE autotask_sync_runs
            SET status=%s, records_processed=%s, pulled_count=%s, inserted_count=%s,
                updated_count=%s, failed_count=%s, checkpoint=%s, resume_token=%s,
                last_error=%s, finished_at=now()
            WHERE id=%s
            """,
            (
                status,
                stats.get("pulled", 0),
                stats.get("pulled", 0),
                stats.get("inserted", 0),
                stats.get("updated", 0),
                stats.get("failed", 0),
                Jsonb(stats.get("checkpoint", {})),
                str(stats.get("checkpoint", {}).get("last_seen_id", "")),
                error,
                run_id,
            ),
        )


def _update_run_progress(run_id: int, stats: dict[str, Any]) -> None:
    with db_connection() as conn:
        conn.execute(
            """
            UPDATE autotask_sync_runs
            SET records_processed=%s, pulled_count=%s, inserted_count=%s,
                updated_count=%s, failed_count=%s, checkpoint=%s, resume_token=%s
            WHERE id=%s
            """,
            (
                stats.get("pulled", 0),
                stats.get("pulled", 0),
                stats.get("inserted", 0),
                stats.get("updated", 0),
                stats.get("failed", 0),
                Jsonb(stats.get("checkpoint", {})),
                str(stats.get("checkpoint", {}).get("last_seen_id", "")),
                run_id,
            ),
        )


def _last_checkpoint(sync_type: str) -> int:
    init_schema()
    with db_connection() as conn:
        row = conn.execute(
            """
            SELECT checkpoint->>'last_seen_id' AS last_seen_id
            FROM autotask_sync_runs
            WHERE sync_type=%s AND status='completed'
            ORDER BY id DESC
            LIMIT 1
            """,
            (sync_type,),
        ).fetchone()
        if not row or not row["last_seen_id"]:
            return 0
        return int(row["last_seen_id"])


def _iter_id_pages(client: AutotaskReadOnlyClient, entity: str, last_seen: int, limit: int | None):
    pulled = 0
    while limit is None or pulled < limit:
        payload = client.query_entity(entity, filters=[{"op": "gt", "field": "id", "value": last_seen}])
        items = payload.get("items") or payload.get("records") or payload.get("value") or []
        if limit is not None:
            items = items[: max(0, limit - pulled)]
        if not items:
            break
        page_last_seen = max(int(item.get("id", last_seen)) for item in items)
        pulled += len(items)
        yield items, page_last_seen
        last_seen = max(last_seen, page_last_seen)
        if len(items) < client.page_size:
            break


def _should_skip_ticket(item: dict[str, Any]) -> bool:
    result = classify_ticket(
        _field(item, "title"),
        _field(item, "description"),
        item,
    )
    return bool(
        result["analytics_exclude"]
        and result["analytics_exclude_reason"] in {"monitoring_alert", "onsite_maintenance"}
    )


def sync_companies(limit: int | None = None, full_sync: bool = False) -> dict[str, Any]:
    run_id = _create_run("companies")
    stats = {"run_id": run_id, "pulled": 0, "inserted": 0, "updated": 0, "failed": 0, "checkpoint": {}}
    try:
        last_seen = 0 if full_sync else _last_checkpoint("companies")
        limit = None if full_sync else (limit or settings.autotask_sync_batch_limit)
        client = AutotaskReadOnlyClient(sync_run_id=run_id)
        for items, page_last_seen in _iter_id_pages(client, "Companies", last_seen, limit):
            with db_connection() as conn:
                for item in items:
                    try:
                        autotask_id = int(item["id"])
                        name = str(_field(item, "companyName", "name", "accountName") or f"Company {autotask_id}")
                        row = conn.execute(
                            """
                            INSERT INTO autotask_companies(autotask_id, name, raw, updated_at)
                            VALUES (%s, %s, %s, now())
                            ON CONFLICT (autotask_id) DO UPDATE
                            SET name=EXCLUDED.name, raw=EXCLUDED.raw, updated_at=now()
                            RETURNING (xmax = 0) AS inserted
                            """,
                            (autotask_id, name, Jsonb(item)),
                        ).fetchone()
                        stats["inserted" if row["inserted"] else "updated"] += 1
                        stats["pulled"] += 1
                        last_seen = max(last_seen, autotask_id)
                    except Exception:
                        stats["failed"] += 1
            last_seen = max(last_seen, page_last_seen)
            stats["checkpoint"] = {"last_seen_id": last_seen}
            _update_run_progress(run_id, stats)
        _finish_run(run_id, "completed", stats)
        return stats
    except Exception as exc:
        _finish_run(run_id, "failed", stats, str(exc))
        raise


def sync_tickets(limit: int | None = None, full_sync: bool = False) -> dict[str, Any]:
    run_id = _create_run("tickets")
    stats = {"run_id": run_id, "pulled": 0, "inserted": 0, "updated": 0, "skipped": 0, "failed": 0, "checkpoint": {}}
    try:
        last_seen = 0 if full_sync else _last_checkpoint("tickets")
        limit = None if full_sync else (limit or settings.autotask_sync_batch_limit)
        client = AutotaskReadOnlyClient(sync_run_id=run_id)
        for items, page_last_seen in _iter_id_pages(client, "Tickets", last_seen, limit):
            with db_connection() as conn:
                for item in items:
                    try:
                        autotask_id = int(item["id"])
                        stats["pulled"] += 1
                        last_seen = max(last_seen, autotask_id)
                        if _should_skip_ticket(item):
                            stats["skipped"] += 1
                            continue
                        company_autotask_id = _field(item, "companyID", "accountID", "companyId")
                        company_row = None
                        if company_autotask_id:
                            company_row = conn.execute(
                                "SELECT id FROM autotask_companies WHERE autotask_id=%s",
                                (int(company_autotask_id),),
                            ).fetchone()
                        row = conn.execute(
                            """
                            INSERT INTO autotask_tickets(
                                autotask_id, company_id, ticket_number, title, description, status, priority,
                                queue, category, issue_type, subissue_type, assigned_resource_id,
                                assigned_resource_name, created_at_autotask, updated_at_autotask,
                                completed_at_autotask, raw
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (autotask_id) DO UPDATE SET
                                company_id=EXCLUDED.company_id, ticket_number=EXCLUDED.ticket_number,
                                title=EXCLUDED.title, description=EXCLUDED.description, status=EXCLUDED.status,
                                priority=EXCLUDED.priority, queue=EXCLUDED.queue, category=EXCLUDED.category,
                                issue_type=EXCLUDED.issue_type, subissue_type=EXCLUDED.subissue_type,
                                assigned_resource_id=EXCLUDED.assigned_resource_id,
                                assigned_resource_name=EXCLUDED.assigned_resource_name,
                                created_at_autotask=EXCLUDED.created_at_autotask,
                                updated_at_autotask=EXCLUDED.updated_at_autotask,
                                completed_at_autotask=EXCLUDED.completed_at_autotask,
                                raw=EXCLUDED.raw
                            RETURNING (xmax = 0) AS inserted
                            """,
                            (
                                autotask_id,
                                company_row["id"] if company_row else None,
                                _field(item, "ticketNumber", "ticket_number"),
                                _field(item, "title"),
                                _field(item, "description"),
                                str(_field(item, "status") or ""),
                                str(_field(item, "priority") or ""),
                                str(_field(item, "queueID", "queue") or ""),
                                str(_field(item, "category", "ticketCategory") or ""),
                                str(_field(item, "issueType", "issueTypeID") or ""),
                                str(_field(item, "subIssueType", "subIssueTypeID") or ""),
                                _field(item, "assignedResourceID", "assignedResourceId"),
                                _field(item, "assignedResourceName"),
                                _parse_dt(_field(item, "createDate", "createdDateTime")),
                                _parse_dt(_field(item, "lastActivityDate", "lastModifiedDateTime")),
                                _parse_dt(_field(item, "completedDate", "resolvedDateTime")),
                                Jsonb(item),
                            ),
                        ).fetchone()
                        stats["inserted" if row["inserted"] else "updated"] += 1
                    except Exception:
                        stats["failed"] += 1
            last_seen = max(last_seen, page_last_seen)
            stats["checkpoint"] = {"last_seen_id": last_seen}
            _update_run_progress(run_id, stats)
        _finish_run(run_id, "completed", stats)
        return stats
    except Exception as exc:
        _finish_run(run_id, "failed", stats, str(exc))
        raise


def sync_ticket_notes(limit: int | None = None, full_sync: bool = False) -> dict[str, Any]:
    run_id = _create_run("ticket_notes")
    stats = {"run_id": run_id, "pulled": 0, "inserted": 0, "updated": 0, "skipped": 0, "failed": 0, "checkpoint": {}}
    try:
        last_seen = 0 if full_sync else _last_checkpoint("ticket_notes")
        limit = None if full_sync else (limit or settings.autotask_sync_batch_limit)
        client = AutotaskReadOnlyClient(sync_run_id=run_id, delay_seconds=0.4)
        for items, page_last_seen in _iter_id_pages(client, "TicketNotes", last_seen, limit):
            with db_connection() as conn:
                for item in items:
                    try:
                        autotask_id = int(item["id"])
                        stats["pulled"] += 1
                        last_seen = max(last_seen, autotask_id)
                        autotask_ticket_id = _field(item, "ticketID", "ticketId")
                        ticket_row = None
                        if autotask_ticket_id:
                            ticket_row = conn.execute(
                                "SELECT id FROM autotask_tickets WHERE autotask_id=%s",
                                (int(autotask_ticket_id),),
                            ).fetchone()
                        if not ticket_row:
                            stats["skipped"] += 1
                            continue
                        row = conn.execute(
                            """
                            INSERT INTO autotask_ticket_notes(
                                autotask_id, ticket_id, autotask_ticket_id, title, note_type, body,
                                resource_id, resource_name, created_at_autotask, updated_at_autotask, raw
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (autotask_id) DO UPDATE SET
                                ticket_id=EXCLUDED.ticket_id, autotask_ticket_id=EXCLUDED.autotask_ticket_id,
                                title=EXCLUDED.title, note_type=EXCLUDED.note_type, body=EXCLUDED.body,
                                resource_id=EXCLUDED.resource_id, resource_name=EXCLUDED.resource_name,
                                created_at_autotask=EXCLUDED.created_at_autotask,
                                updated_at_autotask=EXCLUDED.updated_at_autotask, raw=EXCLUDED.raw
                            RETURNING (xmax = 0) AS inserted
                            """,
                            (
                                autotask_id,
                                ticket_row["id"] if ticket_row else None,
                                int(autotask_ticket_id) if autotask_ticket_id else None,
                                _field(item, "title"),
                                str(_field(item, "noteType", "type") or ""),
                                _field(item, "description", "body", "note"),
                                _field(item, "creatorResourceID", "resourceID"),
                                _field(item, "creatorResourceName", "resourceName"),
                                _parse_dt(_field(item, "createdDateTime", "createDate")),
                                _parse_dt(_field(item, "lastModifiedDateTime")),
                                Jsonb(item),
                            ),
                        ).fetchone()
                        stats["inserted" if row["inserted"] else "updated"] += 1
                    except Exception:
                        stats["failed"] += 1
            last_seen = max(last_seen, page_last_seen)
            stats["checkpoint"] = {"last_seen_id": last_seen}
            _update_run_progress(run_id, stats)
        _finish_run(run_id, "completed", stats)
        return stats
    except Exception as exc:
        _finish_run(run_id, "failed", stats, str(exc))
        raise


def sync_recent(limit: int | None = None) -> dict[str, Any]:
    companies = sync_companies(limit=limit or 100)
    tickets = sync_tickets(limit=limit or 100)
    notes = sync_ticket_notes(limit=limit or 100)
    return {"companies": companies, "tickets": tickets, "ticket_notes": notes}


def sync_status() -> dict[str, Any]:
    init_schema()
    with db_connection() as conn:
        current = conn.execute(
            "SELECT * FROM autotask_sync_runs WHERE status='running' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        last = conn.execute("SELECT * FROM autotask_sync_runs ORDER BY id DESC LIMIT 1").fetchone()
        calls = conn.execute("SELECT count(*) AS count FROM autotask_api_calls").fetchone()
    return {"current_run": current, "last_run": last, "api_call_count": calls["count"] if calls else 0}


def sync_runs(limit: int = 20) -> list[dict[str, Any]]:
    init_schema()
    with db_connection() as conn:
        return list(
            conn.execute(
                "SELECT * FROM autotask_sync_runs ORDER BY id DESC LIMIT %s",
                (min(max(limit, 1), 100),),
            ).fetchall()
        )
