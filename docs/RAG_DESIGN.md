# RAG and Answer Guardrails

Autotask AI is retrieval-first. Live questions search local indexed ticket history and documents; they do not call Autotask.

Every chunk must retain source metadata, including source type, Autotask IDs where applicable, ticket number, company, timestamps, and extraction lineage. Answers include confidence and related ticket IDs.

Required answer sections:

- From CompuOne Ticket History
- General IT Guidance
- Suggested Next Steps
- Based on Tickets

When matching ticket evidence is weak, the assistant must say:

> I do not have enough matching CompuOne ticket history.

Feedback options are stored exactly as:

- Good
- Bad
- Needs Edit
- Save as Known Fix

Curated memory is not authoritative when created. It remains `pending_approval` until an Admin approves it.

The sensitive content scanner flags obvious passwords, API keys, private keys, SSNs, credit cards, and VPN shared secrets. Detected secrets must be redacted from generated answers.

