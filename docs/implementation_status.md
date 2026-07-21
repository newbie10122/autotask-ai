# Autotask AI Implementation Status

**Updated:** 2026-07-21  
**Management target:** 99% verified roadmap completion  
**Current state:** `partial`  
**Active milestone:** Milestone 1 — Security, identity, isolation, and answer trust

## Status confidence

The repository has a substantial implemented MVP foundation, but no roadmap milestone is yet marked `verified_complete` under `AGENTS.md`. Current verified completion cannot be represented honestly as a percentage until acceptance evidence, the capability certification matrix, and Quality Streak records are established.

## Implemented foundation

- Canonical `main` is `a4f02bc0987dfe0ba9cb0fd6164d67310acb2cc6`, which merged PR `newbie10122/autotask-ai#16`.
- GitHub Actions CI workflow and local validation harness were merged through PR `newbie10122/autotask-ai#3`.
- `scripts/validate-ci.sh` runs redacted Compose validation, migration ordering, API image build, API/worker Python compilation, full pytest, static web JavaScript syntax checks, and browser UI RBAC smoke tests.
- `docs/CI_VALIDATION.md` defines the local/CI validation command and a capability-certification receipt format requiring explicit Autotask write-back disclosure.
- `docs/CAPABILITY_CERTIFICATION.md` now tracks capability states, evidence, Quality Streak status, remaining certification work, and the explicit fact that no milestone is `verified_complete`.
- FastAPI API and technician/admin web interface.
- Dockerized web, API, PostgreSQL/pgvector, synchronization, document, embedding, scheduler, nightly, and optional Ollama services.
- Read-only company, ticket, and ticket-note synchronization with checkpoints.
- Local document/chunk generation, classification, embeddings, vector retrieval, lexical fallback, and CPU answer generation.
- Weak-evidence response and timeout fallback.
- Recurring-issue analytics.
- Operations scheduler with locks, pause, disk, conflict, Autotask-threshold controls, scheduler heartbeat/status caching, and bounded related-data gap jobs.
- Automated local TimeEntries and TicketHistory ingestion is present for recent sync, open-ticket gap repair, and estate-wide gap sweeps.
- Sensitive/private-entity redaction and read-only enforcement tests.
- Pending known-fix candidate creation.
- Milestone 1 auth foundation adds PBKDF2 password hashing, signed expiring session tokens, disabled-user and throttling hooks, optional fail-closed API route authentication, admin-operation role denial tests, pre-prompt prompt-injection/secret source filtering, and deterministic answer-verifier citation checks.
- Milestone 1 durable-audit branch `agent/m1-durable-audit-scope-foundation` adds database-backed audit persistence, outcome/scope fields, and authorization-denial audit events.
- Milestone 1 company-scope branch `agent/m1-company-scope-foundation` adds user-company scope tables, fail-closed assistant/analytics route scope checks, and scoped retrieval/recurring-analytics filters.
- Milestone 1 scope-snapshot branch `agent/m1-scope-snapshots-foundation` adds actor/effective-scope snapshots for assistant queries, sources, feedback, and pending memory candidates.
- Milestone 1 verifier-scope branch `agent/m1-verifier-scope-foundation` adds deterministic out-of-scope source rejection in answer verification.
- Milestone 1 UI-auth branch `agent/m1-ui-auth-rbac-foundation` adds static-web token login/logout support, Bearer request headers, app-auth status, role-aware disabled controls, and clearer 401/403 messages.
- Milestone 1 route-authority branch `agent/m1-route-authority-audit-matrix` adds admin gates to manual sync/build/classify/Autotask probe/audit/memory routes, route inventory tests, ReadOnly denial audit coverage, direct database company-scope coverage, and static UI RBAC/accessibility contracts.
- Milestone 1 success-audit branch `agent/m1-success-audit-scope-linkage` adds centralized success-audit recording for material admin, analytics, assistant, and feedback actions with actor, role metadata, outcome, and effective scope.
- Milestone 1 verifier-failure branch `agent/m1-verifier-failure-audit` preserves fail-closed verifier reasons in fallback answers and records verifier-failure audit events with actor/scope metadata.
- Milestone 1 cache/export contract branch `agent/m1-cache-export-scope-contracts` adds a scoped-cache-key contract requiring authority class, roles, explicit scope, version, optional model/config inputs, and a route guard proving export/download endpoints are absent until classified.
- Milestone 1 unsupported-claim verifier branch `agent/m1-unsupported-claim-verifier` rejects unsupported ticket-history resolution claims when retrieved source evidence lacks meaningful overlap.
- Milestone 1 browser RBAC branch `agent/m1-browser-rbac-smoke` adds Playwright browser smoke coverage for anonymous, Admin, and ReadOnly UI authorization states.

## Verified gaps blocking production readiness

