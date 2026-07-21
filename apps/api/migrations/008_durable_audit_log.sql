CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    target TEXT,
    outcome TEXT NOT NULL DEFAULT 'success',
    scope JSONB NOT NULL DEFAULT '{}',
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS actor TEXT;
ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS target TEXT;
ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS outcome TEXT NOT NULL DEFAULT 'success';
ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS scope JSONB NOT NULL DEFAULT '{}';
ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}';

CREATE INDEX IF NOT EXISTS audit_log_created_at_idx
    ON audit_log(created_at DESC, id DESC);

CREATE INDEX IF NOT EXISTS audit_log_actor_created_idx
    ON audit_log(actor, created_at DESC);

CREATE INDEX IF NOT EXISTS audit_log_action_outcome_idx
    ON audit_log(action, outcome, created_at DESC);
