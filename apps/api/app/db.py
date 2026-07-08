from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from .config import settings


@contextmanager
def db_connection() -> Iterator[psycopg.Connection]:
    conn = psycopg.connect(settings.database_url, row_factory=dict_row)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_schema() -> None:
    statements = [
        "CREATE EXTENSION IF NOT EXISTS vector",
        "CREATE EXTENSION IF NOT EXISTS pgcrypto",
        """
        CREATE TABLE IF NOT EXISTS autotask_sync_runs (
            id BIGSERIAL PRIMARY KEY,
            sync_type TEXT NOT NULL,
            status TEXT NOT NULL,
            resume_token TEXT,
            checkpoint JSONB NOT NULL DEFAULT '{}',
            records_processed INTEGER NOT NULL DEFAULT 0,
            pulled_count INTEGER NOT NULL DEFAULT 0,
            inserted_count INTEGER NOT NULL DEFAULT 0,
            updated_count INTEGER NOT NULL DEFAULT 0,
            failed_count INTEGER NOT NULL DEFAULT 0,
            last_error TEXT,
            started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            finished_at TIMESTAMPTZ
        )
        """,
        "ALTER TABLE autotask_sync_runs ADD COLUMN IF NOT EXISTS checkpoint JSONB NOT NULL DEFAULT '{}'",
        "ALTER TABLE autotask_sync_runs ADD COLUMN IF NOT EXISTS pulled_count INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE autotask_sync_runs ADD COLUMN IF NOT EXISTS inserted_count INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE autotask_sync_runs ADD COLUMN IF NOT EXISTS updated_count INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE autotask_sync_runs ADD COLUMN IF NOT EXISTS failed_count INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE autotask_sync_runs ADD COLUMN IF NOT EXISTS last_error TEXT",
        """
        CREATE TABLE IF NOT EXISTS autotask_api_calls (
            id BIGSERIAL PRIMARY KEY,
            sync_run_id BIGINT REFERENCES autotask_sync_runs(id),
            endpoint TEXT NOT NULL,
            method TEXT NOT NULL DEFAULT 'POST',
            record_count INTEGER NOT NULL DEFAULT 0,
            status_code INTEGER,
            duration_ms INTEGER,
            success BOOLEAN NOT NULL DEFAULT FALSE,
            error_message TEXT,
            called_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """,
        "ALTER TABLE autotask_api_calls ADD COLUMN IF NOT EXISTS duration_ms INTEGER",
        "ALTER TABLE autotask_api_calls ADD COLUMN IF NOT EXISTS success BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE autotask_api_calls ADD COLUMN IF NOT EXISTS error_message TEXT",
        "ALTER TABLE autotask_api_calls ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now()",
        """
        CREATE TABLE IF NOT EXISTS autotask_companies (
            id BIGSERIAL PRIMARY KEY,
            autotask_id BIGINT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            raw JSONB NOT NULL DEFAULT '{}',
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS autotask_tickets (
            id BIGSERIAL PRIMARY KEY,
            autotask_id BIGINT NOT NULL UNIQUE,
            company_id BIGINT REFERENCES autotask_companies(id),
            ticket_number TEXT,
            title TEXT,
            description TEXT,
            status TEXT,
            priority TEXT,
            queue TEXT,
            category TEXT,
            issue_type TEXT,
            subissue_type TEXT,
            assigned_resource_id BIGINT,
            assigned_resource_name TEXT,
            created_at_autotask TIMESTAMPTZ,
            updated_at_autotask TIMESTAMPTZ,
            completed_at_autotask TIMESTAMPTZ,
            raw JSONB NOT NULL DEFAULT '{}',
            indexed_at TIMESTAMPTZ
        )
        """,
        "ALTER TABLE autotask_tickets ADD COLUMN IF NOT EXISTS description TEXT",
        "ALTER TABLE autotask_tickets ADD COLUMN IF NOT EXISTS category TEXT",
        "ALTER TABLE autotask_tickets ADD COLUMN IF NOT EXISTS issue_type TEXT",
        "ALTER TABLE autotask_tickets ADD COLUMN IF NOT EXISTS subissue_type TEXT",
        "ALTER TABLE autotask_tickets ADD COLUMN IF NOT EXISTS assigned_resource_id BIGINT",
        "ALTER TABLE autotask_tickets ADD COLUMN IF NOT EXISTS assigned_resource_name TEXT",
        "ALTER TABLE autotask_tickets ADD COLUMN IF NOT EXISTS completed_at_autotask TIMESTAMPTZ",
        """
        CREATE TABLE IF NOT EXISTS autotask_ticket_notes (
            id BIGSERIAL PRIMARY KEY,
            autotask_id BIGINT NOT NULL UNIQUE,
            ticket_id BIGINT REFERENCES autotask_tickets(id),
            autotask_ticket_id BIGINT,
            title TEXT,
            note_type TEXT,
            body TEXT,
            resource_id BIGINT,
            resource_name TEXT,
            created_at_autotask TIMESTAMPTZ,
            updated_at_autotask TIMESTAMPTZ,
            raw JSONB NOT NULL DEFAULT '{}'
        )
        """,
        "ALTER TABLE autotask_ticket_notes ALTER COLUMN ticket_id DROP NOT NULL",
        "ALTER TABLE autotask_ticket_notes ADD COLUMN IF NOT EXISTS autotask_ticket_id BIGINT",
        "ALTER TABLE autotask_ticket_notes ADD COLUMN IF NOT EXISTS title TEXT",
        "ALTER TABLE autotask_ticket_notes ADD COLUMN IF NOT EXISTS resource_id BIGINT",
        "ALTER TABLE autotask_ticket_notes ADD COLUMN IF NOT EXISTS resource_name TEXT",
        "ALTER TABLE autotask_ticket_notes ADD COLUMN IF NOT EXISTS updated_at_autotask TIMESTAMPTZ",
        """
        CREATE TABLE IF NOT EXISTS documents (
            id BIGSERIAL PRIMARY KEY,
            source_type TEXT NOT NULL,
            source_id TEXT NOT NULL,
            title TEXT,
            storage_path TEXT,
            extracted_text TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(source_type, source_id)
        )
        """,
        "ALTER TABLE documents ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now()",
        "CREATE UNIQUE INDEX IF NOT EXISTS documents_source_unique ON documents(source_type, source_id)",
        """
        CREATE TABLE IF NOT EXISTS document_chunks (
            id BIGSERIAL PRIMARY KEY,
            document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            chunk_index INTEGER,
            content TEXT NOT NULL,
            source_metadata JSONB NOT NULL DEFAULT '{}',
            embedding_status TEXT NOT NULL DEFAULT 'pending',
            embedding_error TEXT,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            superseded_at TIMESTAMPTZ,
            content_hash TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(document_id, chunk_index)
        )
        """,
        "ALTER TABLE document_chunks ALTER COLUMN chunk_index DROP NOT NULL",
        "ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS embedding_status TEXT NOT NULL DEFAULT 'pending'",
        "ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS embedding_error TEXT",
        "ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE",
        "ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS superseded_at TIMESTAMPTZ",
        "ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS content_hash TEXT",
        "ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now()",
        "ALTER TABLE document_chunks DROP CONSTRAINT IF EXISTS document_chunks_document_id_chunk_index_key",
        "DROP INDEX IF EXISTS document_chunks_document_index_unique",
        "CREATE INDEX IF NOT EXISTS document_chunks_active_document_idx ON document_chunks(document_id, chunk_index) WHERE is_active",
        "CREATE INDEX IF NOT EXISTS document_chunks_content_hash_idx ON document_chunks(content_hash)",
        "CREATE INDEX IF NOT EXISTS document_chunks_chunk_index_idx ON document_chunks(chunk_index)",
        """
        CREATE TABLE IF NOT EXISTS document_embeddings (
            id BIGSERIAL PRIMARY KEY,
            chunk_id BIGINT NOT NULL REFERENCES document_chunks(id) ON DELETE CASCADE,
            embedding vector(768),
            model_name TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(chunk_id, model_name)
        )
        """,
        "ALTER TABLE document_embeddings ALTER COLUMN embedding TYPE vector(768)",
        "CREATE UNIQUE INDEX IF NOT EXISTS document_embeddings_chunk_model_unique ON document_embeddings(chunk_id, model_name)",
        """
        CREATE TABLE IF NOT EXISTS assistant_queries (
            id BIGSERIAL PRIMARY KEY,
            query TEXT NOT NULL,
            mode TEXT NOT NULL DEFAULT 'normal',
            model_name TEXT,
            duration_ms INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """,
        "ALTER TABLE assistant_queries ADD COLUMN IF NOT EXISTS model_name TEXT",
        "ALTER TABLE assistant_queries ADD COLUMN IF NOT EXISTS duration_ms INTEGER",
        """
        CREATE TABLE IF NOT EXISTS assistant_query_sources (
            id BIGSERIAL PRIMARY KEY,
            query_id BIGINT NOT NULL REFERENCES assistant_queries(id) ON DELETE CASCADE,
            chunk_id BIGINT REFERENCES document_chunks(id),
            ticket_id BIGINT REFERENCES autotask_tickets(id),
            score NUMERIC(8,5),
            source_metadata JSONB NOT NULL DEFAULT '{}'
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS assistant_answers (
            id BIGSERIAL PRIMARY KEY,
            query_id BIGINT NOT NULL REFERENCES assistant_queries(id) ON DELETE CASCADE,
            answer TEXT NOT NULL,
            confidence NUMERIC(4,3) NOT NULL,
            model_name TEXT,
            duration_ms INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """,
        "ALTER TABLE assistant_answers ADD COLUMN IF NOT EXISTS model_name TEXT",
        "ALTER TABLE assistant_answers ADD COLUMN IF NOT EXISTS duration_ms INTEGER",
        """
        CREATE TABLE IF NOT EXISTS assistant_feedback (
            id BIGSERIAL PRIMARY KEY,
            answer_id BIGINT NOT NULL REFERENCES assistant_answers(id) ON DELETE CASCADE,
            rating TEXT NOT NULL CHECK (rating IN ('Good', 'Bad', 'Needs Edit', 'Save as Known Fix')),
            notes TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS curated_memory (
            id BIGSERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending_review',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """,
        "ALTER TABLE curated_memory ALTER COLUMN status SET DEFAULT 'pending_review'",
        """
        CREATE TABLE IF NOT EXISTS sensitive_content_flags (
            id BIGSERIAL PRIMARY KEY,
            source_type TEXT NOT NULL,
            source_id TEXT NOT NULL,
            pattern TEXT NOT NULL,
            reviewed BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """,
        "CREATE INDEX IF NOT EXISTS document_chunks_content_idx ON document_chunks USING gin(to_tsvector('english', content))",
        "CREATE INDEX IF NOT EXISTS document_chunks_active_content_idx ON document_chunks USING gin(to_tsvector('english', content)) WHERE is_active",
    ]
    with db_connection() as conn:
        for statement in statements:
            conn.execute(statement)


def database_available() -> bool:
    try:
        with db_connection() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False