- Route authentication/RBAC is implemented as an opt-in foundation and sensitive mutating/admin-inspection API routes now have a tested authority matrix, but production defaults still keep app-route auth off.
- Audit logging is database-backed for foundation, denial, and first material success events, but identity/company-scope linkage is not yet complete across every workflow.
- Assistant retrieval, recurring-issue analytics, query rows, query sources, feedback, pending memory candidates, answer verification, static web controls, future scoped cache contracts, and first browser RBAC smoke coverage have scope/RBAC plumbing, but scope is not yet fully certified with accessibility checks or active scoped cache consumers.
- Prompt-injection scanning and deterministic answer verification have tests for citations, scope, secrets, injection, required sections, guidance labels, verifier-failure audit, and first unsupported ticket-history resolution claims; broader source sufficiency remains open.
- Capability-specific three-run Quality Streak evidence is not established; the validation harness has three browser-enabled clean evidence points recorded in `docs/CI_VALIDATION.md`.
- Governed memory approval/version/rollback workflow is incomplete.
- Ticket-health related-data synchronization is automated but not fully caught up across the historical estate; TimeEntries and TicketHistory coverage still require continued bounded scheduled sweeps and certification.

## Milestone table

| Milestone | State | Next evidence required |
|---|---|---|
| 0. Governance and continuous validation | partial | Certification matrix added and validation-harness streak recorded; capability Quality Streaks remain open |
| 1. Security, identity, isolation, answer trust | active | Complete durable audit, full route/UI RBAC, company scope wiring, verifier breadth, and three-run evidence |
| 2. Complete operational Autotask data | partial_foundation | TimeEntries/TicketHistory jobs restored; continue bounded catch-up and field certification |
| 3. Ticket Health Analytics | not_started | Deterministic APIs/UI with evidence |
| 4. Redis and CPU performance | not_started | Scoped cache design and benchmarks |
| 5. Real-time technician updates | not_started | Authorized event architecture |
| 6. Technician Performance Assistant | partial_foundation | Current RAG exists; guided/draft workflows not certified |
| 7. Predictive Service Intelligence | not_started | Certified data and evaluation baseline |
| 8. Routing recommendations | not_started | Resource/workload data and evaluation |
| 9. Customer Success Intelligence | not_started | Certified internal capabilities |
| 10. Production certification/99% closeout | not_started | All target milestones and evidence |

## Active execution queue

1. Add broader accessibility evidence and source-sufficiency certification.
2. Continue bounded TimeEntries/TicketHistory estate catch-up certification and status-duration/SLA source-lineage work.
3. Build capability-specific Quality Streak receipts without marking milestones complete prematurely.

Parallel-safe work after roadmap merge:

- Agent A: CI and repository validation.
- Agent B: authentication/RBAC design and negative tests.
- Agent C: client-scope data model and retrieval isolation analysis/tests.
- Agent D: prompt-injection and independent verifier contract/tests.
- Independent verifier: review threat model, overlap, integration order, and acceptance coverage.

Shared schema and integration changes must be serialized by the coordinator.

## Critical blockers

None currently identified for documentation and non-production implementation work. Production deployment, customer-data scope expansion, irreversible migrations, and any Autotask write capability remain approval-gated.

## Latest receipt — Certification matrix and validation-harness streak tracking

- **Slice:** Add governed capability certification matrix and current validation-harness streak tracking on branch `agent/m0-quality-streak-matrix` from canonical `main` `82d30d34032a42ff505de9ef6c88500c9a39b526`.
- **State:** `partial`; Milestone 0 governance evidence is improved, but no production capability or milestone is marked `verified_complete`.
- **Files changed:** `docs/CAPABILITY_CERTIFICATION.md`, `docs/CI_VALIDATION.md`, `apps/api/tests/test_repo_hygiene.py`, and project status docs.
- **Implemented:** Capability matrix tracks CI validation, auth/RBAC, durable audit, company isolation, answer safety, read-only TimeEntries/TicketHistory sync, and browser UI RBAC as partial or partial-foundation with evidence, streak state, and remaining certification work. `docs/CI_VALIDATION.md` records two browser-enabled validation-harness evidence points: local pre-merge validation and PR #17 GitHub Actions.
- **Validation:** Focused repository-hygiene tests passed with `13 passed`. Full `./scripts/validate-ci.sh` passed with redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `88 passed`, static web JavaScript syntax validation, Playwright browser UI RBAC smoke `3 passed`, and `git diff --check`.
- **Read-only evidence:** No sync jobs, production deployment, or Autotask write capability are involved.
- **Rollback:** Revert this branch commit; documentation-only plus test assertions.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Milestone 1 browser UI RBAC smoke

