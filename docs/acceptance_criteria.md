# Autotask AI Acceptance Criteria

These criteria govern milestone completion together with `AGENTS.md` and `docs/PRODUCT_ROADMAP.md`.

## Universal completion criteria

A milestone may be marked `verified_complete` only when:

- its objective and scope are documented at at least 95% confidence;
- code, configuration, schema, documentation, and UI agree;
- applicable unit, integration, negative, authorization, isolation, redaction, prompt-injection, migration, restart, recovery, idempotency, and rollback tests pass;
- material RAG, memory, security, authorization, migration, deployment, and write-capability changes have an independent verifier receipt;
- no unresolved critical security, privacy, client-isolation, data-integrity, or read-only-authority risk remains;
- performance and resource behavior are measured where applicable;
- the affected capability has three consecutive clean certification runs where required;
- `docs/implementation_status.md`, `docs/known_risks.md`, and `docs/codex_next_prompt.md` are current;
- the Second Brain synchronization state and evidence are recorded.

## Milestone 0

- Canonical roadmap and control files exist and are internally consistent.
- Obsolete roadmap PRs are closed or explicitly superseded.
- CI automatically runs the agreed validation suite on pull requests, pushes to `main`, and manual dispatch.
- CI uses read-only repository permissions and a bounded 30-minute job timeout.
- CI delegates command logic to `scripts/validate-ci.sh` instead of duplicating validation steps in workflow YAML.
- The CI validation script runs redacted Compose validation through `scripts/compose-config-redacted.sh` and does not print raw `.env` values.
- The CI validation script verifies migration filename ordering, builds the API image, compiles API/worker Python, runs the full Python test suite, and checks static web JavaScript syntax.
- CI validation uses `.env.example` and must not require live Autotask credentials for ordinary PR validation.
- CI validation does not start sync jobs, deploy production services, or write to Autotask.
- CI failures block completion claims.
- A capability certification and Quality Streak record format exists in `docs/CI_VALIDATION.md`.
- A capability certification matrix exists in `docs/CAPABILITY_CERTIFICATION.md` and explicitly distinguishes partial evidence from `verified_complete` milestone status.
- Repository hygiene tests pin the CI workflow, validation script, redacted Compose usage, migration ordering check, JavaScript syntax check, and receipt format.
- Repository receipts include exact commands, results, commits, risks, rollback, and Second Brain state.
- Local reconciled evidence on branch `agent/m0-ci-validation`: `./scripts/validate-ci.sh` passed with redacted Compose validation, 6 ordered migrations, API image build, Python compile, `53 passed`, and static web JavaScript syntax.
- GitHub Actions evidence: PR `newbie10122/autotask-ai#3` latest run `29850162173` passed workflow `CI`, job `Validate Autotask AI`, for head `67de41334d7c609bfdb9fd52580addd139804ac7`; PR #3 was merged into canonical `main` as `fec62ba9963e0ade35e292f88b337bbbe8bf5714`. Milestone 0 still requires fuller certification matrix/Quality Streak records before it can be marked `verified_complete`.
- Current canonical evidence: PR `newbie10122/autotask-ai#10` merged into `main` as `7ca491b82d1ac1085efbbede3d3ccc1a9fe35057`, with GitHub Actions run `29857699615` passing. Control documents must reference this as current truth rather than stale PR #9/#10 publication steps.

## Milestone 1

