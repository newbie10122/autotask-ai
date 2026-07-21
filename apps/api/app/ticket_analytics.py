from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from psycopg.types.json import Jsonb

from .db import db_connection, init_schema
from .security import redact_private_entities
from .ticket_classifier import classify_ticket, ticket_class_label


REFERENCE_BOOTSTRAP: dict[tuple[str, str], str] = {
    ("category", "2"): "Monitoring Alert",
    ("category", "3"): "Support / Helpdesk",
    ("issue_type", "14"): "Disk Space",
    ("issue_type", "30"): "Security / Endpoint",
    ("subissue_type", "222"): "System Volume 90/95%",
    ("subissue_type", "301"): "Endpoint Security",
    ("queue", "8"): "Monitoring",
    ("queue", "29682833"): "Helpdesk",
    ("queue", "29682969"): "Monitoring / Server",
    ("source", "4"): "Email",
    ("source", "8"): "Monitoring / RMM",
    ("ticket_type", "1"): "Service Request",
    ("ticket_type", "5"): "Monitoring Alert",
    ("status", "1"): "Open",
    ("priority", "2"): "Priority 2",
}

REFERENCE_FIELDS: tuple[tuple[str, str], ...] = (
    ("category", "category"),
    ("issue_type", "issue_type"),
    ("subissue_type", "subissue_type"),
    ("queue", "queue"),
    ("status", "status"),
    ("priority", "priority"),
)


def _clean_value(value: Any) -> str:
    return str(value or "").strip()


def _fallback_label(field_name: str, value: str) -> str:
    pretty = field_name.replace("_", " ").title()
    return f"{pretty} {value}"


def _upsert_reference(conn: Any, field_name: str, value: str, label: str, source: str = "local") -> None:
    if not value:
        return
    conn.execute(
        """
        INSERT INTO autotask_reference_values(field_name, value, label, source, raw, updated_at)
        VALUES (%s, %s, %s, %s, %s, now())
        ON CONFLICT (field_name, value) DO UPDATE
        SET label=EXCLUDED.label, source=EXCLUDED.source, updated_at=now()
        """,
        (field_name, value, label, source, Jsonb({})),
    )


def sync_reference_data() -> dict[str, Any]:
    init_schema()
    upserted = 0
    with db_connection() as conn:
        for (field_name, value), label in REFERENCE_BOOTSTRAP.items():
            _upsert_reference(conn, field_name, value, label, "bootstrap")
            upserted += 1

        for field_name, column_name in REFERENCE_FIELDS:
            rows = conn.execute(
                f"""
                SELECT DISTINCT {column_name} AS value
                FROM autotask_tickets
                WHERE NULLIF({column_name}, '') IS NOT NULL
                """
            ).fetchall()
            for row in rows:
                value = _clean_value(row["value"])
                label = REFERENCE_BOOTSTRAP.get((field_name, value), _fallback_label(field_name, value))
                _upsert_reference(conn, field_name, value, label, "inferred")
                upserted += 1

        for field_name, json_key in (("source", "source"), ("ticket_type", "ticketType")):
            rows = conn.execute(
                """
                SELECT DISTINCT raw->>%s AS value
                FROM autotask_tickets
                WHERE NULLIF(raw->>%s, '') IS NOT NULL
                """,
                (json_key, json_key),
            ).fetchall()
            for row in rows:
                value = _clean_value(row["value"])
                label = REFERENCE_BOOTSTRAP.get((field_name, value), _fallback_label(field_name, value))
                _upsert_reference(conn, field_name, value, label, "inferred")
                upserted += 1
    return reference_data_status() | {"ok": True, "upserted": upserted}


def reference_data_status() -> dict[str, Any]:
    init_schema()
    with db_connection() as conn:
        total = conn.execute("SELECT count(*) AS count FROM autotask_reference_values").fetchone()["count"]
        by_field = list(
            conn.execute(
                """
                SELECT field_name, count(*) AS count
                FROM autotask_reference_values
                GROUP BY field_name
                ORDER BY field_name
                """
            ).fetchall()
        )
    return {"ok": True, "total_reference_values": total, "by_field": by_field}


