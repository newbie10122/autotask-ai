from __future__ import annotations

from typing import Any

from .db import db_connection
from .ticket_health import CLOSED_STATUS_IDS


def _float_or_none(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _score_candidate(candidate: dict[str, Any]) -> int:
    completed = int(candidate.get("completed_related") or 0)
    related = int(candidate.get("related_tickets") or 0)
    open_workload = int(candidate.get("open_workload") or 0)
    customer_familiarity = int(candidate.get("customer_familiarity_count") or 0)
    broader_skill = int(candidate.get("broader_skill_count") or 0)
    average_labor = float(candidate.get("average_labor_hours") or 0)
    availability_bonus = int(candidate.get("availability_score") or 0)
    score = completed * 18 + related * 4 + customer_familiarity * 6 + broader_skill * 2 + availability_bonus - open_workload * 3 - int(average_labor)
    return max(score, 0)


def _availability_signal(open_workload: int) -> dict[str, Any]:
    if open_workload <= 3:
        return {"label": "lighter local workload", "score": 12}
    if open_workload <= 8:
        return {"label": "moderate local workload", "score": 4}
    return {"label": "heavy local workload", "score": -8}


def _availability_context() -> dict[str, Any]:
    return {
        "source": "local_open_workload",
        "calendar_connected": False,
        "calendar_source": None,
        "interpretation": "Availability is a local open-ticket workload proxy only; calendar/free-busy data is not connected.",
    }


def _scope_params(authorized_company_ids: list[int] | None) -> list[Any]:
    if authorized_company_ids is None:
        return [None, []]
    return [authorized_company_ids, authorized_company_ids]


def _candidate_factors(candidate: dict[str, Any]) -> list[str]:
    factors = [
        f"{int(candidate.get('completed_related') or 0)} completed related local tickets",
        f"{int(candidate.get('broader_skill_count') or 0)} broader category/issue local tickets",
        f"{int(candidate.get('customer_familiarity_count') or 0)} completed tickets for this customer",
        f"{int(candidate.get('open_workload') or 0)} currently open assigned tickets",
        f"Availability proxy: {candidate.get('availability_label') or 'unknown'}",
    ]
    if candidate.get("average_resolution_days") is not None:
        factors.append(f"{float(candidate['average_resolution_days']):.1f} day average related resolution")
    if candidate.get("average_labor_hours") is not None:
        factors.append(f"{float(candidate['average_labor_hours']):.1f} average related labor hours")
    return factors


def _routing_feedback_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    outcome_counts = {"accepted": 0, "rejected": 0, "needs_review": 0}
    for row in rows:
        outcome = row.get("outcome")
        if outcome in outcome_counts:
            outcome_counts[outcome] += 1
    return {
        "total_feedback": len(rows),
        "outcome_counts": outcome_counts,
        "latest": rows[0] if rows else None,
        "recent": rows,
        "review_only": True,
        "message": "Routing feedback is local review evidence only and does not change Autotask assignment.",
    }


def technician_skill_profiles(limit: int = 25, authorized_company_ids: list[int] | None = None) -> dict[str, Any]:
    row_limit = min(max(limit, 1), 100)
    with db_connection() as conn:
        profile_rows = list(
            conn.execute(
                """
                WITH labor AS (
                    SELECT ticket_id, sum(COALESCE(hours, 0)) AS labor_hours
                    FROM autotask_time_entries
                    GROUP BY ticket_id
                ),
                open_workload AS (
                    SELECT assigned_resource_id, count(*) AS open_workload
                    FROM autotask_tickets
                    WHERE assigned_resource_id IS NOT NULL
                      AND completed_at_autotask IS NULL
                      AND NOT analytics_exclude
                      AND COALESCE(status, '') <> ALL(%s)
                      AND (%s IS NULL OR company_id = ANY(%s))
                    GROUP BY assigned_resource_id
                )
                SELECT
                    t.assigned_resource_id,
                    COALESCE(NULLIF(t.assigned_resource_name, ''), resource_ref.label, t.assigned_resource_id::text) AS assigned_resource_name,
                    count(*) FILTER (WHERE t.completed_at_autotask IS NOT NULL) AS completed_tickets,
                    count(DISTINCT t.company_id) FILTER (WHERE t.company_id IS NOT NULL) AS completed_customers,
                    avg(COALESCE(labor.labor_hours, 0)) AS average_labor_hours,
                    avg(
                        CASE
                          WHEN t.completed_at_autotask IS NOT NULL AND t.created_at_autotask IS NOT NULL
                          THEN EXTRACT(EPOCH FROM (t.completed_at_autotask - t.created_at_autotask)) / 86400
                          ELSE NULL
                        END
                    ) AS average_resolution_days,
                    COALESCE(open_workload.open_workload, 0) AS open_workload
                FROM autotask_tickets t
                LEFT JOIN labor ON labor.ticket_id=t.id
                LEFT JOIN open_workload ON open_workload.assigned_resource_id=t.assigned_resource_id
                LEFT JOIN autotask_reference_values resource_ref
                    ON resource_ref.field_name='resource' AND resource_ref.value=t.assigned_resource_id::text
                WHERE t.assigned_resource_id IS NOT NULL
                  AND NOT t.analytics_exclude
                  AND t.completed_at_autotask IS NOT NULL
                  AND (%s IS NULL OR t.company_id = ANY(%s))
                GROUP BY
                    t.assigned_resource_id,
                    COALESCE(NULLIF(t.assigned_resource_name, ''), resource_ref.label, t.assigned_resource_id::text),
                    COALESCE(open_workload.open_workload, 0)
                ORDER BY completed_tickets DESC, assigned_resource_name
                LIMIT %s
                """,
                (list(CLOSED_STATUS_IDS), *_scope_params(authorized_company_ids), *_scope_params(authorized_company_ids), row_limit),
            ).fetchall()
        )
        skill_rows = list(
            conn.execute(
                """
                WITH skill_counts AS (
                    SELECT
                        t.assigned_resource_id,
                        concat_ws(
                            ' / ',
                            COALESCE(category_ref.label, NULLIF(t.category, '')),
                            COALESCE(issue_ref.label, NULLIF(t.issue_type, '')),
                            COALESCE(subissue_ref.label, NULLIF(t.subissue_type, ''))
                        ) AS skill_label,
                        count(*) AS count
                    FROM autotask_tickets t
                    LEFT JOIN autotask_reference_values category_ref
                        ON category_ref.field_name='category' AND category_ref.value=t.category
                    LEFT JOIN autotask_reference_values issue_ref
                        ON issue_ref.field_name='issue_type' AND issue_ref.value=t.issue_type
                    LEFT JOIN autotask_reference_values subissue_ref
                        ON subissue_ref.field_name='subissue_type' AND subissue_ref.value=t.subissue_type
                    WHERE t.assigned_resource_id IS NOT NULL
                      AND NOT t.analytics_exclude
                      AND t.completed_at_autotask IS NOT NULL
                      AND (%s IS NULL OR t.company_id = ANY(%s))
                    GROUP BY t.assigned_resource_id, skill_label
                ),
                ranked AS (
                    SELECT
                        assigned_resource_id,
                        NULLIF(skill_label, '') AS skill_label,
                        count,
                        row_number() OVER (PARTITION BY assigned_resource_id ORDER BY count DESC, skill_label) AS rank
                    FROM skill_counts
                    WHERE NULLIF(skill_label, '') IS NOT NULL
                )
                SELECT assigned_resource_id, skill_label, count
                FROM ranked
                WHERE rank <= 3
                ORDER BY assigned_resource_id, rank
                """,
                _scope_params(authorized_company_ids),
            ).fetchall()
        )

    skills_by_resource: dict[Any, list[dict[str, Any]]] = {}
    for row in skill_rows:
        skills_by_resource.setdefault(row["assigned_resource_id"], []).append(
            {"label": row["skill_label"], "count": int(row["count"] or 0)}
        )

    profiles = []
    availability_context = _availability_context()
    for row in profile_rows:
        open_workload = int(row["open_workload"] or 0)
        availability = _availability_signal(open_workload)
        profiles.append(
            {
                "assigned_resource_id": row["assigned_resource_id"],
                "assigned_resource_name": row["assigned_resource_name"],
                "completed_tickets": int(row["completed_tickets"] or 0),
                "completed_customers": int(row["completed_customers"] or 0),
                "open_workload": open_workload,
                "availability_label": availability["label"],
                "availability_source": availability_context["source"],
                "availability_context": availability_context,
                "average_labor_hours": _float_or_none(row.get("average_labor_hours")),
                "average_resolution_days": _float_or_none(row.get("average_resolution_days")),
                "top_skill_groups": skills_by_resource.get(row["assigned_resource_id"], []),
                "profile_source": "local_completed_tickets",
                "recommendation": "review_only",
            }
        )
    return {
        "ok": True,
        "profiles": profiles,
        "summary": {"profiles_returned": len(profiles)},
        "availability_context": availability_context,
        "warnings": [
            "Local skill profiles are directional and review-only. No Autotask assignment is changed.",
            availability_context["interpretation"],
        ],
    }


def ticket_routing_recommendation(
    ticket_id: int,
    limit: int = 5,
    authorized_company_ids: list[int] | None = None,
) -> dict[str, Any]:
    row_limit = min(max(limit, 1), 10)
    with db_connection() as conn:
        target = conn.execute(
            """
            SELECT id, autotask_id, ticket_number, title, category, issue_type, subissue_type, company_id, priority
            FROM autotask_tickets
            WHERE id=%s
              AND (%s IS NULL OR company_id = ANY(%s))
            """,
            (ticket_id, *_scope_params(authorized_company_ids)),
        ).fetchone()
        if not target:
            return {"ok": False, "reason": "ticket_not_found", "recommendations": []}

        related_rows = list(
            conn.execute(
                """
                WITH related AS MATERIALIZED (
                    SELECT
                        id,
                        assigned_resource_id,
                        assigned_resource_name,
                        completed_at_autotask,
                        created_at_autotask
                    FROM autotask_tickets
                    WHERE assigned_resource_id IS NOT NULL
                      AND NOT analytics_exclude
                      AND completed_at_autotask IS NOT NULL
                      AND id <> %s
                      AND (%s IS NULL OR company_id = ANY(%s))
                      AND category IS NOT DISTINCT FROM %s
                      AND issue_type IS NOT DISTINCT FROM %s
                      AND subissue_type IS NOT DISTINCT FROM %s
                ),
                labor AS MATERIALIZED (
                    SELECT te.ticket_id, sum(COALESCE(te.hours, 0)) AS labor_hours
                    FROM autotask_time_entries te
                    JOIN related r ON r.id=te.ticket_id
                    GROUP BY te.ticket_id
                ),
                resource_labels AS MATERIALIZED (
                    SELECT value, label
                    FROM autotask_reference_values
                    WHERE field_name='resource'
                )
                SELECT
                    r.assigned_resource_id,
                    COALESCE(NULLIF(r.assigned_resource_name, ''), resource_labels.label, r.assigned_resource_id::text) AS assigned_resource_name,
                    count(*) AS related_tickets,
                    count(*) FILTER (WHERE r.completed_at_autotask IS NOT NULL) AS completed_related,
                    avg(COALESCE(labor.labor_hours, 0)) AS average_labor_hours,
                    avg(
                        CASE WHEN r.completed_at_autotask IS NOT NULL AND r.created_at_autotask IS NOT NULL
                             THEN EXTRACT(EPOCH FROM (r.completed_at_autotask - r.created_at_autotask)) / 86400
                             ELSE NULL
                        END
                    ) AS average_resolution_days
                FROM related r
                LEFT JOIN labor ON labor.ticket_id = r.id
                LEFT JOIN resource_labels ON resource_labels.value=r.assigned_resource_id::text
                GROUP BY r.assigned_resource_id, COALESCE(NULLIF(r.assigned_resource_name, ''), resource_labels.label, r.assigned_resource_id::text)
                ORDER BY completed_related DESC, related_tickets DESC
                LIMIT 25
                """,
                (ticket_id, *_scope_params(authorized_company_ids), target["category"], target["issue_type"], target["subissue_type"]),
            ).fetchall()
        )
        workload_rows = list(
            conn.execute(
                """
                SELECT assigned_resource_id, count(*) AS open_workload
                FROM autotask_tickets
                WHERE assigned_resource_id IS NOT NULL
                  AND completed_at_autotask IS NULL
                  AND NOT analytics_exclude
                  AND COALESCE(status, '') <> ALL(%s)
                  AND (%s IS NULL OR company_id = ANY(%s))
                GROUP BY assigned_resource_id
                """,
                (list(CLOSED_STATUS_IDS), *_scope_params(authorized_company_ids)),
            ).fetchall()
        )
        customer_rows = list(
            conn.execute(
                """
                SELECT assigned_resource_id, count(*) AS customer_familiarity_count
                FROM autotask_tickets
                WHERE assigned_resource_id IS NOT NULL
                  AND NOT analytics_exclude
                  AND completed_at_autotask IS NOT NULL
                  AND id <> %s
                  AND company_id IS NOT NULL
                  AND company_id = %s
                  AND (%s IS NULL OR company_id = ANY(%s))
                GROUP BY assigned_resource_id
                """,
                (ticket_id, target["company_id"], *_scope_params(authorized_company_ids)),
            ).fetchall()
        )
        skill_rows = list(
            conn.execute(
                """
                SELECT assigned_resource_id, count(*) AS broader_skill_count
                FROM autotask_tickets
                WHERE assigned_resource_id IS NOT NULL
                  AND NOT analytics_exclude
                  AND completed_at_autotask IS NOT NULL
                  AND id <> %s
                  AND (%s IS NULL OR company_id = ANY(%s))
                  AND (
                    COALESCE(category, '') = COALESCE(%s, '')
                    OR COALESCE(issue_type, '') = COALESCE(%s, '')
                  )
                GROUP BY assigned_resource_id
                """,
                (ticket_id, *_scope_params(authorized_company_ids), target["category"], target["issue_type"]),
            ).fetchall()
        )
        feedback_rows = [
            dict(row)
            for row in conn.execute(
                """
                SELECT id, recommended_resource_id, recommended_resource_name, outcome, notes, created_at
                FROM routing_recommendation_feedback
                WHERE ticket_id=%s
                ORDER BY created_at DESC
                LIMIT 10
                """,
                (ticket_id,),
            ).fetchall()
        ]

    workload = {row["assigned_resource_id"]: int(row["open_workload"] or 0) for row in workload_rows}
    customer_familiarity = {
        row["assigned_resource_id"]: int(row["customer_familiarity_count"] or 0)
        for row in customer_rows
    }
    broader_skill = {row["assigned_resource_id"]: int(row["broader_skill_count"] or 0) for row in skill_rows}
    recommendations = []
    availability_context = _availability_context()
    for row in related_rows:
        candidate = dict(row)
        candidate["open_workload"] = workload.get(candidate["assigned_resource_id"], 0)
        availability = _availability_signal(candidate["open_workload"])
        candidate["availability_label"] = availability["label"]
        candidate["availability_score"] = availability["score"]
        candidate["availability_source"] = availability_context["source"]
        candidate["availability_context"] = availability_context
        candidate["customer_familiarity_count"] = customer_familiarity.get(candidate["assigned_resource_id"], 0)
        candidate["broader_skill_count"] = broader_skill.get(candidate["assigned_resource_id"], 0)
        candidate["average_labor_hours"] = _float_or_none(candidate.get("average_labor_hours"))
        candidate["average_resolution_days"] = _float_or_none(candidate.get("average_resolution_days"))
        candidate["recommendation_score"] = _score_candidate(candidate)
        candidate["factors"] = _candidate_factors(candidate)
        candidate["recommendation"] = "review_only"
        recommendations.append(candidate)
    recommendations.sort(key=lambda item: (-item["recommendation_score"], item["open_workload"], item["assigned_resource_name"] or ""))
    return {
        "ok": True,
        "ticket": dict(target),
        "recommendations": recommendations[:row_limit],
        "feedback": _routing_feedback_summary(feedback_rows),
        "availability_context": availability_context,
        "warnings": [
            "Recommendation only. No Autotask assignment is changed.",
            availability_context["interpretation"],
        ],
    }


def store_routing_feedback(
    ticket_id: int,
    recommended_resource_id: int | None,
    recommended_resource_name: str | None,
    outcome: str,
    notes: str | None = None,
    authorized_company_ids: list[int] | None = None,
) -> dict[str, Any]:
    if outcome not in {"accepted", "rejected", "needs_review"}:
        return {"ok": False, "reason": "invalid_outcome"}
    with db_connection() as conn:
        ticket = conn.execute(
            """
            SELECT id, autotask_id
            FROM autotask_tickets
            WHERE id=%s
              AND (%s IS NULL OR company_id = ANY(%s))
            """,
            (ticket_id, *_scope_params(authorized_company_ids)),
        ).fetchone()
        if not ticket:
            return {"ok": False, "reason": "ticket_not_found"}
        row = conn.execute(
            """
            INSERT INTO routing_recommendation_feedback(
                ticket_id, ticket_autotask_id, recommended_resource_id,
                recommended_resource_name, outcome, notes
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, created_at
            """,
            (
                ticket["id"],
                ticket["autotask_id"],
                recommended_resource_id,
                recommended_resource_name,
                outcome,
                notes,
            ),
        ).fetchone()
    return {
        "ok": True,
        "feedback_id": row["id"],
        "created_at": row["created_at"],
        "message": "Routing recommendation feedback stored locally. No Autotask assignment was changed.",
    }
