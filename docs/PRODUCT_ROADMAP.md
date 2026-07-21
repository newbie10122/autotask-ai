# Autotask AI Product Roadmap

**Roadmap version:** 2.0  
**Management target:** 99% verified roadmap completion  
**Authority boundary:** Read-only Autotask until separately approved capabilities satisfy `AGENTS.md`

## Product purpose

Autotask AI is an internal CompuOne technician assistant that synchronizes authorized Autotask history locally, cleans and classifies it, retrieves relevant evidence, and uses local CPU-capable models plus deterministic analytics to help technicians resolve issues faster and improve service operations.

The project priorities are:

1. Protect customer data, client isolation, and read-only authority.
2. Make technicians faster using trustworthy local evidence.
3. Improve operational awareness and ticket health.
4. Add explainable prediction and routing recommendations only after the evidence foundation is certified.
5. Add customer-success intelligence after internal workflows are proven.

## Definition of 99% managed completion

The project may be described as 99% complete only when all release-critical milestones are `verified_complete`, no unresolved critical security/privacy/client-isolation/data-integrity risk remains, CI and Quality Streak evidence exists, rollback/recovery is proven for material capabilities, and the repository plus Second Brain projection are current.

Code presence alone does not count as verified completion. Each milestone requires applicable:

- acceptance and negative tests;
- authorization and client-isolation evidence;
- redaction and prompt-injection evidence;
- restart, recovery, idempotency, and rollback evidence;
- performance and resource measurements;
- independent verification for material changes;
- current implementation status, known risks, exact next prompt, and Second Brain receipt.

## Current implemented foundation

The repository currently contains substantial MVP implementation:

- FastAPI API and static technician/admin web interface.
- Docker services for web, API, PostgreSQL/pgvector, synchronization, document processing, embeddings, scheduling, nightly processing, and optional Ollama.
- Read-only Autotask company, ticket, and ticket-note synchronization with checkpoints and API-call history.
- PostgreSQL storage for tickets, notes, time-entry schema, documents, chunks, embeddings, queries, answers, feedback, memory candidates, settings, and job history.
- Ticket and note document creation with active/superseded chunk history.
- Noise filtering and ticket/chunk classification.
- Local embeddings, vector retrieval, lexical fallback, source limiting, weak-evidence handling, and CPU-model timeout fallback.
- Recurring-issue analytics.
- Operations scheduling, locks, pause controls, disk checks, API-threshold checks, and conservative defaults.
- Sensitive/private-entity redaction and basic read-only tests.
- Feedback that creates pending known-fix candidates.

These capabilities are implemented but not all are production-certified under `AGENTS.md`.

## Roadmap execution order

### Milestone 0 — Governance, status truth, and continuous validation

**Priority:** P0 — immediate  
**Dependency:** None  
**Status:** Active

Deliver:

- Merge this canonical roadmap into `main` and supersede obsolete roadmap drafts.
- Maintain `docs/implementation_status.md`, `docs/acceptance_criteria.md`, `docs/known_risks.md`, and `docs/codex_next_prompt.md`.
- Add GitHub Actions or equivalent CI for Python tests, import/compile checks, migration checks, secret/repository hygiene, read-only enforcement, redaction, prompt-injection, authorization/client isolation, and redacted Compose validation.
- Add machine-readable capability and milestone receipts where useful.
- Establish a production-certification matrix and three-clean-run Quality Streak records.
- Ensure every material milestone update produces the required sanitized Second Brain projection.

Exit criteria:

- Canonical roadmap and control files are current on the working branch/PR.
- CI runs automatically and reports a clear result.
- No milestone is marked complete without linked evidence.
- Second Brain synchronization state is recorded for material changes.

### Milestone 1 — Security, identity, isolation, and answer trust

**Priority:** P0 — release blocker  
**Dependency:** Milestone 0

Deliver:

1. Real authentication and session management.
2. Password hashing, disabled-user handling, expiration, login throttling, and secure cookie/token behavior.
3. Enforced Admin, Technician, and ReadOnly authorization on every API and UI action.
4. Persistent database-backed audit logging for identity, searches, answer sources, feedback, memory actions, settings, jobs, syncs, and denied actions.
5. Explicit user-to-company/client authorization scope.
6. Company/client scope carried through tickets, documents, chunks, embeddings, queries, citations, caches, analytics, and exports.
7. Fail-closed retrieval when client scope is absent or unauthorized.
8. Prompt-injection scanning of retrieved ticket/note content before context assembly.
9. Independent answer verification for citation sufficiency, client isolation, unsupported claims, secret leakage, prompt injection, and guidance labeling.
10. Security and policy-drift release check.

