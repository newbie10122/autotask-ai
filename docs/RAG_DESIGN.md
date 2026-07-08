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

The sensitive content scanner flags obvious passwords, API keys, private keys, SSNs, credit cards, and VPN shared secrets. Detected secrets must be redacted from generated answers.