- **Slice:** Add repeatable Playwright browser evidence for static-web RBAC states on branch `agent/m1-browser-rbac-smoke` from canonical `main` `a4f02bc0987dfe0ba9cb0fd6164d67310acb2cc6`.
- **State:** `partial`; real browser RBAC behavior is now smoke-tested, but Milestone 1 still requires broader accessibility evidence, source-sufficiency certification, production auth enablement, active scoped cache consumer validation, and Quality Streak records.
- **Files changed:** `.gitignore`, `package.json`, `package-lock.json`, `playwright.config.js`, `apps/web/tests/rbac.spec.js`, `scripts/validate-ci.sh`, `apps/api/tests/test_repo_hygiene.py`, and project status docs.
- **Implemented:** Playwright Chromium smoke tests serve the static web UI over localhost, stub API responses, and verify anonymous fail-closed app-auth behavior plus Admin and ReadOnly role-control states. CI validation now installs npm dependencies, installs Chromium dependencies, and runs `npm run test:web`.
- **Validation:** Focused repository-hygiene tests passed with `13 passed`; `npm run test:web` passed with `3 passed`. Full `./scripts/validate-ci.sh` passed with redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `88 passed`, static web JavaScript syntax validation, and Playwright browser UI RBAC smoke `3 passed`. `git diff --check` passed.
- **Read-only evidence:** No sync jobs, production deployment, or Autotask write capability were run or added; browser tests stub API calls.
- **Rollback:** Revert this branch commit; application behavior is unchanged except validation now requires the browser smoke.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Milestone 1 unsupported-claim verifier breadth

- **Slice:** Add conservative unsupported ticket-history resolution-claim verifier checks on branch `agent/m1-unsupported-claim-verifier` from canonical `main` `98820196bb55049dc134183a8bf96ffff63ee32f`.
- **State:** `partial`; verifier breadth is improved for obvious unsupported resolution claims, but Milestone 1 still requires real-browser UI evidence, broader source-sufficiency certification, production auth enablement, active scoped cache consumer validation, and Quality Streak records.
- **Files changed:** `apps/api/app/answer_safety.py`, `apps/api/tests/test_guardrails.py`, and project status docs.
- **Implemented:** `verify_answer()` now inspects the `From CompuOne Ticket History` section for resolution/fix claims and fails closed when retrieved source evidence is empty or lacks meaningful token overlap. Tests cover unsupported firewall replacement claims, empty-source specific-fix claims, and supported print-spooler resolution claims.
- **Validation:** Focused guardrail/RAG tests passed with `51 passed`. Full `./scripts/validate-ci.sh` passed with redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `88 passed`, and static web JavaScript syntax validation. `git diff --check` passed.
- **Read-only evidence:** No sync jobs, production deployment, or Autotask write capability were run or added.
- **Rollback:** Revert this branch commit; no schema or runtime configuration change is included.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Milestone 1 cache/export scope contracts

- **Slice:** Add future scoped-cache and export-route authority contracts on branch `agent/m1-cache-export-scope-contracts` from canonical `main` `ea86e1b50873c9337811fcfae94305d2c64f8c04`.
- **State:** `partial`; future scoped cache/export safety contracts are stronger, but Milestone 1 still requires unsupported-claim verifier breadth, real-browser UI evidence, production auth enablement, active scoped cache consumer validation, and Quality Streak records.
- **Files changed:** `apps/api/app/cache.py`, `apps/api/tests/test_api.py`, `apps/api/tests/test_ingestion_rag.py`, and project status docs.
- **Implemented:** `scoped_cache_key()` requires authority class, at least one role, explicit scope, positive version, optional model name, and config inputs before generating a cache key. Tests assert stable role ordering, scope-sensitive key separation, rejected missing contract inputs, and no export/download API route currently exists outside the route authority matrix.
- **Validation:** Focused API/RAG tests passed with `63 passed`. Full `./scripts/validate-ci.sh` passed with redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `85 passed`, and static web JavaScript syntax validation. `git diff --check` passed.
- **Read-only evidence:** No sync jobs, production deployment, or Autotask write capability were run or added.
- **Rollback:** Revert this branch commit; existing global dashboard caches continue to use the older cache-key helper and are not behaviorally changed by this contract addition.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Milestone 1 verifier-failure audit and fallback reason

