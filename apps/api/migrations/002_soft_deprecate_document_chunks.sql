ALTER TABLE document_chunks
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS superseded_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS content_hash TEXT;

ALTER TABLE document_chunks
    ALTER COLUMN chunk_index DROP NOT NULL;

ALTER TABLE document_chunks
    DROP CONSTRAINT IF EXISTS document_chunks_document_id_chunk_index_key;

DROP INDEX IF EXISTS document_chunks_document_index_unique;

CREATE INDEX IF NOT EXISTS document_chunks_active_document_idx
    ON document_chunks(document_id, chunk_index)
    WHERE is_active;

CREATE INDEX IF NOT EXISTS document_chunks_content_hash_idx
    ON document_chunks(content_hash);

CREATE INDEX IF NOT EXISTS document_chunks_chunk_index_idx
    ON document_chunks(chunk_index);

CREATE INDEX IF NOT EXISTS document_chunks_active_content_idx
    ON document_chunks USING gin(to_tsvector('english', content))
    WHERE is_active;
