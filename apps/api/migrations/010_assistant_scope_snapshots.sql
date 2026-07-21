ALTER TABLE assistant_queries ADD COLUMN IF NOT EXISTS actor_username TEXT;
ALTER TABLE assistant_queries ADD COLUMN IF NOT EXISTS effective_scope JSONB NOT NULL DEFAULT '{}';

ALTER TABLE assistant_query_sources
    ADD COLUMN IF NOT EXISTS company_id BIGINT REFERENCES autotask_companies(id);

ALTER TABLE assistant_feedback ADD COLUMN IF NOT EXISTS actor_username TEXT;
ALTER TABLE assistant_feedback ADD COLUMN IF NOT EXISTS effective_scope JSONB NOT NULL DEFAULT '{}';

ALTER TABLE curated_memory ADD COLUMN IF NOT EXISTS actor_username TEXT;
ALTER TABLE curated_memory ADD COLUMN IF NOT EXISTS effective_scope JSONB NOT NULL DEFAULT '{}';

CREATE INDEX IF NOT EXISTS assistant_queries_actor_created_idx
    ON assistant_queries(actor_username, created_at DESC);

CREATE INDEX IF NOT EXISTS assistant_query_sources_company_idx
    ON assistant_query_sources(company_id, query_id);

CREATE INDEX IF NOT EXISTS assistant_feedback_actor_created_idx
    ON assistant_feedback(actor_username, created_at DESC);