- **Slice:** Preserve verifier fail-closed reasons and audit verifier failures on branch `agent/m1-verifier-failure-audit` from canonical `main` `cb14284fa02c98666358d7015e2664116aca05c8`.
- **State:** `partial`; verifier failures are now more transparent and auditable, but Milestone 1 still requires unsupported-claim verifier breadth, cache/export contracts, real-browser UI evidence, production auth enablement, and Quality Streak records.
- **Files changed:** `apps/api/app/assistant.py`, `apps/api/app/models.py`, `apps/api/tests/test_ingestion_rag.py`, and project status docs.
- **Implemented:** `_fallback_answer()` now preserves the safe warning passed by the failed path instead of rewriting every fallback to a timeout. Assistant verifier failures record `verifier_failed` audit events with actor, outcome `blocked`, effective scope, reason, source count, and source-ticket count. Regression coverage drives the real assistant path with an unretrieved ticket citation and verifies the warning plus sanitized audit record.
- **Validation:** Focused guardrail/RAG tests passed with `46 passed`. Full `./scripts/validate-ci.sh` passed with redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `82 passed`, and static web JavaScript syntax validation. `git diff --check` passed.
- **Read-only evidence:** No sync jobs, production deployment, or Autotask write capability were run or added; tests used fake local DB/chat paths.
- **Rollback:** Revert this branch commit; the audit table schema remains unchanged and new enum use only affects local audit records.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Milestone 1 success audit actor/scope linkage

- **Slice:** Add success-path audit actor/scope linkage for material actions on branch `agent/m1-success-audit-scope-linkage` from canonical `main` `aabecda3217471128e4cc02818cafc01f2a5be17`.
- **State:** `partial`; material admin actions, recurring analytics reads, assistant answers, and feedback now record centralized success audit entries with actor/scope metadata, but Milestone 1 still requires verifier-failure audit records, broader workflow coverage, cache/export contracts, real-browser UI evidence, production auth enablement, and Quality Streak records.
- **Files changed:** `apps/api/app/main.py`, `apps/api/tests/test_api.py`, and project status docs.
- **Implemented:** `record_success_audit()` centralizes success records with actor, target, outcome, scope, and role metadata. Admin Autotask probes, manual sync starts, reference-data sync, document build, embedding run, ticket classification, operations settings/job/pause/resume/stop actions, recurring-issues analytics, assistant ask, and assistant feedback now emit success audit records after the underlying action returns.
- **Validation:** Focused API tests passed with `23 passed`. Full `./scripts/validate-ci.sh` passed with redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `81 passed`, and static web JavaScript syntax validation. `git diff --check` passed.
- **Read-only evidence:** No sync jobs, production deployment, or Autotask write capability were run or added; tests monkeypatched action bodies where needed.
- **Rollback:** Revert this branch commit; the audit schema is unchanged and default Basic Auth deployment remains compatible because `APP_ROUTE_AUTH_REQUIRED=false` remains the default.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Milestone 1 route authority and static UI contract

- **Slice:** Expand Milestone 1 API route authority, denial-audit coverage, company-scope DB coverage, and static web RBAC/accessibility contracts on branch `agent/m1-route-authority-audit-matrix` from canonical `main` `b65683bea439b025f85c0b0708611e44e1a78110`.
- **State:** `partial`; sensitive API route authority is materially stronger and statically verified, but Milestone 1 still requires success-path audit actor/scope linkage, cache/export contracts, verifier breadth, real-browser UI evidence, production auth enablement, and Quality Streak records.
- **Files changed:** `apps/api/app/main.py`, `apps/api/tests/test_api.py`, `apps/api/tests/test_repo_hygiene.py`, `apps/web/index.html`, and project status docs.
- **Implemented:** Admin role gates now cover audit log, Autotask threshold/test probes, manual sync starts, reference-data sync, document build, embedding run, ticket classification, operations mutators, and curated memory. `/ready` exposes the non-secret app-route-auth mode for UI decisions. `authorized_company_ids_for_user()` now imports and uses `db_connection` directly instead of silently failing to empty scope. Static web controls fail closed for unauthenticated users when app-route auth is required, and login fields have explicit labels.
- **Validation:** Focused container validation passed with API plus repository-hygiene tests reporting `34 passed`. Full `./scripts/validate-ci.sh` passed with redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `79 passed`, and static web JavaScript syntax validation. `git diff --check` passed.
- **Read-only evidence:** No sync jobs, production deployment, or Autotask write capability were run or added.
- **Rollback:** Revert this branch commit; default Basic Auth deployment remains compatible because `APP_ROUTE_AUTH_REQUIRED=false` remains the default and the added route gates only apply when app-route auth is enabled.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Control-doc reconciliation and scheduler heartbeat repair

