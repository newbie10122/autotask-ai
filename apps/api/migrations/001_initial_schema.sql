CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS roles (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE CHECK (name IN ('Admin', 'Technician', 'ReadOnly'))
);

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role_id BIGINT NOT NULL REFERENCES roles(id),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    actor_user_id UUID REFERENCES users(id),
    action TEXT NOT NULL,
    target_type TEXT,
    target_id TEXT,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

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
);

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
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    called_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS autotask_companies (
    id BIGSERIAL PRIMARY KEY,
    autotask_id BIGINT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    raw JSONB NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS autotask_contacts (
    id BIGSERIAL PRIMARY KEY,
    autotask_id BIGINT NOT NULL UNIQUE,
    company_id BIGINT REFERENCES autotask_companies(id),
    display_name TEXT,
    email TEXT,
    raw JSONB NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS autotask_tickets (
    id BIGSERIAL PRIMARY KEY,
    autotask_id BIGINT NOT NULL UNIQUE,
    company_id BIGINT REFERENCES autotask_companies(id),
    contact_id BIGINT REFERENCES autotask_contacts(id),
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
);

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
);

CREATE TABLE IF NOT EXISTS autotask_time_entries (
    id BIGSERIAL PRIMARY KEY,
    autotask_id BIGINT NOT NULL UNIQUE,
    ticket_id BIGINT REFERENCES autotask_tickets(id),
    resource_name TEXT,
    summary TEXT,
    hours NUMERIC(8,2),
    created_at_autotask TIMESTAMPTZ,
    raw JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS autotask_assets (
    id BIGSERIAL PRIMARY KEY,
    autotask_id BIGINT NOT NULL UNIQUE,
    company_id BIGINT REFERENCES autotask_companies(id),
    asset_type TEXT,
    name TEXT,
    serial_number TEXT,
    raw JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS autotask_attachments (
    id BIGSERIAL PRIMARY KEY,
    autotask_id BIGINT NOT NULL UNIQUE,
    ticket_id BIGINT REFERENCES autotask_tickets(id),
    filename TEXT NOT NULL,
    content_type TEXT,
    storage_path TEXT,
    raw JSONB NOT NULL DEFAULT '{}'
);

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
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES documents(id),
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    source_metadata JSONB NOT NULL DEFAULT '{}',
    embedding_status TEXT NOT NULL DEFAULT 'pending',
    embedding_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(document_id, chunk_index)
);

CREATE TABLE IF NOT EXISTS document_embeddings (
    id BIGSERIAL PRIMARY KEY,
    chunk_id BIGINT NOT NULL REFERENCES document_chunks(id),
    embedding vector(768),
    model_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(chunk_id, model_name)
);

CREATE TABLE IF NOT EXISTS assistant_queries (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    query TEXT NOT NULL,
    mode TEXT NOT NULL DEFAULT 'normal',
    model_name TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS assistant_query_sources (
    id BIGSERIAL PRIMARY KEY,
    query_id BIGINT NOT NULL REFERENCES assistant_queries(id),
    chunk_id BIGINT REFERENCES document_chunks(id),
    ticket_id BIGINT REFERENCES autotask_tickets(id),
    score NUMERIC(8,5),
    source_metadata JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS assistant_answers (
    id BIGSERIAL PRIMARY KEY,
    query_id BIGINT NOT NULL REFERENCES assistant_queries(id),
    answer TEXT NOT NULL,
    confidence NUMERIC(4,3) NOT NULL,
    model_name TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS assistant_feedback (
    id BIGSERIAL PRIMARY KEY,
    answer_id BIGINT NOT NULL REFERENCES assistant_answers(id),
    user_id UUID REFERENCES users(id),
    rating TEXT NOT NULL CHECK (rating IN ('Good', 'Bad', 'Needs Edit', 'Save as Known Fix')),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS curated_memory (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending_review',
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS curated_memory_sources (
    id BIGSERIAL PRIMARY KEY,
    curated_memory_id BIGINT NOT NULL REFERENCES curated_memory(id),
    ticket_id BIGINT REFERENCES autotask_tickets(id),
    document_id BIGINT REFERENCES documents(id),
    source_metadata JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS sensitive_content_flags (
    id BIGSERIAL PRIMARY KEY,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    pattern TEXT NOT NULL,
    reviewed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS job_queue (
    id BIGSERIAL PRIMARY KEY,
    job_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    payload JSONB NOT NULL DEFAULT '{}',
    attempts INTEGER NOT NULL DEFAULT 0,
    run_after TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO roles(name) VALUES ('Admin'), ('Technician'), ('ReadOnly')
ON CONFLICT (name) DO NOTHING;
