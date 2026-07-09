from __future__ import annotations

import hashlib
from typing import Any

from psycopg.types.json import Jsonb

from .db import db_connection, init_schema
from .knowledge_classifier import classify_chunk
from .security import find_sensitive_content


def _chunk_text(text: str, size: int = 1400, overlap: int = 160) -> list[str]:
    cleaned = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if len(cleaned) < 20:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        chunk = cleaned[start : start + size].strip()
        if len(chunk) >= 20:
            chunks.append(chunk)
        start += size - overlap
    return chunks


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _ticket_text(ticket: dict[str, Any], company_name: str | None, notes: list[dict[str, Any]]) -> str:
    parts = [
        f"Ticket Number: {ticket.get('ticket_number') or ticket.get('autotask_id')}",
        f"Title: {ticket.get('title') or ''}",
        f"Company: {company_name or ''}",
        f"Status: {ticket.get('status') or ''}",
        f"Priority: {ticket.get('priority') or ''}",
        f"Queue: {ticket.get('queue') or ''}",
        f"Category: {ticket.get('category') or ''}",
        f"Issue: {ticket.get('issue_type') or ''} / {ticket.get('subissue_type') or ''}",
        f"Description: {ticket.get('description') or ''}",
        f"Resolved/Completed: {ticket.get('completed_at_autotask') or ''}",
    ]
    if notes:
        parts.append("Ticket Notes:")
        for note in notes:
            parts.append(
                "\n".join(
                    [
                        f"Note Title: {note.get('title') or ''}",
                        f"Note Type: {note.get('note_type') or ''}",
                        f"Note Date: {note.get('created_at_autotask') or ''}",
                        f"Note Resource: {note.get('resource_name') or ''}",
                        f"Note Body: {note.get('body') or ''}",
                    ]
                )
            )
    return "\n".join(parts)


def create_documents_from_tickets(limit: int | None = None) -> dict[str, int]:
    init_schema()
    stats = {
        "documents": 0,
        "chunks": 0,
        "chunks_reused": 0,
        "chunks_superseded": 0,
        "chunks_reclassified": 0,
        "noise_chunks": 0,
        "sensitive_flags": 0,
    }
    with db_connection() as conn:
        tickets = conn.execute(
            """
            SELECT t.*, c.name AS company_name
            FROM autotask_tickets t
            LEFT JOIN autotask_companies c ON c.id = t.company_id
            ORDER BY t.autotask_id
            LIMIT %s
            """,
            (limit or 100000,),
        ).fetchall()
        for ticket in tickets:
            notes = conn.execute(
                """
                SELECT * FROM autotask_ticket_notes
                WHERE ticket_id=%s OR autotask_ticket_id=%s
                ORDER BY created_at_autotask NULLS LAST, autotask_id
                """,
                (ticket["id"], ticket["autotask_id"]),
            ).fetchall()
            text = _ticket_text(ticket, ticket.get("company_name"), notes)
            chunks = _chunk_text(text)
            if not chunks:
                continue
            document = conn.execute(
                """
                INSERT INTO documents(source_type, source_id, title, extracted_text, updated_at)
                VALUES ('autotask_ticket', %s, %s, %s, now())
                ON CONFLICT (source_type, source_id) DO UPDATE
                SET title=EXCLUDED.title, extracted_text=EXCLUDED.extracted_text, updated_at=now()
                RETURNING id
                """,
                (str(ticket["autotask_id"]), ticket.get("title") or ticket.get("ticket_number"), text),
            ).fetchone()
            stats["documents"] += 1
            active_chunks = conn.execute(
                """
                SELECT id, chunk_index, content_hash, content
                FROM document_chunks
                WHERE document_id=%s AND is_active
                ORDER BY chunk_index NULLS LAST, id
                """,
                (document["id"],),
            ).fetchall()
            new_hashes = [_content_hash(chunk) for chunk in chunks]
            active_hashes = [row["content_hash"] for row in active_chunks]
            if active_hashes == new_hashes and all(active_hashes):
                for row in active_chunks:
                    quality = classify_chunk(row["content"])
                    conn.execute(
                        """
                        UPDATE document_chunks
                        SET knowledge_class=%s, quality_score=%s, is_noise=%s, noise_reason=%s, classified_at=now()
                        WHERE id=%s
                        """,
                        (
                            quality["knowledge_class"],
                            quality["quality_score"],
                            quality["is_noise"],
                            quality["noise_reason"],
                            row["id"],
                        ),
                    )
                    stats["chunks_reclassified"] += 1
                    if quality["is_noise"]:
                        stats["noise_chunks"] += 1
                stats["chunks_reused"] += len(active_chunks)
                conn.execute("UPDATE autotask_tickets SET indexed_at=now() WHERE id=%s", (ticket["id"],))
                continue

            metadata = {
                "source_type": "autotask_ticket",
                "ticket_id": ticket["autotask_id"],
                "ticket_number": ticket.get("ticket_number"),
                "company_id": ticket.get("company_id"),
                "company_name": ticket.get("company_name"),
                "created_at": str(ticket.get("created_at_autotask") or ""),
                "modified_at": str(ticket.get("updated_at_autotask") or ""),
                "resolved_at": str(ticket.get("completed_at_autotask") or ""),
                "source_table": "autotask_tickets",
                "source_id": ticket["id"],
            }
            for index, chunk in enumerate(chunks):
                quality = classify_chunk(chunk)
                chunk_row = conn.execute(
                    """
                    INSERT INTO document_chunks(
                        document_id, chunk_index, content, source_metadata, content_hash,
                        is_active, knowledge_class, quality_score, is_noise, noise_reason, classified_at
                    )
                    VALUES (%s, %s, %s, %s, %s, TRUE, %s, %s, %s, %s, now())
                    RETURNING id
                    """,
                    (
                        document["id"],
                        index,
                        chunk,
                        Jsonb(metadata),
                        new_hashes[index],
                        quality["knowledge_class"],
                        quality["quality_score"],
                        quality["is_noise"],
                        quality["noise_reason"],
                    ),
                ).fetchone()
                stats["chunks"] += 1
                if quality["is_noise"]:
                    stats["noise_chunks"] += 1
                for pattern in find_sensitive_content(chunk):
                    conn.execute(
                        """
                        INSERT INTO sensitive_content_flags(source_type, source_id, pattern)
                        VALUES ('document_chunk', %s, %s)
                        """,
                        (str(chunk_row["id"]), pattern),
                    )
                    stats["sensitive_flags"] += 1
            old_active_ids = [row["id"] for row in active_chunks]
            if old_active_ids:
                updated = conn.execute(
                    """
                    UPDATE document_chunks
                    SET is_active=FALSE, superseded_at=now()
                    WHERE id = ANY(%s)
                    """,
                    (old_active_ids,),
                )
                stats["chunks_superseded"] += updated.rowcount or 0
            conn.execute("UPDATE autotask_tickets SET indexed_at=now() WHERE id=%s", (ticket["id"],))
    return stats