- **Slice:** Reconcile stale roadmap control documents after PR #10 and repair scheduler heartbeat freshness after runtime evidence showed jobs completing while `scheduler_heartbeats` stayed stale.
- **State:** `partial`; control documents are current for canonical `main` and heartbeat is repaired, but Milestone 1 and Milestone 2 remain incomplete under their acceptance criteria.
- **Files changed:** `docs/implementation_status.md`, `docs/codex_next_prompt.md`, `docs/acceptance_criteria.md`, `docs/known_risks.md`, `workers/scheduler/main.py`, and `apps/api/tests/test_repo_hygiene.py`.
- **Implemented:** `workers/scheduler/main.py` now records scheduler heartbeat at tick start, tick finish, and failure using `record_scheduler_heartbeat`; stale next-action references to PR #9/#10 were replaced with current Milestone 1 closeout work; acceptance and risk docs now preserve PR #10 evidence, checked-empty TimeEntries semantics, and scheduler readiness criteria.
- **Validation:** Focused container validation passed with `python -m compileall -q apps/api/app workers && pytest -q apps/api/tests/test_repo_hygiene.py` reporting `12 passed`. Full `./scripts/validate-ci.sh` passed with redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `75 passed`, and static web JavaScript syntax validation. `git diff --check` passed.
- **Runtime evidence:** Rebuilt `worker-scheduler` from this branch. `/api/operations/status` reported `scheduler.state=healthy`, `heartbeat_age_seconds=37.2`, `heartbeat_at=2026-07-21T18:58:41.132495+00:00`, `last_tick_started_at=2026-07-21T18:57:47.802317+00:00`, and `last_tick_finished_at=2026-07-21T18:58:41.119964+00:00`. Matching job run `3935` completed `open_ticket_history_gaps` at `2026-07-21T18:58:41.115436+00:00`.
- **Read-only evidence:** The runtime verification read Autotask through existing bounded scheduler jobs and updated local Postgres only; no Autotask write capability was run or added.
- **Rollback:** Revert this branch commit and redeploy `worker-scheduler`; the heartbeat table is additive and existing job execution still remains governed by `scheduled_jobs`, `job_runs`, and `job_locks`.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Latest receipt — Related-data scheduler restoration

- **Slice:** Restore canonical TimeEntries/TicketHistory sync and scheduler automation after detecting runtime/source drift from the live scheduler image.
- **State:** `partial_foundation`; automation is restored and verified, but historical estate coverage still needs continued bounded catch-up and certification before Milestone 2 can be marked complete.
- **Files changed:** `apps/api/app/sync.py`, `apps/api/app/operations.py`, `apps/api/app/db.py`, `apps/api/app/config.py`, `apps/api/app/cache.py`, `apps/api/app/customer_success.py`, `apps/api/app/ticket_health.py`, `apps/api/app/routing.py`, `apps/api/app/realtime.py`, `.env.example`, `docs/OPERATIONS_SCHEDULER.md`, `apps/api/tests/test_ingestion_rag.py`, and `apps/api/tests/test_repo_hygiene.py`.
- **Implemented:** `recent_sync` again pulls TimeEntries; open-ticket TimeEntries/TicketHistory gap jobs are enabled every 15 minutes; estate-wide TimeEntries/TicketHistory sweeps are enabled hourly; scheduler status exposes open and estate coverage; schema initialization includes TimeEntries, TicketHistory, gap-check, scheduler heartbeat, ticket-health/customer-success, and Milestone 1 auth/audit/scope tables.
- **Validation:** `./scripts/validate-ci.sh` passed with redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `74 passed`, and static web JavaScript syntax validation.
- **Runtime evidence:** Local API and scheduler were rebuilt from canonical source; `/api/operations/status` returned `global_pause=false`, no Autotask threshold error, `time_entries=46810`, `ticket_history=28207`, open-ticket labor coverage `90/146`, and open-ticket TicketHistory coverage `146/146`; rebuilt scheduler completed `open_ticket_history_gaps`, `open_ticket_time_entry_gaps`, and `reclassify_chunks`.
- **Post-merge runtime update:** On `2026-07-21`, canonical `main` was verified at `7ca491b82d1ac1085efbbede3d3ccc1a9fe35057`; PR #10 CI run `29857699615` passed. Live operations returned `global_pause=false`, `time_entries=46899`, `ticket_history=28207`, open-ticket labor coverage `90/146` with `56` checked-empty TimeEntries, and open-ticket TicketHistory coverage `146/146`. The scheduler completed `recent_sync`, `open_ticket_history_gaps`, and `open_ticket_time_entry_gaps` after the pause was cleared.
- **Follow-up risk found:** Job execution continued after PR #10, but `scheduler_heartbeats` stopped updating after rebuild while completed runs continued. Scheduler heartbeat freshness required a follow-up repair before it could be used as a production readiness signal.
- **Classification evidence:** `/api/analytics/ticket-class-report` returned `classified_tickets=67726`, `total_tickets=67726`, `unclassified_tickets=0`, and manual bounded `classify_tickets` operation run `3928` completed.
- **Read-only evidence:** Jobs only read from Autotask and update local Postgres; no Autotask write capability was run or added.
- **Rollback:** Revert this branch commit and redeploy API/scheduler; DB additions are additive local tables/columns.

## Previous receipt — Milestone 1 auth/RBAC and answer-safety foundation