- Login rejects invalid credentials and disabled users.
- Passwords are securely hashed and never logged.
- Sessions/tokens expire and are securely configured.
- Admin, Technician, and ReadOnly permissions are enforced at API and UI boundaries.
- Unauthorized requests fail closed and are audited.
- Audit records survive restart and link actor, action, target, scope, and outcome.
- Every retrieval and analytics request has explicit authorized company/client scope.
- Cross-client source, cache, citation, and analytics access is denied by negative tests.
- Retrieved untrusted content is scanned for prompt injection and prohibited secrets.
- Material answers pass an independent verifier or fail closed.
- Three consecutive clean identity/isolation/verifier certification runs exist.
- Every API route has an explicit authority matrix covering anonymous, ReadOnly, Technician, Admin, company-scope requirements, audit requirements, failure status, and Basic Auth compatibility behavior.
- Denied authenticated and unauthenticated requests produce durable audit records with actor, roles where known, effective company scope where known, target, outcome, and sanitized reason metadata.
- Current branch evidence on `agent/m1-auth-rbac-foundation`: password hashing, signed expiring tokens, `/auth/me`, optional bearer-token middleware, disabled-user rejection, invalid-login rejection, route-auth fail-closed behavior, admin-operation role denial, prompt-injection source filtering, secret-source filtering, and unretrieved-ticket citation rejection have tests.
- Current branch validation: focused Docker test command passed with `54 passed`; full `./scripts/validate-ci.sh` passed with 7 ordered migrations and `65 passed`. This is foundation evidence only; durable audit, full UI/API RBAC, company-scope propagation, verifier breadth, and three-run streak evidence remain required.
- Current branch evidence on `agent/m1-durable-audit-scope-foundation`: durable `audit_log` schema, audit outcome/scope fields, database audit insert/list behavior with memory fallback, missing-token denial events, insufficient-role denial events, and no-Postgres API tests exist.
- Current branch validation: focused no-Postgres API test command passed with `14 passed`; full `./scripts/validate-ci.sh` passed with 8 ordered migrations and `67 passed`. This is foundation evidence only; audit coverage across all workflows and identity/company-scope linkage remain required.
- Current branch evidence on `agent/m1-company-scope-foundation`: user-company scope table, assistant fail-closed missing-scope denial, scoped assistant propagation, admin global scope behavior, retrieval company filter, and recurring analytics company filter tests exist.
- Current branch validation: focused no-Postgres API/RAG test command passed with `51 passed`; full `./scripts/validate-ci.sh` passed with 9 ordered migrations and `70 passed`. This is foundation evidence only; scope coverage across feedback, memory, UI, future cache/export, citations, and verifier checks remains required.
- Current branch evidence on `agent/m1-scope-snapshots-foundation`: assistant query, source, feedback, and pending memory scope snapshot columns exist; assistant ask and feedback routes pass actor/scope metadata; focused tests cover route propagation.
- Current branch validation: focused no-Postgres API/RAG test command passed with `52 passed`; full `./scripts/validate-ci.sh` passed with 10 ordered migrations and `71 passed`. This is foundation evidence only; UI enforcement, verifier scope checks, future cache/export contracts, and Quality Streak evidence remain required.
- Current branch evidence on `agent/m1-verifier-scope-foundation`: answer verifier rejects sources outside the effective authorized company scope and assistant calls the verifier with effective scope.
- Current branch validation: focused no-Postgres guardrail/RAG test command passed with `43 passed`; full `./scripts/validate-ci.sh` passed with 10 ordered migrations and `72 passed`. This is foundation evidence only; unsupported-claim verifier breadth, UI enforcement, future cache/export contracts, and Quality Streak evidence remain required.
- Current branch evidence on `agent/m1-ui-auth-rbac-foundation`: static web login/logout token handling, Bearer headers, role display, role-aware admin/technician control disabling, and clearer 401/403 UI messages exist.
- Current branch validation: full `./scripts/validate-ci.sh` passed with 10 ordered migrations, full pytest `72 passed`, and static web JavaScript syntax. This is foundation evidence only; browser/accessibility checks, production auth enablement, cache/export contracts, and Quality Streak evidence remain required.
- Current branch evidence on `agent/m1-route-authority-audit-matrix`: admin-only route gates cover manual sync/build/classify, Autotask probes, audit log, operations mutators, and curated memory; a route inventory contract classifies every GET/POST API route; ReadOnly denial tests assert an audit event for each admin route; direct database company-scope lookup is covered; static web tests assert role markers, login labels, landmarks, sections, and auth-mode fail-closed behavior.
- Current branch validation: focused API/repository-hygiene tests passed with `34 passed`; full `./scripts/validate-ci.sh` passed with 10 ordered migrations, full pytest `79 passed`, static web JavaScript syntax, and `git diff --check`. This is foundation evidence only; success-path audit actor/scope records, real-browser checks, cache/export contracts, verifier breadth, and Quality Streak evidence remain required.
- Current branch evidence on `agent/m1-success-audit-scope-linkage`: centralized success-audit records cover material admin actions, recurring analytics, assistant ask, and assistant feedback with actor, roles, outcome, target, and effective scope metadata.
- Current branch validation: focused API tests passed with `23 passed`; full `./scripts/validate-ci.sh` passed with 10 ordered migrations, full pytest `81 passed`, static web JavaScript syntax, and `git diff --check`. This is foundation evidence only; verifier-failure audit, broader workflow coverage, real-browser checks, cache/export contracts, verifier breadth, and Quality Streak evidence remain required.
- Current branch evidence on `agent/m1-verifier-failure-audit`: assistant fallback preserves verifier fail-closed reasons, and verifier failures emit `verifier_failed` audit events with actor, effective scope, outcome `blocked`, sanitized reason, and source counts.
- Current branch validation: focused guardrail/RAG tests passed with `46 passed`; full `./scripts/validate-ci.sh` passed with 10 ordered migrations, full pytest `82 passed`, static web JavaScript syntax, and `git diff --check`. This is foundation evidence only; unsupported-claim verifier breadth, cache/export contracts, real-browser checks, and Quality Streak evidence remain required.
- Current branch evidence on `agent/m1-cache-export-scope-contracts`: `scoped_cache_key()` requires authority class, role list, explicit scope, positive version, and optional model/config inputs; tests prove role-order stability, scope separation, missing-contract rejection, and absence of unclassified export/download routes.
- Current branch validation: focused API/RAG tests passed with `63 passed`; full `./scripts/validate-ci.sh` passed with 10 ordered migrations, full pytest `85 passed`, static web JavaScript syntax, and `git diff --check`. This is foundation evidence only; active scoped cache consumers, unsupported-claim verifier breadth, real-browser checks, and Quality Streak evidence remain required.
- Current branch evidence on `agent/m1-unsupported-claim-verifier`: answer verification rejects unsupported ticket-history resolution claims when source evidence is empty or lacks meaningful overlap, while allowing supported resolution claims with matching source evidence.
- Current branch validation: focused guardrail/RAG tests passed with `51 passed`; full `./scripts/validate-ci.sh` passed with 10 ordered migrations, full pytest `88 passed`, static web JavaScript syntax, and `git diff --check`. This is foundation evidence only; real-browser checks, broader source-sufficiency certification, active scoped cache consumers, and Quality Streak evidence remain required.
- Current branch evidence on `agent/m1-browser-rbac-smoke`: Playwright Chromium tests cover anonymous app-auth fail-closed controls, Admin enabled admin/technician controls, and ReadOnly disabled privileged controls against the real static web page with stubbed API responses.
- Current branch validation: focused repository-hygiene tests passed with `13 passed`; `npm run test:web` passed with `3 passed`; full `./scripts/validate-ci.sh` passed with 10 ordered migrations, full pytest `88 passed`, static web JavaScript syntax, Playwright browser UI RBAC smoke `3 passed`, and `git diff --check`. This is foundation evidence only; broader accessibility checks, source-sufficiency certification, active scoped cache consumers, and Quality Streak evidence remain required.
- Current branch evidence on `agent/m1-browser-accessibility-smoke`: shared Playwright helpers cover real static-web rendering with stubbed APIs; axe validation asserts no serious or critical dashboard accessibility violations; login controls expose accessible names; the Ask mode selector has a visible label.
- Current branch validation: `npm run test:web` passed with `5 passed`; full `./scripts/validate-ci.sh` passed with 10 ordered migrations, full pytest `88 passed`, static web JavaScript syntax, Playwright browser smoke `5 passed`, and `git diff --check`. This is foundation evidence only; keyboard/focus evidence, source-sufficiency certification, active scoped cache consumers, and Quality Streak evidence remain required.
- Current branch evidence on `agent/m1-keyboard-focus-smoke`: explicit focus-visible styling covers navigation links, buttons, inputs, textareas, and selects; Playwright verifies keyboard Tab traversal through primary navigation, login controls, mode selection, question entry, and the Ask action with visible focus indicators.
- Current branch validation: `npm run test:web` passed with `6 passed`; full `./scripts/validate-ci.sh` passed with 10 ordered migrations, full pytest `88 passed`, static web JavaScript syntax, Playwright browser smoke `6 passed`, and `git diff --check`. This is foundation evidence only; source-sufficiency certification, active scoped cache consumers, production-auth deployment evidence, and Quality Streak evidence remain required.
- Current branch evidence on `agent/m1-source-sufficiency-verifier`: answer verification fails closed for non-weak ticket-history claims that lack matching retrieved source evidence or meaningful source-token overlap, while allowing matching symptom claims with sufficient source overlap.
- Current branch validation: focused guardrail tests passed with `14 passed`; full `./scripts/validate-ci.sh` passed with 10 ordered migrations, full pytest `90 passed`, static web JavaScript syntax, Playwright browser smoke `6 passed`, and `git diff --check`. This is foundation evidence only; broader adversarial source-sufficiency evidence, active scoped cache consumers, production-auth deployment evidence, and Quality Streak evidence remain required.
- Current branch evidence on `agent/m1-active-scoped-cache-consumer`: active operations-status caching uses scoped cache keys with authority class, roles, explicit scope, version, and TTL config; the API route passes authenticated-read role context when route auth is enabled, and namespace invalidation clears all scoped operations-status variants.
- Current branch validation: focused API/RAG tests passed with `65 passed`; full `./scripts/validate-ci.sh` passed with 10 ordered migrations, full pytest `92 passed`, static web JavaScript syntax, Playwright browser smoke `6 passed`, and `git diff --check`. This is foundation evidence only; remaining cache-consumer certification, production-auth deployment evidence, broader adversarial verifier evidence, and Quality Streak evidence remain required.
- Current branch evidence on `agent/m1-production-auth-preflight`: CI validates production auth configuration with `scripts/production-auth-preflight.sh .env.example`; production config must either enable app-route auth or explicitly document the approved external-auth boundary.
- Current branch validation: `scripts/production-auth-preflight.sh .env.example` passed; focused repository-hygiene tests passed with `14 passed`; full `./scripts/validate-ci.sh` passed with production-auth preflight, 10 ordered migrations, full pytest `93 passed`, static web JavaScript syntax, Playwright browser smoke `6 passed`, and `git diff --check`. This is foundation evidence only; live production-auth enforcement, bootstrap/admin-user operations, broader adversarial verifier evidence, and Quality Streak evidence remain required.
- Current branch evidence on `agent/m1-bootstrap-admin-user`: local operators can create or update app users through `scripts/bootstrap-app-user.sh` with `BOOTSTRAP_APP_PASSWORD`; role validation, minimum password length, PBKDF2 hash-only storage, disabled-user support, and safe metadata return are covered by tests.
- Current branch validation: focused API tests passed with `28 passed`; full `./scripts/validate-ci.sh` passed with production-auth preflight, 10 ordered migrations, full pytest `96 passed`, static web JavaScript syntax, Playwright browser smoke `6 passed`, and `git diff --check`. This is foundation evidence only; live production-auth enforcement, broader adversarial verifier evidence, and Quality Streak evidence remain required.
- Current branch evidence on `agent/m1-adversarial-verifier-breadth`: conversational answer verification recognizes ticket IDs in source metadata, rejects cross-ticket evidence substitution for cited ticket-history claims, and allows explicit no-history/no-source fallback language without treating it as a factual claim.
- Current branch validation: focused guardrail tests passed with `17 passed`; full `./scripts/validate-ci.sh` passed with production-auth preflight, 10 ordered migrations, full pytest `99 passed`, static web JavaScript syntax, Playwright browser smoke `6 passed`, and `git diff --check`. This is foundation evidence only; broader adversarial verifier evidence, live production-auth enforcement, and Quality Streak evidence remain required.
- Current branch evidence on `agent/m1-generated-answer-verifier-evidence`: the real generated `ask_assistant()` path preserves source-metadata ticket IDs in limiting, fallback summaries, `based_on_tickets`, and returned source payloads; generated answers with metadata-only ticket IDs can pass verification; cross-ticket evidence substitution fails closed with verifier audit; and private-entity redaction preserves required answer section headers.
- Current branch validation: focused generated-answer/redaction tests passed with `4 passed`; full `./scripts/validate-ci.sh` passed with production-auth preflight, 10 ordered migrations, full pytest `102 passed`, static web JavaScript syntax, Playwright browser smoke `6 passed`, and `git diff --check`. This is foundation evidence only; live production-auth enforcement, remaining scope/cache certification, and Quality Streak evidence remain required.

