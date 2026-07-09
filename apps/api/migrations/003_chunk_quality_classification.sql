ALTER TABLE document_chunks
    ADD COLUMN IF NOT EXISTS knowledge_class TEXT NOT NULL DEFAULT 'unknown',
    ADD COLUMN IF NOT EXISTS quality_score NUMERIC(5,3) NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS is_noise BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS noise_reason TEXT,
    ADD COLUMN IF NOT EXISTS classified_at TIMESTAMPTZ;

ALTER TABLE document_chunks
    ALTER COLUMN quality_score SET DEFAULT 0;

CREATE INDEX IF NOT EXISTS document_chunks_active_non_noise_idx
    ON document_chunks(document_id, knowledge_class, quality_score DESC)
    WHERE is_active AND NOT is_noise;

CREATE INDEX IF NOT EXISTS document_chunks_knowledge_class_idx
    ON document_chunks(knowledge_class);

CREATE INDEX IF NOT EXISTS document_chunks_quality_score_idx
    ON document_chunks(quality_score DESC);

CREATE INDEX IF NOT EXISTS document_chunks_is_noise_idx
    ON document_chunks(is_noise);

CREATE INDEX IF NOT EXISTS document_chunks_active_document_source_idx
    ON document_chunks(document_id, chunk_index, quality_score DESC)
    WHERE is_active;

CREATE INDEX IF NOT EXISTS document_chunks_noise_idx
    ON document_chunks(is_noise, knowledge_class)
    WHERE is_active;