def classify_tickets(limit: int | None = None) -> dict[str, Any]:
    init_schema()
    processed = 0
    included = 0
    excluded = 0
    by_class: Counter[str] = Counter()
    exclude_reasons: Counter[str] = Counter()
    row_limit = min(max(limit or 1000, 1), 100000)
    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, title, description, raw
            FROM autotask_tickets
            ORDER BY classified_at NULLS FIRST, updated_at_autotask DESC NULLS LAST, id DESC
            LIMIT %s
            """,
            (row_limit,),
        ).fetchall()
        for row in rows:
            result = classify_ticket(row.get("title"), row.get("description"), row.get("raw") or {})
            conn.execute(
                """
                UPDATE autotask_tickets
                SET ticket_class=%s,
                    is_support_issue=%s,
                    is_system_generated=%s,
                    analytics_exclude=%s,
                    analytics_exclude_reason=%s,
                    classified_at=now()
                WHERE id=%s
                """,
                (
                    result["ticket_class"],
                    result["is_support_issue"],
                    result["is_system_generated"],
                    result["analytics_exclude"],
                    result["analytics_exclude_reason"],
                    row["id"],
                ),
            )
            processed += 1
            by_class[result["ticket_class"]] += 1
            if result["analytics_exclude"]:
                excluded += 1
                exclude_reasons[result["analytics_exclude_reason"] or "excluded"] += 1
            else:
                included += 1
    return {
        "ok": True,
        "processed": processed,
        "included": included,
        "excluded": excluded,
        "by_ticket_class": dict(by_class),
        "excluded_reasons": dict(exclude_reasons),
    }


def ticket_class_report() -> dict[str, Any]:
    init_schema()
    with db_connection() as conn:
        summary = conn.execute(
            """
            SELECT
              count(*) AS total_tickets,
              count(*) FILTER (WHERE classified_at IS NOT NULL) AS classified_tickets,
              count(*) FILTER (WHERE classified_at IS NULL) AS unclassified_tickets,
              count(*) FILTER (WHERE is_support_issue) AS support_issue_count,
              count(*) FILTER (WHERE analytics_exclude) AS excluded_count,
              count(*) FILTER (WHERE is_system_generated) AS system_generated_count
            FROM autotask_tickets
            """
        ).fetchone()
        by_class = list(
            conn.execute(
                """
                SELECT COALESCE(ticket_class, 'unclassified') AS ticket_class, count(*) AS count
                FROM autotask_tickets
                GROUP BY 1
                ORDER BY count DESC, ticket_class
                LIMIT 30
                """
            ).fetchall()
        )
        top_exclude_reasons = list(
            conn.execute(
                """
                SELECT COALESCE(analytics_exclude_reason, 'excluded') AS reason, count(*) AS count
                FROM autotask_tickets
                WHERE analytics_exclude
                GROUP BY 1
                ORDER BY count DESC, reason
                LIMIT 20
                """
            ).fetchall()
        )
    return {
        "ok": True,
        **dict(summary),
        "by_ticket_class": by_class,
        "top_exclude_reasons": top_exclude_reasons,
    }


def _reference_labels() -> dict[tuple[str, str], str]:
    with db_connection() as conn:
        rows = conn.execute("SELECT field_name, value, label FROM autotask_reference_values").fetchall()
    return {(row["field_name"], row["value"]): row["label"] for row in rows}


def _label(labels: dict[tuple[str, str], str], field_name: str, value: Any) -> str | None:
    clean = _clean_value(value)
    if not clean:
        return None
    label = labels.get((field_name, clean))
    if not label:
        return None
    generic_prefixes = {
        "issue_type": "Issue Type ",
        "subissue_type": "Subissue Type ",
        "queue": "Queue ",
        "status": "Status ",
        "priority": "Priority ",
    }
    if label.startswith(generic_prefixes.get(field_name, "\0")):
        return None
    return label


def _keyword_cluster(title: str | None, ticket_class: str | None) -> str:
    text = (title or "").lower()
    if ticket_class == "disk_space_alert":
        return "System Volume 90/95%"
    if ticket_class == "backup_alert":
        return "No Recent Backups" if "recent backup" in text else "Backup Failure"
    if ticket_class == "vpn_issue":
        return "Authentication or Access"
    if ticket_class == "microsoft_365_issue":
        if "sharepoint" in text:
            return "SharePoint Access"
        if "teams" in text:
            return "Teams"
        if "onedrive" in text:
            return "OneDrive"
        return "Outlook or Mailbox"
    if ticket_class == "printer_scan_issue":
        return "Scan to Email" if "scan" in text else "Printing"
    if ticket_class == "onsite_support":
        return "Maintenance" if "maintenance" in text else "Field Visit"
    if ticket_class == "security_alert":
        return "Endpoint Protection"
    if ticket_class == "access_or_availability_issue":
        return "Website or Application Login" if "login" in text or "down" in text else "Access"
    return "General Requests"


def issue_group_label(row: dict[str, Any], labels: dict[tuple[str, str], str] | None = None) -> str:
    labels = labels or {}
    ticket_class = row.get("ticket_class") or "general_support_issue"
    category = _label(labels, "category", row.get("category"))
    issue = _label(labels, "issue_type", row.get("issue_type"))
    subissue = _label(labels, "subissue_type", row.get("subissue_type"))
    class_label = ticket_class_label(ticket_class)
    cluster = _keyword_cluster(row.get("title"), ticket_class)

    if category and issue and subissue:
        return f"{category} / {issue} / {subissue}"
    if category and issue:
        return f"{category} / {issue}"
    if category:
        return f"{category} / {class_label} / {cluster}"
    if issue:
        return f"{class_label} / {issue} / {cluster}"
    return f"{class_label} / {cluster}"


def recurring_issues_report(
    limit: int = 8,
    include_excluded: bool = False,
    authorized_company_ids: list[int] | None = None,
) -> dict[str, Any]:
    init_schema()
    limit = min(max(limit, 1), 20)
    labels = _reference_labels()
    company_filter_sql = ""
    company_filter_params: tuple[Any, ...] = ()
    if authorized_company_ids is not None:
        if not authorized_company_ids:
            return {
                "ok": True,
                "groups": [],
                "excluded_count": 0,
                "top_skip_reasons": [],
                "warnings": ["No authorized company scope is assigned."],
                "mapping_stats": reference_data_status(),
            }
        company_filter_sql = "AND t.company_id = ANY(%s)"
        company_filter_params = (authorized_company_ids,)
    with db_connection() as conn:
        rows = list(
            conn.execute(
                """
                SELECT
                  t.id, t.autotask_id, t.ticket_number, t.title, t.category, t.issue_type,
                  t.subissue_type, t.queue, t.ticket_class, t.analytics_exclude,
                  t.analytics_exclude_reason, t.completed_at_autotask, t.updated_at_autotask,
                  0 AS non_noise_chunks,
                  0 AS max_quality
                FROM autotask_tickets t
                WHERE (%s OR NOT t.analytics_exclude)
                  AND COALESCE(t.is_support_issue, TRUE)
                  AND t.classified_at IS NOT NULL
                  """ + company_filter_sql + """
                ORDER BY t.completed_at_autotask DESC NULLS LAST,
                         t.updated_at_autotask DESC NULLS LAST,
                         t.id DESC
                LIMIT 50000
                """,
                (include_excluded, *company_filter_params),
            ).fetchall()
        )
        excluded_count = conn.execute(
            "SELECT count(*) AS count FROM autotask_tickets t WHERE analytics_exclude " + company_filter_sql,
            company_filter_params,
        ).fetchone()["count"]
        unclassified_count = conn.execute(
            "SELECT count(*) AS count FROM autotask_tickets t WHERE classified_at IS NULL " + company_filter_sql,
            company_filter_params,
        ).fetchone()[
            "count"
        ]
        top_skip_reasons = list(
            conn.execute(
                """
                SELECT analytics_exclude_reason AS reason, count(*) AS count
                FROM autotask_tickets t
                WHERE analytics_exclude
                """ + company_filter_sql + """
                GROUP BY 1
                ORDER BY count DESC
                LIMIT 10
                """
                ,
                company_filter_params,
            ).fetchall()
        )

    grouped: dict[str, dict[str, Any]] = {}
    warnings: set[str] = set()
    if unclassified_count:
        warnings.add(f"{unclassified_count} tickets are not classified yet; run classify-tickets to include them.")
    for row in rows:
        label = issue_group_label(row, labels)
        key = label
        group = grouped.setdefault(
            key,
            {
                "label": label,
                "ticket_class": row.get("ticket_class") or "general_support_issue",
                "ticket_class_label": ticket_class_label(row.get("ticket_class")),
                "count": 0,
                "representative_tickets": [],
                "category_name": _label(labels, "category", row.get("category")),
                "issue_name": _label(labels, "issue_type", row.get("issue_type")),
                "subissue_name": _label(labels, "subissue_type", row.get("subissue_type")),
                "queue_name": _label(labels, "queue", row.get("queue")),
            },
        )
        group["count"] += 1
        if len(group["representative_tickets"]) < 3:
            ticket_display = row.get("ticket_number") or row.get("autotask_id")
            group["representative_tickets"].append(
                {
                    "ticket_number": ticket_display,
                    "autotask_id": row.get("autotask_id"),
                    "title": redact_private_entities(row.get("title") or ""),
                    "quality_score": float(row.get("max_quality") or 0),
                }
            )

    groups = sorted(grouped.values(), key=lambda item: (-item["count"], item["label"]))[:limit]
    return {
        "ok": True,
        "groups": groups,
        "excluded_count": excluded_count,
        "top_skip_reasons": top_skip_reasons,
        "warnings": sorted(warnings)[:10],
        "mapping_stats": reference_data_status(),
    }


def format_recurring_issues_answer(report: dict[str, Any]) -> tuple[str, list[str]]:
    group_lines: list[str] = []
    evidence_lines: list[str] = []
    ticket_lines: list[str] = []
    tickets: list[str] = []
    representative_budget = 16
    for index, group in enumerate(report.get("groups", []), start=1):
        label = group["label"]
        count = group["count"]
        group_lines.append(f"{index}. {label}: {count} tickets")
        evidence_lines.append(f"- {label}: {count} tickets")
        for ticket in group.get("representative_tickets", []):
            if len(ticket_lines) >= representative_budget:
                break
            display = str(ticket.get("ticket_number") or ticket.get("autotask_id") or "")
            if display and display not in tickets:
                tickets.append(display)
                ticket_lines.append(f"- {display}: {ticket.get('title') or ''}")

    warning_lines = report.get("warnings") or ["Counts are based on currently synced local Autotask tickets."]
    answer = (
        "Confidence: Medium\n\n"
        "Top Recurring Issue Groups\n"
        + ("\n".join(group_lines) or "No recurring issue groups found.")
        + "\n\nEvidence / Counts\n"
        + ("\n".join(evidence_lines) or "- No counts available.")
        + "\n\nRepresentative Tickets\n"
        + ("\n".join(ticket_lines) or "- None")
        + "\n\nSuggested Operational Next Steps\n"
        "- Review the largest human-support and monitoring-alert groups separately.\n"
        "- Sample representative tickets before changing queue/category mappings.\n"
        "- Use excluded counts to keep meetings, newsletters, and vendor notices out of trend work.\n\n"
        "Warnings\n"
        + "\n".join(f"- {warning}" for warning in warning_lines)
    )
    return answer, tickets