## Milestone 2

- Required ticket-health fields are inventoried with Autotask source names and availability.
- Time entries and approved operational fields synchronize read-only with checkpoints.
- Sync is idempotent, resumable, bounded, rate/threshold aware, and restart safe.
- Client scope and source lineage are retained.
- Missing/unmapped fields are visible and not silently guessed.
- Three consecutive clean sync/recovery runs exist.
- Current foundation evidence on PR `newbie10122/autotask-ai#10`: `recent_sync` includes TimeEntries, open-ticket TimeEntries/TicketHistory gap jobs are scheduled every 15 minutes, estate-wide TimeEntries/TicketHistory sweeps are scheduled hourly, operations status reports open-ticket and estate coverage, and regression tests preserve these contracts.
- TimeEntries absence must be classified separately from unchecked or failed synchronization. A ticket with no TimeEntries can only be treated as confirmed-empty when a successful source query recorded a gap-check timestamp and zero-result count.
- Scheduler readiness evidence requires fresh heartbeat updates, restart recovery evidence, bounded job cadence evidence, conflict-lock evidence, and distinct skipped/blocked/failed/idle reasons.
- Current scheduler heartbeat repair evidence: the worker records heartbeat at tick start, tick finish, and failure; focused repo-hygiene validation passed with `12 passed`, full governed validation passed with `75 passed`, and live operations status showed `scheduler.state=healthy` with fresh `heartbeat_at` after rebuilding `worker-scheduler`.

