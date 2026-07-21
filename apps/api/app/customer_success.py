from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from fastapi.encoders import jsonable_encoder

from .cache import cache_delete_namespace, cache_get_json, cache_key, cache_set_json
from .config import settings
from .db import db_connection
from .ticket_health import CLOSED_STATUS_IDS


ESCALATION_SIGNAL_PATTERN = r"(escalat|urgent|outage|down|complain|unhappy|cancel|churn|vip|executive|production)"
SENTIMENT_SIGNAL_PATTERN = r"(not satisf|dissatisf|unhappy|frustrat|complain|poor service|bad service|thank you|thanks|appreciate|great job)"
SURVEY_NOISE_PATTERN = r"(ticket survey|unsubscribe|unsubscribesurvey)"
CUSTOMER_RISK_FEEDBACK_OUTCOMES = {"confirmed_risk", "dismissed", "needs_review"}
CALIBRATION_MIN_FEEDBACK = 10
CALIBRATION_MIN_REVIEWED_ENTITIES = 5


def invalidate_customer_success_summary_cache() -> int:
    return cache_delete_namespace("customer-success-summary")


def _num(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _bucket(score: int) -> str:
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "watch"
    return "normal"


def _score_customer(row: dict[str, Any]) -> dict[str, Any]:
    score = 0
    factors: list[str] = []
    warnings: list[str] = []

    open_tickets = _int(row.get("open_tickets"))
    high_priority = _int(row.get("high_priority_open_tickets"))
    overdue = _int(row.get("overdue_open_tickets"))
    stale = _int(row.get("stale_open_tickets"))
    repeat_groups = _int(row.get("repeat_issue_groups"))
    recent = _int(row.get("recent_tickets"))
    labor_hours = _num(row.get("total_labor_hours"))
    history_events = _int(row.get("history_events"))

    if open_tickets:
        score += min(open_tickets * 4, 28)
        factors.append(f"{open_tickets} open tickets")
    if high_priority:
        score += min(high_priority * 12, 24)
        factors.append(f"{high_priority} high-priority open tickets")
    if overdue:
        score += min(overdue * 14, 28)
        factors.append(f"{overdue} overdue open tickets")
    if stale:
        score += min(stale * 8, 20)
        factors.append(f"{stale} stale open tickets")
    if repeat_groups:
        score += min(repeat_groups * 10, 24)
        factors.append(f"{repeat_groups} repeated issue groups")
    if recent >= 8:
        score += 12
        factors.append(f"{recent} tickets in the recent window")
    elif recent >= 4:
        score += 6
        factors.append(f"{recent} tickets in the recent window")
    if labor_hours >= 24:
        score += 12
        factors.append(f"{labor_hours:.1f} local labor hours")
    elif labor_hours >= 12:
        score += 6
        factors.append(f"{labor_hours:.1f} local labor hours")

    if open_tickets and history_events == 0:
        warnings.append("No local TicketHistory for this customer's tickets; status-duration signals are partial.")
    if not factors:
        factors.append("No elevated local customer-success risk factors")

    score = min(score, 100)
    return {
        "customer_health_score": score,
        "risk_bucket": _bucket(score),
        "factors": factors,
        "warnings": warnings,
        "total_labor_hours": round(labor_hours, 2),
    }


def _feedback_calibration(row: dict[str, Any], base_score: int) -> dict[str, Any]:
    confirmed = _int(row.get("confirmed_risk_feedback"))
    dismissed = _int(row.get("dismissed_feedback"))
    needs_review = _int(row.get("needs_review_feedback"))
    total = confirmed + dismissed + needs_review
    adjustment = max(min((confirmed * 5) - (dismissed * 5), 15), -15)
    factors: list[str] = []
    if confirmed:
        factors.append(f"{confirmed} local confirmed-risk reviews")
    if dismissed:
        factors.append(f"{dismissed} local dismissed-risk reviews")
    if needs_review:
        factors.append(f"{needs_review} local needs-review outcomes")
    if not factors:
        factors.append("No local customer-risk feedback yet")

    return {
        "source": "customer_success_risk_feedback",
        "review_only": True,
        "evidence_count": total,
        "confirmed_risk_feedback": confirmed,
        "dismissed_feedback": dismissed,
        "needs_review_feedback": needs_review,
        "score_adjustment": adjustment,
        "calibrated_review_score": max(min(base_score + adjustment, 100), 0),
        "factors": factors,
        "note": "Calibration is a transparent local review signal and does not change Autotask or replace technician judgment.",
    }


def _calibration_readiness(
    total_feedback: int,
    reviewed_entities: int,
    decisive_outcome_counts: dict[str, int],
    entity_label: str,
) -> dict[str, Any]:
    decisive_outcome_groups = sum(1 for count in decisive_outcome_counts.values() if count > 0)
    blockers = []
    if total_feedback < CALIBRATION_MIN_FEEDBACK:
        blockers.append(f"Need at least {CALIBRATION_MIN_FEEDBACK} local feedback rows before score-weight review.")
    if reviewed_entities < CALIBRATION_MIN_REVIEWED_ENTITIES:
        blockers.append(
            f"Need at least {CALIBRATION_MIN_REVIEWED_ENTITIES} reviewed {entity_label} before score-weight review."
        )
    if decisive_outcome_groups < 2:
        blockers.append("Need confirmed and dismissed feedback before score-weight review.")
    return {
        "status": "ready_for_human_weight_review" if not blockers else "collecting_evidence",
        "ready_for_weight_review": not blockers,
        "minimum_feedback": CALIBRATION_MIN_FEEDBACK,
        "minimum_reviewed_entities": CALIBRATION_MIN_REVIEWED_ENTITIES,
        "decisive_outcome_groups": decisive_outcome_groups,
        "blockers": blockers,
        "interpretation": (
            "Local feedback volume is sufficient for a human score-weight review; no automatic tuning is applied."
            if not blockers
            else "Local feedback remains too sparse for score-weight changes; keep calibration review-only."
        ),
    }


def _customer_row_query(*, company_id: int | None = None) -> str:
    company_filter = "WHERE metrics.total_tickets > 0"
    if company_id is not None:
        company_filter += " AND metrics.company_id = %s"
    return f"""
        WITH labor AS (
            SELECT ticket_id, sum(COALESCE(hours, 0)) AS labor_hours
            FROM autotask_time_entries
            GROUP BY ticket_id
        ),
        history AS (
            SELECT ticket_id, count(*) AS history_events
            FROM autotask_ticket_history
            GROUP BY ticket_id
        ),
        metrics AS (
            SELECT
                c.id AS company_id,
                c.autotask_id AS company_autotask_id,
                c.name AS company_name,
                count(t.id) AS total_tickets,
                count(t.id) FILTER (
                    WHERE t.completed_at_autotask IS NULL
                      AND COALESCE(t.status, '') <> ALL(%s)
                ) AS open_tickets,
                count(t.id) FILTER (WHERE t.created_at_autotask >= %s::timestamptz) AS recent_tickets,
                count(t.id) FILTER (
                    WHERE t.completed_at_autotask IS NULL
                      AND COALESCE(t.status, '') <> ALL(%s)
                      AND t.created_at_autotask < %s::timestamptz
                ) AS stale_open_tickets,
                count(t.id) FILTER (
                    WHERE t.completed_at_autotask IS NULL
                      AND COALESCE(t.status, '') <> ALL(%s)
                      AND (
                        (t.resolved_due_at_autotask IS NOT NULL AND t.resolved_due_at_autotask < %s::timestamptz)
                        OR (t.due_at_autotask IS NOT NULL AND t.due_at_autotask < %s::timestamptz)
                      )
                ) AS overdue_open_tickets,
                count(t.id) FILTER (
                    WHERE t.completed_at_autotask IS NULL
                      AND COALESCE(t.status, '') <> ALL(%s)
                      AND t.priority IN ('1', '4')
                ) AS high_priority_open_tickets,
                COALESCE(sum(COALESCE(labor.labor_hours, 0)), 0) AS total_labor_hours,
                COALESCE(sum(COALESCE(history.history_events, 0)), 0) AS history_events
            FROM autotask_companies c
            LEFT JOIN autotask_tickets t
                ON t.company_id = c.id
               AND NOT t.analytics_exclude
            LEFT JOIN labor ON labor.ticket_id = t.id
            LEFT JOIN history ON history.ticket_id = t.id
            GROUP BY c.id, c.autotask_id, c.name
        ),
        repeat_issue_groups AS (
            SELECT
                grouped.company_id,
                count(*) AS repeat_issue_groups,
                array_agg(grouped.issue_label ORDER BY grouped.issue_count DESC, grouped.issue_label) AS repeat_issue_labels
            FROM (
                SELECT
                    t.company_id,
                    concat_ws(
                        ' / ',
                        COALESCE(NULLIF(t.category, ''), 'Uncategorized'),
                        NULLIF(t.issue_type, ''),
                        NULLIF(t.subissue_type, '')
                    ) AS issue_label,
                    count(*) AS issue_count
                FROM autotask_tickets t
                WHERE t.company_id IS NOT NULL
                  AND NOT t.analytics_exclude
                  AND t.created_at_autotask >= %s::timestamptz
                GROUP BY t.company_id, issue_label
                HAVING count(*) >= 2
            ) grouped
            GROUP BY grouped.company_id
        ),
        feedback AS (
            SELECT
                company_id,
                count(*) FILTER (WHERE outcome = 'confirmed_risk') AS confirmed_risk_feedback,
                count(*) FILTER (WHERE outcome = 'dismissed') AS dismissed_feedback,
                count(*) FILTER (WHERE outcome = 'needs_review') AS needs_review_feedback,
                max(created_at) AS latest_feedback_at
            FROM customer_success_risk_feedback
            GROUP BY company_id
        )
        SELECT
            metrics.*,
            COALESCE(repeat_issue_groups.repeat_issue_groups, 0) AS repeat_issue_groups,
            COALESCE(repeat_issue_groups.repeat_issue_labels, ARRAY[]::text[]) AS repeat_issue_labels,
            COALESCE(feedback.confirmed_risk_feedback, 0) AS confirmed_risk_feedback,
            COALESCE(feedback.dismissed_feedback, 0) AS dismissed_feedback,
            COALESCE(feedback.needs_review_feedback, 0) AS needs_review_feedback,
            feedback.latest_feedback_at
        FROM metrics
        LEFT JOIN repeat_issue_groups ON repeat_issue_groups.company_id = metrics.company_id
        LEFT JOIN feedback ON feedback.company_id = metrics.company_id
        {company_filter}
    """


def _customer_query_params(now: datetime, recent_cutoff: datetime, stale_cutoff: datetime) -> list[Any]:
    return [
        list(CLOSED_STATUS_IDS),
        recent_cutoff,
        list(CLOSED_STATUS_IDS),
        stale_cutoff,
        list(CLOSED_STATUS_IDS),
        now,
        now,
        list(CLOSED_STATUS_IDS),
        recent_cutoff,
    ]


def _customer_payload(row: dict[str, Any]) -> dict[str, Any]:
    score = _score_customer(row)
    repeat_labels = row.get("repeat_issue_labels") or []
    calibration = _feedback_calibration(row, int(score["customer_health_score"]))
    return {
        "company_id": row["company_id"],
        "company_autotask_id": row["company_autotask_id"],
        "company_name": row["company_name"],
        "total_tickets": _int(row.get("total_tickets")),
        "open_tickets": _int(row.get("open_tickets")),
        "recent_tickets": _int(row.get("recent_tickets")),
        "stale_open_tickets": _int(row.get("stale_open_tickets")),
        "overdue_open_tickets": _int(row.get("overdue_open_tickets")),
        "high_priority_open_tickets": _int(row.get("high_priority_open_tickets")),
        "history_events": _int(row.get("history_events")),
        "repeat_issue_groups": _int(row.get("repeat_issue_groups")),
        "repeat_issue_labels": list(repeat_labels)[:5],
        "latest_feedback_at": row.get("latest_feedback_at"),
        "calibration": calibration,
        **score,
    }


def customer_success_summary(limit: int = 25, recent_days: int = 30) -> dict[str, Any]:
    row_limit = min(max(limit, 1), 100)
    window_days = min(max(recent_days, 1), 365)
    summary_cache_key = cache_key(
        "customer-success-summary",
        {
            "limit": row_limit,
            "recent_days": window_days,
            "closed_status_ids": sorted(CLOSED_STATUS_IDS),
        },
    )
    cached = cache_get_json(summary_cache_key)
    if cached is not None:
        cached["cache"] = {"hit": True, "ttl_seconds": settings.customer_success_summary_cache_ttl_seconds}
        return cached

    now = datetime.now(UTC)
    recent_cutoff = now - timedelta(days=window_days)
    stale_cutoff = now - timedelta(days=7)
    query = _customer_row_query() + """
        ORDER BY
            open_tickets DESC,
            overdue_open_tickets DESC,
            stale_open_tickets DESC,
            recent_tickets DESC,
            company_name
        LIMIT %s
    """
    params = [*_customer_query_params(now, recent_cutoff, stale_cutoff), row_limit]
    with db_connection() as conn:
        rows = list(conn.execute(query, params).fetchall())

    customers = []
    buckets = {"critical": 0, "high": 0, "watch": 0, "normal": 0}
    partial_history_customers = 0
    for row in rows:
        customer = _customer_payload(dict(row))
        buckets[customer["risk_bucket"]] += 1
        if customer["warnings"]:
            partial_history_customers += 1
        customers.append(customer)

    customers.sort(
        key=lambda item: (
            -int(item["customer_health_score"]),
            -int(item["open_tickets"]),
            str(item.get("company_name") or ""),
        )
    )
    result = {
        "ok": True,
        "cache": {"hit": False, "ttl_seconds": settings.customer_success_summary_cache_ttl_seconds},
        "limit": row_limit,
        "recent_days": window_days,
        "summary": {
            "customers_sampled": len(customers),
            "critical": buckets["critical"],
            "high": buckets["high"],
            "watch": buckets["watch"],
            "normal": buckets["normal"],
            "partial_history_customers": partial_history_customers,
        },
        "warnings": [
            warning
            for warning in (
                "Some customer signals are partial because local TicketHistory coverage is incomplete."
                if partial_history_customers
                else "",
            )
            if warning
        ],
        "customers": customers,
    }
    encoded_result = jsonable_encoder(result)
    cache_set_json(summary_cache_key, encoded_result, settings.customer_success_summary_cache_ttl_seconds)
    return encoded_result


def _response_days(value: Any, now: datetime) -> float | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        delta = now - value
        return round(max(delta.total_seconds(), 0) / 86400, 1)
    return None


def _round_optional(value: Any, digits: int = 1) -> float | None:
    if value is None:
        return None
    return round(_num(value), digits)


def customer_success_detail(company_id: int, recent_days: int = 30) -> dict[str, Any]:
    window_days = min(max(recent_days, 1), 365)
    now = datetime.now(UTC)
    recent_cutoff = now - timedelta(days=window_days)
    stale_cutoff = now - timedelta(days=7)
    query = _customer_row_query(company_id=company_id)
    params = [*_customer_query_params(now, recent_cutoff, stale_cutoff), company_id]

    with db_connection() as conn:
        row = conn.execute(query, params).fetchone()
        if not row:
            return {"ok": False, "reason": "company_not_found", "company_id": company_id}

        tickets = list(
            conn.execute(
                """
                WITH labor AS (
                    SELECT ticket_id, sum(COALESCE(hours, 0)) AS labor_hours
                    FROM autotask_time_entries
                    GROUP BY ticket_id
                ),
                history AS (
                    SELECT ticket_id, count(*) AS history_events
                    FROM autotask_ticket_history
                    GROUP BY ticket_id
                )
                SELECT
                    t.id,
                    t.autotask_id,
                    t.ticket_number,
                    t.title,
                    t.status,
                    COALESCE(status_ref.label, t.status) AS status_label,
                    t.priority,
                    COALESCE(priority_ref.label, t.priority) AS priority_label,
                    t.created_at_autotask,
                    t.updated_at_autotask,
                    t.completed_at_autotask,
                    t.due_at_autotask,
                    t.resolved_due_at_autotask,
                    COALESCE(labor.labor_hours, 0) AS labor_hours,
                    COALESCE(history.history_events, 0) AS history_events
                FROM autotask_tickets t
                LEFT JOIN labor ON labor.ticket_id = t.id
                LEFT JOIN history ON history.ticket_id = t.id
                LEFT JOIN autotask_reference_values status_ref
                    ON status_ref.field_name='status' AND status_ref.value=t.status
                LEFT JOIN autotask_reference_values priority_ref
                    ON priority_ref.field_name='priority' AND priority_ref.value=t.priority
                WHERE t.company_id = %s
                  AND NOT t.analytics_exclude
                ORDER BY
                    (t.completed_at_autotask IS NULL) DESC,
                    t.resolved_due_at_autotask NULLS LAST,
                    t.due_at_autotask NULLS LAST,
                    t.created_at_autotask DESC NULLS LAST,
                    t.id DESC
                LIMIT 25
                """,
                (company_id,),
            ).fetchall()
        )
        repeat_issues = list(
            conn.execute(
                """
                SELECT
                    concat_ws(
                        ' / ',
                        COALESCE(NULLIF(category, ''), 'Uncategorized'),
                        NULLIF(issue_type, ''),
                        NULLIF(subissue_type, '')
                    ) AS label,
                    count(*) AS count,
                    max(created_at_autotask) AS latest_ticket_at
                FROM autotask_tickets
                WHERE company_id = %s
                  AND NOT analytics_exclude
                  AND created_at_autotask >= %s::timestamptz
                GROUP BY label
                HAVING count(*) >= 2
                ORDER BY count(*) DESC, latest_ticket_at DESC NULLS LAST, label
                LIMIT 10
                """,
                (company_id, recent_cutoff),
            ).fetchall()
        )
        response = conn.execute(
            """
            WITH scoped_notes AS (
                SELECT
                    n.id,
                    n.ticket_id,
                    n.created_at_autotask,
                    (
                        NULLIF(n.raw->>'createdByContactID', '') IS NOT NULL
                        AND n.raw->>'createdByContactID' <> '0'
                    ) AS is_customer_note,
                    (
                        n.resource_id IS NOT NULL
                        OR NULLIF(n.raw->>'creatorResourceID', '') IS NOT NULL
                    ) AS is_technician_note
                FROM autotask_ticket_notes n
                JOIN autotask_tickets t ON t.id = n.ticket_id
                WHERE t.company_id = %s
                  AND NOT t.analytics_exclude
            ),
            customer_notes AS (
                SELECT ticket_id, created_at_autotask AS customer_at
                FROM scoped_notes
                WHERE is_customer_note
                  AND created_at_autotask >= %s::timestamptz
            ),
            response_pairs AS (
                SELECT
                    customer_notes.customer_at,
                    (
                        SELECT min(next_note.created_at_autotask)
                        FROM scoped_notes next_note
                        WHERE next_note.ticket_id = customer_notes.ticket_id
                          AND next_note.is_technician_note
                          AND next_note.created_at_autotask > customer_notes.customer_at
                    ) AS technician_at
                FROM customer_notes
            )
            SELECT
                (SELECT count(*) FROM scoped_notes) AS total_notes,
                (SELECT count(*) FROM scoped_notes WHERE is_customer_note) AS customer_notes,
                (SELECT count(*) FROM scoped_notes WHERE is_technician_note) AS technician_notes,
                (SELECT max(created_at_autotask) FROM scoped_notes WHERE is_customer_note) AS last_customer_response_at,
                (SELECT max(created_at_autotask) FROM scoped_notes WHERE is_technician_note) AS last_technician_response_at,
                (SELECT count(*) FROM response_pairs) AS recent_customer_notes,
                (SELECT count(*) FROM response_pairs WHERE technician_at IS NOT NULL) AS technician_followups_after_customer,
                (
                    SELECT avg(EXTRACT(EPOCH FROM (technician_at - customer_at)) / 3600)
                    FROM response_pairs
                    WHERE technician_at IS NOT NULL
                ) AS avg_technician_followup_hours,
                (
                    SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (technician_at - customer_at)) / 3600)
                    FROM response_pairs
                    WHERE technician_at IS NOT NULL
                ) AS median_technician_followup_hours
            """,
            (company_id, recent_cutoff),
        ).fetchone()
        escalation_signals = list(
            conn.execute(
                """
                SELECT *
                FROM (
                    SELECT
                        'ticket' AS source_type,
                        t.id AS source_id,
                        t.ticket_number,
                        COALESCE(t.updated_at_autotask, t.created_at_autotask) AS happened_at,
                        left(concat_ws(' ', t.title, t.description), 280) AS signal_text
                    FROM autotask_tickets t
                    WHERE t.company_id = %s
                      AND NOT t.analytics_exclude
                      AND COALESCE(t.updated_at_autotask, t.created_at_autotask) >= %s::timestamptz
                      AND concat_ws(' ', t.title, t.description) ~* %s
                    UNION ALL
                    SELECT
                        'note' AS source_type,
                        n.id AS source_id,
                        t.ticket_number,
                        n.created_at_autotask AS happened_at,
                        left(concat_ws(' ', n.title, n.body), 280) AS signal_text
                    FROM autotask_ticket_notes n
                    JOIN autotask_tickets t ON t.id = n.ticket_id
                    WHERE t.company_id = %s
                      AND NOT t.analytics_exclude
                      AND n.created_at_autotask >= %s::timestamptz
                      AND concat_ws(' ', n.title, n.body) ~* %s
                    UNION ALL
                    SELECT
                        'history' AS source_type,
                        h.id AS source_id,
                        t.ticket_number,
                        h.happened_at,
                        left(concat_ws(' ', h.action, h.detail), 280) AS signal_text
                    FROM autotask_ticket_history h
                    JOIN autotask_tickets t ON t.id = h.ticket_id
                    WHERE t.company_id = %s
                      AND NOT t.analytics_exclude
                      AND h.happened_at >= %s::timestamptz
                      AND concat_ws(' ', h.action, h.detail) ~* %s
                ) signals
                ORDER BY happened_at DESC NULLS LAST, source_type, source_id DESC
                LIMIT 20
                """,
                (
                    company_id,
                    recent_cutoff,
                    ESCALATION_SIGNAL_PATTERN,
                    company_id,
                    recent_cutoff,
                    ESCALATION_SIGNAL_PATTERN,
                    company_id,
                    recent_cutoff,
                    ESCALATION_SIGNAL_PATTERN,
                ),
            ).fetchall()
        )
        sentiment_signals = list(
            conn.execute(
                """
                SELECT *
                FROM (
                    SELECT
                        'ticket' AS source_type,
                        t.id AS source_id,
                        t.ticket_number,
                        COALESCE(t.updated_at_autotask, t.created_at_autotask) AS happened_at,
                        left(concat_ws(' ', t.title, t.description), 280) AS signal_text
                    FROM autotask_tickets t
                    WHERE t.company_id = %s
                      AND NOT t.analytics_exclude
                      AND COALESCE(t.updated_at_autotask, t.created_at_autotask) >= %s::timestamptz
                      AND concat_ws(' ', t.title, t.description) ~* %s
                      AND concat_ws(' ', t.title, t.description) !~* %s
                    UNION ALL
                    SELECT
                        'note' AS source_type,
                        n.id AS source_id,
                        t.ticket_number,
                        n.created_at_autotask AS happened_at,
                        left(concat_ws(' ', n.title, n.body), 280) AS signal_text
                    FROM autotask_ticket_notes n
                    JOIN autotask_tickets t ON t.id = n.ticket_id
                    WHERE t.company_id = %s
                      AND NOT t.analytics_exclude
                      AND n.created_at_autotask >= %s::timestamptz
                      AND concat_ws(' ', n.title, n.body) ~* %s
                      AND concat_ws(' ', n.title, n.body) !~* %s
                    UNION ALL
                    SELECT
                        'history' AS source_type,
                        h.id AS source_id,
                        t.ticket_number,
                        h.happened_at,
                        left(concat_ws(' ', h.action, h.detail), 280) AS signal_text
                    FROM autotask_ticket_history h
                    JOIN autotask_tickets t ON t.id = h.ticket_id
                    WHERE t.company_id = %s
                      AND NOT t.analytics_exclude
                      AND h.happened_at >= %s::timestamptz
                      AND concat_ws(' ', h.action, h.detail) ~* %s
                      AND concat_ws(' ', h.action, h.detail) !~* %s
                ) signals
                ORDER BY happened_at DESC NULLS LAST, source_type, source_id DESC
                LIMIT 20
                """,
                (
                    company_id,
                    recent_cutoff,
                    SENTIMENT_SIGNAL_PATTERN,
                    SURVEY_NOISE_PATTERN,
                    company_id,
                    recent_cutoff,
                    SENTIMENT_SIGNAL_PATTERN,
                    SURVEY_NOISE_PATTERN,
                    company_id,
                    recent_cutoff,
                    SENTIMENT_SIGNAL_PATTERN,
                    SURVEY_NOISE_PATTERN,
                ),
            ).fetchall()
        )

    customer = _customer_payload(dict(row))
    response_trends = dict(response or {})
    response_trends["days_since_customer_response"] = _response_days(response_trends.get("last_customer_response_at"), now)
    response_trends["days_since_technician_response"] = _response_days(response_trends.get("last_technician_response_at"), now)
    response_trends["avg_technician_followup_hours"] = _round_optional(response_trends.get("avg_technician_followup_hours"))
    response_trends["median_technician_followup_hours"] = _round_optional(response_trends.get("median_technician_followup_hours"))
    response_warnings = []
    if not _int(response_trends.get("customer_notes")):
        response_warnings.append("No local customer note responses are linked for this customer yet.")
    if not _int(response_trends.get("technician_notes")):
        response_warnings.append("No local technician note responses are linked for this customer yet.")
    recent_customer_notes = _int(response_trends.get("recent_customer_notes"))
    technician_followups = _int(response_trends.get("technician_followups_after_customer"))
    if recent_customer_notes and technician_followups < recent_customer_notes:
        response_warnings.append("Some recent customer notes do not have a later local technician note on the same ticket.")
    avg_followup = response_trends.get("avg_technician_followup_hours")
    if avg_followup is not None and avg_followup >= 24:
        response_warnings.append("Average local technician follow-up after customer notes is over 24 hours in the recent window.")
    escalation_warnings = []
    if escalation_signals:
        escalation_warnings.append("Local escalation/churn language appears in recent customer evidence; review before assuming account risk.")
    sentiment_warnings = []
    if sentiment_signals:
        sentiment_warnings.append("Local sentiment language appears in recent customer evidence; review manually because no structured CSAT score is available.")

    return {
        "ok": True,
        "recent_days": window_days,
        "customer": customer,
        "tickets": [dict(ticket) for ticket in tickets],
        "repeat_issues": [dict(issue) for issue in repeat_issues],
        "response_trends": response_trends,
        "escalation_signals": [dict(signal) for signal in escalation_signals],
        "sentiment_signals": [dict(signal) for signal in sentiment_signals],
        "warnings": [*customer["warnings"], *response_warnings, *escalation_warnings, *sentiment_warnings],
    }


def store_customer_risk_feedback(
    company_id: int,
    risk_bucket: str | None,
    outcome: str,
    notes: str | None = None,
) -> dict[str, Any]:
    if outcome not in CUSTOMER_RISK_FEEDBACK_OUTCOMES:
        return {"ok": False, "reason": "invalid_outcome"}

    with db_connection() as conn:
        company = conn.execute(
            "SELECT id, autotask_id, name FROM autotask_companies WHERE id=%s",
            (company_id,),
        ).fetchone()
        if not company:
            return {"ok": False, "reason": "company_not_found"}
        row = conn.execute(
            """
            INSERT INTO customer_success_risk_feedback(
                company_id, company_autotask_id, company_name, risk_bucket, outcome, notes
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, created_at
            """,
            (company["id"], company["autotask_id"], company["name"], risk_bucket, outcome, notes),
        ).fetchone()

    invalidate_customer_success_summary_cache()
    return {
        "ok": True,
        "feedback_id": row["id"],
        "created_at": row["created_at"],
        "message": "Customer risk feedback stored locally. No Autotask account or ticket was changed.",
    }


def customer_success_calibration_report(limit: int = 25) -> dict[str, Any]:
    row_limit = min(max(limit, 1), 100)
    with db_connection() as conn:
        summary = conn.execute(
            """
            SELECT
                count(*) AS total_feedback,
                count(*) FILTER (WHERE outcome = 'confirmed_risk') AS confirmed_risk,
                count(*) FILTER (WHERE outcome = 'dismissed') AS dismissed,
                count(*) FILTER (WHERE outcome = 'needs_review') AS needs_review,
                count(DISTINCT company_id) AS reviewed_customers,
                max(created_at) AS latest_feedback_at
            FROM customer_success_risk_feedback
            """
        ).fetchone()
        by_bucket = list(
            conn.execute(
                """
                SELECT
                    COALESCE(risk_bucket, 'unknown') AS risk_bucket,
                    outcome,
                    count(*) AS count
                FROM customer_success_risk_feedback
                GROUP BY COALESCE(risk_bucket, 'unknown'), outcome
                ORDER BY risk_bucket, outcome
                """
            ).fetchall()
        )
        recent = list(
            conn.execute(
                """
                SELECT
                    id,
                    company_id,
                    company_autotask_id,
                    company_name,
                    risk_bucket,
                    outcome,
                    notes,
                    created_at
                FROM customer_success_risk_feedback
                ORDER BY created_at DESC, id DESC
                LIMIT %s
                """,
                (row_limit,),
            ).fetchall()
        )

    summary_row = dict(summary or {})
    total = _int(summary_row.get("total_feedback"))
    confirmed = _int(summary_row.get("confirmed_risk"))
    dismissed = _int(summary_row.get("dismissed"))
    needs_review = _int(summary_row.get("needs_review"))
    reviewed_customers = _int(summary_row.get("reviewed_customers"))
    readiness = _calibration_readiness(
        total,
        reviewed_customers,
        {"confirmed_risk": confirmed, "dismissed": dismissed},
        "customers",
    )
    return {
        "ok": True,
        "limit": row_limit,
        "summary": {
            "total_feedback": total,
            "confirmed_risk": confirmed,
            "dismissed": dismissed,
            "needs_review": needs_review,
            "reviewed_customers": reviewed_customers,
            "latest_feedback_at": summary_row.get("latest_feedback_at"),
        },
        "by_bucket": [dict(row) for row in by_bucket],
        "recent_feedback": [dict(row) for row in recent],
        "calibration_readiness": readiness,
        "guidance": [
            "Use this local feedback to calibrate scoring weights during human review.",
            "Feedback is review-only and does not write to Autotask or automatically change account-risk status.",
            readiness["interpretation"],
        ],
        "warnings": [
            warning
            for warning in (
                "No local customer-risk feedback has been captured yet." if total == 0 else "",
                "Dismissed-risk feedback is outpacing confirmed-risk feedback; review score weights before treating high scores as reliable."
                if dismissed > confirmed and total >= 3
                else "",
                "Needs-review outcomes are the largest feedback group; more analyst review is needed before calibration is reliable."
                if needs_review > max(confirmed, dismissed) and total >= 3
                else "",
                *readiness["blockers"],
            )
            if warning
        ],
    }


def customer_success_review_queue(
    limit: int = 25,
    recent_days: int = 30,
    risk_bucket: str | None = None,
    min_priority: int = 0,
    needs_review_only: bool = False,
) -> dict[str, Any]:
    row_limit = min(max(limit, 1), 100)
    priority_floor = min(max(int(min_priority or 0), 0), 100)
    allowed_bucket = risk_bucket if risk_bucket in {"critical", "high", "watch", "normal"} else None
    summary = customer_success_summary(limit=100, recent_days=recent_days)
    items: list[dict[str, Any]] = []
    for customer in summary.get("customers", []):
        calibration = customer.get("calibration") or {}
        reasons: list[str] = []
        if calibration.get("needs_review_feedback"):
            reasons.append(f"{calibration['needs_review_feedback']} local needs-review feedback outcomes")
        if customer.get("risk_bucket") in {"critical", "high"}:
            reasons.append(f"{customer.get('risk_bucket')} heuristic customer risk")
        if customer.get("overdue_open_tickets"):
            reasons.append(f"{customer['overdue_open_tickets']} overdue open tickets")
        if customer.get("stale_open_tickets"):
            reasons.append(f"{customer['stale_open_tickets']} stale open tickets")
        if customer.get("repeat_issue_groups"):
            reasons.append(f"{customer['repeat_issue_groups']} repeated issue groups")
        if not reasons:
            continue
        priority = 0
        priority += 30 if calibration.get("needs_review_feedback") else 0
        priority += int(customer.get("customer_health_score") or 0)
        priority += min(int(customer.get("overdue_open_tickets") or 0) * 5, 20)
        priority += min(int(customer.get("stale_open_tickets") or 0) * 3, 15)
        review_priority = min(priority, 100)
        if allowed_bucket and customer.get("risk_bucket") != allowed_bucket:
            continue
        if needs_review_only and not calibration.get("needs_review_feedback"):
            continue
        if review_priority < priority_floor:
            continue
        items.append(
            {
                "company_id": customer["company_id"],
                "company_autotask_id": customer["company_autotask_id"],
                "company_name": customer["company_name"],
                "risk_bucket": customer["risk_bucket"],
                "customer_health_score": customer["customer_health_score"],
                "calibrated_review_score": calibration.get("calibrated_review_score"),
                "review_priority": review_priority,
                "reasons": reasons,
                "calibration": calibration,
            }
        )

    items.sort(key=lambda item: (-int(item["review_priority"]), str(item.get("company_name") or "")))
    return {
        "ok": True,
        "limit": row_limit,
        "recent_days": summary.get("recent_days", recent_days),
        "filters": {
            "risk_bucket": allowed_bucket,
            "min_priority": priority_floor,
            "needs_review_only": bool(needs_review_only),
        },
        "summary": {
            "review_candidates": len(items),
            "returned": min(len(items), row_limit),
            "needs_review_feedback_customers": sum(1 for item in items if item["calibration"].get("needs_review_feedback")),
        },
        "items": items[:row_limit],
        "guidance": [
            "This queue is local and review-only.",
            "Use it to prioritize human customer-success review; it does not write to Autotask or assign work.",
        ],
    }


def customer_success_trends(days: int = 30) -> dict[str, Any]:
    window_days = min(max(days, 1), 365)
    since = datetime.now(UTC) - timedelta(days=window_days)
    with db_connection() as conn:
        feedback_rows = list(
            conn.execute(
                """
                SELECT
                    date_trunc('day', created_at)::date AS day,
                    count(*) AS total,
                    count(*) FILTER (WHERE outcome = 'confirmed_risk') AS confirmed_risk,
                    count(*) FILTER (WHERE outcome = 'dismissed') AS dismissed,
                    count(*) FILTER (WHERE outcome = 'needs_review') AS needs_review
                FROM customer_success_risk_feedback
                WHERE created_at >= %s::timestamptz
                GROUP BY date_trunc('day', created_at)::date
                ORDER BY day
                """,
                (since,),
            ).fetchall()
        )
        snapshot_rows = list(
            conn.execute(
                """
                SELECT
                    date_trunc('day', snapshot_at)::date AS day,
                    count(*) AS snapshots,
                    avg(customer_health_score) AS average_health_score,
                    avg(calibrated_review_score) AS average_calibrated_review_score,
                    count(*) FILTER (WHERE risk_bucket = 'critical') AS critical,
                    count(*) FILTER (WHERE risk_bucket = 'high') AS high,
                    count(*) FILTER (WHERE risk_bucket = 'watch') AS watch,
                    count(*) FILTER (WHERE risk_bucket = 'normal') AS normal
                FROM customer_success_score_snapshots
                WHERE snapshot_at >= %s::timestamptz
                GROUP BY date_trunc('day', snapshot_at)::date
                ORDER BY day
                """,
                (since,),
            ).fetchall()
        )

    current = customer_success_summary(limit=100, recent_days=window_days)
    buckets = {"critical": 0, "high": 0, "watch": 0, "normal": 0}
    calibrated_delta_total = 0
    calibrated_evidence_customers = 0
    for customer in current.get("customers", []):
        bucket = customer.get("risk_bucket")
        if bucket in buckets:
            buckets[bucket] += 1
        calibration = customer.get("calibration") or {}
        if calibration.get("evidence_count"):
            calibrated_evidence_customers += 1
            calibrated_delta_total += _int(calibration.get("score_adjustment"))

    score_snapshots_by_day = [
        {
            **dict(row),
            "average_health_score": _round_optional(row.get("average_health_score")),
            "average_calibrated_review_score": _round_optional(row.get("average_calibrated_review_score")),
        }
        for row in snapshot_rows
    ]
    latest_stored = score_snapshots_by_day[-1] if score_snapshots_by_day else None
    previous_stored = score_snapshots_by_day[-2] if len(score_snapshots_by_day) > 1 else None
    latest_summary = None
    if latest_stored:
        latest_summary = {
            "day": latest_stored.get("day"),
            "snapshots": _int(latest_stored.get("snapshots")),
            "average_health_score": latest_stored.get("average_health_score"),
            "average_calibrated_review_score": latest_stored.get("average_calibrated_review_score"),
            "risk_buckets": {
                "critical": _int(latest_stored.get("critical")),
                "high": _int(latest_stored.get("high")),
                "watch": _int(latest_stored.get("watch")),
                "normal": _int(latest_stored.get("normal")),
            },
            "previous_day_delta": None,
        }
        if previous_stored:
            latest_summary["previous_day_delta"] = {
                "day": previous_stored.get("day"),
                "snapshots": _int(latest_stored.get("snapshots")) - _int(previous_stored.get("snapshots")),
                "average_health_score": _round_optional(
                    (latest_stored.get("average_health_score") or 0) - (previous_stored.get("average_health_score") or 0)
                ),
                "critical": _int(latest_stored.get("critical")) - _int(previous_stored.get("critical")),
                "high": _int(latest_stored.get("high")) - _int(previous_stored.get("high")),
                "watch": _int(latest_stored.get("watch")) - _int(previous_stored.get("watch")),
                "normal": _int(latest_stored.get("normal")) - _int(previous_stored.get("normal")),
            }

    return {
        "ok": True,
        "days": window_days,
        "feedback_by_day": [dict(row) for row in feedback_rows],
        "score_snapshots_by_day": score_snapshots_by_day,
        "latest_stored_score_snapshot": latest_summary,
        "current_score_snapshot": {
            "sampled_customers": len(current.get("customers", [])),
            "risk_buckets": buckets,
            "customers_with_feedback_calibration": calibrated_evidence_customers,
            "net_calibration_adjustment": calibrated_delta_total,
        },
        "guidance": [
            "Feedback trend rows are historical local review events.",
            "Score snapshot rows come from explicit local snapshot captures.",
            "Latest stored score snapshot compares against the previous stored day when available.",
            "Current score distribution remains a live sample for immediate comparison.",
            "No Autotask data is written or changed by this report.",
        ],
    }


def capture_customer_success_score_snapshot(limit: int = 100, recent_days: int = 30) -> dict[str, Any]:
    row_limit = min(max(limit, 1), 500)
    report = customer_success_summary(limit=row_limit, recent_days=recent_days)
    customers = report.get("customers", [])
    with db_connection() as conn:
        inserted = 0
        for customer in customers:
            calibration = customer.get("calibration") or {}
            conn.execute(
                """
                INSERT INTO customer_success_score_snapshots(
                    company_id,
                    company_autotask_id,
                    company_name,
                    customer_health_score,
                    risk_bucket,
                    calibrated_review_score,
                    open_tickets,
                    overdue_open_tickets,
                    stale_open_tickets,
                    repeat_issue_groups
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    customer["company_id"],
                    customer["company_autotask_id"],
                    customer["company_name"],
                    customer["customer_health_score"],
                    customer["risk_bucket"],
                    calibration.get("calibrated_review_score"),
                    customer.get("open_tickets", 0),
                    customer.get("overdue_open_tickets", 0),
                    customer.get("stale_open_tickets", 0),
                    customer.get("repeat_issue_groups", 0),
                ),
            )
            inserted += 1

    return {
        "ok": True,
        "snapshot_rows_inserted": inserted,
        "recent_days": report.get("recent_days", recent_days),
        "message": "Customer Success score snapshot stored locally. No Autotask account or ticket was changed.",
    }


def cleanup_customer_success_score_snapshots(retention_days: int = 180) -> dict[str, Any]:
    days = min(max(int(retention_days or 0), 1), 3650)
    cutoff = datetime.now(UTC) - timedelta(days=days)
    with db_connection() as conn:
        rows = list(
            conn.execute(
                """
                DELETE FROM customer_success_score_snapshots
                WHERE snapshot_at < %s::timestamptz
                RETURNING id
                """,
                (cutoff,),
            ).fetchall()
        )

    return {
        "ok": True,
        "retention_days": days,
        "deleted_count": len(rows),
        "message": "Old Customer Success score snapshots were pruned locally. No Autotask account or ticket was changed.",
    }