def reclassify_chunks(limit: int | None = None, include_inactive: bool = False) -> dict[str, Any]:
    init_schema()
    stats: dict[str, Any] = {
        "processed": 0,
        "useful": 0,
        "noise": 0,
        "unknown": 0,
        "by_knowledge_class": {},
    }
    with db_connection() as conn:
        chunks = conn.execute(
            """
            SELECT id, content
            FROM document_chunks
            WHERE (%s OR is_active)
            ORDER BY id
            LIMIT %s
            """,
            (include_inactive, limit or 100000),
        ).fetchall()
        for chunk in chunks:
            quality = classify_chunk(chunk["content"])
            conn.execute(
                """
                UPDATE document_chunks
                SET knowledge_class=%s,
                    quality_score=%s,
                    is_noise=%s,
                    noise_reason=%s,
                    classified_at=now()
                WHERE id=%s
                """,
                (
                    quality["knowledge_class"],
                    quality["quality_score"],
                    quality["is_noise"],
                    quality["noise_reason"],
                    chunk["id"],
                ),
            )
            knowledge_class = str(quality["knowledge_class"])
            stats["processed"] += 1
            stats["by_knowledge_class"][knowledge_class] = stats["by_knowledge_class"].get(knowledge_class, 0) + 1
            if quality["is_noise"]:
                stats["noise"] += 1
            elif knowledge_class == "unknown":
                stats["unknown"] += 1
            else:
                stats["useful"] += 1
    return stats


def noise_report() -> dict[str, Any]:
    init_schema()
    with db_connection() as conn:
        totals = conn.execute(
            """
            SELECT
              count(DISTINCT dc.id) FILTER (WHERE dc.is_active)::int AS total_active_chunks,
              count(DISTINCT dc.id) FILTER (WHERE dc.is_active AND dc.is_noise)::int AS active_noise_chunks,
              count(DISTINCT dc.id) FILTER (WHERE dc.is_active AND NOT dc.is_noise AND dc.knowledge_class <> 'unknown')::int AS active_useful_chunks,
              count(DISTINCT dc.id) FILTER (WHERE dc.is_active AND dc.knowledge_class = 'unknown')::int AS unknown_chunks,
              count(DISTINCT dc.id) FILTER (WHERE dc.is_active AND NOT dc.is_noise)::int AS embedding_eligible_chunks,
              count(DISTINCT dc.id) FILTER (
                WHERE dc.is_active
                  AND NOT dc.is_noise
                  AND de.id IS NULL
              )::int AS eligible_missing_embeddings
            FROM document_chunks dc
            LEFT JOIN document_embeddings de
              ON de.chunk_id = dc.id
            """
        ).fetchone()
        classes = conn.execute(
            """
            SELECT knowledge_class, count(*)::int AS count
            FROM document_chunks
            WHERE is_active
            GROUP BY knowledge_class
            ORDER BY count DESC, knowledge_class
            """
        ).fetchall()
        reasons = conn.execute(
            """
            SELECT noise_reason, count(*)::int AS count
            FROM document_chunks
            WHERE is_active AND is_noise AND noise_reason IS NOT NULL
            GROUP BY noise_reason
            ORDER BY count DESC, noise_reason
            LIMIT 20
            """
        ).fetchall()
    return {
        **dict(totals or {}),
        "counts_by_knowledge_class": classes,
        "top_noise_reasons": reasons,
    }
