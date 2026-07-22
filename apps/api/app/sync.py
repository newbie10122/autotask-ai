from __future__ import annotations

from contextlib import nullcontext
from datetime import UTC, datetime, timedelta
from typing import Any

from psycopg.types.json import Jsonb

from .autotask import AutotaskReadOnlyClient
from .cache import invalidate_dashboard_caches
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


def _parse_hours(value: Any) -> Any:
    if value in (None, ""):
        return None
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def _json_ready(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    return value


def _sync_run_response(row: dict[str, Any]) -> dict[str, Any]:
    item = dict(row)
    checkpoint = item.get("checkpoint") or {}
    if not isinstance(checkpoint, dict):
        checkpoint = {}
    failures = checkpoint.get("item_failures") or []
    if not isinstance(failures, list):
        failures = []
    item["checkpoint"] = checkpoint
    item["last_item_error"] = checkpoint.get("last_item_error")
    item["item_failures"] = failures[:5]
    item["item_failure_count"] = len(failures)
    return item


def _create_run(sync_type: str) -> int:
    init_schema()
    with db_connection() as conn:
        row = conn.execute(
            "INSERT INTO autotask_sync_runs(sync_type, status) VALUES (%s, 'running') RETURNING id",
            (sync_type,),
        ).fetchone()
        return int(row["id"])


def _finish_run(run_id: int, status: str, stats: dict[str, Any], error: str | None = None) -> None:
    if error is None and status == "completed" and int(stats.get("failed") or 0) > 0:
        error = f"completed with {int(stats.get('failed') or 0)} item-level failure(s)"
        last_item_error = (stats.get("checkpoint") or {}).get("last_item_error")
        if last_item_error:
            error = f"{error}; last item error: {last_item_error}"
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
                stats.get("processed_tickets", stats.get("pulled", 0)),
                stats.get("processed_tickets", stats.get("pulled", 0)),
                stats.get("inserted", 0),
                stats.get("updated", 0),
                stats.get("failed", 0),
                Jsonb(_json_ready(stats.get("checkpoint", {}))),
                str(stats.get("checkpoint", {}).get("last_seen_id", "")),
                error,
                run_id,
            ),
        )
    if status == "completed":
        invalidate_dashboard_caches()


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
                Jsonb(_json_ready(stats.get("checkpoint", {}))),
                str(stats.get("checkpoint", {}).get("last_seen_id", "")),
                run_id,
            ),
        )