Exit criteria:

- Placeholder login/token behavior is removed.
- Unauthorized routes and cross-client retrieval are denied by tests and real integration checks.
- Audit evidence survives restart.
- Material answers fail closed when verification fails.
- Three consecutive clean security/isolation/answer-verifier runs are recorded.

### Milestone 2 — Complete read-only Autotask operational data

**Priority:** P1  
**Dependency:** Milestone 1 authorization/data-scope model

Confirm fields and implement resumable read-only synchronization for:

- time entries and total labor;
- ticket status and status history where available;
- SLA target, due, response, and resolution fields;
- ticket priority/queue history where available;
- customer and technician response timestamps;
- waiting state/reason;
- resources involved;
- related problem/outage/ticket relationships;
- configuration items/assets needed for operational context;
- reference values required to show labels instead of raw IDs.

Requirements:

- document source lineage and freshness;
- retain checkpoints, API-call budgets, retries, idempotency, and recovery;
- preserve read-only authority;
- avoid unbounded historical pulls;
- measure data completeness and unmapped fields.

Exit criteria:

- Required ticket-health fields are available locally or explicitly documented as unavailable.
- Backfill and recent synchronization are restart-safe and idempotent.
- Client scope is enforced throughout ingestion and storage.
- Three consecutive clean sync/recovery runs are recorded.

### Milestone 3 — Ticket Health Analytics

**Priority:** P1 — first major new user value  
**Dependency:** Milestone 2

Deliver technician and manager views, filters, APIs, and assistant routes for:

- ticket age;
- total labor hours;
- time since last technician action;
- time since last customer response;
- time waiting on customer, vendor, or technician;
- number of technicians/resources involved;
- customer-response count;
- SLA risk and overdue status;
- stalled tickets;
- tickets with unusually high labor relative to similar work;
- customers consuming disproportionate support time;
- clear drill-down to supporting tickets and calculations.

Prefer deterministic SQL/rules before model generation. Every calculated result must show freshness, scope, assumptions, and evidence.

Exit criteria:

- Core ticket-health questions return deterministic scoped results.
- Calculations have unit/integration tests and representative production-data validation.
- UI supports keyboard, responsive, empty, loading, error, and reduced-motion states.
- No raw client data appears outside authorized scope.

### Milestone 4 — Local CPU performance and Redis caching

**Priority:** P1  
**Dependency:** Milestones 1 and 3

Deliver:

- Redis service and health checks.
- Scoped cache keys including company/client, permissions, model, embedding, prompt, document/chunk version, and relevant configuration.
- Safe caching for operations status, reference data, ticket-health summaries, recurring-issue reports, and identical authorized retrievals.
- Explicit invalidation after synchronization, document rebuild, reclassification, embedding/model change, permission change, and memory promotion.
- Cache hit/miss, latency, memory, and stale-result metrics.
- CPU model benchmarks for normal and deep-dive paths.

Do not cache unverified generated answers by default. Any reusable answer cache requires verifier success, scope-safe keys, short TTLs, and explicit invalidation.

Exit criteria:

- Measurable latency/CPU improvement without cross-client leakage or stale evidence.
- Cache outage degrades safely to uncached behavior.
- Three consecutive clean cache/isolation/recovery runs are recorded.

### Milestone 5 — Real-time technician updates

**Priority:** P2  
**Dependency:** Milestone 4 event/cache infrastructure and Milestone 1 authorization

Add WebSocket or server-sent event delivery for authorized events such as:

- ticket assignment/reassignment discovered during synchronization;
- customer response;
- ticket status or priority change;
- AI analysis completion/failure;
- scheduled synchronization or knowledge-job completion/failure;
- data-freshness and stale-index warnings.

Requirements:

- authorized scoped subscriptions;
- reconnect and replay strategy;
- rate limits and backpressure;
- no event payload containing unnecessary customer data;
- safe behavior when Redis/event infrastructure is unavailable.

Exit criteria:

- Technicians receive scoped updates without manual refresh.
- Reconnect, duplicate, authorization-denial, and outage behavior are tested.

### Milestone 6 — Technician Performance Assistant

**Priority:** P2  
**Dependency:** Milestones 1 through 4

Expand the assistant from evidence search into reviewable technician guidance:

- next troubleshooting-step suggestions;
- related tickets and approved internal documents;
- missing-step detection;
- known-outage warnings;
- escalation recommendations;
- customer-ready update drafts;
- internal work-note drafts;
- evidence, confidence, warnings, and explicit missing information.

