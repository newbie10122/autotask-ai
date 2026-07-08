from __future__ import annotations

import time
from typing import Any

from psycopg.types.json import Jsonb

from .answer_guardrails import WEAK_EVIDENCE_MESSAGE, build_guarded_answer
from .config import settings
from .db import db_connection, init_schema
from .ollama import OllamaUnavailable, chat, embed_text
from .security import redact_sensitive_content


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"


def _confidence_label(score: float) -> str:
    if score >= 0.75:
        return "High"
    if score >= 0.45:
        return "Medium"
    return "Low"


def ask_assistant(question: str, mode: str = "ticket_history_only", limit: int = 5) -> dict[str, Any]:
    init_schema()
    started = time.monotonic()
    limit = min(max(limit, 1), 12)
    with db_connection() as conn:
        query_row = conn.execute(
            "INSERT INTO assistant_queries(query, mode, model_name) VALUES (%s, %s, %s) RETURNING id",
            (question, mode, settings.ollama_chat_model),
        ).fetchone()
    query_id = query_row["id"]
    sources: list[dict[str, Any]] = []
    try:
        embedding = embed_text(question)
        with db_connection() as conn:
            sources = list(
                conn.execute(
                    """
                    SELECT dc.id AS chunk_id, dc.content, dc.source_metadata,
                           t.id AS ticket_pk, t.autotask_id, t.ticket_number,
                           1 - (de.embedding <=> %s::vector) AS score
                    FROM document_embeddings de
                    JOIN document_chunks dc ON dc.id = de.chunk_id
                    LEFT JOIN autotask_tickets t ON (dc.source_metadata->>'ticket_id')::bigint = t.autotask_id
                    WHERE de.model_name=%s
                      AND dc.is_active
                    ORDER BY de.embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (_vector_literal(embedding), settings.ollama_embedding_model, _vector_literal(embedding), limit),
                ).fetchall()
            )
    except OllamaUnavailable:
        sources = []

    if not sources:
        with db_connection() as conn:
            sources = list(
                conn.execute(
                    """
                    SELECT dc.id AS chunk_id, dc.content, dc.source_metadata,
                           t.id AS ticket_pk, t.autotask_id, t.ticket_number,
                           ts_rank_cd(to_tsvector('english', dc.content), plainto_tsquery('english', %s)) AS score
                    FROM document_chunks dc
                    LEFT JOIN autotask_tickets t ON (dc.source_metadata->>'ticket_id')::bigint = t.autotask_id
                    WHERE dc.is_active
                      AND to_tsvector('english', dc.content) @@ plainto_tsquery('english', %s)
                    ORDER BY score DESC
                    LIMIT %s
                    """,
                    (question, question, limit),
                ).fetchall()
            )

    best_score = float(sources[0]["score"] or 0) if sources else 0.0
    tickets = [
        str(source.get("ticket_number") or source.get("autotask_id"))
        for source in sources
        if source.get("ticket_number") or source.get("autotask_id")
    ]
    weak = not sources or best_score < 0.05
    context = "\n\n---\n\n".join(redact_sensitive_content(source["content"]) for source in sources)
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
        prompt = (
            "Answer using only the CompuOne ticket-history context below. "
            "Keep ticket history separate from general IT guidance. "
            "Use this exact section format: Confidence, From CompuOne Ticket History, "
            "General IT Guidance, Suggested Next Steps, Based on Tickets, Warnings.\n\n"
            f"Question:\n{question}\n\nContext:\n{context}\n"
        )
        try:
            generated = chat(prompt)
        except OllamaUnavailable:
            generated = ""
        confidence = min(max(best_score, 0.35), 0.95)
        if generated and "From CompuOne Ticket History" in generated:
            answer = redact_sensitive_content(generated)
        else:
            answer = build_guarded_answer(
                ticket_history=context[:1600],
                general_guidance="Use standard troubleshooting only after validating it against the cited ticket history.",
                next_steps=["Review the cited tickets.", "Verify environment details before applying a fix."],
                tickets=tickets,
                confidence=confidence,
            )

    duration_ms = int((time.monotonic() - started) * 1000)
    with db_connection() as conn:
        for source in sources:
            conn.execute(
                """
                INSERT INTO assistant_query_sources(query_id, chunk_id, ticket_id, score, source_metadata)
                SELECT %s, %s, %s, %s, %s
                WHERE EXISTS (SELECT 1 FROM document_chunks WHERE id=%s)
                """,
                (
                    query_id,
                    source.get("chunk_id"),
                    source.get("ticket_pk"),
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
            }
            for source in sources
        ],
        "warnings": [] if not weak else [WEAK_EVIDENCE_MESSAGE],
        "duration_ms": duration_ms,
    }


def store_feedback(answer_id: int, rating: str, notes: str | None = None) -> dict[str, Any]:
    init_schema()
    with db_connection() as conn:
        feedback = conn.execute(
            "INSERT INTO assistant_feedback(answer_id, rating, notes) VALUES (%s, %s, %s) RETURNING id",
            (answer_id, rating, notes),
        ).fetchone()
        memory = None
        if rating == "Save as Known Fix":
            answer = conn.execute("SELECT answer FROM assistant_answers WHERE id=%s", (answer_id,)).fetchone()
            memory = conn.execute(
                """
                INSERT INTO curated_memory(title, body, status)
                VALUES (%s, %s, 'pending_review')
                RETURNING id, status
                """,
                (f"Known fix candidate from answer {answer_id}", answer["answer"] if answer else ""),
            ).fetchone()
    return {"feedback_id": feedback["id"], "curated_memory": memory}


def pending_memory() -> list[dict[str, Any]]:
    init_schema()
    with db_connection() as conn:
        return list(conn.execute("SELECT * FROM curated_memory WHERE status='pending_review' ORDER BY id DESC").fetchall())
