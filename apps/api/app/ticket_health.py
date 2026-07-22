from __future__ import annotations

from collections import Counter
import time
from datetime import UTC, datetime
import re
from typing import Any

from fastapi.encoders import jsonable_encoder

from .cache import cache_delete_namespace, cache_get_json, cache_set_json, scoped_cache_key
from .config import settings
from .db import db_connection, init_schema


REQUIRED_FIELDS: tuple[dict[str, Any], ...] = (
    {
        "key": "ticket_creation_date",
        "label": "Ticket creation date",
        "source": "autotask_tickets.created_at_autotask / raw.createDate",
        "sql": "count(*) FILTER (WHERE created_at_autotask IS NOT NULL OR NULLIF(raw->>'createDate', '') IS NOT NULL)",
        "needed_for": "Ticket age and open-duration calculations.",
    },
    {
        "key": "ticket_open_date",
        "label": "Ticket open date",
        "source": "Autotask createDate treated as open date until status history is synced",
        "sql": "count(*) FILTER (WHERE created_at_autotask IS NOT NULL OR NULLIF(raw->>'createDate', '') IS NOT NULL)",
        "needed_for": "Open ticket age baseline.",
    },
    {
        "key": "ticket_status",
        "label": "Ticket status",
        "source": "autotask_tickets.status / raw.status",
        "sql": "count(*) FILTER (WHERE NULLIF(status, '') IS NOT NULL OR NULLIF(raw->>'status', '') IS NOT NULL)",
        "needed_for": "Open, closed, waiting, and overdue filters.",
    },
    {
        "key": "ticket_status_history",
        "label": "Ticket status history",
        "source": "autotask_ticket_history from TicketHistory",
        "history_sql": "count(*)",
        "needed_for": "Accurate time spent in waiting/customer/vendor/technician states.",
        "missing_reason": "No local ticket history records have been synced yet.",
        "partial_reason": "TicketHistory has been synced for a subset of tickets; continue backfill for full duration analytics.",
    },
    {
        "key": "time_entries",
        "label": "Time entries",
        "source": "autotask_time_entries",
        "table": "autotask_time_entries",
        "needed_for": "Labor totals and high-labor warnings.",
    },
    {
        "key": "labor_hours",
        "label": "Labor hours",
        "source": "autotask_time_entries.hours",
        "table_sql": "count(*) FILTER (WHERE hours IS NOT NULL AND hours > 0)",
        "needed_for": "High-labor and effort trend analytics.",
    },
    {
        "key": "sla_information",
        "label": "SLA information",
        "source": "SLA raw fields and normalized SLA columns",
        "sql": "count(*) FILTER (WHERE sla_id IS NOT NULL OR raw ? 'serviceLevelAgreementID' OR raw ? 'serviceLevelAgreementHasBeenMet' OR raw ? 'firstResponseDueDateTime' OR raw ? 'resolvedDueDateTime')",
        "needed_for": "SLA risk and overdue status.",
    },
    {
        "key": "technician_assignment",
        "label": "Technician assignment",
        "source": "assigned_resource_id / assigned_resource_name",
        "sql": "count(*) FILTER (WHERE assigned_resource_id IS NOT NULL OR NULLIF(assigned_resource_name, '') IS NOT NULL OR NULLIF(raw->>'assignedResourceID', '') IS NOT NULL)",
        "needed_for": "Technician involvement and routing analytics.",
    },
    {
        "key": "customer_responses",
        "label": "Customer responses",
        "source": "ticket notes with createdByContactID",
        "note_sql": "count(*) FILTER (WHERE NULLIF(raw->>'createdByContactID', '') IS NOT NULL AND raw->>'createdByContactID' <> '0')",
        "needed_for": "Time since last customer action.",
    },
    {
        "key": "technician_responses",
        "label": "Technician responses",
        "source": "ticket notes with resource_id / creatorResourceID",
        "note_sql": "count(*) FILTER (WHERE resource_id IS NOT NULL OR NULLIF(raw->>'creatorResourceID', '') IS NOT NULL)",
        "needed_for": "Time since last technician action.",
    },
    {
        "key": "waiting_states",
        "label": "Waiting states",
        "source": "Current status plus TicketHistory transitions when synced",
        "sql": "count(*) FILTER (WHERE NULLIF(status, '') IS NOT NULL OR NULLIF(raw->>'status', '') IS NOT NULL)",
        "needed_for": "Waiting-on-customer/vendor/technician durations.",
        "partial_reason": "Current status is available, but TicketHistory records are required for precise durations.",
    },
    {
        "key": "priority",
        "label": "Priority",
        "source": "priority / raw.priority",
        "sql": "count(*) FILTER (WHERE NULLIF(priority, '') IS NOT NULL OR NULLIF(raw->>'priority', '') IS NOT NULL)",
        "needed_for": "Risk and urgency filters.",
    },
    {
        "key": "category",
        "label": "Category",
        "source": "category / issue_type / subissue_type",
        "sql": "count(*) FILTER (WHERE NULLIF(category, '') IS NOT NULL OR NULLIF(issue_type, '') IS NOT NULL OR NULLIF(subissue_type, '') IS NOT NULL)",
        "needed_for": "Ticket grouping and routing.",
    },
    {
        "key": "queue",
        "label": "Queue",
        "source": "queue / raw.queueID",
        "sql": "count(*) FILTER (WHERE NULLIF(queue, '') IS NOT NULL OR NULLIF(raw->>'queueID', '') IS NOT NULL)",
        "needed_for": "Operational ownership and queue-based reporting.",
    },
    {
        "key": "company",
        "label": "Company",
        "source": "company_id / raw.companyID",
        "sql": "count(*) FILTER (WHERE company_id IS NOT NULL OR NULLIF(raw->>'companyID', '') IS NOT NULL)",
        "needed_for": "Customer context and support history.",
    },
    {
        "key": "contact",
        "label": "Contact",
        "source": "contact_autotask_id / raw.contactID",
        "sql": "count(*) FILTER (WHERE contact_autotask_id IS NOT NULL OR NULLIF(raw->>'contactID', '') IS NOT NULL)",
        "needed_for": "Customer response attribution.",
    },
)

CLOSED_STATUS_IDS = {"5", "16", "20"}
TICKET_HEALTH_FEEDBACK_OUTCOMES = {"accurate", "too_high", "too_low", "needs_review"}
CALIBRATION_MIN_FEEDBACK = 10
CALIBRATION_MIN_REVIEWED_ENTITIES = 5
PREDICTION_PRIOR_SAMPLE_SIZE = 5
PREDICTION_MIN_SAMPLE_SIZE = 5


def invalidate_ticket_health_summary_cache() -> int:
    return cache_delete_namespace("ticket-health-summary")


def ticket_health_summary_cache_key(
    payload: dict[str, Any],
    *,
    authority_class: str = "outer-auth",
    roles: list[str] | None = None,
    scope: dict[str, Any] | None = None,
) -> str:
    return scoped_cache_key(
        "ticket-health-summary",
        payload,
        authority_class=authority_class,
        roles=roles or ["OuterAuth"],
        scope=scope or {"global": True},
        version=1,
        config={"ttl_seconds": settings.ticket_health_summary_cache_ttl_seconds},
    )


def _status(available: int, total: int, *, partial: bool = False, forced_missing: bool = False) -> str:
    if forced_missing or total == 0 or available == 0:
        return "missing"
    if partial or available < total:
        return "partial"
    return "available"