All drafts remain review-only. No Autotask writeback is permitted.

Exit criteria:

- Suggestions resolve to authorized evidence.
- Drafts are clearly labeled and never auto-submitted.
- Independent verifier, weak-evidence refusal, redaction, injection resistance, latency, and technician feedback metrics pass.

### Milestone 7 — Predictive Service Intelligence

**Priority:** P3  
**Dependency:** Certified data quality and Milestone 6 evidence framework

Start with explainable deterministic and lightweight statistical methods for:

- likely cause category;
- historically successful fixes;
- expected resolution-time range;
- escalation likelihood;
- wider outage/recurring-problem likelihood;
- recommended internal specialist, document, or vendor.

Every prediction must show:

- evidence and representative tickets;
- sample size and freshness;
- confidence/calibration;
- client scope;
- limitations and reason codes.

Exit criteria:

- Offline evaluation baselines and holdout tests are documented.
- Predictions outperform a defined simple baseline without unacceptable client or category bias.
- Low-confidence predictions abstain.

### Milestone 8 — Technician routing recommendations

**Priority:** P3  
**Dependency:** Milestone 7 and reliable workload/resource data

Recommend, but do not automatically assign, technicians based on:

- demonstrated skills and prior outcomes;
- current workload and availability;
- customer familiarity;
- category, priority, and escalation requirements;
- similar-ticket history;
- fairness and concentration safeguards.

Exit criteria:

- Recommendation accuracy and technician acceptance are measured.
- Every recommendation has evidence and reason codes.
- No Autotask assignment write occurs.
- Automatic routing remains a separately approved future capability with its own kill switch, rollback, idempotency, read-after-write verification, and Quality Streak.

### Milestone 9 — Customer Success Intelligence

**Priority:** P4 — after internal proof  
**Dependency:** Certified internal technician and operational milestones

Deliver authorized account-level insights for:

- rising ticket volume;
- recurring issues by customer, device, system, location, or service;
- replacement or redesign candidates;
- training opportunities;
- preventative maintenance recommendations;
- standards/documentation/project opportunities;
- customer health summaries for account review.

Exit criteria:

- Insights are explainable, scoped, fresh, and linked to evidence.
- Account-facing drafts are review-only.
- Business recommendations distinguish evidence from inference.

### Milestone 10 — Production certification and 99% closeout

**Priority:** P0 final gate  
**Dependency:** All release-target milestones

Deliver:

- full capability certification matrix;
- CI and three-run Quality Streak evidence for every production capability;
- restore/backup and rollback drills;
- restart and dependency-outage drills;
- performance/capacity benchmarks on `helix-prod-01` or approved target;
- monitoring, alerting, logs, retention, and operational runbooks;
- security/privacy/access-control policy-to-runtime review;
- deployment and rollback receipt;
- current Second Brain projection and source links;
- residual noncritical 1% backlog with explicit deferral rationale.

Exit criteria:

- No open critical blockers or release-critical unknowns.
- Required milestones are `verified_complete`.
- Remaining work is explicitly noncritical, deferred, and does not undermine security, correctness, read-only authority, or core success measures.

## Cross-cutting requirements

### Local-first CPU architecture

Every milestone must prefer retrieval, SQL, rules, similarity, caching, and lightweight models before expensive generation. Cloud models remain optional and require approved sanitization and model-egress controls.

### Read-only authority

No Autotask create, update, delete, note, ticket, contract, assignment, or other write operation is authorized by this roadmap. Future write capabilities require separate registration and explicit approval under `AGENTS.md`.

### Second Brain

After material state changes, update project-local truth first and then prepare the sanitized Second Brain projection according to `AGENTS.override.md`. Second Brain status must be recorded in every material receipt.

### Autonomous project management

The harness should continue from one eligible slice to the next, use parallel agents for independent non-overlapping work, update control files continuously, and notify John only when a critical blockage prevents all further safe progress.

## Success measures

Track at minimum:

- average technician search time;
- time to first useful action;
- normal and deep-dive response latency;
- ticket resolution time;
- repeat-ticket rate;
- known-fix use and approval rate;
- stalled, overdue, and high-labor tickets;
- retrieval citation sufficiency;
- verifier pass/fail rate;
- weak-evidence abstention accuracy;
- cross-client isolation failures, target zero;
- cache hit rate and avoided model calls;
- technician acceptance/correction rate;
- routing recommendation acceptance;
- proactive customer opportunities supported by evidence.
