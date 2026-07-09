ALTER TABLE autotask_tickets
    ADD COLUMN IF NOT EXISTS ticket_class TEXT,
    ADD COLUMN IF NOT EXISTS is_support_issue BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS is_system_generated BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS analytics_exclude BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS analytics_exclude_reason TEXT,
    ADD COLUMN IF NOT EXISTS classified_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS autotask_tickets_ticket_class_idx
    ON autotask_tickets(ticket_class);

CREATE INDEX IF NOT EXISTS autotask_tickets_analytics_exclude_idx
    ON autotask_tickets(analytics_exclude, updated_at_autotask DESC NULLS LAST);

CREATE INDEX IF NOT EXISTS autotask_tickets_issue_class_idx
    ON autotask_tickets(ticket_class, category, issue_type, subissue_type);

CREATE INDEX IF NOT EXISTS autotask_tickets_classified_at_idx
    ON autotask_tickets(classified_at DESC NULLS LAST);

CREATE TABLE IF NOT EXISTS autotask_reference_values (
    field_name TEXT NOT NULL,
    value TEXT NOT NULL,
    label TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'local',
    raw JSONB NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (field_name, value)
);

CREATE INDEX IF NOT EXISTS autotask_reference_values_field_idx
    ON autotask_reference_values(field_name, label);