## Milestone 3

- Ticket age, labor, last action, waiting state, resource count, response count, SLA risk, stalled state, and high-labor outliers are calculated deterministically where data permits.
- Every result shows scope, freshness, evidence, and assumptions.
- Filters, APIs, assistant routes, and UI agree.
- Empty, loading, stale, error, keyboard, responsive, and reduced-motion states are tested.
- Representative real-data calculations are independently checked.

## Milestone 4

- Redis health and safe fallback behavior are implemented.
- Cache keys contain authorization scope and all relevant version inputs.
- Invalidation prevents stale data after sync, permissions, model, embedding, prompt, document, and memory changes.
- Cache outage does not break core read-only behavior.
- Benchmarks show measurable benefit without leakage or correctness regression.
- Three consecutive clean cache/isolation/recovery runs exist.

## Milestone 5

- Real-time subscriptions are authenticated and client scoped.
- Reconnect, replay, duplicate, rate-limit, and outage behavior are tested.
- Events contain only necessary data.
- Event infrastructure failure degrades safely.

## Milestone 6

- Technician suggestions and drafts cite authorized evidence and label inference.
- Weak evidence abstains or clearly qualifies.
- Drafts are review-only and never written to Autotask.
- Prompt-injection, secret leakage, cross-client, timeout, and verifier-failure cases fail safely.
- Technician acceptance/correction metrics are captured.

