from __future__ import annotations

import hashlib
from typing import Any

from psycopg.types.json import Jsonb

from .db import db_connection, init_schema
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
    stats = {"documents": 0, "chunks": 0, "chunks_reused": 0, "chunks_superseded": 0, "sensitive_flags": 0}
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
                SELECT id, chunk_index, content_hash
                FROM document_chunks
                WHERE document_id=%s AND is_active
                ORDER BY chunk_index NULLS LAST, id
                """,
                (document["id"],),
            ).fetchall()
            new_hashes = [_content_hash(chunk) for chunk in chunks]
            active_hashes = [row["content_hash"] for row in active_chunks]
            if active_hashes == new_hashes and all(active_hashes):
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
                chunk_row = conn.execute(
                    """
                    INSERT INTO document_chunks(document_id, chunk_index, content, source_metadata, content_hash, is_active)
                    VALUES (%s, %s, %s, %s, %s, TRUE)
                    RETURNING id
                    """,
                    (document["id"], index, chunk, Jsonb(metadata), new_hashes[index]),
                ).fetchone()
                stats["chunks"] += 1
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