def _mark_gap_check(
    conn: Any,
    *,
    ticket_id: int,
    sync_type: str,
    run_id: int,
    result_count: int,
    error: str | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO ticket_gap_sync_checks(ticket_id, sync_type, last_checked_at, last_run_id, last_result_count, last_error)
        VALUES (%s, %s, now(), %s, %s, %s)
        ON CONFLICT (ticket_id, sync_type) DO UPDATE SET
            last_checked_at=now(),
            last_run_id=EXCLUDED.last_run_id,
            last_result_count=EXCLUDED.last_result_count,
            last_error=EXCLUDED.last_error
        """,
        (ticket_id, sync_type, run_id, result_count, error),
    )


def _record_item_failure(stats: dict[str, Any], exc: Exception, **context: Any) -> None:
    checkpoint = stats.setdefault("checkpoint", {})
    message = str(exc) or exc.__class__.__name__
    checkpoint["last_item_error"] = message[:500]
    failures = checkpoint.setdefault("item_failures", [])
    if len(failures) < 5:
        failures.append(
            {
                **{key: value for key, value in context.items() if value is not None},
                "error": message[:500],
            }
        )


def _item_write_scope(conn: Any):
    transaction = getattr(conn, "transaction", None)
    if callable(transaction):
        return transaction()
    return nullcontext()


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
                    except Exception as exc:
                        stats["failed"] += 1
                        _record_item_failure(
                            stats,
                            exc,
                            company_autotask_id=item.get("id") if isinstance(item, dict) else None,
                        )
            last_seen = max(last_seen, page_last_seen)
            stats["checkpoint"].update({"last_seen_id": last_seen})
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
                                completed_at_autotask, contact_autotask_id, due_at_autotask,
                                first_response_at_autotask, first_response_due_at_autotask,
                                resolution_plan_at_autotask, resolution_plan_due_at_autotask,
                                resolved_due_at_autotask, sla_id, sla_met,
                                sla_paused_next_event_hours, completed_by_resource_id, raw
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                                contact_autotask_id=EXCLUDED.contact_autotask_id,
                                due_at_autotask=EXCLUDED.due_at_autotask,
                                first_response_at_autotask=EXCLUDED.first_response_at_autotask,
                                first_response_due_at_autotask=EXCLUDED.first_response_due_at_autotask,
                                resolution_plan_at_autotask=EXCLUDED.resolution_plan_at_autotask,
                                resolution_plan_due_at_autotask=EXCLUDED.resolution_plan_due_at_autotask,
                                resolved_due_at_autotask=EXCLUDED.resolved_due_at_autotask,
                                sla_id=EXCLUDED.sla_id,
                                sla_met=EXCLUDED.sla_met,
                                sla_paused_next_event_hours=EXCLUDED.sla_paused_next_event_hours,
                                completed_by_resource_id=EXCLUDED.completed_by_resource_id,
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
                                _field(item, "contactID", "contactId"),
                                _parse_dt(_field(item, "dueDateTime")),
                                _parse_dt(_field(item, "firstResponseDateTime")),
                                _parse_dt(_field(item, "firstResponseDueDateTime")),
                                _parse_dt(_field(item, "resolutionPlanDateTime")),
                                _parse_dt(_field(item, "resolutionPlanDueDateTime")),
                                _parse_dt(_field(item, "resolvedDueDateTime")),
                                _field(item, "serviceLevelAgreementID"),
                                _field(item, "serviceLevelAgreementHasBeenMet"),
                                _field(item, "serviceLevelAgreementPausedNextEventHours"),
                                _field(item, "completedByResourceID"),
                                Jsonb(item),
                            ),
                        ).fetchone()
                        stats["inserted" if row["inserted"] else "updated"] += 1
                    except Exception as exc:
                        stats["failed"] += 1
                        _record_item_failure(
                            stats,
                            exc,
                            autotask_ticket_id=item.get("id") if isinstance(item, dict) else None,
                        )
            last_seen = max(last_seen, page_last_seen)
            stats["checkpoint"].update({"last_seen_id": last_seen})
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
                                _parse_dt(_field(item, "createDateTime", "createdDateTime", "createDate")),
                                _parse_dt(_field(item, "lastModifiedDateTime")),
                                Jsonb(item),
                            ),
                        ).fetchone()
                        stats["inserted" if row["inserted"] else "updated"] += 1
                    except Exception as exc:
                        stats["failed"] += 1
                        _record_item_failure(
                            stats,
                            exc,
                            ticket_id=ticket_pk,
                            autotask_ticket_id=autotask_ticket_id,
                            note_id=item.get("id") if isinstance(item, dict) else None,
                        )
            last_seen = max(last_seen, page_last_seen)
            stats["checkpoint"].update({"last_seen_id": last_seen})
            _update_run_progress(run_id, stats)
        _finish_run(run_id, "completed", stats)
        return stats
    except Exception as exc:
        _finish_run(run_id, "failed", stats, str(exc))
        raise


def _upsert_ticket_note(conn: Any, *, item: dict[str, Any], ticket_pk: int, autotask_ticket_id: int | None) -> bool:
    autotask_id = int(item["id"])
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
            ticket_pk,
            int(autotask_ticket_id) if autotask_ticket_id else None,
            _field(item, "title"),
            str(_field(item, "noteType", "type") or ""),
            _field(item, "description", "body", "note"),
            _field(item, "creatorResourceID", "resourceID"),
            _field(item, "creatorResourceName", "resourceName"),
            _parse_dt(_field(item, "createDateTime", "createdDateTime", "createDate")),
            _parse_dt(_field(item, "lastModifiedDateTime")),
            Jsonb(item),
        ),
    ).fetchone()
    return bool(row["inserted"])


def sync_ticket_note_gaps(limit: int | None = None) -> dict[str, Any]:
    run_id = _create_run("ticket_note_gaps")
    row_limit = max(limit or 25, 1)
    stats = {
        "run_id": run_id,
        "processed_tickets": 0,
        "pulled": 0,
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
        "target": "tickets_missing_or_stale_notes",
        "checkpoint": {},
    }
    try:
        client = AutotaskReadOnlyClient(sync_run_id=run_id, delay_seconds=0.35)
        with db_connection() as conn:
            tickets = conn.execute(
                """
                SELECT
                    t.id,
                    t.autotask_id,
                    COALESCE(notes.note_count, 0) AS note_count,
                    notes.last_note_observed_at,
                    gap_check.last_checked_at AS last_gap_checked_at,
                    gap_check.last_result_count AS last_gap_result_count
                FROM autotask_tickets t
                LEFT JOIN (
                    SELECT
                        ticket_id,
                        count(*) AS note_count,
                        max(COALESCE(updated_at_autotask, created_at_autotask)) AS last_note_observed_at
                    FROM autotask_ticket_notes
                    GROUP BY ticket_id
                ) notes ON notes.ticket_id=t.id
                LEFT JOIN ticket_gap_sync_checks gap_check
                  ON gap_check.ticket_id=t.id AND gap_check.sync_type='ticket_note_gaps'
                ORDER BY
                    (COALESCE(notes.note_count, 0) = 0) DESC,
                    gap_check.last_checked_at NULLS FIRST,
                    notes.last_note_observed_at NULLS FIRST,
                    t.updated_at_autotask DESC NULLS LAST,
                    t.id
                LIMIT %s
                """,
                (row_limit,),
            ).fetchall()

        for ticket in tickets:
            ticket_pk = int(ticket["id"])
            autotask_ticket_id = int(ticket["autotask_id"])
            payload = client.query_entity(
                "TicketNotes",
                filters=[{"op": "eq", "field": "ticketID", "value": autotask_ticket_id}],
            )
            items = payload.get("items") or payload.get("records") or payload.get("value") or []
            item_count = len(items)
            with db_connection() as conn:
                for item in items:
                    try:
                        if _upsert_ticket_note(
                            conn,
                            item=item,
                            ticket_pk=ticket_pk,
                            autotask_ticket_id=autotask_ticket_id,
                        ):
                            stats["inserted"] += 1
                        else:
                            stats["updated"] += 1
                        stats["pulled"] += 1
                    except Exception as exc:
                        stats["failed"] += 1
                        _record_item_failure(
                            stats,
                            exc,
                            ticket_id=ticket_pk,
                            autotask_ticket_id=autotask_ticket_id,
                            note_id=item.get("id") if isinstance(item, dict) else None,
                        )
                _mark_gap_check(
                    conn,
                    ticket_id=ticket_pk,
                    sync_type="ticket_note_gaps",
                    run_id=run_id,
                    result_count=item_count,
                )
            stats["processed_tickets"] += 1
            stats["checkpoint"].update({
                "last_seen_id": ticket_pk,
                "last_ticket_pk": ticket_pk,
                "note_count": int(ticket.get("note_count") or 0),
                "last_gap_checked_at": ticket.get("last_gap_checked_at"),
                "last_gap_result_count": int(ticket.get("last_gap_result_count") or 0),
            })
            _update_run_progress(run_id, stats)

        _finish_run(run_id, "completed", stats)
        return stats
    except Exception as exc:
        _finish_run(run_id, "failed", stats, str(exc))
        raise


def sync_time_entries(limit: int | None = None, full_sync: bool = False) -> dict[str, Any]:
    run_id = _create_run("time_entries")
    stats = {"run_id": run_id, "pulled": 0, "inserted": 0, "updated": 0, "skipped": 0, "failed": 0, "checkpoint": {}}
    try:
        last_seen = 0 if full_sync else _last_checkpoint("time_entries")
        limit = None if full_sync else (limit or settings.autotask_sync_batch_limit)
        client = AutotaskReadOnlyClient(sync_run_id=run_id, delay_seconds=0.35)
        for items, page_last_seen in _iter_id_pages(client, "TimeEntries", last_seen, limit):
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
                        if _upsert_time_entry(
                            conn,
                            item=item,
                            ticket_pk=int(ticket_row["id"]),
                            autotask_ticket_id=int(autotask_ticket_id) if autotask_ticket_id else None,
                        ):
                            stats["inserted"] += 1
                        else:
                            stats["updated"] += 1
                    except Exception as exc:
                        stats["failed"] += 1
                        _record_item_failure(
                            stats,
                            exc,
                            ticket_id=int(ticket_row["id"]) if ticket_row else None,
                            autotask_ticket_id=autotask_ticket_id,
                            time_entry_id=item.get("id") if isinstance(item, dict) else None,
                        )
            last_seen = max(last_seen, page_last_seen)
            stats["checkpoint"].update({"last_seen_id": last_seen})
            _update_run_progress(run_id, stats)
        _finish_run(run_id, "completed", stats)
        return stats
    except Exception as exc:
        _finish_run(run_id, "failed", stats, str(exc))
        raise


def _upsert_time_entry(conn: Any, *, item: dict[str, Any], ticket_pk: int, autotask_ticket_id: int | None) -> bool:
    autotask_id = int(item["id"])
    row = conn.execute(
        """
        INSERT INTO autotask_time_entries(
            autotask_id, ticket_id, autotask_ticket_id, resource_id, resource_name,
            summary, hours, created_at_autotask, updated_at_autotask, raw
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (autotask_id) DO UPDATE SET
            ticket_id=EXCLUDED.ticket_id,
            autotask_ticket_id=EXCLUDED.autotask_ticket_id,
            resource_id=EXCLUDED.resource_id,
            resource_name=EXCLUDED.resource_name,
            summary=EXCLUDED.summary,
            hours=EXCLUDED.hours,
            created_at_autotask=EXCLUDED.created_at_autotask,
            updated_at_autotask=EXCLUDED.updated_at_autotask,
            raw=EXCLUDED.raw
        RETURNING (xmax = 0) AS inserted
        """,
        (
            autotask_id,
            ticket_pk,
            int(autotask_ticket_id) if autotask_ticket_id else None,
            _field(item, "resourceID", "resourceId", "creatorResourceID"),
            _field(item, "resourceName", "creatorResourceName"),
            _field(item, "summaryNotes", "summary", "description", "internalNotes"),
            _parse_hours(_field(item, "hoursWorked", "hoursToBill", "billingHours", "hours")),
            _parse_dt(_field(item, "dateWorked", "createdDateTime", "createDate")),
            _parse_dt(_field(item, "lastModifiedDateTime", "lastActivityDate")),
            Jsonb(item),
        ),
    ).fetchone()
    return bool(row["inserted"])


def sync_open_ticket_time_entry_gaps(limit: int | None = None) -> dict[str, Any]:
    run_id = _create_run("open_ticket_time_entry_gaps")
    row_limit = max(limit or 25, 1)
    stats = {
        "run_id": run_id,
        "processed_tickets": 0,
        "pulled": 0,
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
        "checked_empty": 0,
        "target": "open_tickets_missing_or_stale_time_entries",
        "checkpoint": {},
    }
    try:
        client = AutotaskReadOnlyClient(sync_run_id=run_id, delay_seconds=0.35)
        with db_connection() as conn:
            tickets = conn.execute(
                """
                SELECT
                    t.id,
                    t.autotask_id,
                    COALESCE(status_ref.label, t.status) AS status_label,
                    COALESCE(time_entries.entry_count, 0) AS time_entry_count,
                    COALESCE(time_entries.labor_hours, 0) AS labor_hours,
                    time_entries.last_time_entry_observed_at,
                    gap_check.last_checked_at AS last_gap_checked_at,
                    gap_check.last_result_count AS last_gap_result_count
                FROM autotask_tickets t
                LEFT JOIN autotask_reference_values status_ref
                  ON status_ref.field_name='status' AND status_ref.value=t.status
                LEFT JOIN (
                    SELECT
                        ticket_id,
                        count(*) AS entry_count,
                        sum(COALESCE(hours, 0)) AS labor_hours,
                        max(COALESCE(updated_at_autotask, created_at_autotask)) AS last_time_entry_observed_at
                    FROM autotask_time_entries
                    GROUP BY ticket_id
                ) time_entries ON time_entries.ticket_id=t.id
                LEFT JOIN ticket_gap_sync_checks gap_check
                  ON gap_check.ticket_id=t.id AND gap_check.sync_type='open_ticket_time_entry_gaps'
                WHERE t.completed_at_autotask IS NULL
                  AND COALESCE(t.status, '') <> ALL(%s)
                ORDER BY
                    (COALESCE(time_entries.entry_count, 0) = 0) DESC,
                    gap_check.last_checked_at NULLS FIRST,
                    time_entries.last_time_entry_observed_at NULLS FIRST,
                    t.updated_at_autotask DESC NULLS LAST,
                    t.id
                LIMIT %s
                """,
                (["5", "16", "20"], row_limit),
            ).fetchall()

        for ticket in tickets:
            ticket_pk = int(ticket["id"])
            autotask_ticket_id = int(ticket["autotask_id"])
            payload = client.query_entity(
                "TimeEntries",
                filters=[{"op": "eq", "field": "ticketID", "value": autotask_ticket_id}],
            )
            items = payload.get("items") or payload.get("records") or payload.get("value") or []
            item_count = len(items)
            with db_connection() as conn:
                for item in items:
                    try:
                        with _item_write_scope(conn):
                            if _upsert_time_entry(
                                conn,
                                item=item,
                                ticket_pk=ticket_pk,
                                autotask_ticket_id=autotask_ticket_id,
                            ):
                                stats["inserted"] += 1
                            else:
                                stats["updated"] += 1
                            stats["pulled"] += 1
                    except Exception as exc:
                        stats["failed"] += 1
                        _record_item_failure(
                            stats,
                            exc,
                            ticket_id=ticket_pk,
                            autotask_ticket_id=autotask_ticket_id,
                            time_entry_id=item.get("id") if isinstance(item, dict) else None,
                        )
                _mark_gap_check(
                    conn,
                    ticket_id=ticket_pk,
                    sync_type="open_ticket_time_entry_gaps",
                    run_id=run_id,
                    result_count=item_count,
                )
            checked_at = datetime.now(UTC).isoformat()
            if item_count == 0:
                stats["checked_empty"] += 1
            stats["processed_tickets"] += 1
            stats["checkpoint"].update({
                "last_seen_id": ticket_pk,
                "last_ticket_pk": ticket_pk,
                "tickets_checked": stats["processed_tickets"],
                "status_label": ticket.get("status_label"),
                "time_entry_count": int(ticket.get("time_entry_count") or 0),
                "labor_hours": float(ticket.get("labor_hours") or 0),
                "last_gap_checked_at": checked_at,
                "last_gap_result_count": item_count,
                "checked_empty": stats["checked_empty"],
                "last_successful_completion_at": checked_at,
            })
            _update_run_progress(run_id, stats)

        _finish_run(run_id, "completed", stats)
        return stats
    except Exception as exc:
        _finish_run(run_id, "failed", stats, str(exc))
        raise


def sync_ticket_time_entry_gaps(limit: int | None = None) -> dict[str, Any]:
    run_id = _create_run("ticket_time_entry_gaps")
    row_limit = max(limit or 25, 1)
    stats = {
        "run_id": run_id,
        "processed_tickets": 0,
        "pulled": 0,
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
        "checked_empty": 0,
        "target": "tickets_missing_or_stale_time_entries",
        "checkpoint": {},
    }
    try:
        client = AutotaskReadOnlyClient(sync_run_id=run_id, delay_seconds=0.35)
        with db_connection() as conn:
            tickets = conn.execute(
                """
                SELECT
                    t.id,
                    t.autotask_id,
                    COALESCE(time_entries.entry_count, 0) AS time_entry_count,
                    COALESCE(time_entries.labor_hours, 0) AS labor_hours,
                    time_entries.last_time_entry_observed_at,
                    gap_check.last_checked_at AS last_gap_checked_at,
                    gap_check.last_result_count AS last_gap_result_count
                FROM autotask_tickets t
                LEFT JOIN (
                    SELECT
                        ticket_id,
                        count(*) AS entry_count,
                        sum(COALESCE(hours, 0)) AS labor_hours,
                        max(COALESCE(updated_at_autotask, created_at_autotask)) AS last_time_entry_observed_at
                    FROM autotask_time_entries
                    GROUP BY ticket_id
                ) time_entries ON time_entries.ticket_id=t.id
                LEFT JOIN ticket_gap_sync_checks gap_check
                  ON gap_check.ticket_id=t.id AND gap_check.sync_type='ticket_time_entry_gaps'
                ORDER BY
                    (COALESCE(time_entries.entry_count, 0) = 0) DESC,
                    gap_check.last_checked_at NULLS FIRST,
                    time_entries.last_time_entry_observed_at NULLS FIRST,
                    t.updated_at_autotask DESC NULLS LAST,
                    t.id
                LIMIT %s
                """,
                (row_limit,),
            ).fetchall()

        for ticket in tickets:
            ticket_pk = int(ticket["id"])
            autotask_ticket_id = int(ticket["autotask_id"])
            payload = client.query_entity(
                "TimeEntries",
                filters=[{"op": "eq", "field": "ticketID", "value": autotask_ticket_id}],
            )
            items = payload.get("items") or payload.get("records") or payload.get("value") or []
            item_count = len(items)
            with db_connection() as conn:
                for item in items:
                    try:
                        with _item_write_scope(conn):
                            if _upsert_time_entry(
                                conn,
                                item=item,
                                ticket_pk=ticket_pk,
                                autotask_ticket_id=autotask_ticket_id,
                            ):
                                stats["inserted"] += 1
                            else:
                                stats["updated"] += 1
                            stats["pulled"] += 1
                    except Exception as exc:
                        stats["failed"] += 1
                        _record_item_failure(
                            stats,
                            exc,
                            ticket_id=ticket_pk,
                            autotask_ticket_id=autotask_ticket_id,
                            time_entry_id=item.get("id") if isinstance(item, dict) else None,
                        )
                _mark_gap_check(
                    conn,
                    ticket_id=ticket_pk,
                    sync_type="ticket_time_entry_gaps",
                    run_id=run_id,
                    result_count=item_count,
                )
            checked_at = datetime.now(UTC).isoformat()
            if item_count == 0:
                stats["checked_empty"] += 1
            stats["processed_tickets"] += 1
            stats["checkpoint"].update(
                {
                    "last_seen_id": ticket_pk,
                    "last_ticket_pk": ticket_pk,
                    "tickets_checked": stats["processed_tickets"],
                    "time_entry_count": int(ticket.get("time_entry_count") or 0),
                    "labor_hours": float(ticket.get("labor_hours") or 0),
                    "last_gap_checked_at": checked_at,
                    "last_gap_result_count": item_count,
                    "checked_empty": stats["checked_empty"],
                    "last_successful_completion_at": checked_at,
                }
            )
            _update_run_progress(run_id, stats)

        _finish_run(run_id, "completed", stats)
        return stats
    except Exception as exc:
        _finish_run(run_id, "failed", stats, str(exc))
        raise


def sync_ticket_history(limit: int | None = None, full_sync: bool = False) -> dict[str, Any]:
    run_id = _create_run("ticket_history")
    stats = {
        "run_id": run_id,
        "processed_tickets": 0,
        "pulled": 0,
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
        "checkpoint": {},
    }
    try:
        last_ticket_pk = 0 if full_sync else _last_checkpoint("ticket_history")
        row_limit = None if full_sync else (limit or settings.autotask_sync_batch_limit)
        client = AutotaskReadOnlyClient(sync_run_id=run_id, delay_seconds=0.35)
        with db_connection() as conn:
            if row_limit is None:
                tickets = conn.execute(
                    """
                    SELECT id, autotask_id
                    FROM autotask_tickets
                    WHERE id > %s
                    ORDER BY id
                    """,
                    (last_ticket_pk,),
                ).fetchall()
            else:
                tickets = conn.execute(
                    """
                    SELECT id, autotask_id
                    FROM autotask_tickets
                    WHERE id > %s
                    ORDER BY id
                    LIMIT %s
                    """,
                    (last_ticket_pk, max(row_limit, 1)),
                ).fetchall()

        for ticket in tickets:
            ticket_pk = int(ticket["id"])
            autotask_ticket_id = int(ticket["autotask_id"])
            payload = client.query_entity(
                "TicketHistory",
                filters=[{"op": "eq", "field": "ticketID", "value": autotask_ticket_id}],
            )
            items = payload.get("items") or payload.get("records") or payload.get("value") or []
            with db_connection() as conn:
                for item in items:
                    try:
                        autotask_id = int(item["id"])
                        row = conn.execute(
                            """
                            INSERT INTO autotask_ticket_history(
                                autotask_id, ticket_id, autotask_ticket_id, action, detail,
                                resource_id, happened_at, raw, synced_at
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, now())
                            ON CONFLICT (autotask_id) DO UPDATE SET
                                ticket_id=EXCLUDED.ticket_id,
                                autotask_ticket_id=EXCLUDED.autotask_ticket_id,
                                action=EXCLUDED.action,
                                detail=EXCLUDED.detail,
                                resource_id=EXCLUDED.resource_id,
                                happened_at=EXCLUDED.happened_at,
                                raw=EXCLUDED.raw,
                                synced_at=now()
                            RETURNING (xmax = 0) AS inserted
                            """,
                            (
                                autotask_id,
                                ticket_pk,
                                autotask_ticket_id,
                                _field(item, "action"),
                                _field(item, "detail"),
                                _field(item, "resourceID", "resourceId"),
                                _parse_dt(_field(item, "date", "createdDateTime", "createDate")),
                                Jsonb(item),
                            ),
                        ).fetchone()
                        stats["inserted" if row["inserted"] else "updated"] += 1
                        stats["pulled"] += 1
                    except Exception as exc:
                        stats["failed"] += 1
                        _record_item_failure(
                            stats,
                            exc,
                            ticket_id=ticket_pk,
                            autotask_ticket_id=autotask_ticket_id,
                            history_id=item.get("id") if isinstance(item, dict) else None,
                        )
            stats["processed_tickets"] += 1
            last_ticket_pk = ticket_pk
            stats["checkpoint"].update({"last_seen_id": last_ticket_pk, "last_ticket_pk": last_ticket_pk})
            _update_run_progress(run_id, stats)

        _finish_run(run_id, "completed", stats)
        return stats
    except Exception as exc:
        _finish_run(run_id, "failed", stats, str(exc))
        raise


def sync_waiting_ticket_history(limit: int | None = None) -> dict[str, Any]:
    run_id = _create_run("waiting_ticket_history")
    row_limit = max(limit or 25, 1)
    stats = {
        "run_id": run_id,
        "processed_tickets": 0,
        "pulled": 0,
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
        "target": "open_waiting_status_tickets",
        "checkpoint": {},
    }
    try:
        client = AutotaskReadOnlyClient(sync_run_id=run_id, delay_seconds=0.35)
        with db_connection() as conn:
            tickets = conn.execute(
                """
                SELECT t.id, t.autotask_id, COALESCE(status_ref.label, t.status) AS status_label
                FROM autotask_tickets t
                LEFT JOIN autotask_reference_values status_ref
                  ON status_ref.field_name='status' AND status_ref.value=t.status
                LEFT JOIN (
                    SELECT ticket_id, max(synced_at) AS last_history_synced_at
                    FROM autotask_ticket_history
                    GROUP BY ticket_id
                ) history ON history.ticket_id=t.id
                WHERE t.completed_at_autotask IS NULL
                  AND COALESCE(t.status, '') <> ALL(%s)
                  AND (
                    lower(COALESCE(status_ref.label, t.status, '')) LIKE '%%waiting%%'
                    OR lower(COALESCE(status_ref.label, t.status, '')) LIKE '%%hold%%'
                    OR lower(COALESCE(status_ref.label, t.status, '')) LIKE '%%material%%'
                    OR lower(COALESCE(status_ref.label, t.status, '')) LIKE '%%customer%%'
                    OR lower(COALESCE(status_ref.label, t.status, '')) LIKE '%%vendor%%'
                  )
                ORDER BY history.last_history_synced_at NULLS FIRST, t.updated_at_autotask DESC NULLS LAST, t.id
                LIMIT %s
                """,
                (["5", "16", "20"], row_limit),
            ).fetchall()

        for ticket in tickets:
            ticket_pk = int(ticket["id"])
            autotask_ticket_id = int(ticket["autotask_id"])
            payload = client.query_entity(
                "TicketHistory",
                filters=[{"op": "eq", "field": "ticketID", "value": autotask_ticket_id}],
            )
            items = payload.get("items") or payload.get("records") or payload.get("value") or []
            with db_connection() as conn:
                for item in items:
                    try:
                        autotask_id = int(item["id"])
                        row = conn.execute(
                            """
                            INSERT INTO autotask_ticket_history(
                                autotask_id, ticket_id, autotask_ticket_id, action, detail,
                                resource_id, happened_at, raw, synced_at
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, now())
                            ON CONFLICT (autotask_id) DO UPDATE SET
                                ticket_id=EXCLUDED.ticket_id,
                                autotask_ticket_id=EXCLUDED.autotask_ticket_id,
                                action=EXCLUDED.action,
                                detail=EXCLUDED.detail,
                                resource_id=EXCLUDED.resource_id,
                                happened_at=EXCLUDED.happened_at,
                                raw=EXCLUDED.raw,
                                synced_at=now()
                            RETURNING (xmax = 0) AS inserted
                            """,
                            (
                                autotask_id,
                                ticket_pk,
                                autotask_ticket_id,
                                _field(item, "action"),
                                _field(item, "detail"),
                                _field(item, "resourceID", "resourceId"),
                                _parse_dt(_field(item, "date", "createdDateTime", "createDate")),
                                Jsonb(item),
                            ),
                        ).fetchone()
                        stats["inserted" if row["inserted"] else "updated"] += 1
                        stats["pulled"] += 1
                    except Exception as exc:
                        stats["failed"] += 1
                        _record_item_failure(
                            stats,
                            exc,
                            ticket_id=ticket_pk,
                            autotask_ticket_id=autotask_ticket_id,
                            history_id=item.get("id") if isinstance(item, dict) else None,
                        )
            stats["processed_tickets"] += 1
            stats["checkpoint"].update(
                {
                    "last_seen_id": ticket_pk,
                    "last_ticket_pk": ticket_pk,
                    "status_label": ticket.get("status_label"),
                }
            )
            _update_run_progress(run_id, stats)

        _finish_run(run_id, "completed", stats)
        return stats
    except Exception as exc:
        _finish_run(run_id, "failed", stats, str(exc))
        raise


def sync_status_sample_ticket_history(limit: int | None = None) -> dict[str, Any]:
    run_id = _create_run("status_sample_ticket_history")
    row_limit = max(limit or 25, 1)
    stats = {
        "run_id": run_id,
        "processed_tickets": 0,
        "pulled": 0,
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
        "target": "open_ticket_status_samples",
        "checkpoint": {},
    }
    try:
        client = AutotaskReadOnlyClient(sync_run_id=run_id, delay_seconds=0.35)
        with db_connection() as conn:
            tickets = conn.execute(
                """
                WITH history AS (
                    SELECT ticket_id, count(*) AS history_count, max(synced_at) AS last_history_synced_at
                    FROM autotask_ticket_history
                    GROUP BY ticket_id
                ),
                status_sample_summary AS (
                    SELECT COALESCE(t.status, '') AS status_value, count(*) AS status_sampled_tickets
                    FROM autotask_tickets t
                    JOIN ticket_gap_sync_checks gap_check
                      ON gap_check.ticket_id=t.id
                     AND gap_check.sync_type='status_sample_ticket_history'
                    WHERE t.completed_at_autotask IS NULL
                      AND COALESCE(t.status, '') <> ALL(%s)
                    GROUP BY COALESCE(t.status, '')
                ),
                candidates AS (
                    SELECT
                        t.id,
                        t.autotask_id,
                        COALESCE(status_ref.label, t.status, '[Blank]') AS status_label,
                        COALESCE(t.status, '') AS status_value,
                        COALESCE(status_sample_summary.status_sampled_tickets, 0) AS status_sampled_tickets,
                        COALESCE(history.history_count, 0) AS history_count,
                        history.last_history_synced_at,
                        gap_check.last_checked_at AS last_gap_checked_at,
                        gap_check.last_result_count AS last_gap_result_count,
                        row_number() OVER (
                            PARTITION BY COALESCE(t.status, '')
                            ORDER BY
                                gap_check.last_checked_at NULLS FIRST,
                                (COALESCE(history.history_count, 0) = 0) DESC,
                                history.last_history_synced_at NULLS FIRST,
                                t.updated_at_autotask DESC NULLS LAST,
                                t.id
                        ) AS status_sample_rank
                    FROM autotask_tickets t
                    LEFT JOIN autotask_reference_values status_ref
                      ON status_ref.field_name='status' AND status_ref.value=t.status
                    LEFT JOIN history ON history.ticket_id=t.id
                    LEFT JOIN status_sample_summary
                      ON status_sample_summary.status_value=COALESCE(t.status, '')
                    LEFT JOIN ticket_gap_sync_checks gap_check
                      ON gap_check.ticket_id=t.id AND gap_check.sync_type='status_sample_ticket_history'
                    WHERE t.completed_at_autotask IS NULL
                      AND COALESCE(t.status, '') <> ALL(%s)
                )
                SELECT *
                FROM candidates
                ORDER BY
                    (status_sampled_tickets = 0) DESC,
                    status_sample_rank,
                    status_label,
                    last_gap_checked_at NULLS FIRST,
                    id
                LIMIT %s
                """,
                (["5", "16", "20"], ["5", "16", "20"], row_limit),
            ).fetchall()

        for ticket in tickets:
            ticket_pk = int(ticket["id"])
            autotask_ticket_id = int(ticket["autotask_id"])
            payload = client.query_entity(
                "TicketHistory",
                filters=[{"op": "eq", "field": "ticketID", "value": autotask_ticket_id}],
            )
            items = payload.get("items") or payload.get("records") or payload.get("value") or []
            item_count = len(items)
            with db_connection() as conn:
                for item in items:
                    try:
                        autotask_id = int(item["id"])
                        row = conn.execute(
                            """
                            INSERT INTO autotask_ticket_history(
                                autotask_id, ticket_id, autotask_ticket_id, action, detail,
                                resource_id, happened_at, raw, synced_at
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, now())
                            ON CONFLICT (autotask_id) DO UPDATE SET
                                ticket_id=EXCLUDED.ticket_id,
                                autotask_ticket_id=EXCLUDED.autotask_ticket_id,
                                action=EXCLUDED.action,
                                detail=EXCLUDED.detail,
                                resource_id=EXCLUDED.resource_id,
                                happened_at=EXCLUDED.happened_at,
                                raw=EXCLUDED.raw,
                                synced_at=now()
                            RETURNING (xmax = 0) AS inserted
                            """,
                            (
                                autotask_id,
                                ticket_pk,
                                autotask_ticket_id,
                                _field(item, "action"),
                                _field(item, "detail"),
                                _field(item, "resourceID", "resourceId"),
                                _parse_dt(_field(item, "date", "createdDateTime", "createDate")),
                                Jsonb(item),
                            ),
                        ).fetchone()
                        stats["inserted" if row["inserted"] else "updated"] += 1
                        stats["pulled"] += 1
                    except Exception as exc:
                        stats["failed"] += 1
                        _record_item_failure(
                            stats,
                            exc,
                            ticket_id=ticket_pk,
                            autotask_ticket_id=autotask_ticket_id,
                            history_id=item.get("id") if isinstance(item, dict) else None,
                        )
                _mark_gap_check(
                    conn,
                    ticket_id=ticket_pk,
                    sync_type="status_sample_ticket_history",
                    run_id=run_id,
                    result_count=item_count,
                )
            stats["processed_tickets"] += 1
            stats["checkpoint"].update({
                "last_seen_id": ticket_pk,
                "last_ticket_pk": ticket_pk,
                "status_label": ticket.get("status_label"),
                "status_value": ticket.get("status_value"),
                "status_sampled_tickets": int(ticket.get("status_sampled_tickets") or 0),
                "status_sample_rank": int(ticket.get("status_sample_rank") or 0),
                "history_count": int(ticket.get("history_count") or 0),
                "last_gap_checked_at": ticket.get("last_gap_checked_at"),
                "last_gap_result_count": int(ticket.get("last_gap_result_count") or 0),
            })
            _update_run_progress(run_id, stats)

        _finish_run(run_id, "completed", stats)
        return stats
    except Exception as exc:
        _finish_run(run_id, "failed", stats, str(exc))
        raise


def sync_open_ticket_history_gaps(limit: int | None = None) -> dict[str, Any]:
    run_id = _create_run("open_ticket_history_gaps")
    row_limit = max(limit or 25, 1)
    stats = {
        "run_id": run_id,
        "processed_tickets": 0,
        "pulled": 0,
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
        "checked_empty": 0,
        "target": "open_tickets_missing_or_stale_history",
        "checkpoint": {},
    }
    try:
        client = AutotaskReadOnlyClient(sync_run_id=run_id, delay_seconds=0.35)
        with db_connection() as conn:
            tickets = conn.execute(
                """
                SELECT
                    t.id,
                    t.autotask_id,
                    COALESCE(status_ref.label, t.status) AS status_label,
                    COALESCE(history.history_count, 0) AS history_count,
                    history.last_history_synced_at,
                    gap_check.last_checked_at AS last_gap_checked_at,
                    gap_check.last_result_count AS last_gap_result_count
                FROM autotask_tickets t
                LEFT JOIN autotask_reference_values status_ref
                  ON status_ref.field_name='status' AND status_ref.value=t.status
                LEFT JOIN (
                    SELECT ticket_id, count(*) AS history_count, max(synced_at) AS last_history_synced_at
                    FROM autotask_ticket_history
                    GROUP BY ticket_id
                ) history ON history.ticket_id=t.id
                LEFT JOIN ticket_gap_sync_checks gap_check
                  ON gap_check.ticket_id=t.id AND gap_check.sync_type='open_ticket_history_gaps'
                WHERE t.completed_at_autotask IS NULL
                  AND COALESCE(t.status, '') <> ALL(%s)
                ORDER BY
                    (COALESCE(history.history_count, 0) = 0) DESC,
                    gap_check.last_checked_at NULLS FIRST,
                    history.last_history_synced_at NULLS FIRST,
                    t.updated_at_autotask DESC NULLS LAST,
                    t.id
                LIMIT %s
                """,
                (["5", "16", "20"], row_limit),
            ).fetchall()

        for ticket in tickets:
            ticket_pk = int(ticket["id"])
            autotask_ticket_id = int(ticket["autotask_id"])
            payload = client.query_entity(
                "TicketHistory",
                filters=[{"op": "eq", "field": "ticketID", "value": autotask_ticket_id}],
            )
            items = payload.get("items") or payload.get("records") or payload.get("value") or []
            item_count = len(items)
            with db_connection() as conn:
                for item in items:
                    try:
                        autotask_id = int(item["id"])
                        row = conn.execute(
                            """
                            INSERT INTO autotask_ticket_history(
                                autotask_id, ticket_id, autotask_ticket_id, action, detail,
                                resource_id, happened_at, raw, synced_at
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, now())
                            ON CONFLICT (autotask_id) DO UPDATE SET
                                ticket_id=EXCLUDED.ticket_id,
                                autotask_ticket_id=EXCLUDED.autotask_ticket_id,
                                action=EXCLUDED.action,
                                detail=EXCLUDED.detail,
                                resource_id=EXCLUDED.resource_id,
                                happened_at=EXCLUDED.happened_at,
                                raw=EXCLUDED.raw,
                                synced_at=now()
                            RETURNING (xmax = 0) AS inserted
                            """,
                            (
                                autotask_id,
                                ticket_pk,
                                autotask_ticket_id,
                                _field(item, "action"),
                                _field(item, "detail"),
                                _field(item, "resourceID", "resourceId"),
                                _parse_dt(_field(item, "date", "createdDateTime", "createDate")),
                                Jsonb(item),
                            ),
                        ).fetchone()
                        stats["inserted" if row["inserted"] else "updated"] += 1
                        stats["pulled"] += 1
                    except Exception as exc:
                        stats["failed"] += 1
                        _record_item_failure(
                            stats,
                            exc,
                            ticket_id=ticket_pk,
                            autotask_ticket_id=autotask_ticket_id,
                            history_id=item.get("id") if isinstance(item, dict) else None,
                        )
                _mark_gap_check(
                    conn,
                    ticket_id=ticket_pk,
                    sync_type="open_ticket_history_gaps",
                    run_id=run_id,
                    result_count=item_count,
                )
            checked_at = datetime.now(UTC).isoformat()
            if item_count == 0:
                stats["checked_empty"] += 1
            stats["processed_tickets"] += 1
            stats["checkpoint"].update({
                "last_seen_id": ticket_pk,
                "last_ticket_pk": ticket_pk,
                "tickets_checked": stats["processed_tickets"],
                "status_label": ticket.get("status_label"),
                "history_count": int(ticket.get("history_count") or 0),
                "last_gap_checked_at": checked_at,
                "last_gap_result_count": item_count,
                "checked_empty": stats["checked_empty"],
                "last_successful_completion_at": checked_at,
            })
            _update_run_progress(run_id, stats)

        _finish_run(run_id, "completed", stats)
        return stats
    except Exception as exc:
        _finish_run(run_id, "failed", stats, str(exc))
        raise


def sync_ticket_history_gaps(limit: int | None = None) -> dict[str, Any]:
    run_id = _create_run("ticket_history_gaps")
    row_limit = max(limit or 25, 1)
    stats = {
        "run_id": run_id,
        "processed_tickets": 0,
        "pulled": 0,
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
        "checked_empty": 0,
        "target": "tickets_missing_or_stale_history",
        "checkpoint": {},
    }
    try:
        client = AutotaskReadOnlyClient(sync_run_id=run_id, delay_seconds=0.35)
        with db_connection() as conn:
            tickets = conn.execute(
                """
                SELECT
                    t.id,
                    t.autotask_id,
                    COALESCE(status_ref.label, t.status) AS status_label,
                    COALESCE(history.history_count, 0) AS history_count,
                    history.last_history_synced_at,
                    gap_check.last_checked_at AS last_gap_checked_at,
                    gap_check.last_result_count AS last_gap_result_count
                FROM autotask_tickets t
                LEFT JOIN autotask_reference_values status_ref
                  ON status_ref.field_name='status' AND status_ref.value=t.status
                LEFT JOIN (
                    SELECT ticket_id, count(*) AS history_count, max(synced_at) AS last_history_synced_at
                    FROM autotask_ticket_history
                    GROUP BY ticket_id
                ) history ON history.ticket_id=t.id
                LEFT JOIN ticket_gap_sync_checks gap_check
                  ON gap_check.ticket_id=t.id AND gap_check.sync_type='ticket_history_gaps'
                ORDER BY
                    (COALESCE(history.history_count, 0) = 0) DESC,
                    gap_check.last_checked_at NULLS FIRST,
                    history.last_history_synced_at NULLS FIRST,
                    t.updated_at_autotask DESC NULLS LAST,
                    t.id
                LIMIT %s
                """,
                (row_limit,),
            ).fetchall()

        for ticket in tickets:
            ticket_pk = int(ticket["id"])
            autotask_ticket_id = int(ticket["autotask_id"])
            payload = client.query_entity(
                "TicketHistory",
                filters=[{"op": "eq", "field": "ticketID", "value": autotask_ticket_id}],
            )
            items = payload.get("items") or payload.get("records") or payload.get("value") or []
            item_count = len(items)
            with db_connection() as conn:
                for item in items:
                    try:
                        autotask_id = int(item["id"])
                        row = conn.execute(
                            """
                            INSERT INTO autotask_ticket_history(
                                autotask_id, ticket_id, autotask_ticket_id, action, detail,
                                resource_id, happened_at, raw, synced_at
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, now())
                            ON CONFLICT (autotask_id) DO UPDATE SET
                                ticket_id=EXCLUDED.ticket_id,
                                autotask_ticket_id=EXCLUDED.autotask_ticket_id,
                                action=EXCLUDED.action,
                                detail=EXCLUDED.detail,
                                resource_id=EXCLUDED.resource_id,
                                happened_at=EXCLUDED.happened_at,
                                raw=EXCLUDED.raw,
                                synced_at=now()
                            RETURNING (xmax = 0) AS inserted
                            """,
                            (
                                autotask_id,
                                ticket_pk,
                                autotask_ticket_id,
                                _field(item, "action"),
                                _field(item, "detail"),
                                _field(item, "resourceID", "resourceId"),
                                _parse_dt(_field(item, "date", "createdDateTime", "createDate")),
                                Jsonb(item),
                            ),
                        ).fetchone()
                        stats["inserted" if row["inserted"] else "updated"] += 1
                        stats["pulled"] += 1
                    except Exception as exc:
                        stats["failed"] += 1
                        _record_item_failure(
                            stats,
                            exc,
                            ticket_id=ticket_pk,
                            autotask_ticket_id=autotask_ticket_id,
                            history_id=item.get("id") if isinstance(item, dict) else None,
                        )
                _mark_gap_check(
                    conn,
                    ticket_id=ticket_pk,
                    sync_type="ticket_history_gaps",
                    run_id=run_id,
                    result_count=item_count,
                )
            checked_at = datetime.now(UTC).isoformat()
            if item_count == 0:
                stats["checked_empty"] += 1
            stats["processed_tickets"] += 1
            stats["checkpoint"].update(
                {
                    "last_seen_id": ticket_pk,
                    "last_ticket_pk": ticket_pk,
                    "tickets_checked": stats["processed_tickets"],
                    "status_label": ticket.get("status_label"),
                    "history_count": int(ticket.get("history_count") or 0),
                    "last_gap_checked_at": checked_at,
                    "last_gap_result_count": item_count,
                    "checked_empty": stats["checked_empty"],
                    "last_successful_completion_at": checked_at,
                }
            )
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
    time_entries = sync_time_entries(limit=limit or 100)
    return {"companies": companies, "tickets": tickets, "ticket_notes": notes, "time_entries": time_entries}


def sync_status() -> dict[str, Any]:
    init_schema()
    stale_cutoff = datetime.now(UTC) - timedelta(hours=6)
    with db_connection() as conn:
        current = conn.execute(
            """
            SELECT * FROM autotask_sync_runs
            WHERE status='running' AND started_at >= %s::timestamptz
            ORDER BY id DESC LIMIT 1
            """,
            (stale_cutoff,),
        ).fetchone()
        stale = list(
            conn.execute(
                """
                SELECT *
                FROM autotask_sync_runs
                WHERE status='running' AND started_at < %s::timestamptz
                ORDER BY started_at
                LIMIT 20
                """,
                (stale_cutoff,),
            ).fetchall()
        )
        last = conn.execute("SELECT * FROM autotask_sync_runs ORDER BY id DESC LIMIT 1").fetchone()
        calls = conn.execute("SELECT count(*) AS count FROM autotask_api_calls").fetchone()
    return {
        "current_run": current,
        "last_run": last,
        "stale_running_runs": stale,
        "api_call_count": calls["count"] if calls else 0,
    }


def cleanup_stale_sync_runs(max_age_hours: int = 6) -> dict[str, Any]:
    hours = min(max(int(max_age_hours or 0), 1), 168)
    cutoff = datetime.now(UTC) - timedelta(hours=hours)
    with db_connection() as conn:
        rows = list(
            conn.execute(
                """
                UPDATE autotask_sync_runs
                SET status='failed',
                    finished_at=now(),
                    last_error=COALESCE(last_error, 'stale running sync reconciled locally')
                WHERE status='running' AND started_at < %s::timestamptz
                RETURNING id, sync_type, started_at, last_error
                """,
                (cutoff,),
            ).fetchall()
        )
    return {
        "ok": True,
        "max_age_hours": hours,
        "updated": len(rows),
        "runs": rows,
        "message": "Stale local sync-run rows were marked failed locally. No Autotask data was changed.",
    }


def sync_runs(limit: int = 20) -> list[dict[str, Any]]:
    init_schema()
    with db_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM autotask_sync_runs ORDER BY id DESC LIMIT %s",
            (min(max(limit, 1), 100),),
        ).fetchall()
    return [_sync_run_response(row) for row in rows]