- **Slice:** Add local authentication/RBAC foundation plus first deterministic answer-safety gates on branch `agent/m1-auth-rbac-foundation` from canonical `main` `fec62ba9963e0ade35e292f88b337bbbe8bf5714`.
- **State:** `partial`; Milestone 1 is active, not verified complete.
- **Files changed:** `.env.example`, `apps/api/app/config.py`, `apps/api/app/security.py`, `apps/api/app/answer_safety.py`, `apps/api/app/main.py`, `apps/api/app/db.py`, `apps/api/migrations/007_auth_rbac_foundation.sql`, `apps/api/app/assistant.py`, `apps/api/tests/test_api.py`, `apps/api/tests/test_guardrails.py`, and `apps/api/tests/test_ingestion_rag.py`.
- **Implemented:** PBKDF2-SHA256 password hashing, signed expiring HMAC session tokens, DB-backed `app_users` and `app_login_attempts` schema, disabled-user and login-throttle hooks, `/auth/me`, optional fail-closed bearer-token middleware, admin role checks for operations mutation routes when app route auth is enabled, prompt-injection detection, unsafe source filtering before prompt context, and citation-subset answer verification.
- **Compatibility boundary:** `APP_ROUTE_AUTH_REQUIRED=false` remains the default so existing Nginx Basic Auth deployments continue to work while app-level auth is certified.
- **Company-scope status:** `_retrieve_sources` now accepts `authorized_company_ids` and SQL includes `source_metadata->>'company_id'` filtering when supplied; full request identity-to-company scope propagation remains unfinished and release-blocking.
- **Validation:** `docker compose run --rm -T --no-deps -v "$PWD":/workspace -w /workspace api sh -c 'python -m compileall -q apps/api/app workers && pytest -q apps/api/tests/test_api.py apps/api/tests/test_guardrails.py apps/api/tests/test_ingestion_rag.py'` passed with `54 passed`. `docker compose run --rm -T --no-deps -e DATABASE_URL=postgresql://autotask_ai:change-me@postgres-missing:5432/autotask_ai -v "$PWD":/workspace -w /workspace api sh -c 'python -m compileall -q apps/api/app workers && pytest -q apps/api/tests/test_api.py'` passed with `12 passed`, covering CI's no-Postgres test environment.
- **Full CI validation:** `./scripts/validate-ci.sh` passed with redacted Compose validation, 7 ordered migrations, API image build, API/worker Python compile, full pytest `65 passed`, and static web JavaScript syntax validation.
- **Remote CI repair:** Initial PR #4 run `29854738844` failed because an admin-route RBAC test depended on a reachable `postgres` hostname after auth succeeded; the test was made hermetic by monkeypatching the operations settings write after RBAC authorization is proven.
- **Read-only evidence:** No sync jobs, production deployment, or Autotask write capability were run or added.
- **Rollback:** Revert this branch commit or set `APP_ROUTE_AUTH_REQUIRED=false`; migration is additive and leaves new local auth tables inert if unused.

## Previous receipt — Milestone 1 durable audit foundation

- **Slice:** Add database-backed audit persistence and authorization-denial audit evidence on branch `agent/m1-durable-audit-scope-foundation` from canonical `main` `9d92d704e862c8d94404a109b922a2a306514522`.
- **State:** `partial`; durable audit is improved, but Milestone 1 still requires identity-linked audit on all protected workflows, full company-scope propagation, UI/API RBAC completion, verifier breadth, and three-run evidence.
- **Files changed:** `apps/api/app/audit.py`, `apps/api/app/models.py`, `apps/api/app/db.py`, `apps/api/app/main.py`, `apps/api/migrations/008_durable_audit_log.sql`, and `apps/api/tests/test_api.py`.
- **Implemented:** `audit_log` local table, durable audit insert/list behavior with in-memory fallback, audit entry outcome/scope fields, missing-token authorization denial events, insufficient-role denial events, and tests for no-Postgres API behavior plus audit persistence insert shape.
- **Validation:** `docker compose run --rm -T --no-deps -e DATABASE_URL=postgresql://autotask_ai:change-me@postgres-missing:5432/autotask_ai -v "$PWD":/workspace -w /workspace api sh -c 'python -m compileall -q apps/api/app workers && pytest -q apps/api/tests/test_api.py'` passed with `14 passed`.
- **Full CI validation:** `./scripts/validate-ci.sh` passed with redacted Compose validation, 8 ordered migrations, API image build, API/worker Python compile, full pytest `67 passed`, and static web JavaScript syntax validation.
- **Read-only evidence:** No sync jobs, production deployment, or Autotask write capability were run or added.
- **Rollback:** Revert this branch commit; migration is additive and audit falls back to memory if the DB table is unavailable.

## Previous receipt — Milestone 1 company-scope foundation

