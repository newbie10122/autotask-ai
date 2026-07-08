from __future__ import annotations

from typing import Any

from .config import settings
from .db import db_connection, init_schema
from .ollama import OllamaUnavailable, embed_text


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"


def run_embedding_batch(limit: int | None = None) -> dict[str, Any]:
    init_schema()
    stats = {"processed": 0, "embedded": 0, "failed": 0, "error": None}
    batch_size = limit or settings.embedding_batch_size
    with db_connection() as conn:
        chunks = conn.execute(
            """
            SELECT dc.id, dc.content
            FROM document_chunks dc
            LEFT JOIN document_embeddings de
              ON de.chunk_id = dc.id AND de.model_name = %s
            WHERE de.id IS NULL
              AND dc.is_active
              AND dc.embedding_status IN ('pending', 'failed')
            ORDER BY dc.id
            LIMIT %s
            """,
            (settings.ollama_embedding_model, batch_size),
        ).fetchall()
    for chunk in chunks:
        stats["processed"] += 1
        try:
            embedding = embed_text(chunk["content"])
            with db_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO document_embeddings(chunk_id, embedding, model_name)
                    VALUES (%s, %s::vector, %s)
                    ON CONFLICT (chunk_id, model_name) DO UPDATE
                    SET embedding=EXCLUDED.embedding, created_at=now()
                    """,
                    (chunk["id"], _vector_literal(embedding), settings.ollama_embedding_model),
                )
                conn.execute(
                    "UPDATE document_chunks SET embedding_status='embedded', embedding_error=NULL WHERE id=%s",
                    (chunk["id"],),
                )
            stats["embedded"] += 1
        except OllamaUnavailable as exc:
            stats["failed"] += 1
            stats["error"] = str(exc)
            with db_connection() as conn:
                conn.execute(
                    "UPDATE document_chunks SET embedding_status='failed', embedding_error=%s WHERE id=%s",
                    (str(exc)[:500], chunk["id"]),
                )
            break
    return stats
