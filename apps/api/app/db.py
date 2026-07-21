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
        "ALTER TABLE autotask_tickets ADD COLUMN IF NOT EXISTS ticket_class TEXT",
        "ALTER TABLE autotask_tickets ADD COLUMN IF NOT EXISTS is_support_issue BOOLEAN NOT NULL DEFAULT TRUE",
        "ALTER TABLE autotask_tickets ADD COLUMN IF NOT EXISTS is_system_generated BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE autotask_tickets ADD COLUMN IF NOT EXISTS analytics_exclude BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE autotask_tickets ADD COLUMN IF NOT EXISTS analytics_exclude_reason TEXT",
        "ALTER TABLE autotask_tickets ADD COLUMN IF NOT EXISTS classified_at TIMESTAMPTZ",
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
        "CREATE INDEX IF NOT EXISTS autotask_ticket_notes_ticket_id_idx ON autotask_ticket_notes(ticket_id, created_at_autotask NULLS LAST, autotask_id)",
        "CREATE INDEX IF NOT EXISTS autotask_ticket_notes_autotask_ticket_id_idx ON autotask_ticket_notes(autotask_ticket_id, created_at_autotask NULLS LAST, autotask_id)",
        "CREATE INDEX IF NOT EXISTS autotask_tickets_autotask_id_idx ON autotask_tickets(autotask_id)",
        "CREATE INDEX IF NOT EXISTS autotask_tickets_ticket_class_idx ON autotask_tickets(ticket_class)",
        "CREATE INDEX IF NOT EXISTS autotask_tickets_analytics_exclude_idx ON autotask_tickets(analytics_exclude, updated_at_autotask DESC NULLS LAST)",
        "CREATE INDEX IF NOT EXISTS autotask_tickets_issue_class_idx ON autotask_tickets(ticket_class, category, issue_type, subissue_type)",
        "CREATE INDEX IF NOT EXISTS autotask_tickets_classified_at_idx ON autotask_tickets(classified_at DESC NULLS LAST)",
        """
        CREATE TABLE IF NOT EXISTS autotask_reference_values (
            field_name TEXT NOT NULL,
            value TEXT NOT NULL,
            label TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'local',
            raw JSONB NOT NULL DEFAULT '{}',
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (field_name, value)
        )
        """,
        "CREATE INDEX IF NOT EXISTS autotask_reference_values_field_idx ON autotask_reference_values(field_name, label)",
        """
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value JSONB NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS scheduled_jobs (
            job_name TEXT PRIMARY KEY,
            enabled BOOLEAN NOT NULL DEFAULT TRUE,
            cadence_seconds INTEGER,
            schedule TEXT,
            status TEXT NOT NULL DEFAULT 'idle',
            current_step TEXT,
            last_checkpoint JSONB NOT NULL DEFAULT '{}',
            last_error TEXT,
            last_started_at TIMESTAMPTZ,
            last_finished_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS job_runs (
            id BIGSERIAL PRIMARY KEY,
            job_name TEXT NOT NULL,
            status TEXT NOT NULL,
            started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            finished_at TIMESTAMPTZ,
            duration_ms INTEGER,
            pulled_count INTEGER NOT NULL DEFAULT 0,
            inserted_count INTEGER NOT NULL DEFAULT 0,
            updated_count INTEGER NOT NULL DEFAULT 0,
            failed_count INTEGER NOT NULL DEFAULT 0,
            last_checkpoint JSONB NOT NULL DEFAULT '{}',
            last_error TEXT,
            triggered_by TEXT NOT NULL DEFAULT 'scheduler',
            config_snapshot JSONB NOT NULL DEFAULT '{}',
            current_step TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """,
        "CREATE INDEX IF NOT EXISTS job_runs_job_started_idx ON job_runs(job_name, started_at DESC)",
        "CREATE INDEX IF NOT EXISTS job_runs_status_idx ON job_runs(status, started_at DESC)",
        """
        CREATE TABLE IF NOT EXISTS job_locks (
            job_name TEXT PRIMARY KEY,
            run_id BIGINT,
            locked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            heartbeat_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            owner TEXT NOT NULL
        )
        """,
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
            knowledge_class TEXT NOT NULL DEFAULT 'unknown',
            quality_score NUMERIC(5,3) NOT NULL DEFAULT 0,
            is_noise BOOLEAN NOT NULL DEFAULT FALSE,
            noise_reason TEXT,
            classified_at TIMESTAMPTZ,
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
        "ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS knowledge_class TEXT NOT NULL DEFAULT 'unknown'",
        "ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS quality_score NUMERIC(5,3) NOT NULL DEFAULT 0",
        "ALTER TABLE document_chunks ALTER COLUMN quality_score SET DEFAULT 0",
        "ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS is_noise BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS noise_reason TEXT",
        "ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS classified_at TIMESTAMPTZ",
        "ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now()",
        "ALTER TABLE document_chunks DROP CONSTRAINT IF EXISTS document_chunks_document_id_chunk_index_key",
        "DROP INDEX IF EXISTS document_chunks_document_index_unique",
        "CREATE INDEX IF NOT EXISTS document_chunks_active_document_idx ON document_chunks(document_id, chunk_index) WHERE is_active",
        "CREATE INDEX IF NOT EXISTS document_chunks_content_hash_idx ON document_chunks(content_hash)",
        "CREATE INDEX IF NOT EXISTS document_chunks_chunk_index_idx ON document_chunks(chunk_index)",
        "CREATE INDEX IF NOT EXISTS document_chunks_active_non_noise_idx ON document_chunks(document_id, knowledge_class, quality_score DESC) WHERE is_active AND NOT is_noise",
        "CREATE INDEX IF NOT EXISTS document_chunks_knowledge_class_idx ON document_chunks(knowledge_class)",
        "CREATE INDEX IF NOT EXISTS document_chunks_quality_score_idx ON document_chunks(quality_score DESC)",
        "CREATE INDEX IF NOT EXISTS document_chunks_is_noise_idx ON document_chunks(is_noise)",
        "CREATE INDEX IF NOT EXISTS document_chunks_active_document_source_idx ON document_chunks(document_id, chunk_index, quality_score DESC) WHERE is_active",
        "CREATE INDEX IF NOT EXISTS document_chunks_noise_idx ON document_chunks(is_noise, knowledge_class) WHERE is_active",
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
        """
        CREATE TABLE IF NOT EXISTS app_users (
            id BIGSERIAL PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            roles JSONB NOT NULL DEFAULT '["ReadOnly"]',
            disabled BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            last_login_at TIMESTAMPTZ
        )
        """,
        "CREATE INDEX IF NOT EXISTS app_users_disabled_idx ON app_users(disabled)",
        """
        CREATE TABLE IF NOT EXISTS app_login_attempts (
            id BIGSERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            ip_address TEXT,
            success BOOLEAN NOT NULL DEFAULT FALSE,
            failure_reason TEXT,
            attempted_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """,
        "CREATE INDEX IF NOT EXISTS app_login_attempts_username_time_idx ON app_login_attempts(username, attempted_at DESC)",
        "CREATE INDEX IF NOT EXISTS app_login_attempts_ip_time_idx ON app_login_attempts(ip_address, attempted_at DESC)",
        """
        CREATE TABLE IF NOT EXISTS audit_log (
            id BIGSERIAL PRIMARY KEY,
            actor TEXT NOT NULL,
            action TEXT NOT NULL,
            target TEXT,
            outcome TEXT NOT NULL DEFAULT 'success',
            scope JSONB NOT NULL DEFAULT '{}',
            metadata JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """,
        "ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS actor TEXT",
        "ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS target TEXT",
        "ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS outcome TEXT NOT NULL DEFAULT 'success'",
        "ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS scope JSONB NOT NULL DEFAULT '{}'",
        "ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'",
        "CREATE INDEX IF NOT EXISTS audit_log_created_at_idx ON audit_log(created_at DESC, id DESC)",
        "CREATE INDEX IF NOT EXISTS audit_log_actor_created_idx ON audit_log(actor, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS audit_log_action_outcome_idx ON audit_log(action, outcome, created_at DESC)",
        """
        CREATE TABLE IF NOT EXISTS app_user_company_scopes (
            username TEXT NOT NULL REFERENCES app_users(username) ON DELETE CASCADE,
            company_id BIGINT NOT NULL REFERENCES autotask_companies(id) ON DELETE CASCADE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (username, company_id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS app_user_company_scopes_company_idx ON app_user_company_scopes(company_id)",
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