- **Slice:** Add user-company scope table and fail-closed assistant/analytics scope plumbing on branch `agent/m1-company-scope-foundation` from canonical `main` `4f7fb1f268e18d9aace0d873d73b9d2be5bb8096`.
- **State:** `partial`; assistant and recurring analytics now have first authenticated scope gates, but Milestone 1 still requires scope linkage across query sources, feedback, memory, UI, future cache/export paths, and broader negative tests.
- **Files changed:** `apps/api/app/db.py`, `apps/api/app/main.py`, `apps/api/app/assistant.py`, `apps/api/app/ticket_analytics.py`, `apps/api/migrations/009_user_company_scope.sql`, `apps/api/tests/test_api.py`, and `apps/api/tests/test_ingestion_rag.py`.
- **Implemented:** `app_user_company_scopes` table, admin-global scope handling, fail-closed non-admin assistant/analytics access when no company scope exists, scoped assistant route propagation, scoped retrieval SQL, and scoped recurring-issues SQL.
- **Validation:** `docker compose run --rm -T --no-deps -e DATABASE_URL=postgresql://autotask_ai:change-me@postgres-missing:5432/autotask_ai -v "$PWD":/workspace -w /workspace api sh -c 'python -m compileall -q apps/api/app workers && pytest -q apps/api/tests/test_api.py apps/api/tests/test_ingestion_rag.py'` passed with `51 passed`.
- **Full CI validation:** `./scripts/validate-ci.sh` passed with redacted Compose validation, 9 ordered migrations, API image build, API/worker Python compile, full pytest `70 passed`, and static web JavaScript syntax validation.
- **Read-only evidence:** No sync jobs, production deployment, or Autotask write capability were run or added.
- **Rollback:** Revert this branch commit; migration is additive and default app-route auth remains off.

## Previous receipt — Milestone 1 scope snapshot foundation

- **Slice:** Add actor and effective-scope snapshots for assistant queries, query sources, feedback, and pending memory candidates on branch `agent/m1-scope-snapshots-foundation` from canonical `main` `99c454c40b45981b7d7579d45515621bbbfa91cd`.
- **State:** `partial`; scope provenance is improved, but Milestone 1 still requires UI enforcement, verifier scope checks, future cache/export contracts, and Quality Streak evidence.
- **Files changed:** `apps/api/app/db.py`, `apps/api/app/main.py`, `apps/api/app/assistant.py`, `apps/api/migrations/010_assistant_scope_snapshots.sql`, and `apps/api/tests/test_api.py`.
- **Implemented:** `actor_username` and `effective_scope` snapshots on assistant queries/feedback/memory, `company_id` on assistant query sources, actor propagation from authenticated assistant routes, and feedback scope snapshot route tests.
- **Validation:** `docker compose run --rm -T --no-deps -e DATABASE_URL=postgresql://autotask_ai:change-me@postgres-missing:5432/autotask_ai -v "$PWD":/workspace -w /workspace api sh -c 'python -m compileall -q apps/api/app workers && pytest -q apps/api/tests/test_api.py apps/api/tests/test_ingestion_rag.py'` passed with `52 passed`.
- **Full CI validation:** `./scripts/validate-ci.sh` passed with redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `71 passed`, and static web JavaScript syntax validation.
- **Read-only evidence:** No sync jobs, production deployment, or Autotask write capability were run or added.
- **Rollback:** Revert this branch commit; migration is additive and default app-route auth remains off.

## Previous receipt — Milestone 1 verifier scope foundation

- **Slice:** Add deterministic verifier rejection for sources outside the effective authorized company scope on branch `agent/m1-verifier-scope-foundation` from canonical `main` `76292b640f4843659b504d19168e0352909cb73c`.
- **State:** `partial`; answer verification now checks source scope, but Milestone 1 still requires broader unsupported-claim verifier work, UI enforcement, cache/export contracts, and Quality Streak evidence.
- **Files changed:** `apps/api/app/answer_safety.py`, `apps/api/app/assistant.py`, and `apps/api/tests/test_guardrails.py`.
- **Implemented:** `verify_answer(..., authorized_company_ids=...)`, out-of-scope source detection, scope violation warnings/reason, assistant verifier call wired to effective scope, and direct negative test.
- **Validation:** `docker compose run --rm -T --no-deps -e DATABASE_URL=postgresql://autotask_ai:change-me@postgres-missing:5432/autotask_ai -v "$PWD":/workspace -w /workspace api sh -c 'python -m compileall -q apps/api/app workers && pytest -q apps/api/tests/test_guardrails.py apps/api/tests/test_ingestion_rag.py'` passed with `43 passed`.
- **Full CI validation:** `./scripts/validate-ci.sh` passed with redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `72 passed`, and static web JavaScript syntax validation.
- **Read-only evidence:** No sync jobs, production deployment, or Autotask write capability were run or added.
- **Rollback:** Revert this branch commit; no migration is included in this slice.

