ALTER TABLE document_chunks
    ADD COLUMN IF NOT EXISTS knowledge_class TEXT NOT NULL DEFAULT 'unknown',
    ADD COLUMN IF NOT EXISTS quality_score NUMERIC(5,3) NOT NULL DEFAULT 0.5,
    ADD COLUMN IF NOT EXISTS is_noise BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS noise_reason TEXT;

CREATE INDEX IF NOT EXISTS document_chunks_active_non_noise_idx
    ON document_chunks(document_id, knowledge_class, quality_score DESC)
    WHERE is_active AND NOT is_noise;

CREATE INDEX IF NOT EXISTS document_chunks_noise_idx
    ON document_chunks(is_noise, knowledge_class)
    WHERE is_active;