def _percent(available: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((available / total) * 100, 1)


def _num(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _round_optional(value: Any, digits: int = 2) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return None


def _priority_points(priority: Any) -> tuple[int, str | None]:
    clean = str(priority or "").strip()
    if clean == "4":
        return 25, "Critical priority"
    if clean == "1":
        return 18, "High priority"
    if clean == "2":
        return 8, "Medium priority"
    return 0, None


def _risk_bucket(score: int) -> str:
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "watch"
    return "normal"


def _ticket_score(row: dict[str, Any]) -> dict[str, Any]:
    score = 0
    factors: list[str] = []
    warnings: list[str] = []

    age_hours = _num(row.get("age_hours"))
    age_days = round(age_hours / 24, 1) if age_hours > 0 else 0.0
    if age_hours >= 24 * 14:
        score += 25
        factors.append(f"Open {age_days} days")
    elif age_hours >= 24 * 7:
        score += 18
        factors.append(f"Open {age_days} days")
    elif age_hours >= 24 * 3:
        score += 10
        factors.append(f"Open {age_days} days")

    priority_points, priority_label = _priority_points(row.get("priority"))
    if priority_points:
        score += priority_points
        factors.append(priority_label or "Priority risk")

    if row.get("resolved_overdue"):
        score += 25
        factors.append("Resolution due date passed")
    elif row.get("due_overdue"):
        score += 15
        factors.append("Due date passed")
    elif row.get("first_response_overdue"):
        score += 12
        factors.append("First response due date passed")

    labor_hours = _num(row.get("labor_hours"))
    if labor_hours >= 12:
        score += 18
        factors.append(f"{labor_hours:.1f} labor hours")
    elif labor_hours >= 6:
        score += 12
        factors.append(f"{labor_hours:.1f} labor hours")
    elif labor_hours >= 3:
        score += 6
        factors.append(f"{labor_hours:.1f} labor hours")

    if not row.get("assigned_resource_id") and not row.get("assigned_resource_name"):
        score += 8
        factors.append("No technician assignment")

    status_label = str(row.get("status_label") or row.get("status") or "").lower()
    if any(word in status_label for word in ("waiting", "hold", "customer", "vendor")):
        score += 8
        factors.append("Waiting status")

    history_events = int(row.get("history_events") or 0)
    if history_events == 0:
        warnings.append("TicketHistory not backfilled for this ticket; waiting-duration factors use current status only.")

    if not factors:
        factors.append("No elevated risk factors")

    score = min(score, 100)
    return {
        "health_score": score,
        "risk_bucket": _risk_bucket(score),
        "factors": factors,
        "warnings": warnings,
        "age_days": age_days,
        "labor_hours": round(labor_hours, 2),
        "history_events": history_events,
    }


def _ticket_health_feedback_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {outcome: 0 for outcome in sorted(TICKET_HEALTH_FEEDBACK_OUTCOMES)}
    for row in rows:
        outcome = str(row.get("outcome") or "")
        if outcome in counts:
            counts[outcome] += 1
    total = sum(counts.values())
    return {
        "total_feedback": total,
        "counts": counts,
        "latest_feedback_at": rows[0].get("created_at") if rows else None,
        "review_only": True,
        "message": "Local Ticket Health feedback calibrates the heuristic score for human review only and does not change Autotask.",
    }


def _ticket_health_feedback_calibration(base_score: int, feedback_rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = _ticket_health_feedback_summary(feedback_rows)["counts"]
    adjustment = 0
    factors: list[str] = []
    if counts["too_high"]:
        change = min(counts["too_high"] * 8, 24)
        adjustment -= change
        factors.append(f"{counts['too_high']} local review(s) marked score too high")
    if counts["too_low"]:
        change = min(counts["too_low"] * 8, 24)
        adjustment += change
        factors.append(f"{counts['too_low']} local review(s) marked score too low")
    if counts["accurate"]:
        factors.append(f"{counts['accurate']} local review(s) marked score accurate")
    if counts["needs_review"]:
        factors.append(f"{counts['needs_review']} local review(s) requested review")
    adjusted = max(0, min(100, int(base_score or 0) + adjustment))
    return {
        "base_score": int(base_score or 0),
        "calibrated_review_score": adjusted,
        "score_adjustment": adjustment,
        "risk_bucket": _risk_bucket(adjusted),
        "source": "local_ticket_health_feedback",
        "factors": factors or ["No local Ticket Health calibration feedback for this ticket."],
        "review_only": True,
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
        blockers.append("Need at least two decisive feedback outcome groups before score-weight review.")
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


CHANGE_RE = re.compile(r"^(?P<field>.+?) changed from (?P<from>.*?) to (?P<to>.*)$", re.IGNORECASE)


def _clean_history_value(value: Any) -> str | None:
    clean = str(value or "").strip()
    if not clean or clean.lower() in {"[blank]", "blank"}:
        return None
    return clean


def parse_history_transition(action: Any, detail: Any) -> dict[str, Any]:
    action_text = str(action or "").strip()
    detail_text = str(detail or "").strip()
    match = CHANGE_RE.match(detail_text)
    field = action_text.removesuffix(" Changed").strip() if action_text else None
    if match:
        field = match.group("field").strip() or field
        return {
            "is_transition": True,
            "field": field,
            "from": _clean_history_value(match.group("from")),
            "to": _clean_history_value(match.group("to")),
        }
    if "status" in action_text.lower() and detail_text:
        return {"is_transition": True, "field": "Status", "from": None, "to": _clean_history_value(detail_text)}
    return {"is_transition": False, "field": field, "from": None, "to": None}


def classify_history_transition_field(field: Any) -> str:
    clean = str(field or "").strip().lower()
    if not clean:
        return "unknown"
    if "status" in clean:
        return "status"
    if "customer" in clean or "client" in clean:
        return "customer_activity"
    if "resource" in clean or "assigned" in clean or "co-managing" in clean:
        return "assignment"
    if "service level" in clean or "sla" in clean:
        return "sla"
    if "resolution" in clean:
        return "resolution"
    if "date" in clean or "time" in clean or "activity" in clean or "target" in clean or "due" in clean:
        return "date_timing"
    if "checklist" in clean:
        return "checklist"
    if any(term in clean for term in ("created", "edited", "deleted", "merged", "absorbed")):
        return "lifecycle"
    return "other"


def _waiting_bucket(status: Any) -> str | None:
    clean = str(status or "").strip().lower()
    if not clean:
        return None
    if "vendor" in clean:
        return "vendor"
    if "customer" in clean or "client" in clean:
        return "customer"
    if "technician" in clean or "tech" in clean or "internal" in clean:
        return "technician"
    if "waiting" in clean or "hold" in clean:
        return "other"
    return None


def status_duration_summary(
    transitions: list[dict[str, Any]],
    *,
    current_status: Any = None,
    fallback_started_at: datetime | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    status_transitions = [
        transition
        for transition in transitions
        if str(transition.get("field") or "").strip().lower() == "status" and transition.get("happened_at")
    ]
    status_transitions.sort(key=lambda transition: transition["happened_at"])
    waiting_hours = {"customer": 0.0, "vendor": 0.0, "technician": 0.0, "other": 0.0}
    fallback_status = current_status
    current_status = None
    current_status_started_at = None
    reference_now = now or datetime.now(UTC)
    for index, transition in enumerate(status_transitions):
        started_at = transition["happened_at"]
        ended_at = status_transitions[index + 1]["happened_at"] if index + 1 < len(status_transitions) else reference_now
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=UTC)
        if ended_at.tzinfo is None:
            ended_at = ended_at.replace(tzinfo=UTC)
        hours = max((ended_at - started_at).total_seconds(), 0) / 3600
        status = transition.get("to")
        bucket = _waiting_bucket(status)
        if bucket:
            waiting_hours[bucket] += hours
        current_status = status
        current_status_started_at = started_at

    duration_source = "status_transitions" if status_transitions else "missing"
    if not status_transitions:
        current_status = fallback_status
        bucket = _waiting_bucket(current_status)
        if bucket and fallback_started_at:
            started_at = fallback_started_at
            if started_at.tzinfo is None:
                started_at = started_at.replace(tzinfo=UTC)
            hours = max((reference_now - started_at).total_seconds(), 0) / 3600
            waiting_hours[bucket] += hours
            current_status_started_at = started_at
            duration_source = "current_status_lower_bound"

    rounded = {key: round(value, 1) for key, value in waiting_hours.items()}
    total_waiting = round(sum(rounded.values()), 1)
    return {
        "status_transitions": len(status_transitions),
        "current_status": current_status,
        "current_status_started_at": current_status_started_at,
        "duration_source": duration_source,
        "waiting_hours": rounded,
        "total_waiting_hours": total_waiting,
        "warnings": [
            warning
            for warning in (
                "No parsed local status transitions; current waiting duration is a lower-bound estimate from the latest local ticket timestamp."
                if duration_source == "current_status_lower_bound"
                else "No parsed local status transitions; waiting-duration analytics remain partial."
                if not status_transitions
                else "",
            )
            if warning
        ],
    }


def ticket_history_transition_diagnostics(limit: int = 5000) -> dict[str, Any]:
    started = time.monotonic()
    row_limit = min(max(limit, 1), 20000)
    init_schema()
    with db_connection() as conn:
        counts = conn.execute(
            """
            SELECT
              count(*) AS ticket_history,
              count(*) FILTER (
                WHERE lower(COALESCE(action, '')) LIKE '%status%'
                   OR lower(COALESCE(detail, '')) LIKE '%status%'
              ) AS status_candidate_rows,
              count(*) FILTER (
                WHERE lower(COALESCE(detail, '')) LIKE '%waiting%'
                   OR lower(COALESCE(detail, '')) LIKE '%hold%'
                   OR lower(COALESCE(detail, '')) LIKE '%vendor%'
                   OR lower(COALESCE(detail, '')) LIKE '%technician%'
              ) AS waiting_keyword_rows,
              count(*) FILTER (
                WHERE lower(COALESCE(action, '')) LIKE '%customer%'
                   OR lower(COALESCE(detail, '')) LIKE '%customer%'
              ) AS customer_activity_rows
            FROM autotask_ticket_history
            """
        ).fetchone()
        action_rows = list(
            conn.execute(
                """
                SELECT COALESCE(NULLIF(action, ''), '[Blank]') AS action, count(*) AS count
                FROM autotask_ticket_history
                GROUP BY COALESCE(NULLIF(action, ''), '[Blank]')
                ORDER BY count(*) DESC, action
                LIMIT 20
                """
            ).fetchall()
        )
        rows = list(
            conn.execute(
                """
                SELECT id, ticket_id, action, detail, happened_at
                FROM autotask_ticket_history
                ORDER BY happened_at DESC NULLS LAST, id DESC
                LIMIT %s
                """,
                (row_limit,),
            ).fetchall()
        )
        source_row = conn.execute(
            """
            WITH observed_keys AS (
                SELECT DISTINCT key
                FROM autotask_ticket_history
                CROSS JOIN LATERAL jsonb_object_keys(raw) AS key
            ),
            raw_counts AS (
                SELECT
                    count(*) FILTER (WHERE raw::text ILIKE '%status%') AS raw_status_string_rows
                FROM autotask_ticket_history
            )
            SELECT
                COALESCE(array_agg(key ORDER BY key), ARRAY[]::text[]) AS observed_raw_fields,
                COALESCE(
                    array_agg(key ORDER BY key) FILTER (WHERE lower(key) LIKE '%status%'),
                    ARRAY[]::text[]
                ) AS observed_status_field_names,
                raw_counts.raw_status_string_rows
            FROM observed_keys
            CROSS JOIN raw_counts
            GROUP BY raw_counts.raw_status_string_rows
            """
        ).fetchone()

    field_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    status_candidate_samples: list[dict[str, Any]] = []
    parsed_transitions = 0
    parsed_status_transitions = 0
    for row in rows:
        parsed = parse_history_transition(row.get("action"), row.get("detail"))
        field = str(parsed.get("field") or "").strip() or "[Blank]"
        if parsed["is_transition"]:
            parsed_transitions += 1
            field_counts[field] += 1
            category_counts[classify_history_transition_field(field)] += 1
            if field.lower() == "status":
                parsed_status_transitions += 1
        row_text = f"{row.get('action') or ''} {row.get('detail') or ''}".lower()
        if len(status_candidate_samples) < 12 and any(
            term in row_text for term in ("status", "waiting", "hold", "vendor", "technician")
        ):
            status_candidate_samples.append(
                {
                    "id": row["id"],
                    "ticket_id": row["ticket_id"],
                    "action": row["action"],
                    "detail": row["detail"],
                    "happened_at": row["happened_at"],
                    "parsed": parsed,
                }
            )

    total_history = int(counts["ticket_history"] or 0)
    inspected = len(rows)
    warnings = [
        "No parsed local status transitions were found in the inspected TicketHistory rows."
        if parsed_status_transitions == 0
        else "",
        "Current local TicketHistory is dominated by non-status activity/date/SLA changes; duration analytics remain partial until status-change events are backfilled."
        if int(counts["status_candidate_rows"] or 0) == 0 or parsed_status_transitions == 0
        else "",
        "Observed local TicketHistory raw fields do not include a status field; exact status durations require status changes to appear in action/detail history rows or another read-only source."
        if not list((source_row or {}).get("observed_status_field_names") or [])
        else "",
    ]
    observed_raw_fields = list((source_row or {}).get("observed_raw_fields") or [])
    observed_status_field_names = list((source_row or {}).get("observed_status_field_names") or [])
    raw_status_string_rows = int((source_row or {}).get("raw_status_string_rows") or 0)
    return {
        "ok": True,
        "generated_at_ms": int((time.monotonic() - started) * 1000),
        "counts": {
            "ticket_history": total_history,
            "inspected_history": inspected,
            "parsed_transitions": parsed_transitions,
            "parsed_status_transitions": parsed_status_transitions,
            "status_candidate_rows": int(counts["status_candidate_rows"] or 0),
            "waiting_keyword_rows": int(counts["waiting_keyword_rows"] or 0),
            "customer_activity_rows": int(counts["customer_activity_rows"] or 0),
        },
        "coverage": {
            "parsed_transition_percent": _percent(parsed_transitions, inspected),
            "parsed_status_transition_percent": _percent(parsed_status_transitions, inspected),
        },
        "top_actions": [dict(row) for row in action_rows],
        "parsed_field_counts": [{"field": field, "count": count} for field, count in field_counts.most_common(20)],
        "parsed_transition_categories": [
            {"category": category, "count": count} for category, count in category_counts.most_common()
        ],
        "status_candidate_samples": status_candidate_samples,
        "source_capability": {
            "observed_raw_fields": observed_raw_fields,
            "observed_status_field_names": observed_status_field_names,
            "raw_status_string_rows": raw_status_string_rows,
            "has_observed_status_field": bool(observed_status_field_names),
            "interpretation": (
                "Local TicketHistory raw rows include status-like fields or values; parser calibration should inspect the samples."
                if observed_status_field_names or raw_status_string_rows
                else "Local TicketHistory raw rows currently expose action/detail/date/resource/ticket identifiers only, with no status-like raw field or value."
            ),
        },
        "warnings": [warning for warning in warnings if warning],
    }


def ticket_history_coverage_report(limit: int = 10) -> dict[str, Any]:
    row_limit = min(max(limit, 1), 100)
    init_schema()
    with db_connection() as conn:
        summary = conn.execute(
            """
            WITH open_tickets AS (
                SELECT t.id
                FROM autotask_tickets t
                WHERE t.completed_at_autotask IS NULL
                  AND COALESCE(t.status, '') <> ALL(%s)
            ),
            history AS (
                SELECT ticket_id, count(*) AS history_count, max(synced_at) AS last_history_synced_at
                FROM autotask_ticket_history
                GROUP BY ticket_id
            )
            SELECT
                count(*) AS open_tickets,
                count(*) FILTER (WHERE COALESCE(history.history_count, 0) > 0) AS open_tickets_with_history,
                count(*) FILTER (WHERE COALESCE(history.history_count, 0) = 0) AS open_tickets_without_history,
                count(*) FILTER (WHERE gap_check.last_checked_at IS NOT NULL) AS open_tickets_checked_for_history,
                count(*) FILTER (
                    WHERE COALESCE(history.history_count, 0) = 0
                      AND gap_check.last_checked_at IS NOT NULL
                      AND COALESCE(gap_check.last_result_count, 0) = 0
                ) AS open_tickets_checked_empty_history,
                count(*) FILTER (
                    WHERE COALESCE(history.history_count, 0) = 0
                      AND gap_check.last_checked_at IS NULL
                ) AS open_tickets_unchecked_history,
                COALESCE(sum(history.history_count), 0) AS open_ticket_history_rows
            FROM open_tickets
            LEFT JOIN history ON history.ticket_id=open_tickets.id
            LEFT JOIN ticket_gap_sync_checks gap_check
              ON gap_check.ticket_id=open_tickets.id AND gap_check.sync_type='open_ticket_history_gaps'
            """,
            (list(CLOSED_STATUS_IDS),),
        ).fetchone()
        by_status = list(
            conn.execute(
                """
                WITH history AS (
                    SELECT ticket_id, count(*) AS history_count, max(synced_at) AS last_history_synced_at
                    FROM autotask_ticket_history
                    GROUP BY ticket_id
                )
                SELECT
                    COALESCE(status_ref.label, t.status, '[Blank]') AS status_label,
                    count(*) AS open_tickets,
                    count(*) FILTER (WHERE COALESCE(history.history_count, 0) > 0) AS with_history,
                    count(*) FILTER (WHERE COALESCE(history.history_count, 0) = 0) AS without_history,
                    max(history.last_history_synced_at) AS latest_history_synced_at
                FROM autotask_tickets t
                LEFT JOIN autotask_reference_values status_ref
                  ON status_ref.field_name='status' AND status_ref.value=t.status
                LEFT JOIN history ON history.ticket_id=t.id
                WHERE t.completed_at_autotask IS NULL
                  AND COALESCE(t.status, '') <> ALL(%s)
                GROUP BY COALESCE(status_ref.label, t.status, '[Blank]')
                ORDER BY without_history DESC, open_tickets DESC, status_label
                LIMIT 25
                """,
                (list(CLOSED_STATUS_IDS),),
            ).fetchall()
        )
        next_targets = list(
            conn.execute(
                """
                WITH history AS (
                    SELECT ticket_id, count(*) AS history_count, max(synced_at) AS last_history_synced_at
                    FROM autotask_ticket_history
                    GROUP BY ticket_id
                )
                SELECT
                    t.id,
                    t.autotask_id,
                    t.ticket_number,
                    t.title,
                    COALESCE(status_ref.label, t.status, '[Blank]') AS status_label,
                    t.updated_at_autotask,
                    COALESCE(history.history_count, 0) AS history_count,
                    history.last_history_synced_at,
                    gap_check.last_checked_at AS last_gap_checked_at,
                    gap_check.last_result_count AS last_gap_result_count
                FROM autotask_tickets t
                LEFT JOIN autotask_reference_values status_ref
                  ON status_ref.field_name='status' AND status_ref.value=t.status
                LEFT JOIN history ON history.ticket_id=t.id
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
                (list(CLOSED_STATUS_IDS), row_limit),
            ).fetchall()
        )

    open_tickets = int(summary["open_tickets"] or 0)
    with_history = int(summary["open_tickets_with_history"] or 0)
    without_history = int(summary["open_tickets_without_history"] or 0)
    coverage_percent = round((with_history / open_tickets) * 100, 2) if open_tickets else 100.0
    warnings = []
    if without_history:
        warnings.append(
            f"{without_history} open local tickets do not have local TicketHistory yet; use bounded open-ticket gap sync before trusting duration coverage."
        )
    return {
        "ok": True,
        "summary": {
            "open_tickets": open_tickets,
            "open_tickets_with_history": with_history,
            "open_tickets_without_history": without_history,
            "open_tickets_checked_for_history": int(summary["open_tickets_checked_for_history"] or 0),
            "open_tickets_checked_empty_history": int(summary["open_tickets_checked_empty_history"] or 0),
            "open_tickets_unchecked_history": int(summary["open_tickets_unchecked_history"] or 0),
            "open_ticket_history_rows": int(summary["open_ticket_history_rows"] or 0),
            "coverage_percent": coverage_percent,
        },
        "by_status": [dict(row) for row in by_status],
        "next_targets": [dict(row) for row in next_targets],
        "warnings": warnings,
    }


def labor_coverage_report(limit: int = 10) -> dict[str, Any]:
    row_limit = min(max(limit, 1), 100)
    init_schema()
    with db_connection() as conn:
        summary = conn.execute(
            """
            WITH open_tickets AS (
                SELECT t.id
                FROM autotask_tickets t
                WHERE t.completed_at_autotask IS NULL
                  AND COALESCE(t.status, '') <> ALL(%s)
            ),
            labor AS (
                SELECT
                    ticket_id,
                    count(*) AS entry_count,
                    sum(COALESCE(hours, 0)) AS labor_hours,
                    max(COALESCE(updated_at_autotask, created_at_autotask)) AS last_time_entry_observed_at
                FROM autotask_time_entries
                GROUP BY ticket_id
            )
            SELECT
                count(*) AS open_tickets,
                count(*) FILTER (WHERE COALESCE(labor.entry_count, 0) > 0) AS open_tickets_with_time_entries,
                count(*) FILTER (WHERE COALESCE(labor.entry_count, 0) = 0) AS open_tickets_without_time_entries,
                count(*) FILTER (WHERE gap_check.last_checked_at IS NOT NULL) AS open_tickets_checked_for_time_entries,
                count(*) FILTER (
                    WHERE COALESCE(labor.entry_count, 0) = 0
                      AND gap_check.last_checked_at IS NOT NULL
                      AND COALESCE(gap_check.last_result_count, 0) = 0
                ) AS open_tickets_checked_empty_time_entries,
                count(*) FILTER (
                    WHERE COALESCE(labor.entry_count, 0) = 0
                      AND gap_check.last_checked_at IS NULL
                ) AS open_tickets_unchecked_time_entries,
                COALESCE(sum(labor.entry_count), 0) AS open_ticket_time_entry_rows,
                COALESCE(sum(labor.labor_hours), 0) AS open_ticket_labor_hours
            FROM open_tickets
            LEFT JOIN labor ON labor.ticket_id=open_tickets.id
            LEFT JOIN ticket_gap_sync_checks gap_check
              ON gap_check.ticket_id=open_tickets.id AND gap_check.sync_type='open_ticket_time_entry_gaps'
            """,
            (list(CLOSED_STATUS_IDS),),
        ).fetchone()
        by_status = list(
            conn.execute(
                """
                WITH labor AS (
                    SELECT
                        ticket_id,
                        count(*) AS entry_count,
                        sum(COALESCE(hours, 0)) AS labor_hours,
                        max(COALESCE(updated_at_autotask, created_at_autotask)) AS last_time_entry_observed_at
                    FROM autotask_time_entries
                    GROUP BY ticket_id
                )
                SELECT
                    COALESCE(status_ref.label, t.status, '[Blank]') AS status_label,
                    count(*) AS open_tickets,
                    count(*) FILTER (WHERE COALESCE(labor.entry_count, 0) > 0) AS with_time_entries,
                    count(*) FILTER (WHERE COALESCE(labor.entry_count, 0) = 0) AS without_time_entries,
                    count(*) FILTER (WHERE gap_check.last_checked_at IS NOT NULL) AS checked_for_time_entries,
                    count(*) FILTER (
                        WHERE COALESCE(labor.entry_count, 0) = 0
                          AND gap_check.last_checked_at IS NOT NULL
                          AND COALESCE(gap_check.last_result_count, 0) = 0
                    ) AS checked_empty_time_entries,
                    count(*) FILTER (
                        WHERE COALESCE(labor.entry_count, 0) = 0
                          AND gap_check.last_checked_at IS NULL
                    ) AS unchecked_time_entries,
                    COALESCE(sum(labor.labor_hours), 0) AS labor_hours,
                    max(labor.last_time_entry_observed_at) AS latest_time_entry_observed_at
                FROM autotask_tickets t
                LEFT JOIN autotask_reference_values status_ref
                  ON status_ref.field_name='status' AND status_ref.value=t.status
                LEFT JOIN labor ON labor.ticket_id=t.id
                LEFT JOIN ticket_gap_sync_checks gap_check
                  ON gap_check.ticket_id=t.id AND gap_check.sync_type='open_ticket_time_entry_gaps'
                WHERE t.completed_at_autotask IS NULL
                  AND COALESCE(t.status, '') <> ALL(%s)
                GROUP BY COALESCE(status_ref.label, t.status, '[Blank]')
                ORDER BY without_time_entries DESC, open_tickets DESC, status_label
                LIMIT 25
                """,
                (list(CLOSED_STATUS_IDS),),
            ).fetchall()
        )
        next_targets = list(
            conn.execute(
                """
                WITH labor AS (
                    SELECT
                        ticket_id,
                        count(*) AS entry_count,
                        sum(COALESCE(hours, 0)) AS labor_hours,
                        max(COALESCE(updated_at_autotask, created_at_autotask)) AS last_time_entry_observed_at
                    FROM autotask_time_entries
                    GROUP BY ticket_id
                )
                SELECT
                    t.id,
                    t.autotask_id,
                    t.ticket_number,
                    t.title,
                    COALESCE(status_ref.label, t.status, '[Blank]') AS status_label,
                    t.updated_at_autotask,
                    COALESCE(labor.entry_count, 0) AS time_entry_count,
                    COALESCE(labor.labor_hours, 0) AS labor_hours,
                    labor.last_time_entry_observed_at,
                    gap_check.last_checked_at AS last_gap_checked_at,
                    gap_check.last_result_count AS last_gap_result_count
                FROM autotask_tickets t
                LEFT JOIN autotask_reference_values status_ref
                  ON status_ref.field_name='status' AND status_ref.value=t.status
                LEFT JOIN labor ON labor.ticket_id=t.id
                LEFT JOIN ticket_gap_sync_checks gap_check
                  ON gap_check.ticket_id=t.id AND gap_check.sync_type='open_ticket_time_entry_gaps'
                WHERE t.completed_at_autotask IS NULL
                  AND COALESCE(t.status, '') <> ALL(%s)
                ORDER BY
                    (COALESCE(labor.entry_count, 0) = 0) DESC,
                    gap_check.last_checked_at NULLS FIRST,
                    labor.last_time_entry_observed_at NULLS FIRST,
                    t.updated_at_autotask DESC NULLS LAST,
                    t.id
                LIMIT %s
                """,
                (list(CLOSED_STATUS_IDS), row_limit),
            ).fetchall()
        )

    open_tickets = int(summary["open_tickets"] or 0)
    with_time_entries = int(summary["open_tickets_with_time_entries"] or 0)
    without_time_entries = int(summary["open_tickets_without_time_entries"] or 0)
    coverage_percent = round((with_time_entries / open_tickets) * 100, 2) if open_tickets else 100.0
    warnings = []
    if without_time_entries:
        warnings.append(
            f"{without_time_entries} open local tickets do not have local TimeEntries yet; use bounded open-ticket labor gap sync before trusting labor coverage."
        )
    return {
        "ok": True,
        "summary": {
            "open_tickets": open_tickets,
            "open_tickets_with_time_entries": with_time_entries,
            "open_tickets_without_time_entries": without_time_entries,
            "open_tickets_checked_for_time_entries": int(summary["open_tickets_checked_for_time_entries"] or 0),
            "open_tickets_checked_empty_time_entries": int(summary["open_tickets_checked_empty_time_entries"] or 0),
            "open_tickets_unchecked_time_entries": int(summary["open_tickets_unchecked_time_entries"] or 0),
            "open_ticket_time_entry_rows": int(summary["open_ticket_time_entry_rows"] or 0),
            "open_ticket_labor_hours": round(float(summary["open_ticket_labor_hours"] or 0), 2),
            "coverage_percent": coverage_percent,
        },
        "by_status": [dict(row) for row in by_status],
        "next_targets": [dict(row) for row in next_targets],
        "warnings": warnings,
    }


def _summary_where(queue: str | None, assigned_resource_id: int | None) -> tuple[str, list[Any]]:
    clauses = ["t.completed_at_autotask IS NULL", "NOT t.analytics_exclude", "COALESCE(t.status, '') <> ALL(%s)"]
    params: list[Any] = [list(CLOSED_STATUS_IDS)]
    if queue:
        clauses.append("t.queue = %s")
        params.append(queue)
    if assigned_resource_id is not None:
        clauses.append("t.assigned_resource_id = %s")
        params.append(assigned_resource_id)
    return " AND ".join(clauses), params


def _company_scope_clause(
    authorized_company_ids: list[int] | None,
    *,
    alias: str = "t",
) -> tuple[str, list[Any]]:
    if authorized_company_ids is None:
        return "", []
    if not authorized_company_ids:
        return f" AND {alias}.company_id = ANY(%s)", [[]]
    return f" AND {alias}.company_id = ANY(%s)", [authorized_company_ids]


def _score_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    tickets: list[dict[str, Any]] = []
    buckets = {"critical": 0, "high": 0, "watch": 0, "normal": 0, "partial_history_tickets": 0}
    for row in rows:
        score = _ticket_score(row)
        buckets["partial_history_tickets"] += 1 if score["history_events"] == 0 else 0
        buckets[score["risk_bucket"]] += 1
        tickets.append(
            {
                "id": row["id"],
                "autotask_id": row["autotask_id"],
                "ticket_number": row["ticket_number"],
                "title": row["title"],
                "status": row["status"],
                "status_label": row["status_label"],
                "priority": row["priority"],
                "priority_label": row["priority_label"],
                "queue": row["queue"],
                "queue_label": row["queue_label"],
                "assigned_resource_id": row["assigned_resource_id"],
                "assigned_resource_name": row["assigned_resource_name"],
                "created_at_autotask": row["created_at_autotask"],
                "updated_at_autotask": row["updated_at_autotask"],
                "due_at_autotask": row["due_at_autotask"],
                "resolved_due_at_autotask": row["resolved_due_at_autotask"],
                **score,
            }
        )
    tickets.sort(key=lambda item: (-int(item["health_score"]), str(item.get("ticket_number") or "")))
    return tickets, buckets


def field_coverage_report(authorized_company_ids: list[int] | None = None) -> dict[str, Any]:
    started = time.monotonic()
    init_schema()
    company_scope_sql, company_scope_params = _company_scope_clause(authorized_company_ids)
    with db_connection() as conn:
        counts = conn.execute(
            f"""
            SELECT
              (SELECT count(*) FROM autotask_tickets t WHERE true {company_scope_sql}) AS tickets,
              (
                SELECT count(*)
                FROM autotask_ticket_notes n
                JOIN autotask_tickets t ON t.id=n.ticket_id
                WHERE true {company_scope_sql}
              ) AS ticket_notes,
              (
                SELECT count(*)
                FROM autotask_time_entries e
                JOIN autotask_tickets t ON t.id=e.ticket_id
                WHERE true {company_scope_sql}
              ) AS time_entries,
              (
                SELECT count(*)
                FROM autotask_ticket_history h
                JOIN autotask_tickets t ON t.id=h.ticket_id
                WHERE true {company_scope_sql}
              ) AS ticket_history,
              (
                SELECT count(*)
                FROM autotask_ticket_history h
                JOIN autotask_tickets t ON t.id=h.ticket_id
                WHERE true {company_scope_sql}
                  AND (
                    lower(COALESCE(action, '')) LIKE '%%status%%'
                    OR lower(COALESCE(detail, '')) LIKE '%%status%%'
                    OR lower(COALESCE(detail, '')) LIKE '%%waiting%%'
                    OR lower(COALESCE(detail, '')) LIKE '%%hold%%'
                    OR lower(COALESCE(detail, '')) LIKE '%%vendor%%'
                    OR lower(COALESCE(detail, '')) LIKE '%%technician%%'
                  )
              ) AS ticket_history_status_candidates
            """,
            (*company_scope_params, *company_scope_params, *company_scope_params, *company_scope_params, *company_scope_params),
        ).fetchone()
        ticket_total = int(counts["tickets"] or 0)
        note_total = int(counts["ticket_notes"] or 0)
        time_total = int(counts["time_entries"] or 0)
        history_total = int(counts["ticket_history"] or 0)
        history_status_candidates = int(counts.get("ticket_history_status_candidates", 0) or 0)

        ticket_specs = [spec for spec in REQUIRED_FIELDS if "sql" in spec]
        note_specs = [spec for spec in REQUIRED_FIELDS if "note_sql" in spec]
        time_specs = [spec for spec in REQUIRED_FIELDS if "table_sql" in spec]
        history_specs = [spec for spec in REQUIRED_FIELDS if "history_sql" in spec]
        ticket_counts: dict[str, int] = {}
        note_counts: dict[str, int] = {}
        time_counts: dict[str, int] = {}
        history_counts: dict[str, int] = {}

        if ticket_specs:
            select_list = ", ".join(f"{spec['sql']} AS {spec['key']}" for spec in ticket_specs)
            ticket_counts = dict(
                conn.execute(
                    f"SELECT {select_list} FROM (SELECT t.* FROM autotask_tickets t WHERE true {company_scope_sql}) scoped_tickets",
                    tuple(company_scope_params),
                ).fetchone()
            )
        if note_specs:
            select_list = ", ".join(f"{spec['note_sql']} AS {spec['key']}" for spec in note_specs)
            note_counts = dict(
                conn.execute(
                    f"""
                    SELECT {select_list}
                    FROM (
                        SELECT n.*
                        FROM autotask_ticket_notes n
                        JOIN autotask_tickets t ON t.id=n.ticket_id
                        WHERE true {company_scope_sql}
                    ) scoped_notes
                    """,
                    tuple(company_scope_params),
                ).fetchone()
            )
        if time_specs:
            select_list = ", ".join(f"{spec['table_sql']} AS {spec['key']}" for spec in time_specs)
            time_counts = dict(
                conn.execute(
                    f"""
                    SELECT {select_list}
                    FROM (
                        SELECT e.*
                        FROM autotask_time_entries e
                        JOIN autotask_tickets t ON t.id=e.ticket_id
                        WHERE true {company_scope_sql}
                    ) scoped_time_entries
                    """,
                    tuple(company_scope_params),
                ).fetchone()
            )
        if history_specs:
            select_list = ", ".join(f"{spec['history_sql']} AS {spec['key']}" for spec in history_specs)
            history_counts = dict(
                conn.execute(
                    f"""
                    SELECT {select_list}
                    FROM (
                        SELECT h.*
                        FROM autotask_ticket_history h
                        JOIN autotask_tickets t ON t.id=h.ticket_id
                        WHERE true {company_scope_sql}
                    ) scoped_ticket_history
                    """,
                    tuple(company_scope_params),
                ).fetchone()
            )

        rows: list[dict[str, Any]] = []
        for spec in REQUIRED_FIELDS:
            if "table" in spec:
                available = time_total
                denominator = time_total
            elif "table_sql" in spec:
                available = int(time_counts.get(spec["key"], 0) or 0)
                denominator = time_total
            elif "history_sql" in spec:
                available = int(history_counts.get(spec["key"], 0) or 0)
                denominator = ticket_total
            elif "note_sql" in spec:
                available = int(note_counts.get(spec["key"], 0) or 0)
                denominator = note_total
            else:
                available = int(ticket_counts.get(spec["key"], 0) or 0)
                denominator = ticket_total

            partial = bool(spec.get("partial_reason"))
            if spec["key"] == "waiting_states":
                partial = history_status_candidates == 0 or history_total < ticket_total
            status = _status(
                available,
                denominator,
                partial=partial,
                forced_missing=bool(spec.get("missing_reason")) and available == 0,
            )
            note = ""
            if status == "missing":
                note = str(spec.get("missing_reason") or "")
            elif status == "partial":
                note = str(spec.get("partial_reason") or "")
                if spec["key"] == "waiting_states" and history_total > 0 and history_status_candidates == 0:
                    note = (
                        "Current status is available, but local TicketHistory has no status/waiting transition candidates yet; "
                        "precise waiting durations remain partial."
                    )
            rows.append(
                {
                    "key": spec["key"],
                    "label": spec["label"],
                    "status": status,
                    "available_count": available,
                    "total_count": denominator,
                    "coverage_percent": _percent(available, denominator),
                    "source": spec["source"],
                    "needed_for": spec["needed_for"],
                    "note": note,
                }
            )

    missing = [row["key"] for row in rows if row["status"] == "missing"]
    partial = [row["key"] for row in rows if row["status"] == "partial"]
    ready_for_ticket_health = not missing and not partial
    blockers = [
        "Sync Autotask time entries before labor-hour analytics."
        if "time_entries" in missing or "labor_hours" in missing
        else "",
        "Add status-history ingestion before precise waiting-state duration analytics."
        if "ticket_status_history" in missing
        else "",
        "Local TicketHistory has no status/waiting transition candidates yet; precise waiting durations need status-change action/detail events or another read-only source."
        if history_total > 0 and history_status_candidates == 0 and ("ticket_status_history" in partial or "waiting_states" in partial)
        else "Continue TicketHistory backfill before precise waiting-state duration analytics."
        if "ticket_status_history" in partial or "waiting_states" in partial
        else "",
    ]
    blockers = [item for item in blockers if item]

    return {
        "ok": True,
        "generated_at_ms": int((time.monotonic() - started) * 1000),
        "counts": {
            "tickets": ticket_total,
            "ticket_notes": note_total,
            "time_entries": time_total,
            "ticket_history": history_total,
            "ticket_history_status_candidates": history_status_candidates,
        },
        "ready_for_ticket_health": ready_for_ticket_health,
        "available_fields": [row["key"] for row in rows if row["status"] == "available"],
        "partial_fields": partial,
        "missing_fields": missing,
        "blockers": blockers,
        "fields": rows,
    }


def ticket_status_source_diagnostics(authorized_company_ids: list[int] | None = None) -> dict[str, Any]:
    started = time.monotonic()
    init_schema()
    company_scope_sql, company_scope_params = _company_scope_clause(authorized_company_ids)
    with db_connection() as conn:
        counts = conn.execute(
            f"""
            SELECT
              count(*) AS tickets,
              count(*) FILTER (WHERE NULLIF(status, '') IS NOT NULL OR NULLIF(raw->>'status', '') IS NOT NULL)
                AS tickets_with_current_status,
              count(*) FILTER (WHERE updated_at_autotask IS NOT NULL) AS tickets_with_autotask_updated_at
            FROM autotask_tickets
            t
            WHERE true {company_scope_sql}
            """,
            tuple(company_scope_params),
        ).fetchone()
        status_field_rows = list(
            conn.execute(
                f"""
                SELECT key, count(*) AS ticket_count
                FROM autotask_tickets
                t
                CROSS JOIN LATERAL jsonb_object_keys(raw) AS key
                WHERE lower(key) LIKE '%%status%%'
                  {company_scope_sql}
                GROUP BY key
                ORDER BY key
                """,
                tuple(company_scope_params),
            ).fetchall()
        )
        timestamp_field_rows = list(
            conn.execute(
                f"""
                SELECT key, count(*) AS ticket_count
                FROM autotask_tickets
                t
                CROSS JOIN LATERAL jsonb_object_keys(raw) AS key
                WHERE (
                    lower(key) LIKE '%%date%%'
                    OR lower(key) LIKE '%%time%%'
                    OR lower(key) LIKE '%%activity%%'
                    OR lower(key) LIKE '%%response%%'
                    OR lower(key) LIKE '%%resolved%%'
                    OR lower(key) LIKE '%%completed%%'
                )
                  {company_scope_sql}
                GROUP BY key
                ORDER BY key
                """,
                tuple(company_scope_params),
            ).fetchall()
        )
        distribution_rows = list(
            conn.execute(
                f"""
                SELECT
                    COALESCE(ref.label, NULLIF(t.status, ''), '[Blank]') AS status_label,
                    NULLIF(t.status, '') AS status,
                    count(*) AS ticket_count,
                    min(t.updated_at_autotask) AS oldest_autotask_update,
                    max(t.updated_at_autotask) AS newest_autotask_update
                FROM autotask_tickets t
                LEFT JOIN autotask_reference_values ref
                  ON ref.field_name='status' AND ref.value=t.status
                WHERE true {company_scope_sql}
                GROUP BY COALESCE(ref.label, NULLIF(t.status, ''), '[Blank]'), NULLIF(t.status, '')
                ORDER BY count(*) DESC, status_label
                LIMIT 20
                """,
                tuple(company_scope_params),
            ).fetchall()
        )
        status_sample_rows = list(
            conn.execute(
                f"""
                WITH history_probe AS (
                    SELECT
                        ticket_id,
                        count(*) AS history_rows,
                        count(*) FILTER (
                            WHERE lower(COALESCE(action, '')) LIKE '%%status%%'
                               OR lower(COALESCE(detail, '')) LIKE '%%status%%'
                        ) AS status_candidate_rows,
                        count(*) FILTER (
                            WHERE lower(COALESCE(detail, '')) LIKE '%%waiting%%'
                               OR lower(COALESCE(detail, '')) LIKE '%%hold%%'
                               OR lower(COALESCE(detail, '')) LIKE '%%vendor%%'
                               OR lower(COALESCE(detail, '')) LIKE '%%technician%%'
                        ) AS waiting_keyword_rows
                    FROM autotask_ticket_history
                    GROUP BY ticket_id
                )
                SELECT
                    COALESCE(ref.label, NULLIF(t.status, ''), '[Blank]') AS status_label,
                    NULLIF(t.status, '') AS status,
                    count(*) AS open_tickets,
                    count(sample_check.ticket_id) AS sampled_tickets,
                    count(*) FILTER (
                        WHERE sample_check.ticket_id IS NOT NULL
                          AND COALESCE(sample_check.last_result_count, 0) = 0
                    ) AS sampled_empty_tickets,
                    COALESCE(sum(sample_check.last_result_count), 0) AS sampled_history_rows,
                    COALESCE(
                        sum(history_probe.status_candidate_rows) FILTER (WHERE sample_check.ticket_id IS NOT NULL),
                        0
                    ) AS sampled_status_candidate_rows,
                    COALESCE(
                        sum(history_probe.waiting_keyword_rows) FILTER (WHERE sample_check.ticket_id IS NOT NULL),
                        0
                    ) AS sampled_waiting_keyword_rows,
                    count(*) FILTER (
                        WHERE sample_check.ticket_id IS NOT NULL
                          AND COALESCE(sample_check.last_result_count, 0) > 0
                          AND COALESCE(history_probe.status_candidate_rows, 0) = 0
                    ) AS sampled_tickets_without_status_candidates,
                    min(sample_check.last_checked_at) AS first_sampled_at,
                    max(sample_check.last_checked_at) AS last_sampled_at
                FROM autotask_tickets t
                LEFT JOIN autotask_reference_values ref
                  ON ref.field_name='status' AND ref.value=t.status
                LEFT JOIN ticket_gap_sync_checks sample_check
                  ON sample_check.ticket_id=t.id
                 AND sample_check.sync_type='status_sample_ticket_history'
                LEFT JOIN history_probe ON history_probe.ticket_id=t.id
                WHERE t.completed_at_autotask IS NULL
                  AND COALESCE(t.status, '') <> ALL(%s)
                  {company_scope_sql}
                GROUP BY COALESCE(ref.label, NULLIF(t.status, ''), '[Blank]'), NULLIF(t.status, '')
                ORDER BY count(sample_check.ticket_id) ASC, count(*) DESC, status_label
                """,
                (["5", "16", "20"], *company_scope_params),
            ).fetchall()
        )
        open_history_context = conn.execute(
            f"""
            WITH open_tickets AS (
                SELECT t.id
                FROM autotask_tickets t
                WHERE t.completed_at_autotask IS NULL
                  AND COALESCE(t.status, '') <> ALL(%s)
                  {company_scope_sql}
            ),
            history AS (
                SELECT ticket_id, count(*) AS history_count
                FROM autotask_ticket_history
                GROUP BY ticket_id
            )
            SELECT
                count(*) AS open_tickets,
                count(*) FILTER (WHERE COALESCE(history.history_count, 0) > 0) AS open_tickets_with_history,
                count(*) FILTER (WHERE COALESCE(history.history_count, 0) = 0) AS open_tickets_without_history,
                count(*) FILTER (WHERE gap_check.last_checked_at IS NOT NULL) AS open_tickets_checked_for_history,
                count(*) FILTER (
                    WHERE COALESCE(history.history_count, 0) = 0
                      AND gap_check.last_checked_at IS NOT NULL
                      AND COALESCE(gap_check.last_result_count, 0) = 0
                ) AS open_tickets_checked_empty_history,
                count(*) FILTER (
                    WHERE COALESCE(history.history_count, 0) = 0
                      AND gap_check.last_checked_at IS NULL
                ) AS open_tickets_unchecked_history,
                COALESCE(sum(history.history_count), 0) AS open_ticket_history_rows
            FROM open_tickets
            LEFT JOIN history ON history.ticket_id=open_tickets.id
            LEFT JOIN ticket_gap_sync_checks gap_check
              ON gap_check.ticket_id=open_tickets.id AND gap_check.sync_type='open_ticket_history_gaps'
            """,
            (list(CLOSED_STATUS_IDS), *company_scope_params),
        ).fetchone()

    status_fields = [dict(row) for row in status_field_rows]
    timestamp_fields = [dict(row) for row in timestamp_field_rows]
    status_keys = {str(row["key"]).strip() for row in status_fields}
    timestamp_keys = {str(row["key"]).strip() for row in timestamp_fields}
    exact_status_transition_fields = sorted(
        key
        for key in status_keys | timestamp_keys
        if "status" in key.lower()
        and any(token in key.lower() for token in ("date", "time", "changed", "modified", "activity"))
        and key not in {"status", "rmaStatus", "changeApprovalStatus"}
    )
    proxy_timestamp_candidates = [
        key
        for key in (
            "lastActivityDate",
            "lastTrackedModificationDateTime",
            "lastCustomerNotificationDateTime",
            "lastCustomerVisibleActivityDateTime",
            "firstResponseDateTime",
            "resolvedDateTime",
            "completedDate",
        )
        if key in timestamp_keys
    ]
    ticket_total = int(counts["tickets"] or 0)
    current_status_count = int(counts["tickets_with_current_status"] or 0)
    status_sample_coverage = [dict(row) for row in status_sample_rows]
    for row in status_sample_coverage:
        for key in (
            "open_tickets",
            "sampled_tickets",
            "sampled_empty_tickets",
            "sampled_history_rows",
            "sampled_status_candidate_rows",
            "sampled_waiting_keyword_rows",
            "sampled_tickets_without_status_candidates",
        ):
            row[key] = int(row.get(key) or 0)
    open_status_groups = len(status_sample_coverage)
    sampled_status_groups = sum(1 for row in status_sample_coverage if int(row.get("sampled_tickets") or 0) > 0)
    sampled_history_rows = sum(int(row.get("sampled_history_rows") or 0) for row in status_sample_coverage)
    sampled_status_candidate_rows = sum(
        int(row.get("sampled_status_candidate_rows") or 0) for row in status_sample_coverage
    )
    sampled_waiting_keyword_rows = sum(
        int(row.get("sampled_waiting_keyword_rows") or 0) for row in status_sample_coverage
    )
    sampled_status_groups_without_status_candidates = sum(
        1
        for row in status_sample_coverage
        if int(row.get("sampled_tickets") or 0) > 0 and int(row.get("sampled_status_candidate_rows") or 0) == 0
    )
    open_history_total = int(open_history_context["open_tickets"] or 0)
    open_history_with = int(open_history_context["open_tickets_with_history"] or 0)
    open_history_without = int(open_history_context["open_tickets_without_history"] or 0)
    open_history_unchecked = int(open_history_context["open_tickets_unchecked_history"] or 0)
    warnings = [
        "Local Tickets expose current status but no exact status-transition timestamp field.",
        "Proxy ticket timestamps can explain activity freshness, but they must not be treated as precise status-duration evidence.",
        f"{open_history_without} open local tickets still lack TicketHistory; continue bounded open-ticket history gap sync before treating status-duration coverage as complete."
        if open_history_without
        else "",
        "Status-sample TicketHistory probes have covered every open status group but found no status-change candidate rows; treat precise status-duration analytics as source-limited until another read-only source or new event shape appears."
        if open_status_groups > 0
        and sampled_status_groups == open_status_groups
        and sampled_status_candidate_rows == 0
        and not exact_status_transition_fields
        else "",
    ]
    return {
        "ok": True,
        "generated_at_ms": int((time.monotonic() - started) * 1000),
        "counts": {
            "tickets": ticket_total,
            "tickets_with_current_status": current_status_count,
            "tickets_with_autotask_updated_at": int(counts["tickets_with_autotask_updated_at"] or 0),
            "current_status_coverage_percent": _percent(current_status_count, ticket_total),
        },
        "source_capability": {
            "current_status_field_available": current_status_count > 0,
            "exact_status_transition_timestamp_fields": exact_status_transition_fields,
            "has_exact_status_transition_timestamp": bool(exact_status_transition_fields),
            "proxy_timestamp_fields": proxy_timestamp_candidates,
            "interpretation": (
                "Local ticket raw fields include exact status-transition timestamp candidates."
                if exact_status_transition_fields
                else "Local ticket raw fields provide current status and activity timestamps, but no exact status-transition timestamp."
            ),
        },
        "status_fields": status_fields,
        "timestamp_fields": timestamp_fields,
        "status_distribution": [dict(row) for row in distribution_rows],
        "status_sample_coverage": {
            "open_status_groups": open_status_groups,
            "sampled_status_groups": sampled_status_groups,
            "unsampled_status_groups": max(open_status_groups - sampled_status_groups, 0),
            "coverage_percent": _percent(sampled_status_groups, open_status_groups),
            "sampled_history_rows": sampled_history_rows,
            "sampled_status_candidate_rows": sampled_status_candidate_rows,
            "sampled_waiting_keyword_rows": sampled_waiting_keyword_rows,
            "sampled_status_groups_without_status_candidates": sampled_status_groups_without_status_candidates,
            "by_status": status_sample_coverage,
        },
        "open_ticket_history_context": {
            "open_tickets": open_history_total,
            "open_tickets_with_history": open_history_with,
            "open_tickets_without_history": open_history_without,
            "open_tickets_checked_for_history": int(open_history_context["open_tickets_checked_for_history"] or 0),
            "open_tickets_checked_empty_history": int(
                open_history_context["open_tickets_checked_empty_history"] or 0
            ),
            "open_tickets_unchecked_history": open_history_unchecked,
            "open_ticket_history_rows": int(open_history_context["open_ticket_history_rows"] or 0),
            "coverage_percent": _percent(open_history_with, open_history_total),
            "interpretation": (
                "Open-ticket TicketHistory coverage is complete; remaining status-duration limitations are source/parser related."
                if open_history_total and open_history_without == 0
                else "Open-ticket TicketHistory coverage is still incomplete; use bounded gap sync to reduce unchecked tickets before treating status-duration evidence as complete."
                if open_history_unchecked
                else "Open-ticket TicketHistory has been checked for current gaps; remaining status-duration limitations are likely source/parser related."
            ),
        },
        "warnings": [] if exact_status_transition_fields else [warning for warning in warnings if warning],
    }


def _field_row_status(coverage_report: dict[str, Any], key: str) -> dict[str, Any]:
    for row in coverage_report.get("fields") or []:
        if row.get("key") == key:
            return row
    return {"key": key, "status": "missing", "available_count": 0, "total_count": 0, "coverage_percent": 0.0}


def _certification_status(*statuses: str, source_limited: bool = False) -> str:
    if source_limited:
        return "source_limited"
    if not statuses or any(status == "missing" for status in statuses):
        return "missing"
    if all(status == "available" for status in statuses):
        return "certified"
    return "partial"


def field_certification_report(
    coverage_report: dict[str, Any] | None = None,
    status_diagnostics: dict[str, Any] | None = None,
    authorized_company_ids: list[int] | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    coverage = coverage_report or field_coverage_report(authorized_company_ids=authorized_company_ids)
    status_diag = status_diagnostics or ticket_status_source_diagnostics(authorized_company_ids=authorized_company_ids)
    source_capability = status_diag.get("source_capability") or {}
    open_history = status_diag.get("open_ticket_history_context") or {}
    status_sample = status_diag.get("status_sample_coverage") or {}
    exact_status_transition = bool(source_capability.get("has_exact_status_transition_timestamp"))
    open_history_complete = (
        int(open_history.get("open_tickets") or 0) > 0 and int(open_history.get("open_tickets_without_history") or 0) == 0
    )
    sampled_status_candidates = int(status_sample.get("sampled_status_candidate_rows") or 0)
    status_duration_source_limited = not exact_status_transition or not open_history_complete or sampled_status_candidates == 0

    ticket_history = _field_row_status(coverage, "ticket_status_history")
    time_entries = _field_row_status(coverage, "time_entries")
    labor_hours = _field_row_status(coverage, "labor_hours")
    sla_information = _field_row_status(coverage, "sla_information")
    waiting_states = _field_row_status(coverage, "waiting_states")
    ticket_status = _field_row_status(coverage, "ticket_status")

    targets = [
        {
            "key": "ticket_status_history",
            "label": "TicketHistory coverage",
            "certification_status": _certification_status(str(ticket_history.get("status") or "missing")),
            "source": ticket_history.get("source"),
            "coverage_percent": ticket_history.get("coverage_percent"),
            "available_count": ticket_history.get("available_count"),
            "total_count": ticket_history.get("total_count"),
            "prediction_use": "excluded_until_complete",
            "note": ticket_history.get("note") or "TicketHistory remains read-only local evidence.",
        },
        {
            "key": "status_duration",
            "label": "Status-duration and waiting-time lineage",
            "certification_status": _certification_status(
                str(ticket_status.get("status") or "missing"),
                str(ticket_history.get("status") or "missing"),
                str(waiting_states.get("status") or "missing"),
                source_limited=status_duration_source_limited,
            ),
            "source": "current ticket status plus TicketHistory transition candidates",
            "coverage_percent": open_history.get("coverage_percent"),
            "available_count": open_history.get("open_tickets_with_history"),
            "total_count": open_history.get("open_tickets"),
            "prediction_use": "excluded_until_certified",
            "note": (
                "Status-duration analytics remain source-limited until exact transition timestamps, open-ticket history coverage, and parsed status candidates are certified."
                if status_duration_source_limited
                else "Status-duration local evidence is structurally available for deterministic review."
            ),
        },
        {
            "key": "time_entries",
            "label": "TimeEntries and labor-hour lineage",
            "certification_status": _certification_status(
                str(time_entries.get("status") or "missing"), str(labor_hours.get("status") or "missing")
            ),
            "source": "autotask_time_entries and normalized labor hours",
            "coverage_percent": labor_hours.get("coverage_percent"),
            "available_count": labor_hours.get("available_count"),
            "total_count": labor_hours.get("total_count"),
            "prediction_use": "excluded_until_certified_for_model_training",
            "note": labor_hours.get("note") or "Labor evidence is local and read-only; model use still requires outcome/leakage review.",
        },
        {
            "key": "sla_information",
            "label": "SLA target/due/response/resolution lineage",
            "certification_status": _certification_status(str(sla_information.get("status") or "missing")),
            "source": sla_information.get("source"),
            "coverage_percent": sla_information.get("coverage_percent"),
            "available_count": sla_information.get("available_count"),
            "total_count": sla_information.get("total_count"),
            "prediction_use": "excluded_until_certified_for_model_training",
            "note": sla_information.get("note") or "SLA fields are read-only local evidence; unmapped/blank records keep certification partial.",
        },
        {
            "key": "waiting_states",
            "label": "Waiting state/reason lineage",
            "certification_status": _certification_status(
                str(waiting_states.get("status") or "missing"), source_limited=status_duration_source_limited
            ),
            "source": waiting_states.get("source"),
            "coverage_percent": waiting_states.get("coverage_percent"),
            "available_count": waiting_states.get("available_count"),
            "total_count": waiting_states.get("total_count"),
            "prediction_use": "excluded_until_status_duration_certified",
            "note": waiting_states.get("note")
            or "Waiting-state precision depends on current status labels and parsed TicketHistory transitions.",
        },
    ]
    summary = Counter(target["certification_status"] for target in targets)
    certification_state = (
        "certified"
        if targets and all(target["certification_status"] == "certified" for target in targets)
        else "partial_field_certification"
    )
    blockers = [
        target["key"]
        for target in targets
        if target["certification_status"] in {"missing", "partial", "source_limited"}
    ]
    return {
        "ok": True,
        "generated_at_ms": int((time.monotonic() - started) * 1000),
        "certification_state": certification_state,
        "summary": dict(summary),
        "targets": targets,
        "blockers": blockers,
        "source_reports": {
            "field_coverage": {
                "ready_for_ticket_health": coverage.get("ready_for_ticket_health"),
                "counts": coverage.get("counts"),
                "blockers": coverage.get("blockers") or [],
            },
            "status_source": {
                "source_capability": source_capability,
                "open_ticket_history_context": open_history,
                "status_sample_coverage": {
                    key: value for key, value in status_sample.items() if key != "by_status"
                },
            },
        },
        "predictive_policy": {
            "review_only": True,
            "authorized_company_scope_applied": authorized_company_ids is not None,
            "certified_inputs_allowed": ["created_at_autotask", "completed_at_autotask", "authorized_company_scope"],
            "excluded_until_certified": blockers,
            "automatic_model_or_workflow_changes_allowed": False,
        },
        "warnings": [
            "Field certification is local read-only evidence and does not trigger Autotask writes or synchronization.",
            "Predictive models must not consume source-limited or partial operational fields until Milestone 2 certification advances.",
        ],
    }


def ticket_health_summary(
    limit: int = 50,
    queue: str | None = None,
    assigned_resource_id: int | None = None,
    cache_context: dict[str, Any] | None = None,
    authorized_company_ids: list[int] | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    row_limit = min(max(limit, 1), 200)
    summary_cache_key = ticket_health_summary_cache_key(
        {
            "limit": row_limit,
            "queue": queue,
            "assigned_resource_id": assigned_resource_id,
            "authorized_company_ids": sorted(authorized_company_ids) if authorized_company_ids is not None else None,
            "closed_status_ids": sorted(CLOSED_STATUS_IDS),
        },
        **(cache_context or {}),
    )
    cached = cache_get_json(summary_cache_key)
    if cached is not None:
        cached["cache"] = {"hit": True, "ttl_seconds": settings.ticket_health_summary_cache_ttl_seconds, "scoped": True}
        return cached

    now = datetime.now(UTC)
    where_sql, filter_params = _summary_where(queue, assigned_resource_id)
    company_scope_sql, company_scope_params = _company_scope_clause(authorized_company_ids)
    where_sql += company_scope_sql
    filter_params.extend(company_scope_params)
    with db_connection() as conn:
        rows = list(
            conn.execute(
                f"""
                WITH labor AS (
                    SELECT ticket_id, sum(COALESCE(hours, 0)) AS labor_hours
                    FROM autotask_time_entries
                    GROUP BY ticket_id
                ),
                history AS (
                    SELECT ticket_id, count(*) AS history_events, max(happened_at) AS last_history_at
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
                    t.queue,
                    COALESCE(queue_ref.label, t.queue) AS queue_label,
                    t.company_id,
                    t.assigned_resource_id,
                    COALESCE(NULLIF(t.assigned_resource_name, ''), resource_ref.label) AS assigned_resource_name,
                    t.created_at_autotask,
                    t.updated_at_autotask,
                    t.due_at_autotask,
                    t.first_response_due_at_autotask,
                    t.resolved_due_at_autotask,
                    t.sla_met,
                    EXTRACT(EPOCH FROM (%s::timestamptz - COALESCE(t.created_at_autotask, t.updated_at_autotask, %s::timestamptz))) / 3600 AS age_hours,
                    COALESCE(labor.labor_hours, 0) AS labor_hours,
                    COALESCE(history.history_events, 0) AS history_events,
                    history.last_history_at,
                    t.due_at_autotask IS NOT NULL AND t.due_at_autotask < %s::timestamptz AS due_overdue,
                    t.first_response_due_at_autotask IS NOT NULL
                        AND t.first_response_at_autotask IS NULL
                        AND t.first_response_due_at_autotask < %s::timestamptz AS first_response_overdue,
                    t.resolved_due_at_autotask IS NOT NULL
                        AND t.completed_at_autotask IS NULL
                        AND t.resolved_due_at_autotask < %s::timestamptz AS resolved_overdue
                FROM autotask_tickets t
                LEFT JOIN labor ON labor.ticket_id = t.id
                LEFT JOIN history ON history.ticket_id = t.id
                LEFT JOIN autotask_reference_values status_ref
                    ON status_ref.field_name='status' AND status_ref.value=t.status
                LEFT JOIN autotask_reference_values priority_ref
                    ON priority_ref.field_name='priority' AND priority_ref.value=t.priority
                LEFT JOIN autotask_reference_values queue_ref
                    ON queue_ref.field_name='queue' AND queue_ref.value=t.queue
                LEFT JOIN autotask_reference_values resource_ref
                    ON resource_ref.field_name='resource' AND resource_ref.value=t.assigned_resource_id::text
                WHERE {where_sql}
                ORDER BY
                    t.resolved_due_at_autotask NULLS LAST,
                    t.due_at_autotask NULLS LAST,
                    t.created_at_autotask NULLS LAST,
                    t.id DESC
                LIMIT %s
                """,
                (now, now, now, now, now, *filter_params, row_limit),
            ).fetchall()
        )
        queue_options = list(
            conn.execute(
                f"""
                SELECT t.queue AS value, COALESCE(queue_ref.label, t.queue) AS label, count(*) AS count
                FROM autotask_tickets t
                LEFT JOIN autotask_reference_values queue_ref
                    ON queue_ref.field_name='queue' AND queue_ref.value=t.queue
                WHERE t.completed_at_autotask IS NULL
                  AND NOT t.analytics_exclude
                  AND COALESCE(t.status, '') <> ALL(%s)
                  {company_scope_sql}
                  AND NULLIF(t.queue, '') IS NOT NULL
                GROUP BY t.queue, COALESCE(queue_ref.label, t.queue)
                ORDER BY count(*) DESC, label
                LIMIT 50
                """,
                (list(CLOSED_STATUS_IDS), *company_scope_params),
            ).fetchall()
        )
        technician_options = list(
            conn.execute(
                f"""
                SELECT t.assigned_resource_id AS value,
                       COALESCE(NULLIF(t.assigned_resource_name, ''), resource_ref.label, t.assigned_resource_id::text) AS label,
                       count(*) AS count
                FROM autotask_tickets t
                LEFT JOIN autotask_reference_values resource_ref
                    ON resource_ref.field_name='resource' AND resource_ref.value=t.assigned_resource_id::text
                WHERE t.completed_at_autotask IS NULL
                  AND NOT t.analytics_exclude
                  AND COALESCE(t.status, '') <> ALL(%s)
                  {company_scope_sql}
                  AND t.assigned_resource_id IS NOT NULL
                GROUP BY t.assigned_resource_id, COALESCE(NULLIF(t.assigned_resource_name, ''), resource_ref.label, t.assigned_resource_id::text)
                ORDER BY count(*) DESC, label
                LIMIT 50
                """,
                (list(CLOSED_STATUS_IDS), *company_scope_params),
            ).fetchall()
        )

    tickets, buckets = _score_rows([dict(row) for row in rows])
    partial_history_count = buckets["partial_history_tickets"]
    result = {
        "ok": True,
        "generated_at_ms": int((time.monotonic() - started) * 1000),
        "cache": {"hit": False, "ttl_seconds": settings.ticket_health_summary_cache_ttl_seconds, "scoped": True},
        "limit": row_limit,
        "filters": {"queue": queue, "assigned_resource_id": assigned_resource_id},
        "filter_options": {
            "queues": [dict(row) for row in queue_options],
            "technicians": [dict(row) for row in technician_options],
        },
        "summary": {
            "open_tickets_sampled": len(tickets),
            "critical": buckets["critical"],
            "high": buckets["high"],
            "watch": buckets["watch"],
            "normal": buckets["normal"],
            "partial_history_tickets": partial_history_count,
        },
        "warnings": [
            warning
            for warning in (
                "Some tickets lack local TicketHistory; waiting-duration scoring falls back to current status."
                if partial_history_count
                else "",
            )
            if warning
        ],
        "tickets": tickets,
    }
    encoded_result = jsonable_encoder(result)
    cache_set_json(summary_cache_key, encoded_result, settings.ticket_health_summary_cache_ttl_seconds)
    return encoded_result


def store_ticket_health_risk_feedback(
    ticket_id: int,
    health_score: int | None,
    risk_bucket: str | None,
    outcome: str,
    notes: str | None = None,
    authorized_company_ids: list[int] | None = None,
) -> dict[str, Any]:
    if outcome not in TICKET_HEALTH_FEEDBACK_OUTCOMES:
        return {"ok": False, "reason": "invalid_outcome"}

    with db_connection() as conn:
        company_scope_sql, company_scope_params = _company_scope_clause(authorized_company_ids)
        ticket = conn.execute(
            f"SELECT id, autotask_id, ticket_number FROM autotask_tickets WHERE id=%s{company_scope_sql}",
            (ticket_id, *company_scope_params),
        ).fetchone()
        if not ticket:
            return {"ok": False, "reason": "ticket_not_found"}
        row = conn.execute(
            """
            INSERT INTO ticket_health_risk_feedback(
                ticket_id, ticket_autotask_id, ticket_number, health_score, risk_bucket, outcome, notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, created_at
            """,
            (
                ticket["id"],
                ticket["autotask_id"],
                ticket["ticket_number"],
                health_score,
                risk_bucket,
                outcome,
                notes,
            ),
        ).fetchone()

    invalidate_ticket_health_summary_cache()
    return {
        "ok": True,
        "feedback_id": row["id"],
        "created_at": row["created_at"],
        "message": "Ticket Health risk feedback stored locally. No Autotask ticket was changed.",
    }


def ticket_health_calibration_report(limit: int = 25) -> dict[str, Any]:
    row_limit = min(max(limit, 1), 100)
    with db_connection() as conn:
        summary = conn.execute(
            """
            SELECT
                count(*) AS total_feedback,
                count(*) FILTER (WHERE outcome = 'accurate') AS accurate,
                count(*) FILTER (WHERE outcome = 'too_high') AS too_high,
                count(*) FILTER (WHERE outcome = 'too_low') AS too_low,
                count(*) FILTER (WHERE outcome = 'needs_review') AS needs_review,
                count(DISTINCT ticket_id) AS reviewed_tickets,
                max(created_at) AS latest_feedback_at
            FROM ticket_health_risk_feedback
            """
        ).fetchone()
        recent = list(
            conn.execute(
                """
                SELECT id, ticket_id, ticket_autotask_id, ticket_number, health_score, risk_bucket, outcome, notes, created_at
                FROM ticket_health_risk_feedback
                ORDER BY created_at DESC, id DESC
                LIMIT %s
                """,
                (row_limit,),
            ).fetchall()
        )
    summary_row = dict(summary or {})
    total_feedback = int(summary_row.get("total_feedback") or 0)
    accurate = int(summary_row.get("accurate") or 0)
    too_high = int(summary_row.get("too_high") or 0)
    too_low = int(summary_row.get("too_low") or 0)
    needs_review = int(summary_row.get("needs_review") or 0)
    reviewed_tickets = int(summary_row.get("reviewed_tickets") or 0)
    readiness = _calibration_readiness(
        total_feedback,
        reviewed_tickets,
        {"accurate": accurate, "too_high": too_high, "too_low": too_low},
        "tickets",
    )
    return {
        "ok": True,
        "summary": {
            "total_feedback": total_feedback,
            "accurate": accurate,
            "too_high": too_high,
            "too_low": too_low,
            "needs_review": needs_review,
            "reviewed_tickets": reviewed_tickets,
            "latest_feedback_at": summary_row.get("latest_feedback_at"),
        },
        "recent_feedback": [dict(row) for row in recent],
        "calibration_readiness": readiness,
        "warnings": [
            "Ticket Health calibration is review-only local evidence and does not automatically change score weights.",
            "No Autotask ticket is updated by this report or feedback capture.",
            *readiness["blockers"],
        ],
    }


def _ticket_health_feedback_counts(ticket_ids: list[int]) -> dict[int, dict[str, int]]:
    if not ticket_ids:
        return {}
    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                ticket_id,
                count(*) AS total_feedback,
                count(*) FILTER (WHERE outcome = 'accurate') AS accurate,
                count(*) FILTER (WHERE outcome = 'too_high') AS too_high,
                count(*) FILTER (WHERE outcome = 'too_low') AS too_low,
                count(*) FILTER (WHERE outcome = 'needs_review') AS needs_review
            FROM ticket_health_risk_feedback
            WHERE ticket_id = ANY(%s)
            GROUP BY ticket_id
            """,
            (ticket_ids,),
        ).fetchall()
    return {
        int(row["ticket_id"]): {
            "total_feedback": int(row.get("total_feedback") or 0),
            "accurate": int(row.get("accurate") or 0),
            "too_high": int(row.get("too_high") or 0),
            "too_low": int(row.get("too_low") or 0),
            "needs_review": int(row.get("needs_review") or 0),
        }
        for row in rows
    }


def _historical_completion_stats(
    tickets: list[dict[str, Any]],
    authorized_company_ids: list[int] | None = None,
) -> dict[tuple[str, str], dict[str, Any]]:
    queues = sorted({str(ticket.get("queue") or "") for ticket in tickets})
    priorities = sorted({str(ticket.get("priority") or "") for ticket in tickets})
    if not queues or not priorities:
        return {}
    company_scope_sql, company_scope_params = _company_scope_clause(authorized_company_ids)
    with db_connection() as conn:
        rows = conn.execute(
            f"""
            WITH completed AS (
                SELECT
                    COALESCE(t.queue, '') AS queue_key,
                    COALESCE(t.priority, '') AS priority_key,
                    COALESCE(labor.labor_hours, 0) AS labor_hours,
                    EXTRACT(EPOCH FROM (t.completed_at_autotask - t.created_at_autotask)) / 86400 AS resolution_days
                FROM autotask_tickets t
                LEFT JOIN (
                    SELECT ticket_id, sum(COALESCE(hours, 0)) AS labor_hours
                    FROM autotask_time_entries
                    GROUP BY ticket_id
                ) labor ON labor.ticket_id = t.id
                WHERE t.completed_at_autotask IS NOT NULL
                  AND t.created_at_autotask IS NOT NULL
                  AND COALESCE(t.queue, '') = ANY(%s)
                  AND COALESCE(t.priority, '') = ANY(%s)
                  AND NOT t.analytics_exclude
                  {company_scope_sql}
            )
            SELECT
                queue_key,
                priority_key,
                count(*) AS sample_size,
                avg(resolution_days) AS avg_resolution_days,
                avg(labor_hours) AS avg_labor_hours,
                count(*) FILTER (WHERE resolution_days > 7) AS delayed_count
            FROM completed
            GROUP BY queue_key, priority_key
            """,
            (queues, priorities, *company_scope_params),
        ).fetchall()
    return {
        (str(row["queue_key"] or ""), str(row["priority_key"] or "")): {
            "sample_size": int(row.get("sample_size") or 0),
            "avg_resolution_days": _round_optional(row.get("avg_resolution_days")),
            "avg_labor_hours": _round_optional(row.get("avg_labor_hours")),
            "delayed_count": int(row.get("delayed_count") or 0),
        }
        for row in rows
    }


def _ticket_predictive_review_signal(
    ticket: dict[str, Any],
    feedback: dict[str, int],
    historical_stats: dict[str, Any] | None,
) -> dict[str, Any]:
    stats = historical_stats or {}
    sample_size = int(stats.get("sample_size") or 0)
    delayed_count = int(stats.get("delayed_count") or 0)
    smoothed_delay_rate = round(
        (delayed_count + (0.5 * PREDICTION_PRIOR_SAMPLE_SIZE)) / (sample_size + PREDICTION_PRIOR_SAMPLE_SIZE),
        3,
    )
    if sample_size < PREDICTION_MIN_SAMPLE_SIZE:
        return {
            "review_only": True,
            "abstained": True,
            "confidence": "low",
            "sample_size": sample_size,
            "minimum_sample_size": PREDICTION_MIN_SAMPLE_SIZE,
            "bayesian_delay_rate": smoothed_delay_rate,
            "statistical_review_score": None,
            "reason_codes": ["insufficient_local_history"],
            "limitations": [
                "Low-confidence predictions abstain until enough scoped completed-ticket examples exist.",
                "This signal is local review guidance only and never writes to Autotask.",
            ],
        }

    score = int(ticket.get("health_score") or 0)
    reason_codes = [f"bayesian_delay_rate={smoothed_delay_rate}"]
    avg_resolution_days = _num(stats.get("avg_resolution_days"), 0.0)
    avg_labor_hours = _num(stats.get("avg_labor_hours"), 0.0)
    if avg_resolution_days > 0 and _num(ticket.get("age_days")) > avg_resolution_days * 1.25:
        score += 12
        reason_codes.append("open_age_exceeds_similar_resolution_average")
    if avg_labor_hours > 0 and _num(ticket.get("labor_hours")) > avg_labor_hours * 1.5:
        score += 10
        reason_codes.append("labor_exceeds_similar_average")
    if feedback.get("needs_review"):
        score += 8
        reason_codes.append("local_needs_review_feedback")
    if feedback.get("too_low"):
        score += 6
        reason_codes.append("local_feedback_score_too_low")
    if feedback.get("too_high"):
        score -= 6
        reason_codes.append("local_feedback_score_too_high")
    score += round(smoothed_delay_rate * 12)
    confidence = "strong" if sample_size >= 25 else "moderate"
    return {
        "review_only": True,
        "abstained": False,
        "confidence": confidence,
        "sample_size": sample_size,
        "minimum_sample_size": PREDICTION_MIN_SAMPLE_SIZE,
        "bayesian_delay_rate": smoothed_delay_rate,
        "average_resolution_days": stats.get("avg_resolution_days"),
        "average_labor_hours": stats.get("avg_labor_hours"),
        "statistical_review_score": max(0, min(score, 100)),
        "reason_codes": reason_codes,
        "limitations": [
            "Calibrated with scoped local completed-ticket history and local feedback only.",
            "No Autotask ticket, assignment, status, or priority is changed.",
        ],
    }


def _binary_classification_metrics(rows: list[dict[str, Any]], prediction_key: str) -> dict[str, Any]:
    total = len(rows)
    true_positive = sum(1 for row in rows if row.get("actual_delayed") and row.get(prediction_key))
    true_negative = sum(1 for row in rows if not row.get("actual_delayed") and not row.get(prediction_key))
    false_positive = sum(1 for row in rows if not row.get("actual_delayed") and row.get(prediction_key))
    false_negative = sum(1 for row in rows if row.get("actual_delayed") and not row.get(prediction_key))
    predicted_positive = true_positive + false_positive
    actual_positive = true_positive + false_negative
    return {
        "total": total,
        "true_positive": true_positive,
        "true_negative": true_negative,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "accuracy": round((true_positive + true_negative) / total, 3) if total else None,
        "precision": round(true_positive / predicted_positive, 3) if predicted_positive else None,
        "recall": round(true_positive / actual_positive, 3) if actual_positive else None,
        "f1": (
            round((2 * true_positive) / ((2 * true_positive) + false_positive + false_negative), 3)
            if true_positive or false_positive or false_negative
            else None
        ),
    }


def _threshold_sweep(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sweep: list[dict[str, Any]] = []
    for threshold in (0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5):
        threshold_rows = [
            {
                **row,
                "threshold_predicted_delayed": _num(row.get("bayesian_delay_rate")) >= threshold,
            }
            for row in rows
        ]
        metrics = _binary_classification_metrics(threshold_rows, "threshold_predicted_delayed")
        sweep.append({"threshold": threshold, **metrics})
    sweep.sort(key=lambda item: (-(item["f1"] or 0), -(item["recall"] or 0), item["threshold"]))
    return sweep


def _brier_score(rows: list[dict[str, Any]], probability_key: str = "bayesian_delay_rate") -> float | None:
    scored = [row for row in rows if row.get(probability_key) is not None]
    if not scored:
        return None
    total = 0.0
    for row in scored:
        actual = 1.0 if row.get("actual_delayed") else 0.0
        probability = min(max(_num(row.get(probability_key)), 0.0), 1.0)
        total += (probability - actual) ** 2
    return round(total / len(scored), 3)


def _calibration_bands(rows: list[dict[str, Any]], probability_key: str = "bayesian_delay_rate") -> list[dict[str, Any]]:
    bands: list[dict[str, Any]] = []
    for index in range(10):
        lower = index / 10
        upper = (index + 1) / 10
        band_rows = [
            row
            for row in rows
            if row.get(probability_key) is not None
            and lower <= min(max(_num(row.get(probability_key)), 0.0), 1.0) < upper
        ]
        if index == 9:
            band_rows = [
                row
                for row in rows
                if row.get(probability_key) is not None
                and lower <= min(max(_num(row.get(probability_key)), 0.0), 1.0) <= upper
            ]
        if not band_rows:
            continue
        predicted_average = sum(min(max(_num(row.get(probability_key)), 0.0), 1.0) for row in band_rows) / len(band_rows)
        observed_rate = sum(1 for row in band_rows if row.get("actual_delayed")) / len(band_rows)
        bands.append(
            {
                "range": f"{lower:.1f}-{upper:.1f}",
                "count": len(band_rows),
                "average_prediction": round(predicted_average, 3),
                "observed_delay_rate": round(observed_rate, 3),
                "absolute_error": round(abs(predicted_average - observed_rate), 3),
            }
        )
    return bands


def _probability_auc(rows: list[dict[str, Any]], probability_key: str = "bayesian_delay_rate") -> dict[str, Any]:
    scored = [
        {
            "score": min(max(_num(row.get(probability_key)), 0.0), 1.0),
            "actual": bool(row.get("actual_delayed")),
        }
        for row in rows
        if row.get(probability_key) is not None
    ]
    positives = [row for row in scored if row["actual"]]
    negatives = [row for row in scored if not row["actual"]]
    roc_auc = None
    if positives and negatives:
        wins = 0.0
        for positive in positives:
            for negative in negatives:
                if positive["score"] > negative["score"]:
                    wins += 1.0
                elif positive["score"] == negative["score"]:
                    wins += 0.5
        roc_auc = round(wins / (len(positives) * len(negatives)), 3)

    sorted_rows = sorted(scored, key=lambda row: row["score"], reverse=True)
    precision_recall_points: list[dict[str, Any]] = []
    true_positive = 0
    false_positive = 0
    for row in sorted_rows:
        if row["actual"]:
            true_positive += 1
        else:
            false_positive += 1
        if positives:
            precision_recall_points.append(
                {
                    "recall": round(true_positive / len(positives), 3),
                    "precision": round(true_positive / (true_positive + false_positive), 3),
                }
            )
    pr_auc = None
    if precision_recall_points:
        previous_recall = 0.0
        area = 0.0
        for point in precision_recall_points:
            recall = _num(point["recall"])
            area += (recall - previous_recall) * _num(point["precision"])
            previous_recall = recall
        pr_auc = round(area, 3)
    return {
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "positive_count": len(positives),
        "negative_count": len(negatives),
    }


def _sanitized_concentration(rows: list[dict[str, Any]], key: str, label_prefix: str) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    delayed_counts: Counter[str] = Counter()
    for row in rows:
        value = row.get(key)
        bucket_key = "unknown" if value in (None, "") else str(value)
        counts[bucket_key] += 1
        if row.get("actual_delayed"):
            delayed_counts[bucket_key] += 1
    total = sum(counts.values())
    top_buckets: list[dict[str, Any]] = []
    for index, (bucket_key, count) in enumerate(counts.most_common(5), start=1):
        delayed_count = delayed_counts[bucket_key]
        top_buckets.append(
            {
                "bucket": f"{label_prefix}_{index}",
                "count": count,
                "share": round(count / total, 3) if total else None,
                "delayed_count": delayed_count,
                "delayed_rate": round(delayed_count / count, 3) if count else None,
            }
        )
    return {
        "dimension": label_prefix,
        "distinct_buckets": len(counts),
        "largest_bucket_share": top_buckets[0]["share"] if top_buckets else None,
        "top_buckets": top_buckets,
        "sanitized": True,
    }


def _sanitized_stratified_metrics(rows: list[dict[str, Any]], key: str, label_prefix: str) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        value = row.get(key)
        bucket_key = "unknown" if value in (None, "") else str(value)
        grouped.setdefault(bucket_key, []).append(row)
    total = len(rows)
    buckets: list[dict[str, Any]] = []
    for index, (_bucket_key, bucket_rows) in enumerate(
        sorted(grouped.items(), key=lambda item: len(item[1]), reverse=True)[:5],
        start=1,
    ):
        statistical_rows = [row for row in bucket_rows if not row.get("statistical_abstained")]
        buckets.append(
            {
                "bucket": f"{label_prefix}_{index}",
                "count": len(bucket_rows),
                "share": round(len(bucket_rows) / total, 3) if total else None,
                "actual_delayed_rate": (
                    round(sum(1 for row in bucket_rows if row.get("actual_delayed")) / len(bucket_rows), 3)
                    if bucket_rows
                    else None
                ),
                "baseline": _binary_classification_metrics(bucket_rows, "baseline_predicted_delayed"),
                "statistical": _binary_classification_metrics(statistical_rows, "statistical_predicted_delayed"),
                "statistical_brier_score": _brier_score(statistical_rows),
            }
        )
    return {
        "dimension": label_prefix,
        "sanitized": True,
        "top_buckets": buckets,
        "note": "Bucket labels are ordinal within this response and do not expose customer names or raw category labels.",
    }


def _model_comparison(
    baseline_metrics: dict[str, Any],
    statistical_metrics: dict[str, Any],
    calibration: dict[str, Any],
) -> dict[str, Any]:
    baseline_f1 = baseline_metrics.get("f1") or 0
    statistical_f1 = statistical_metrics.get("f1") or 0
    baseline_recall = baseline_metrics.get("recall") or 0
    statistical_recall = statistical_metrics.get("recall") or 0
    return {
        "models": [
            {
                "name": "simple_priority_baseline",
                "type": "deterministic_rule",
                "metrics": baseline_metrics,
            },
            {
                "name": "bayesian_queue_priority_delay_signal",
                "type": "lightweight_statistical",
                "metrics": statistical_metrics,
                "brier_score": calibration.get("brier_score"),
                "roc_auc": (calibration.get("secondary_metrics") or {}).get("roc_auc"),
                "pr_auc": (calibration.get("secondary_metrics") or {}).get("pr_auc"),
            },
        ],
        "statistical_f1_delta": round(statistical_f1 - baseline_f1, 3),
        "statistical_recall_delta": round(statistical_recall - baseline_recall, 3),
        "current_finding": (
            "statistical_signal_not_better_on_f1_or_recall"
            if statistical_f1 <= baseline_f1 and statistical_recall <= baseline_recall
            else "statistical_signal_has_some_metric_lift"
        ),
        "selection_policy": "Do not select or deploy a model from this comparison without human review and bias/leakage certification.",
    }


def _leakage_review(holdout_start: Any, row_limit: int, training_group_count: int) -> dict[str, Any]:
    return {
        "temporal_split": "training_completed_before_holdout_start",
        "holdout_started_at": holdout_start,
        "training_groups": training_group_count,
        "holdout_limit": row_limit,
        "training_rows_after_or_during_holdout_included": 0,
        "label_available_only_after_completion": True,
        "known_limitations": [
            "The label uses completed-ticket duration, so open-ticket predictions remain shadow evidence until outcomes complete.",
            "Queue and priority are current local ticket fields; historical queue/priority-at-creation lineage is not yet certified.",
            "Broader leakage review must continue as more source-lineage fields are certified.",
        ],
    }


def _predictive_source_lineage(field_certification: dict[str, Any] | None = None) -> dict[str, Any]:
    field_policy = (field_certification or {}).get("predictive_policy") or {}
    return {
        "certification_state": "partial_source_lineage",
        "milestone_2_field_certification_state": (field_certification or {}).get("certification_state"),
        "fields": [
            {
                "field": "created_at_autotask",
                "source": "autotask_tickets.created_at_autotask",
                "used_for": "resolution_days label and temporal split",
                "lineage_status": "available_locally",
                "certified_for_prediction": True,
            },
            {
                "field": "completed_at_autotask",
                "source": "autotask_tickets.completed_at_autotask",
                "used_for": "completed-ticket holdout, label construction, and training cutoff",
                "lineage_status": "available_locally",
                "certified_for_prediction": True,
            },
            {
                "field": "queue",
                "source": "autotask_tickets.queue",
                "used_for": "Bayesian queue/priority historical grouping",
                "lineage_status": "current_local_field; queue-at-creation history is not certified",
                "certified_for_prediction": False,
            },
            {
                "field": "priority",
                "source": "autotask_tickets.priority",
                "used_for": "simple priority baseline and Bayesian queue/priority historical grouping",
                "lineage_status": "current_local_field; priority-at-creation history is not certified",
                "certified_for_prediction": False,
            },
            {
                "field": "company_id",
                "source": "autotask_tickets.company_id",
                "used_for": "authorized scope filtering and sanitized concentration review",
                "lineage_status": "available_locally; output is bucketed/sanitized",
                "certified_for_prediction": True,
            },
            {
                "field": "category / issue_type / subissue_type",
                "source": "autotask_tickets category fields",
                "used_for": "sanitized concentration and stratified review only",
                "lineage_status": "available_locally; label/reference completeness remains under Milestone 2 certification",
                "certified_for_prediction": False,
            },
        ],
        "not_used_for_current_model": [
            "ticket_status_history",
            "time_entries",
            "SLA fields",
            "technician workload",
            "routing outcomes",
        ],
        "milestone_2_excluded_until_certified": field_policy.get("excluded_until_certified") or [
            "ticket_status_history",
            "status_duration",
            "time_entries",
            "sla_information",
            "waiting_states",
        ],
        "limitations": [
            "Current predictive grouping uses current local queue/priority values, not certified queue/priority-at-ticket-creation history.",
            "Status-duration, SLA, and labor signals remain outside this model until Milestone 2 source-lineage certification is complete.",
            "This lineage record is evidence only and does not authorize prediction-driven workflow changes.",
        ],
    }


def _prediction_target_policy(threshold_days: int, row_limit: int) -> dict[str, Any]:
    return {
        "target": "completed_ticket_resolution_duration",
        "positive_label": f"resolution_days_greater_than_{threshold_days}",
        "negative_label": f"resolution_days_less_than_or_equal_{threshold_days}",
        "label_source": "local completed Autotask ticket created/completed timestamps",
        "training_window": "tickets completed before the current holdout window",
        "holdout_window": "most recent locally completed tickets within the requested limit",
        "holdout_limit": row_limit,
        "review_authority": "advisory_human_review_only",
        "prohibited_actions": [
            "no automatic threshold changes",
            "no model weight changes",
            "no Autotask writes",
            "no routing, escalation, notification, assignment, status, or priority changes",
        ],
    }


def ticket_health_predictive_evaluation(
    limit: int = 500,
    delayed_days_threshold: int = 7,
    authorized_company_ids: list[int] | None = None,
) -> dict[str, Any]:
    row_limit = min(max(limit, 50), 1000)
    threshold_days = min(max(int(delayed_days_threshold or 7), 1), 90)
    company_scope_sql, company_scope_params = _company_scope_clause(authorized_company_ids)
    with db_connection() as conn:
        holdout_rows = [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT
                    t.id,
                    t.ticket_number,
                    t.company_id,
                    COALESCE(NULLIF(t.category, ''), NULLIF(t.issue_type, ''), NULLIF(t.subissue_type, ''), 'uncategorized') AS category_key,
                    COALESCE(t.queue, '') AS queue_key,
                    COALESCE(t.priority, '') AS priority_key,
                    t.created_at_autotask,
                    t.completed_at_autotask,
                    EXTRACT(EPOCH FROM (t.completed_at_autotask - t.created_at_autotask)) / 86400 AS resolution_days
                FROM autotask_tickets t
                WHERE t.completed_at_autotask IS NOT NULL
                  AND t.created_at_autotask IS NOT NULL
                  AND NOT t.analytics_exclude
                  {company_scope_sql}
                ORDER BY t.completed_at_autotask DESC, t.id DESC
                LIMIT %s
                """,
                (*company_scope_params, row_limit),
            ).fetchall()
        ]
        if not holdout_rows:
            field_certification = field_certification_report(authorized_company_ids=authorized_company_ids)
            return {
                "ok": True,
                "review_only": True,
                "target": _prediction_target_policy(threshold_days, row_limit),
                "summary": {"holdout_size": 0, "training_groups": 0},
                "baseline": _binary_classification_metrics([], "baseline_predicted_delayed"),
                "statistical": _binary_classification_metrics([], "statistical_predicted_delayed"),
                "calibration": {"brier_score": None, "bands": [], "secondary_metrics": _probability_auc([])},
                "concentration": {
                    "company": _sanitized_concentration([], "company_id", "company_bucket"),
                    "category": _sanitized_concentration([], "category_key", "category_bucket"),
                },
                "stratified_metrics": {
                    "company": _sanitized_stratified_metrics([], "company_id", "company_bucket"),
                    "category": _sanitized_stratified_metrics([], "category_key", "category_bucket"),
                },
                "model_comparison": _model_comparison(
                    _binary_classification_metrics([], "baseline_predicted_delayed"),
                    _binary_classification_metrics([], "statistical_predicted_delayed"),
                    {"brier_score": None, "secondary_metrics": _probability_auc([])},
                ),
                "leakage_review": _leakage_review(None, row_limit, 0),
                "field_certification": field_certification,
                "source_lineage": _predictive_source_lineage(field_certification),
                "human_review_threshold_policy": {
                    "selection_mode": "human_review_required",
                    "automatic_changes_allowed": False,
                },
                "warnings": ["No completed local tickets are available for predictive holdout evaluation."],
            }
        holdout_start = min(row["created_at_autotask"] for row in holdout_rows if row.get("created_at_autotask"))
        training_rows = conn.execute(
            f"""
            SELECT
                COALESCE(t.queue, '') AS queue_key,
                COALESCE(t.priority, '') AS priority_key,
                count(*) AS sample_size,
                count(*) FILTER (
                    WHERE EXTRACT(EPOCH FROM (t.completed_at_autotask - t.created_at_autotask)) / 86400 > %s
                ) AS delayed_count
            FROM autotask_tickets t
            WHERE t.completed_at_autotask IS NOT NULL
              AND t.created_at_autotask IS NOT NULL
              AND t.completed_at_autotask < %s
              AND NOT t.analytics_exclude
              {company_scope_sql}
            GROUP BY COALESCE(t.queue, ''), COALESCE(t.priority, '')
            """,
            (threshold_days, holdout_start, *company_scope_params),
        ).fetchall()
    training_stats = {
        (str(row["queue_key"] or ""), str(row["priority_key"] or "")): {
            "sample_size": int(row.get("sample_size") or 0),
            "delayed_count": int(row.get("delayed_count") or 0),
        }
        for row in training_rows
    }
    evaluated: list[dict[str, Any]] = []
    abstentions = 0
    for row in holdout_rows:
        key = (str(row.get("queue_key") or ""), str(row.get("priority_key") or ""))
        stats = training_stats.get(key, {"sample_size": 0, "delayed_count": 0})
        sample_size = int(stats.get("sample_size") or 0)
        delayed_count = int(stats.get("delayed_count") or 0)
        smoothed_delay_rate = (
            delayed_count + (0.5 * PREDICTION_PRIOR_SAMPLE_SIZE)
        ) / (sample_size + PREDICTION_PRIOR_SAMPLE_SIZE)
        statistical_abstained = sample_size < PREDICTION_MIN_SAMPLE_SIZE
        abstentions += 1 if statistical_abstained else 0
        evaluated.append(
            {
                "ticket_number": row.get("ticket_number"),
                "company_id": row.get("company_id"),
                "category_key": row.get("category_key"),
                "queue_key": row.get("queue_key"),
                "priority_key": row.get("priority_key"),
                "resolution_days": _round_optional(row.get("resolution_days")),
                "actual_delayed": _num(row.get("resolution_days")) > threshold_days,
                "baseline_predicted_delayed": str(row.get("priority_key") or "") in {"1", "4"},
                "statistical_predicted_delayed": (
                    False if statistical_abstained else smoothed_delay_rate >= 0.5
                ),
                "statistical_abstained": statistical_abstained,
                "training_sample_size": sample_size,
                "bayesian_delay_rate": round(smoothed_delay_rate, 3),
            }
        )
    statistical_rows = [row for row in evaluated if not row["statistical_abstained"]]
    threshold_sweep = _threshold_sweep(statistical_rows)
    statistical_metrics = _binary_classification_metrics(statistical_rows, "statistical_predicted_delayed")
    calibration = {
        "brier_score": _brier_score(statistical_rows),
        "bands": _calibration_bands(statistical_rows),
        "secondary_metrics": _probability_auc(statistical_rows),
        "note": "Calibration measures compare Bayesian delay probability to observed delayed labels; they do not tune the model.",
    }
    concentration = {
        "company": _sanitized_concentration(evaluated, "company_id", "company_bucket"),
        "category": _sanitized_concentration(evaluated, "category_key", "category_bucket"),
        "note": "Buckets are sanitized and intended to reveal concentration risk without exposing customer names or ticket text.",
    }
    stratified_metrics = {
        "company": _sanitized_stratified_metrics(evaluated, "company_id", "company_bucket"),
        "category": _sanitized_stratified_metrics(evaluated, "category_key", "category_bucket"),
    }
    coverage = {
        "holdout_size": len(evaluated),
        "statistical_evaluated": len(statistical_rows),
        "statistical_abstentions": abstentions,
        "statistical_coverage_rate": round(len(statistical_rows) / len(evaluated), 3) if evaluated else None,
        "abstention_rate": round(abstentions / len(evaluated), 3) if evaluated else None,
    }
    policy = {
        "selection_mode": "human_review_required",
        "automatic_changes_allowed": False,
        "default_threshold": 0.5,
        "candidate_threshold_source": "threshold_sweep_best_f1",
        "minimum_review_evidence": [
            "delayed-ticket recall",
            "precision and false-positive burden",
            "Brier score and calibration bands",
            "PR/ROC secondary metrics",
            "coverage and abstention rates",
            "client/category concentration",
            "leakage review",
        ],
        "prohibited_actions": _prediction_target_policy(threshold_days, row_limit)["prohibited_actions"],
    }
    shadow_evaluation = {
        "enabled": True,
        "mode": "local_read_only_shadow_report",
        "bounded_recent_sample": row_limit,
        "authorized_company_scope_applied": authorized_company_ids is not None,
        "writes_to_autotask": False,
        "sends_notifications": False,
        "changes_thresholds_or_workflows": False,
    }
    field_certification = field_certification_report(authorized_company_ids=authorized_company_ids)
    warnings = [
        "This is offline local evaluation evidence only; it does not tune weights automatically.",
        "Threshold sweep is advisory evidence only; review before changing scoring or alert thresholds.",
        "Training rows are limited to tickets completed before the holdout window to reduce leakage.",
        "No Autotask ticket, assignment, status, or priority is changed.",
        "Bias and client/category concentration review remains required before production trust.",
    ]
    if statistical_metrics.get("recall") == 0:
        warnings.append("Default statistical recall is zero for delayed tickets in this holdout; do not treat high accuracy as predictive usefulness.")
    best_threshold = threshold_sweep[0] if threshold_sweep else None
    if best_threshold and (best_threshold.get("precision") or 0) < 0.2:
        warnings.append("The best-F1 threshold has low precision in this holdout; human review must weigh false-positive burden.")
    baseline_metrics = _binary_classification_metrics(evaluated, "baseline_predicted_delayed")
    return {
        "ok": True,
        "review_only": True,
        "threshold_days": threshold_days,
        "target": _prediction_target_policy(threshold_days, row_limit),
        "summary": {
            "holdout_size": len(evaluated),
            "training_groups": len(training_stats),
            "statistical_evaluated": len(statistical_rows),
            "statistical_abstentions": abstentions,
            "holdout_started_at": holdout_start,
        },
        "baseline": baseline_metrics,
        "statistical": statistical_metrics,
        "coverage": coverage,
        "calibration": calibration,
        "concentration": concentration,
        "stratified_metrics": stratified_metrics,
        "model_comparison": _model_comparison(baseline_metrics, statistical_metrics, calibration),
        "leakage_review": _leakage_review(holdout_start, row_limit, len(training_stats)),
        "field_certification": field_certification,
        "source_lineage": _predictive_source_lineage(field_certification),
        "threshold_sweep": threshold_sweep,
        "best_threshold_by_f1": best_threshold,
        "human_review_threshold_policy": policy,
        "shadow_evaluation": shadow_evaluation,
        "sample": [
            {key: value for key, value in row.items() if key not in {"company_id", "category_key"}}
            for row in evaluated[:25]
        ],
        "warnings": warnings,
    }


def ticket_health_review_queue(
    limit: int = 25,
    queue: str | None = None,
    assigned_resource_id: int | None = None,
    risk_bucket: str | None = None,
    min_priority: int = 0,
    needs_review_only: bool = False,
    authorized_company_ids: list[int] | None = None,
) -> dict[str, Any]:
    row_limit = min(max(limit, 1), 100)
    priority_floor = min(max(int(min_priority or 0), 0), 100)
    allowed_bucket = risk_bucket if risk_bucket in {"critical", "high", "watch", "normal"} else None
    summary = ticket_health_summary(
        limit=100,
        queue=queue,
        assigned_resource_id=assigned_resource_id,
        authorized_company_ids=authorized_company_ids,
    )
    tickets = list(summary.get("tickets", []))
    feedback_by_ticket = _ticket_health_feedback_counts([int(ticket["id"]) for ticket in tickets])
    completion_stats = _historical_completion_stats(tickets, authorized_company_ids=authorized_company_ids)
    items: list[dict[str, Any]] = []
    for ticket in tickets:
        feedback = feedback_by_ticket.get(int(ticket["id"]), {})
        predictive_signal = _ticket_predictive_review_signal(
            ticket,
            feedback,
            completion_stats.get((str(ticket.get("queue") or ""), str(ticket.get("priority") or ""))),
        )
        reasons: list[str] = []
        factors = ticket.get("factors") or []
        warnings = ticket.get("warnings") or []
        if feedback.get("needs_review"):
            reasons.append(f"{feedback['needs_review']} local needs-review feedback outcomes")
        if ticket.get("risk_bucket") in {"critical", "high"}:
            reasons.append(f"{ticket.get('risk_bucket')} heuristic ticket risk")
        if warnings:
            reasons.append("partial local evidence warnings")
        for factor in factors:
            if any(word in str(factor).lower() for word in ("overdue", "critical", "high priority", "labor", "waiting", "assignment")):
                reasons.append(str(factor))
        if not reasons:
            continue
        review_priority = min(
            int(ticket.get("health_score") or 0)
            + (30 if feedback.get("needs_review") else 0)
            + (10 if warnings else 0),
            100,
        )
        predictive_review_priority = (
            predictive_signal["statistical_review_score"]
            if predictive_signal.get("statistical_review_score") is not None
            else review_priority
        )
        if allowed_bucket and ticket.get("risk_bucket") != allowed_bucket:
            continue
        if needs_review_only and not feedback.get("needs_review"):
            continue
        if review_priority < priority_floor:
            continue
        items.append(
            {
                "ticket_id": ticket["id"],
                "ticket_autotask_id": ticket["autotask_id"],
                "ticket_number": ticket["ticket_number"],
                "title": ticket.get("title"),
                "risk_bucket": ticket["risk_bucket"],
                "health_score": ticket["health_score"],
                "review_priority": review_priority,
                "predictive_review_priority": predictive_review_priority,
                "predictive_signal": predictive_signal,
                "status_label": ticket.get("status_label") or ticket.get("status"),
                "queue_label": ticket.get("queue_label") or ticket.get("queue"),
                "assigned_resource_name": ticket.get("assigned_resource_name"),
                "feedback": feedback,
                "reasons": list(dict.fromkeys(reasons)),
            }
        )
    items.sort(key=lambda item: (-int(item["predictive_review_priority"]), str(item.get("ticket_number") or "")))
    return {
        "ok": True,
        "limit": row_limit,
        "filters": {
            "queue": queue,
            "assigned_resource_id": assigned_resource_id,
            "risk_bucket": allowed_bucket,
            "min_priority": priority_floor,
            "needs_review_only": bool(needs_review_only),
        },
        "summary": {
            "review_candidates": len(items),
            "returned": min(len(items), row_limit),
            "needs_review_feedback_tickets": sum(1 for item in items if item["feedback"].get("needs_review")),
            "predictive_ranked_tickets": sum(1 for item in items if not item["predictive_signal"].get("abstained")),
            "predictive_abstentions": sum(1 for item in items if item["predictive_signal"].get("abstained")),
        },
        "items": items[:row_limit],
        "guidance": [
            "This queue is local and review-only.",
            "Use it to prioritize human Ticket Health review; it does not write to Autotask or change tickets.",
            "Statistical ranking abstains when scoped local historical samples are too small.",
        ],
    }


def ticket_health_detail(ticket_id: int) -> dict[str, Any]:
    return ticket_health_detail_scoped(ticket_id)


def ticket_health_detail_scoped(ticket_id: int, authorized_company_ids: list[int] | None = None) -> dict[str, Any]:
    now = datetime.now(UTC)
    company_scope_sql, company_scope_params = _company_scope_clause(authorized_company_ids)
    with db_connection() as conn:
        rows = list(
            conn.execute(
                f"""
                WITH labor AS (
                    SELECT ticket_id, sum(COALESCE(hours, 0)) AS labor_hours
                    FROM autotask_time_entries
                    GROUP BY ticket_id
                ),
                history AS (
                    SELECT ticket_id, count(*) AS history_events, max(happened_at) AS last_history_at
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
                    t.queue,
                    COALESCE(queue_ref.label, t.queue) AS queue_label,
                    t.company_id,
                    t.assigned_resource_id,
                    COALESCE(NULLIF(t.assigned_resource_name, ''), resource_ref.label) AS assigned_resource_name,
                    t.created_at_autotask,
                    t.updated_at_autotask,
                    t.due_at_autotask,
                    t.first_response_due_at_autotask,
                    t.resolved_due_at_autotask,
                    t.sla_met,
                    EXTRACT(EPOCH FROM (%s::timestamptz - COALESCE(t.created_at_autotask, t.updated_at_autotask, %s::timestamptz))) / 3600 AS age_hours,
                    COALESCE(labor.labor_hours, 0) AS labor_hours,
                    COALESCE(history.history_events, 0) AS history_events,
                    history.last_history_at,
                    t.due_at_autotask IS NOT NULL AND t.due_at_autotask < %s::timestamptz AS due_overdue,
                    t.first_response_due_at_autotask IS NOT NULL
                        AND t.first_response_at_autotask IS NULL
                        AND t.first_response_due_at_autotask < %s::timestamptz AS first_response_overdue,
                    t.resolved_due_at_autotask IS NOT NULL
                        AND t.completed_at_autotask IS NULL
                        AND t.resolved_due_at_autotask < %s::timestamptz AS resolved_overdue
                FROM autotask_tickets t
                LEFT JOIN labor ON labor.ticket_id = t.id
                LEFT JOIN history ON history.ticket_id = t.id
                LEFT JOIN autotask_reference_values status_ref
                    ON status_ref.field_name='status' AND status_ref.value=t.status
                LEFT JOIN autotask_reference_values priority_ref
                    ON priority_ref.field_name='priority' AND priority_ref.value=t.priority
                LEFT JOIN autotask_reference_values queue_ref
                    ON queue_ref.field_name='queue' AND queue_ref.value=t.queue
                LEFT JOIN autotask_reference_values resource_ref
                    ON resource_ref.field_name='resource' AND resource_ref.value=t.assigned_resource_id::text
                WHERE t.id = %s
                {company_scope_sql}
                """,
                (now, now, now, now, now, ticket_id, *company_scope_params),
            ).fetchall()
        )
        if not rows:
            return {"ok": False, "error": "ticket_not_found", "ticket_id": ticket_id}
        ticket = _score_rows([dict(rows[0])])[0][0]
        history_rows = list(
            conn.execute(
                """
                SELECT id, autotask_id, action, detail, resource_id, happened_at
                FROM autotask_ticket_history
                WHERE ticket_id=%s
                ORDER BY happened_at DESC NULLS LAST, id DESC
                LIMIT 100
                """,
                (ticket_id,),
            ).fetchall()
        )
        labor_rows = list(
            conn.execute(
                """
                SELECT id, resource_id, resource_name, summary, hours, created_at_autotask
                FROM autotask_time_entries
                WHERE ticket_id=%s
                ORDER BY created_at_autotask DESC NULLS LAST, id DESC
                LIMIT 100
                """,
                (ticket_id,),
            ).fetchall()
        )
        feedback_rows = list(
            conn.execute(
                """
                SELECT id, health_score, risk_bucket, outcome, notes, created_at
                FROM ticket_health_risk_feedback
                WHERE ticket_id=%s
                ORDER BY created_at DESC, id DESC
                LIMIT 20
                """,
                (ticket_id,),
            ).fetchall()
        )

    history_events = []
    transitions = []
    for row in history_rows:
        event = dict(row)
        parsed = parse_history_transition(event.get("action"), event.get("detail"))
        event["transition"] = parsed
        history_events.append(event)
        if parsed["is_transition"]:
            transitions.append({"happened_at": event.get("happened_at"), **parsed})

    return {
        "ok": True,
        "ticket": ticket,
        "history_events": history_events,
        "transitions": transitions,
        "status_duration_summary": status_duration_summary(
            transitions,
            current_status=ticket.get("status_label") or ticket.get("status"),
            fallback_started_at=ticket.get("updated_at_autotask") or ticket.get("created_at_autotask"),
        ),
        "labor_entries": [dict(row) for row in labor_rows],
        "feedback": {
            "summary": _ticket_health_feedback_summary([dict(row) for row in feedback_rows]),
            "recent_feedback": [dict(row) for row in feedback_rows],
        },
        "calibration": _ticket_health_feedback_calibration(
            int(ticket.get("health_score") or 0),
            [dict(row) for row in feedback_rows],
        ),
        "warnings": ticket["warnings"],
    }


def ticket_health_detail_by_number(ticket_number: str) -> dict[str, Any]:
    return ticket_health_detail_by_number_scoped(ticket_number)


def ticket_health_detail_by_number_scoped(
    ticket_number: str,
    authorized_company_ids: list[int] | None = None,
) -> dict[str, Any]:
    ticket_lookup = (ticket_number or "").strip()
    if not ticket_lookup:
        return {"ok": False, "error": "ticket_number_required", "ticket_number": ticket_lookup}
    company_scope_sql, company_scope_params = _company_scope_clause(authorized_company_ids)
    with db_connection() as conn:
        row = conn.execute(
            """
            SELECT id
            FROM autotask_tickets
            WHERE (ticket_number = %s OR autotask_id::text = %s)
            {company_scope_sql}
            ORDER BY id DESC
            LIMIT 1
            """.format(company_scope_sql=company_scope_sql),
            (ticket_lookup, ticket_lookup, *company_scope_params),
        ).fetchone()
    if not row:
        return {"ok": False, "error": "ticket_not_found", "ticket_number": ticket_lookup}
    return ticket_health_detail_scoped(int(row["id"]), authorized_company_ids=authorized_company_ids)
