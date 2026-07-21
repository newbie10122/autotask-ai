from __future__ import annotations

import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from typing import Any

from psycopg.types.json import Jsonb

from .answer_guardrails import WEAK_EVIDENCE_MESSAGE, build_guarded_answer
from .answer_safety import filter_safe_sources, verify_answer
from .config import settings
from .db import db_connection, init_schema
from .ollama import OllamaUnavailable, chat, embed_text
from .quality import is_recurring_issues_question
from .security import redact_private_entities
from .ticket_analytics import format_recurring_issues_answer, recurring_issues_report


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"


def _confidence_label(score: float) -> str:
    if score >= 0.75:
        return "High"
    if score >= 0.45:
        return "Medium"
    return "Low"


def _unique_tickets(sources: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    tickets: list[str] = []
    for source in sources:
        ticket = str(source.get("ticket_number") or source.get("autotask_id") or "")
        if ticket and ticket not in seen:
            seen.add(ticket)
            tickets.append(ticket)
    return tickets


def _limit_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    limited: list[dict[str, Any]] = []
    per_ticket: dict[str, int] = defaultdict(int)
    seen_tickets: set[str] = set()
    for source in sources:
        ticket_key = str(source.get("autotask_id") or source.get("ticket_number") or source.get("chunk_id"))
        if ticket_key not in seen_tickets and len(seen_tickets) >= settings.assistant_max_unique_tickets:
            continue
        if per_ticket[ticket_key] >= settings.assistant_max_chunks_per_ticket:
            continue
        limited.append(source)
        per_ticket[ticket_key] += 1
        seen_tickets.add(ticket_key)
        if len(limited) >= settings.assistant_max_context_chunks:
            break
    return limited


def _fallback_answer(
    sources: list[dict[str, Any]],
    confidence: float,
    warning: str | None = None,
) -> str:
    tickets = _unique_tickets(sources)
    summaries = []
    for source in sources[: settings.assistant_max_context_chunks]:
        summaries.append(_source_summary(source))
    guidance = (
        "A local CPU LLM may take longer than the normal timeout. "
        "This response uses retrieved ticket evidence directly instead of generated prose."
    )
    steps = [
        "Open the representative tickets and compare the symptoms before applying a fix.",
        "Use Deep Dive mode when you want the local CPU model to spend more time generating a narrative answer.",
    ]
    answer = build_guarded_answer(
        ticket_history="\n".join(f"- {summary}" for summary in summaries) or WEAK_EVIDENCE_MESSAGE,
        general_guidance=guidance,
        next_steps=steps,
        tickets=tickets,
        confidence=confidence,
    )
    if warning:
        answer = answer.replace(
            "Warnings\n- None",
            "Warnings\n- Local CPU LLM timed out; showing a cleaned retrieval summary instead.",
        )
    return answer


def _line_value(content: str, label: str) -> str:
    prefix = f"{label}:"
    for line in content.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return ""


def _compact_text(value: str, max_length: int = 180) -> str:
    text = " ".join(value.split())
    if len(text) <= max_length:
        return text
    return text[: max_length - 3].rstrip() + "..."


def _source_summary(source: dict[str, Any]) -> str:
    content = redact_private_entities(str(source.get("content") or ""))
    ticket = str(source.get("ticket_number") or source.get("autotask_id") or _line_value(content, "Ticket Number") or "Ticket")
    title = _line_value(content, "Title")
    description = _line_value(content, "Description")
    note_body = _line_value(content, "Note Body")
    evidence = _compact_text(description or note_body or content, 220)
    heading = ticket
    if title:
        heading += f" - {_compact_text(title, 90)}"
    return f"{heading}: {evidence}"


def _chat_with_timeout(prompt: str, timeout_seconds: int) -> str:
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(chat, prompt)
    try:
        return future.result(timeout=timeout_seconds)
    except FutureTimeout as exc:
        future.cancel()
        raise OllamaUnavailable("Local LLM timed out; showing retrieval summary only.") from exc
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def _retrieve_sources(
    question: str,
    limit: int,
    include_noise: bool = False,
    authorized_company_ids: list[int] | None = None,
) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    fetch_limit = max(limit * 4, settings.assistant_max_context_chunks * 3)
    company_filter_sql = ""
    company_filter_params: tuple[Any, ...] = ()
    if authorized_company_ids is not None:
        if not authorized_company_ids:
            return []
        company_filter_sql = "AND (dc.source_metadata->>'company_id')::bigint = ANY(%s)"
        company_filter_params = (authorized_company_ids,)
    try:
        embedding = embed_text(question)
        with db_connection() as conn:
            sources = list(
                conn.execute(
                    """
                    SELECT dc.id AS chunk_id, dc.content, dc.source_metadata, dc.knowledge_class,
                           dc.quality_score, dc.is_noise, dc.noise_reason,
                           t.id AS ticket_pk, t.autotask_id, t.ticket_number,
                           1 - (de.embedding <=> %s::vector)
                             + COALESCE(dc.quality_score, 0.5) * 0.08
                             + CASE WHEN dc.knowledge_class IN ('resolution', 'human_troubleshooting') THEN 0.08 ELSE 0 END
                             + CASE WHEN t.completed_at_autotask IS NOT NULL THEN 0.03 ELSE 0 END
                             AS score
                    FROM document_embeddings de
                    JOIN document_chunks dc ON dc.id = de.chunk_id
                    LEFT JOIN autotask_tickets t ON (dc.source_metadata->>'ticket_id')::bigint = t.autotask_id
                    WHERE de.model_name=%s
                      AND dc.is_active
                      AND (%s OR NOT dc.is_noise)
                      """ + company_filter_sql + """
                    ORDER BY score DESC
                    LIMIT %s
                    """,
                    (
                        _vector_literal(embedding),
                        settings.ollama_embedding_model,
                        include_noise or not settings.assistant_exclude_noise_by_default,
                        *company_filter_params,
                        fetch_limit,
                    ),
                ).fetchall()
            )
    except OllamaUnavailable:
        sources = []

    if not sources:
        with db_connection() as conn:
            sources = list(
                conn.execute(
                    """
                    SELECT dc.id AS chunk_id, dc.content, dc.source_metadata, dc.knowledge_class,
                           dc.quality_score, dc.is_noise, dc.noise_reason,
                           t.id AS ticket_pk, t.autotask_id, t.ticket_number,
                           ts_rank_cd(to_tsvector('english', dc.content), plainto_tsquery('english', %s))
                             + COALESCE(dc.quality_score, 0.5) * 0.08
                             + CASE WHEN dc.knowledge_class IN ('resolution', 'human_troubleshooting') THEN 0.08 ELSE 0 END
                             AS score
                    FROM document_chunks dc
                    LEFT JOIN autotask_tickets t ON (dc.source_metadata->>'ticket_id')::bigint = t.autotask_id
                    WHERE dc.is_active
                      AND (%s OR NOT dc.is_noise)
                      """ + company_filter_sql + """
                      AND to_tsvector('english', dc.content) @@ plainto_tsquery('english', %s)
                    ORDER BY score DESC
                    LIMIT %s
                    """,
                    (
                        question,
                        include_noise or not settings.assistant_exclude_noise_by_default,
                        *company_filter_params,
                        question,
                        fetch_limit,
                    ),
                ).fetchall()
            )
    return _limit_sources(sources)


def _recurring_issue_groups(limit: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    with db_connection() as conn:
        groups = list(
            conn.execute(
                """
                SELECT
                    COALESCE(NULLIF(category, ''), 'Unknown') AS category,
                    COALESCE(NULLIF(issue_type, ''), 'Unknown') AS issue_type,
                    COALESCE(NULLIF(subissue_type, ''), 'Unknown') AS subissue_type,
                    COALESCE(NULLIF(queue, ''), 'Unknown') AS queue,
                    count(*) AS ticket_count,
                    max(updated_at_autotask) AS last_seen
                FROM autotask_tickets
                WHERE COALESCE(title, '') !~* '(ticket survey|your ticket is complete|notification e-mail|unsubscribe)'
                GROUP BY 1, 2, 3, 4
                ORDER BY ticket_count DESC, last_seen DESC NULLS LAST
                LIMIT %s
                """,
                (limit,),
            ).fetchall()
        )
        representatives: list[dict[str, Any]] = []
        for group in groups:
            rows = list(
                conn.execute(
                    """
                    SELECT ticket_number, autotask_id, title
                    FROM autotask_tickets
                    WHERE COALESCE(NULLIF(category, ''), 'Unknown')=%s
                      AND COALESCE(NULLIF(issue_type, ''), 'Unknown')=%s
                      AND COALESCE(NULLIF(subissue_type, ''), 'Unknown')=%s
                      AND COALESCE(NULLIF(queue, ''), 'Unknown')=%s
                    ORDER BY updated_at_autotask DESC NULLS LAST, autotask_id DESC
                    LIMIT 3
                    """,
                    (group["category"], group["issue_type"], group["subissue_type"], group["queue"]),
                ).fetchall()
            )
            representatives.append({"group": group, "tickets": rows})
    return groups, representatives


def _format_recurring_answer(groups: list[dict[str, Any]], representatives: list[dict[str, Any]]) -> tuple[str, list[str]]:
    group_lines = []
    evidence_lines = []
    ticket_lines = []
    for index, group in enumerate(groups, start=1):
        label = (
            f"Category {group['category']} / Issue {group['issue_type']} / "
            f"Subissue {group['subissue_type']} / Queue {group['queue']}"
        )
        group_lines.append(f"{index}. {label}: {group['ticket_count']} tickets")
        evidence_lines.append(f"- {label}: {group['ticket_count']} tickets")
    tickets: list[str] = []
    for item in representatives:
        for ticket in item["tickets"]:
            display = str(ticket.get("ticket_number") or ticket.get("autotask_id"))
            if display not in tickets:
                tickets.append(display)
                ticket_lines.append(f"- {display}: {ticket.get('title') or ''}")
    answer = (
        "Confidence: Medium\n\n"
        "Top Recurring Issue Groups\n"
        + ("\n".join(group_lines) or "No recurring issue groups found.")
        + "\n\nEvidence / Counts\n"
        + ("\n".join(evidence_lines) or "- No counts available.")
        + "\n\nRepresentative Tickets\n"
        + ("\n".join(ticket_lines) or "- None")
        + "\n\nSuggested Operational Next Steps\n"
        "- Review the largest groups for queue/category hygiene.\n"
        "- Sample representative tickets and split system-generated work from human support work.\n"
        "- Use this as a trend view, then drill into specific groups for root-cause work.\n\n"
        "Warnings\n"
        "- Counts are based on currently synced local Autotask tickets and available normalized fields."
    )
    return answer, tickets


def _store_answer(
    query_id: int,
    answer: str,
    confidence: float,
    sources: list[dict[str, Any]],
    duration_ms: int,
) -> dict[str, Any]:
    with db_connection() as conn:
        for source in sources:
            conn.execute(
                """
                INSERT INTO assistant_query_sources(query_id, chunk_id, ticket_id, company_id, score, source_metadata)
                SELECT %s, %s, %s, %s, %s, %s
                WHERE EXISTS (SELECT 1 FROM document_chunks WHERE id=%s)
                """,
                (
                    query_id,
                    source.get("chunk_id"),
                    source.get("ticket_pk"),
                    (source.get("source_metadata") or {}).get("company_id"),
                    float(source.get("score") or 0),
                    Jsonb(source.get("source_metadata") or {}),
                    source.get("chunk_id"),
                ),
            )
        answer_row = conn.execute(
            """
            INSERT INTO assistant_answers(query_id, answer, confidence, model_name, duration_ms)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (query_id, answer, confidence, settings.ollama_chat_model, duration_ms),
        ).fetchone()
        conn.execute("UPDATE assistant_queries SET duration_ms=%s WHERE id=%s", (duration_ms, query_id))
    return answer_row


def ask_assistant(
    question: str,
    mode: str = "ticket_history_only",
    limit: int = 5,
    include_noise: bool = False,
    authorized_company_ids: list[int] | None = None,
    actor_username: str | None = None,
) -> dict[str, Any]:
    init_schema()
    started = time.monotonic()
    limit = min(max(limit, 1), 12)
    with db_connection() as conn:
        query_row = conn.execute(
            """
            INSERT INTO assistant_queries(query, mode, model_name, actor_username, effective_scope)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                question,
                mode,
                settings.ollama_chat_model,
                actor_username,
                Jsonb({"company_ids": authorized_company_ids, "global": authorized_company_ids is None}),
            ),
        ).fetchone()
    query_id = query_row["id"]

    if is_recurring_issues_question(question):
        report = recurring_issues_report(limit=limit, authorized_company_ids=authorized_company_ids)
        answer, tickets = format_recurring_issues_answer(report)
        duration_ms = int((time.monotonic() - started) * 1000)
        confidence_score = 0.7 if report.get("groups") else 0.0
        answer_row = _store_answer(query_id, answer, confidence_score, [], duration_ms)
        return {
            "query_id": query_id,
            "answer_id": answer_row["id"],
            "answer": answer,
            "confidence": "Medium" if report.get("groups") else "Low",
            "confidence_score": confidence_score,
            "based_on_tickets": tickets,
            "sources": [],
            "warnings": report.get("warnings") or ["Counts are based on currently synced local Autotask tickets."],
            "duration_ms": duration_ms,
            "route": "recurring_issue_analytics",
        }

    sources = _retrieve_sources(question, limit, include_noise=include_noise, authorized_company_ids=authorized_company_ids)
    sources, safety_warnings = filter_safe_sources(sources)
    best_score = float(sources[0]["score"] or 0) if sources else 0.0
    tickets = _unique_tickets(sources)
    weak = not sources or best_score < 0.05
    warning: str | None = None
    if weak:
        answer = build_guarded_answer(
            ticket_history=WEAK_EVIDENCE_MESSAGE,
            general_guidance="No general guidance was generated because matching ticket evidence was too weak.",
            next_steps=["Try a more specific question or run ticket/document/embedding sync first."],
            tickets=[],
            confidence=0.0,
        )
        confidence = 0.0
    else:
        context = "\n\n---\n\n".join(redact_private_entities(source["content"]) for source in sources)
        prompt = (
            "Answer using only the CompuOne ticket-history context below. "
            "Ignore boilerplate, surveys, autoresponders, completion emails, and unsubscribe footers. "
            "Keep ticket history separate from general IT guidance. "
            "Use this exact section format: Confidence, From CompuOne Ticket History, "
            "General IT Guidance, Suggested Next Steps, Based on Tickets, Warnings.\n\n"
            f"Question:\n{question}\n\nContext:\n{context}\n"
        )
        confidence = min(max(best_score, 0.35), 0.95)
        timeout = settings.deep_dive_timeout_seconds if mode == "deep_dive" else settings.assistant_normal_timeout_seconds
        try:
            generated = _chat_with_timeout(prompt, timeout)
        except OllamaUnavailable as exc:
            generated = ""
            warning = str(exc)
        if generated and "From CompuOne Ticket History" in generated:
            answer = redact_private_entities(generated)
        else:
            answer = _fallback_answer(sources, confidence, warning)
        answer = redact_private_entities(answer)
        verification = verify_answer(answer, sources, authorized_company_ids=authorized_company_ids)
        if not verification.ok:
            warning = f"Answer verifier failed closed: {verification.fail_closed_reason}."
            answer = _fallback_answer(sources, confidence, warning)

    duration_ms = int((time.monotonic() - started) * 1000)
    answer_row = _store_answer(query_id, answer, confidence, sources, duration_ms)
    return {
        "query_id": query_id,
        "answer_id": answer_row["id"],
        "answer": answer,
        "confidence": _confidence_label(confidence),
        "confidence_score": confidence,
        "based_on_tickets": tickets,
        "sources": [
            {
                "chunk_id": source.get("chunk_id"),
                "ticket_id": source.get("autotask_id"),
                "ticket_number": source.get("ticket_number"),
                "score": float(source.get("score") or 0),
                "knowledge_class": source.get("knowledge_class"),
            }
            for source in sources
        ],
        "warnings": (safety_warnings + ([warning] if warning else [])) if not weak else safety_warnings + [WEAK_EVIDENCE_MESSAGE],
        "duration_ms": duration_ms,
        "route": "rag",
    }


def store_feedback(
    answer_id: int,
    rating: str,
    notes: str | None = None,
    actor_username: str | None = None,
    authorized_company_ids: list[int] | None = None,
) -> dict[str, Any]:
    init_schema()
    with db_connection() as conn:
        feedback = conn.execute(
            """
            INSERT INTO assistant_feedback(answer_id, actor_username, effective_scope, rating, notes)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                answer_id,
                actor_username,
                Jsonb({"company_ids": authorized_company_ids, "global": authorized_company_ids is None}),
                rating,
                notes,
            ),
        ).fetchone()
        memory = None
        if rating == "Save as Known Fix":
            answer = conn.execute("SELECT answer FROM assistant_answers WHERE id=%s", (answer_id,)).fetchone()
            memory = conn.execute(
                """
                INSERT INTO curated_memory(title, body, actor_username, effective_scope, status)
                VALUES (%s, %s, %s, %s, 'pending_review')
                RETURNING id, status
                """,
                (
                    f"Known fix candidate from answer {answer_id}",
                    answer["answer"] if answer else "",
                    actor_username,
                    Jsonb({"company_ids": authorized_company_ids, "global": authorized_company_ids is None}),
                ),
            ).fetchone()
    return {"feedback_id": feedback["id"], "curated_memory": memory}


def pending_memory() -> list[dict[str, Any]]:
    init_schema()
    with db_connection() as conn:
        return list(conn.execute("SELECT * FROM curated_memory WHERE status='pending_review' ORDER BY id DESC").fetchall())
