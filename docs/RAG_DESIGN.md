# RAG and Answer Guardrails

Autotask AI is retrieval-first. Live questions search local indexed ticket history and documents; they do not call Autotask.

Every chunk must retain source metadata, including source type, Autotask IDs where applicable, ticket number, company, timestamps, and extraction lineage. Answers include confidence and related ticket IDs.

Required answer sections:

- Confidence: High / Medium / Low
- From CompuOne Ticket History
- General IT Guidance
- Suggested Next Steps
- Based on Tickets
- Warnings

When matching ticket evidence is weak, the assistant must say:

> I do not have enough matching CompuOne ticket history.

Feedback options are stored exactly as:

- Good
- Bad
- Needs Edit
- Save as Known Fix

Curated memory is not authoritative when created. It remains `pending_review` until an Admin approves it.

Pipeline:

1. Autotask Companies, Tickets, and TicketNotes are pulled read-only and stored with raw JSON.
2. Ticket and note text is normalized into `documents`.
3. `document_chunks` stores chunk text and source metadata.
4. The embedding worker sends chunks to Ollama and stores pgvector embeddings in `document_embeddings`.
5. `/api/assistant/ask` embeds the question, retrieves similar chunks, falls back to keyword search where practical, and sends only retrieved context to Ollama.
6. Feedback is stored in `assistant_feedback`; Save as Known Fix creates a `curated_memory` candidate with `pending_review` status.

Document rebuilds never hard-delete chunks. When ticket text changes, new active chunks are inserted and old chunks are marked inactive with `superseded_at`, so prior `assistant_query_sources` rows continue to resolve for answer/source audit history. Search and embedding workers use active chunks only.

Chunks are deterministically classified during document creation. Survey emails, completion emails, autoresponders, notification boilerplate, unsubscribe footers, and low-value email headers remain stored for audit but are marked `is_noise=true` and excluded from default assistant search and embedding work. Human troubleshooting and resolution chunks receive higher quality scores and are preferred in retrieval.

Questions about common or recurring issues are routed to local ticket analytics rather than raw semantic retrieval. The assistant aggregates synced Autotask tickets by category, issue, subissue, queue, and representative tickets, then returns counts in the required recurring-issue format.

## Noise Filtering Before Full Embedding

Raw tickets and notes can be synced first. Before a large document or embedding pass, run document build and chunk classification on a bounded sample, inspect `/api/knowledge/noise-report`, then reclassify existing chunks as rules improve.

Noisy chunks are retained for audit history and prior answer-source references. They are not hard-deleted. Default retrieval and embeddings use only active non-noise chunks; set `include_noise=true` on the assistant request only for debugging, and set `EMBED_NOISE_CHUNKS=true` only for explicit admin experiments.

Recurring issue questions use deterministic analytics over synced ticket fields and representative tickets. They should not be answered by dumping arbitrary semantic chunks.

The sensitive content scanner flags obvious passwords, API keys, private keys, SSNs, credit cards, and VPN shared secrets. Detected secrets must be redacted from generated answers.
