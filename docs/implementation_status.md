# Autotask AI Implementation Status

**Updated:** 2026-07-21  
**Management target:** 99% verified roadmap completion  
**Current state:** `partial`  
**Active milestone:** Milestone 1 — Security, identity, isolation, and answer trust

## Status confidence

The repository has a substantial implemented MVP foundation, but no roadmap milestone is yet marked `verified_complete` under `AGENTS.md`. Current verified completion cannot be represented honestly as a percentage until acceptance evidence, the capability certification matrix, and Quality Streak records are established.

## Implemented foundation

- GitHub Actions CI workflow and local validation harness were merged through PR `newbie10122/autotask-ai#3`; canonical `main` is `fec62ba9963e0ade35e292f88b337bbbe8bf5714`.
- `scripts/validate-ci.sh` runs redacted Compose validation, migration ordering, API image build, API/worker Python compilation, full pytest, and static web JavaScript syntax checks.
- `docs/CI_VALIDATION.md` defines the local/CI validation command and a capability-certification receipt format requiring explicit Autotask write-back disclosure.
- FastAPI API and technician/admin web interface.
- Dockerized web, API, PostgreSQL/pgvector, synchronization, document, embedding, scheduler, nightly, and optional Ollama services.
- Read-only company, ticket, and ticket-note synchronization with checkpoints.
- Local document/chunk generation, classification, embeddings, vector retrieval, lexical fallback, and CPU answer generation.
- Weak-evidence response and timeout fallback.
- Recurring-issue analytics.
- Operations scheduler with locks, pause, disk, conflict, and Autotask-threshold controls.
- Sensitive/private-entity redaction and read-only enforcement tests.
- Pending known-fix candidate creation.
- Milestone 1 auth foundation adds PBKDF2 password hashing, signed expiring session tokens, disabled-user and throttling hooks, optional fail-closed API route authentication, admin-operation role denial tests, pre-prompt prompt-injection/secret source filtering, and deterministic answer-verifier citation checks.
- Milestone 1 durable-audit branch `agent/m1-durable-audit-scope-foundation` adds database-backed audit persistence, outcome/scope fields, and authorization-denial audit events.

## Verified gaps blocking production readiness

- Route authentication/RBAC is implemented as an opt-in foundation but is not yet enforced end to end in production defaults or UI.
- Audit logging is database-backed for foundation events, but identity/company-scope linkage is not yet complete across every workflow.
- Retrieval has an `authorized_company_ids` filter contract, but request identity-to-company scope is not fully wired through every route, analytics path, citation, cache, and UI flow.
- Prompt-injection scanning and deterministic answer verification have initial tests, but independent verifier coverage is not yet sufficient for Milestone 1 completion.
- Three-run Quality Streak evidence is not established.
- Governed memory approval/version/rollback workflow is incomplete.
- Ticket-health data synchronization and analytics are incomplete.

## Milestone table

| Milestone | State | Next evidence required |
|---|---|---|
| 0. Governance and continuous validation | partial | CI PR merged; certification matrix/Quality Streak records still required |
| 1. Security, identity, isolation, answer trust | active | Complete durable audit, full route/UI RBAC, company scope wiring, verifier breadth, and three-run evidence |
| 2. Complete operational Autotask data | not_started | Field inventory and resumable scoped sync |
| 3. Ticket Health Analytics | not_started | Deterministic APIs/UI with evidence |
| 4. Redis and CPU performance | not_started | Scoped cache design and benchmarks |
| 5. Real-time technician updates | not_started | Authorized event architecture |
| 6. Technician Performance Assistant | partial_foundation | Current RAG exists; guided/draft workflows not certified |
| 7. Predictive Service Intelligence | not_started | Certified data and evaluation baseline |
| 8. Routing recommendations | not_started | Resource/workload data and evaluation |
| 9. Customer Success Intelligence | not_started | Certified internal capabilities |
| 10. Production certification/99% closeout | not_started | All target milestones and evidence |

## Active execution queue

1. Publish and verify the durable-audit PR.
2. Wire authenticated actor/company scope through assistant retrieval, recurring analytics, query sources, feedback, memory, and future cache/export contracts.
3. Expand route and UI RBAC for Admin, Technician, and ReadOnly across all API actions.
4. Expand deterministic verifier coverage for unsupported claims, source subset, section labeling, injection, secrets, and scope violations.
5. Prepare the existing governed Second Brain projection update after this durable-audit branch PR is opened.

Parallel-safe work after roadmap merge:

- Agent A: CI and repository validation.
- Agent B: authentication/RBAC design and negative tests.
- Agent C: client-scope data model and retrieval isolation analysis/tests.
- Agent D: prompt-injection and independent verifier contract/tests.
- Independent verifier: review threat model, overlap, integration order, and acceptance coverage.

Shared schema and integration changes must be serialized by the coordinator.

## Critical blockers

None currently identified for documentation and non-production implementation work. Production deployment, customer-data scope expansion, irreversible migrations, and any Autotask write capability remain approval-gated.

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

## Latest receipt — Milestone 1 durable audit foundation

- **Slice:** Add database-backed audit persistence and authorization-denial audit evidence on branch `agent/m1-durable-audit-scope-foundation` from canonical `main` `9d92d704e862c8d94404a109b922a2a306514522`.
- **State:** `partial`; durable audit is improved, but Milestone 1 still requires identity-linked audit on all protected workflows, full company-scope propagation, UI/API RBAC completion, verifier breadth, and three-run evidence.
- **Files changed:** `apps/api/app/audit.py`, `apps/api/app/models.py`, `apps/api/app/db.py`, `apps/api/app/main.py`, `apps/api/migrations/008_durable_audit_log.sql`, and `apps/api/tests/test_api.py`.
- **Implemented:** `audit_log` local table, durable audit insert/list behavior with in-memory fallback, audit entry outcome/scope fields, missing-token authorization denial events, insufficient-role denial events, and tests for no-Postgres API behavior plus audit persistence insert shape.
- **Validation:** `docker compose run --rm -T --no-deps -e DATABASE_URL=postgresql://autotask_ai:change-me@postgres-missing:5432/autotask_ai -v "$PWD":/workspace -w /workspace api sh -c 'python -m compileall -q apps/api/app workers && pytest -q apps/api/tests/test_api.py'` passed with `14 passed`.
- **Full CI validation:** `./scripts/validate-ci.sh` passed with redacted Compose validation, 8 ordered migrations, API image build, API/worker Python compile, full pytest `67 passed`, and static web JavaScript syntax validation.
- **Read-only evidence:** No sync jobs, production deployment, or Autotask write capability were run or added.
- **Rollback:** Revert this branch commit; migration is additive and audit falls back to memory if the DB table is unavailable.

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

`pull-request-open` — branch `agent/autotask-ai-governed-roadmap-projection`, draft PR `newbie10122/helix-second-brain#6`, exact branch head `a624c6caf1bfead3e9af87adf45a54d4c40871cd` records the Autotask AI PR #3 merge. Local Second Brain validation passed with `python3 tools/validate_knowledge.py`. Remote `Validate knowledge` run `29854057777` failed before useful job steps with no runner/job detail; this is recorded on PR #6 and still needs follow-up before merge. Do not mark `merged` until PR #6 is merged. This M1 branch will require another sanitized projection after its Autotask AI PR is opened.

## Exact next action

Open a draft PR for branch `agent/m1-durable-audit-scope-foundation`, let GitHub CI run, update the existing governed Second Brain projection with durable-audit branch/PR evidence, then continue Milestone 1 full company-scope wiring.