## Latest receipt — Milestone 1 UI auth/RBAC foundation

- **Slice:** Add static-web app-auth token support and role-aware controls on branch `agent/m1-ui-auth-rbac-foundation` from canonical `main` `b846be3a4e76e3621ab05eec22432b2a421cb084`.
- **State:** `partial`; UI now participates in auth/RBAC state, but Milestone 1 still requires browser/accessibility verification, complete production auth enablement, broader verifier checks, cache/export contracts, and Quality Streak evidence.
- **Files changed:** `apps/web/index.html`, `apps/web/styles.css`, and project status docs.
- **Implemented:** local login/logout panel, stored Bearer token header propagation, `/auth/me` role display, role-aware disabled controls for admin/technician actions, dynamic admin controls generated from jobs/runs, and clearer 401/403 UI messages.
- **Validation:** `./scripts/validate-ci.sh` passed with redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `72 passed`, and static web JavaScript syntax validation.
- **Read-only evidence:** No sync jobs, production deployment, or Autotask write capability were run or added.
- **Rollback:** Revert this branch commit; default Basic Auth deployment remains compatible because app-route auth remains off unless explicitly enabled.

## Previous receipt — Milestone 0 CI reconciliation

- **Slice:** Preserve local CI commit `dc18106` on governed branch `agent/m0-ci-validation` based on canonical `origin/main` `792eca2c943e4276cc3b8e93093d5dc193c6174f`.
- **State:** `partial`; CI was implemented, remotely proven, and merged, but Milestone 0 still needs fuller certification matrix/Quality Streak records before `verified_complete`.
- **Backup:** Local branch `backup/dc18106-ci-harness` points to source commit `dc18106`.
- **Files preserved/reconciled:** `.github/workflows/ci.yml`, `scripts/validate-ci.sh`, `docs/CI_VALIDATION.md`, `apps/api/tests/test_repo_hygiene.py`, `README.md`, `docs/implementation_status.md`, `docs/acceptance_criteria.md`, `docs/known_risks.md`, and `docs/codex_next_prompt.md`.
- **Local validation:** `./scripts/validate-ci.sh` passed on the reconciled branch with redacted Compose validation, 6 ordered migrations, API image build, API/worker Python compile, full canonical pytest result `53 passed`, and static web JavaScript syntax validation.
- **GitHub CI evidence:** PR `newbie10122/autotask-ai#3` was merged after latest GitHub Actions run `29850162173` passed workflow `CI`, job `Validate Autotask AI`, for head `67de41334d7c609bfdb9fd52580addd139804ac7`.
- **Additional validation:** `git diff --check` passed; `python3 -m compileall apps/api/app apps/api/tests` passed; `./scripts/compose-config-redacted.sh >/tmp/autotask-ai-compose-redacted.txt` passed; standalone static web JavaScript syntax check passed.
- **Host limitation:** `cd apps/api && pytest` could not run on the host because `pytest` is not installed there; pytest passed inside the API container through the CI validator.
- **Runtime sanity:** Local non-production rebuild of `api` and `web` passed; `/health` returned `{"status":"ok"}`, `/ready` returned `{"status":"ready","database":"available","autotask":"configured"}`, and the local Nginx UI returned `HTTP 200`.
- **Ready endpoint source:** The current canonical `apps/api/app/main.py` `/ready` route returns only `status`, `database`, and `autotask`; any earlier `cache` field came from a stale local branch/runtime image and is not claimed as reconciled evidence.
- **Read-only evidence:** The validator and runtime sanity did not start sync jobs, deploy production services, or perform Autotask writes.
- **Rollback:** Revert the reconciled CI commit or delete branch `agent/m0-ci-validation`; source commit remains recoverable at `backup/dc18106-ci-harness`.

## Second Brain state

`pull-request-open` — branch `agent/autotask-ai-governed-roadmap-projection`, draft PR `newbie10122/helix-second-brain#6`, branch head `07423b9` records PR #16, canonical commit `a4f02bc0987dfe0ba9cb0fd6164d67310acb2cc6`, unsupported-claim verifier breadth, cache/export contracts, verifier-failure audit, success audit actor/scope linkage, route authority/static UI contracts, scheduler heartbeat repair, and runtime evidence. Local Second Brain validation passed with `python3 tools/validate_knowledge.py`. Remote validation status remains separately tracked on PR #6. Do not mark `merged` until PR #6 is merged.

## Exact next action

Merge the current Milestone 1 browser UI RBAC smoke branch after CI passes, update the existing Second Brain projection, then continue Milestone 1 closeout with broader accessibility evidence, source-sufficiency certification, and Quality Streak receipts.
