CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

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
);

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
);

CREATE INDEX IF NOT EXISTS job_runs_job_started_idx
    ON job_runs(job_name, started_at DESC);

CREATE INDEX IF NOT EXISTS job_runs_status_idx
    ON job_runs(status, started_at DESC);

CREATE TABLE IF NOT EXISTS job_locks (
    job_name TEXT PRIMARY KEY,
    run_id BIGINT,
    locked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    heartbeat_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    owner TEXT NOT NULL
);