## Milestone 7

- Prediction targets, labels, training/evaluation data, and leakage controls are documented.
- Predictions show evidence, sample size, freshness, confidence, limitations, and reason codes.
- Holdout evaluation beats a defined simple baseline.
- Calibration and abstention are measured.
- Bias and client/category concentration risks are reviewed.

## Milestone 8

- Routing remains recommendation-only.
- Recommendations include workload, skill, history, customer familiarity, and reason codes.
- Accuracy, acceptance, concentration, and fairness metrics are recorded.
- No assignment write route or hidden write path exists.

## Milestone 9

- Customer-success insights are authorized, fresh, evidence linked, and explainable.
- Evidence is separated from inference and business recommendation.
- Account-facing drafts remain review-only.
- Cross-client aggregation is prohibited unless explicitly authorized.

## Milestone 10

- All release-target milestones are `verified_complete`.
- Full CI and Quality Streak evidence is current.
- Backup/restore, restart, dependency-outage, deployment, and rollback drills pass.
- Monitoring, alerting, retention, capacity, and runbooks are verified.
- Policy-to-runtime review passes.
- No critical blocker or release-critical unknown remains.
- The residual 1% backlog is documented as noncritical and explicitly deferred.
- The sanitized Second Brain projection is current with exact source evidence.
