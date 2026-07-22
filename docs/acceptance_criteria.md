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
- Current canonical evidence: PR `newbie10122/autotask-ai#42` merged into `main` as `c688c6d622e60e866ee63302a1f577f498635741`, with GitHub Actions run `29882172665` passing. Control documents must reference PR #42 and the current runtime/predictive evidence rather than stale PR #41 or `agent/predictive-threshold-sweep` completion steps.

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
- Current branch evidence on `agent/m1-answer-safety-quality-streak`: `scripts/answer-safety-quality-streak.sh` runs the guardrail and RAG conversational test subset three consecutive times in the API container; repository-hygiene coverage verifies the script contract and no-sync/no-production behavior.
- Current branch validation: `./scripts/answer-safety-quality-streak.sh` passed 3/3 runs, each with `20 passed`; full `./scripts/validate-ci.sh` passed with production-auth preflight, 10 ordered migrations, full pytest `102 passed`, static web JavaScript syntax, Playwright browser smoke `6 passed`, and `git diff --check`. This is answer-safety streak evidence only; live production-auth enforcement, remaining scope/cache certification, and other capability Quality Streak evidence remain required.
- Current branch evidence on `agent/m1-summary-cache-scope-contracts`: ticket-health and customer-success summary caches now use scoped cache-key helpers with authority class, roles, explicit scope, version, and TTL config; tests prove role/scope separation for both active summary cache consumers.
- Current branch validation: focused cache contract tests passed with `5 passed`; full `./scripts/validate-ci.sh` passed with production-auth preflight, 10 ordered migrations, full pytest `104 passed`, static web JavaScript syntax, Playwright browser smoke `6 passed`, and `git diff --check`. This is cache isolation evidence only; live production-auth enforcement and broader capability Quality Streak evidence remain required.
- Current branch evidence on `agent/m1-scope-certification-ticket-health-routing`: ticket-health, customer-success, and routing local capability functions accept authorized company scope; scoped calls add local SQL filters; customer detail/feedback and ticket/routing lookups fail closed when scope does not include the requested company.
- Current branch validation: focused API/RAG tests passed with `47 passed`; full `./scripts/validate-ci.sh` passed with production-auth preflight, 10 ordered migrations, full pytest `107 passed`, static web JavaScript syntax, Playwright browser smoke `6 passed`, and `git diff --check`. This is local capability isolation evidence only; live production-auth enforcement, route exposure decisions, and broader capability Quality Streak evidence remain required.
- Current branch evidence on `agent/m1-realtime-scope-certification`: realtime ticket-history helpers accept authorized company scope, filter ticket-history events by ticket company, and hide global job events from scoped callers unless explicitly allowed.
- Current branch validation: focused API/RAG tests passed with `48 passed`; full `./scripts/validate-ci.sh` passed with production-auth preflight, 10 ordered migrations, full pytest `108 passed`, static web JavaScript syntax, Playwright browser smoke `6 passed`, and `git diff --check`. This is realtime isolation evidence only; live production-auth enforcement, route exposure decisions, and broader capability Quality Streak evidence remain required.
- Current branch evidence on `agent/m1-scoped-local-capability-routes`: read-only ticket-health, customer-success, routing, and realtime GET routes are company-scoped in the API route matrix; route tests prove authorized company scope and scoped cache context are passed into local capability functions.
- Current branch validation: focused API tests passed with `30 passed`; full `./scripts/validate-ci.sh` passed with production-auth preflight, 10 ordered migrations, full pytest `110 passed`, static web JavaScript syntax, Playwright browser smoke `6 passed`, and `git diff --check`. This is route-contract evidence only; live production-auth enforcement, local feedback POST exposure decisions, and broader capability Quality Streak evidence remain required.
- Current branch evidence on `agent/m1-scoped-local-feedback-routes`: local ticket-health, customer-success, and routing feedback POST routes are restricted to Technician/Admin roles, pass authorized company scope into local feedback helpers, and deny ReadOnly users.
- Current branch validation: focused API/RAG tests passed with `79 passed`; full `./scripts/validate-ci.sh` passed with production-auth preflight, 10 ordered migrations, full pytest `111 passed`, static web JavaScript syntax, Playwright browser smoke `6 passed`, and `git diff --check`. This is local feedback route-contract evidence only; live production-auth enforcement and broader capability Quality Streak evidence remain required.
- Current branch evidence on `agent/m1-cache-export-consumer-certification`: current active cache consumers are certified to use scoped cache machinery, direct unscoped cache-key imports are absent from active cache modules, and export/download API routes remain absent.
- Current branch validation: focused API/RAG tests passed with `49 passed`; full `./scripts/validate-ci.sh` passed with production-auth preflight, 10 ordered migrations, full pytest `112 passed`, static web JavaScript syntax, Playwright browser smoke `6 passed`, and `git diff --check`. This is cache/export certification evidence only; live production-auth enforcement and broader capability Quality Streak evidence remain required.
- Current branch evidence on `agent/m1-security-isolation-quality-streak`: `scripts/security-isolation-quality-streak.sh` runs the existing auth, route RBAC, audit, scope, scoped-cache, realtime, feedback, and verifier subset three consecutive times inside the API container.
- Current branch validation: `./scripts/security-isolation-quality-streak.sh` passed 3/3 runs, each with `46 passed`. This is local synthetic Quality Streak evidence only; live production-auth deployment evidence remains required.
- Current branch evidence on `agent/ask-ticket-detail-modal`: Ask Assistant `Based on Tickets` entries render as clickable buttons that open a local ticket-health detail modal using the existing scoped `/api/ticket-health/ticket-number/{ticket_number}` route; the modal shows ticket summary, status-duration, recent history, recent labor, and warnings.
- Current branch validation: `npm run test:web` passed with `8 passed`; full `./scripts/validate-ci.sh` passed with production-auth preflight, 10 ordered migrations, full pytest `112 passed`, static web JavaScript syntax, Playwright browser smoke `8 passed`, and `git diff --check`. This is conversational UI evidence only; live production-auth deployment evidence remains required.
- Current branch evidence on `agent/answer-ticket-links`: Ask Assistant ticket IDs embedded inside rendered answer paragraphs and bullet evidence render as clickable buttons that open the same scoped ticket-health detail modal.
- Current branch validation: `npm run test:web` passed with `9 passed`. This is conversational UI evidence only; live production-auth deployment evidence remains required.

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
- Current branch evidence on `agent/operations-automation-visibility`: the Operations UI exposes local TimeEntries/TicketHistory totals, scheduler state, heartbeat age, next due job, and recent related-data automation movement for open-ticket and estate TimeEntries/TicketHistory jobs.
- Current branch runtime evidence: read-only local operations checks on 2026-07-22 showed `scheduler.state=healthy`, `global_pause=false`, fresh heartbeat, `time_entries=49054`, `ticket_history=29340`, and recent successful related-data pulls/updates with zero failures.
- Current branch validation: `npm run test:web -- operations-automation.spec.js` passed with `1 passed`; `npm run test:web` passed with `10 passed`; full `./scripts/validate-ci.sh && git diff --check` passed with production-auth preflight, 10 ordered migrations, full pytest `112 passed`, static web JavaScript syntax, Playwright browser smoke `10 passed`, and whitespace checks. This is visibility and scheduler evidence only; historical catch-up, field certification, and three-run sync/recovery evidence remain required.

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
- Current branch evidence on `agent/predictive-ticket-review-ranking`: `/api/ticket-health/review-queue` exposes scoped review-only ticket ranking with Bayesian-smoothed local completed-ticket delay rates, local feedback calibration, sample size, confidence, reason codes, limitations, and low-sample abstention.
- Current branch validation: focused container tests passed with `4 passed` for route authority, scoped route propagation, predictive abstention, and Bayesian history/feedback score movement. This is predictive foundation evidence only; holdout evaluation, leakage controls, bias/concentration review, and production certification remain required.
- Current branch evidence on `agent/predictive-review-ui`: the Ticket Health web section displays predictive review queue counts, abstentions, confidence, sample size, reason codes, review-only guidance, and ticket-detail drilldown.
- Current branch validation: `npm run test:web -- ticket-health.spec.js` passed with `1 passed`; `npm run test:web` passed with `11 passed`. This is browser visibility evidence only; predictive evaluation and certification remain required.
- Current branch evidence on `agent/predictive-evaluation-baseline`: `/api/ticket-health/predictive-evaluation` reports holdout accuracy, precision, and recall for a simple priority baseline versus the Bayesian queue/priority delay signal, using older completed tickets for training and recent completed tickets for holdout.
- Current branch validation: focused container tests passed with `3 passed` for route authority, scoped route propagation, and binary metric calculations. This is initial evaluation evidence only; target/label documentation, leakage review, bias/concentration review, and production certification remain required.
- Current branch evidence on `agent/predictive-threshold-sweep`: predictive evaluation includes F1 and an advisory threshold sweep for Bayesian delay-rate thresholds without automatically changing ranking thresholds.
- Current branch validation: focused container tests passed with `2 passed` for binary metric F1 and threshold sweep ordering. This is evaluation evidence only; human review is required before changing thresholds.
- Current runtime evaluation evidence on canonical `main` `c688c6d622e60e866ee63302a1f577f498635741`: `/api/ticket-health/predictive-evaluation?limit=100&delayed_days_threshold=7` returned holdout size `100`, training groups `32`, statistical evaluated `100`, abstentions `0`, default statistical `accuracy=0.94`, `precision=null`, `recall=0.0`, and `f1=0.0`. The advisory best-F1 threshold was `0.05`, with `accuracy=0.3`, `precision=0.068`, `recall=0.833`, and `f1=0.125`.
- The default predictive signal must not be described as useful merely because aggregate accuracy is high; the measured default behavior misses all delayed tickets in the current local holdout.
- Lowering the threshold improves delayed-ticket recall in the current local holdout but causes substantial precision loss. Any threshold selection remains human-reviewed and advisory; no automatic threshold, model, routing, escalation, notification, assignment, or workflow change is authorized by this evidence.
- Next acceptance evidence must document target/label semantics, calibration bands, Brier score, PR/ROC secondary metrics, threshold confusion matrices, coverage/abstention, leakage review, sanitized client/category concentration analysis, a human-review threshold policy artifact, and a local read-only shadow evaluation mechanism.
- Current branch evidence on `agent/predictive-calibration-policy`: predictive evaluation now returns target/label semantics, Brier score, calibration bands, PR/ROC secondary metrics, coverage and abstention rates, sanitized company/category concentration buckets, a human-review threshold policy, and a local read-only shadow-evaluation contract. This is evidence only; no automatic threshold, model, routing, escalation, notification, assignment, or workflow change is authorized.
- Current branch validation: focused container validation passed for `apps/api/tests/test_ingestion_rag.py` with `56 passed`, scoped API route propagation coverage passed for `test_scoped_local_capability_routes_pass_company_scope`, and full governed validation passed with `119` API tests plus `11` Playwright tests. Local runtime evaluation after API rebuild returned coverage `1.0`, abstention rate `0.0`, Brier score `0.056`, ROC AUC `0.613`, PR AUC `0.115`, sanitized largest company bucket share `0.67`, and sanitized largest category bucket share `0.99`. Leakage review, broader bias review, model comparison, and production certification remain required.
- Current branch evidence on `agent/predictive-leakage-bias-review`: predictive evaluation now returns temporal leakage review, model comparison, and sanitized stratified company/category bucket metrics. It documents that training rows are completed before the holdout start, labels are only available after completion, queue/priority-at-creation source lineage is not yet certified, and model selection remains human-review only.
- Current branch validation: focused container validation passed for `apps/api/tests/test_ingestion_rag.py` with `59 passed`, and full governed validation passed with `122` API tests plus `11` Playwright tests. Local runtime evaluation after API rebuild returned `model_comparison.current_finding=statistical_signal_not_better_on_f1_or_recall`, F1/recall deltas of `0`, leakage review with `training_rows_after_or_during_holdout_included=0`, sanitized top company bucket share `0.67`, and sanitized top category bucket share `0.99`. Broader model evaluation, source-lineage certification, and production certification remain required.
- Current branch evidence on `agent/predictive-source-lineage`: predictive evaluation now returns source-lineage status for each current model input. Created/completed timestamps and company scope are marked locally available; queue, priority, and category-derived fields remain not fully certified for prediction until historical queue/priority-at-creation and reference completeness are certified.
- Current branch validation: focused container validation passed for `apps/api/tests/test_ingestion_rag.py` with `60 passed`, and full governed validation passed with `123` API tests plus `11` Playwright tests. Local runtime evaluation after API rebuild returned `source_lineage.certification_state=partial_source_lineage` with queue, priority, and category-derived fields marked not fully certified for prediction.
- Current branch evidence on `agent/m2-field-certification`: `/api/ticket-health/field-certification` returns scoped certification targets for TicketHistory, status-duration, TimeEntries/labor, SLA, and waiting-state lineage, and `/api/ticket-health/predictive-evaluation` includes that field-certification state in predictive source lineage.
- Current branch validation: focused container validation passed for field-certification and predictive source-lineage tests with `2 passed`, scoped route authority/scope propagation tests with `2 passed`, runtime local Postgres report execution succeeded, and `git diff --check` passed. Runtime field certification returned `partial_field_certification` with blockers `ticket_status_history`, `status_duration`, and `waiting_states`; this is read-only evidence and does not authorize model, threshold, routing, workflow, or Autotask changes.
- Current branch evidence on `agent/predictive-model-variants`: predictive evaluation now returns model-variant comparison for simple priority, global-prior, queue-only, priority-only, and queue+priority Bayesian signals. Runtime 100-ticket holdout evidence showed all variants retain default recall `0.0`; queue+priority remains the strongest secondary signal by ROC AUC `0.613` and PR AUC `0.115`, but no model selection or threshold/workflow change is authorized.
- Current branch validation: focused container validation passed for variant/model-comparison tests with `3 passed`, runtime local Postgres evaluation passed for 50-ticket and 100-ticket samples, and full governed validation passed with `125` API tests plus `11` Playwright browser tests.
- Current branch evidence on `agent/status-transition-certification`: field certification now includes a scoped TicketHistory transition parser summary. Runtime local evidence found `0` parsed status transitions and `0` timestamped status transitions in the inspected local TicketHistory sample, so status-duration and waiting-state analytics remain source-limited.
- Current branch validation: focused container validation passed for field-certification/parser tests with `2 passed`, runtime local Postgres field-certification smoke passed, and full governed validation passed with `126` API tests plus `11` Playwright browser tests.
- Current branch evidence on `agent/operations-field-certification-ui`: the Operations UI now displays scoped field-certification state, blockers, parser counts, and target certification cards from `/api/ticket-health/field-certification`.
- Current branch validation: focused Playwright validation passed for `apps/web/tests/operations-automation.spec.js` with `1 passed`, static web JavaScript syntax validation passed, and full governed validation passed with `126` API tests plus `11` Playwright browser tests.
- Current branch evidence on `agent/status-transition-source-candidates`: `/api/ticket-health/status-transition-sources` returns a scoped, read-only source-candidate contract for local TicketHistory, current ticket status, proxy ticket timestamps, and unprobed candidate Autotask status-history entities. Field certification embeds the same report. The report explicitly states that no live Autotask probe ran, no Autotask writes are allowed, and no automatic sync-path/model/workflow changes are authorized.
- Current branch validation: focused container validation passed for field-certification/source-candidate/parser tests with `3 passed`, scoped route authority/scope propagation tests with `2 passed`, and full governed validation passed with `127` API tests plus `11` Playwright browser tests.
- Current branch evidence on `agent/status-history-entity-probe`: `POST /api/autotask/probe/status-transition-sources` gives Admin users a manual bounded read-only availability probe for candidate status-history entities with `MaxRecords=1` per entity, per-entity error isolation, safe audit metadata, and explicit policy flags blocking Autotask writes, automatic sync-path changes, and automatic model/workflow changes.
- Current branch validation: focused container validation passed for bounded probe/client and company-sync compatibility tests with `3 passed`; focused admin route matrix, route authority, and success-audit tests passed with `3 passed`.
- Current branch evidence on `agent/status-probe-error-isolation`: repeated unavailable candidate entities no longer trip the read-only client's consecutive-error breaker across candidates; every candidate is attempted independently and reported with per-entity status.
- Current branch validation: focused container validation passed for bounded probe/error-isolation tests with `2 passed`.
- Current branch evidence on `agent/status-probe-entity-filters`: the bounded status-transition probe now uses per-entity read-only filters and reports the filter used; `TicketHistory` is probed by `ticketID` instead of generic `id`, matching the existing read-only sync contract.
- Current branch validation: focused container validation passed for bounded probe filter/error-isolation tests with `3 passed`.
- Current branch evidence on `agent/status-probe-ticket-history-sample`: the bounded `TicketHistory` availability probe now prefers a real local `autotask_tickets.autotask_id` and queries `ticketID eq <local ticket>` with `MaxRecords=1`; if no local ticket exists it falls back to `ticketID >= 0`.
- Current branch validation: focused container validation passed for bounded probe sample-ticket/filter/error-isolation tests with `4 passed`.
- Post-merge runtime evidence on canonical `main` `9cc33aaf6ed3987d45a43e96713a7c39609bdcfc`: the bounded read-only probe returned 404 for `TicketStatusHistory`, `TicketStatusHistories`, and `TicketChangeHistory`; `TicketHistory` was available with one sampled row using `ticketID eq <local ticket>` and reported a next page. This confirms the current reachable read-only history source is still `TicketHistory`; status-duration/waiting certification remains blocked by row content/parser shape, not by lack of basic `TicketHistory` reachability.
- Current branch evidence on `agent/ticket-history-content-certification`: `/api/ticket-health/ticket-history-content-certification` returns scoped aggregate-only TicketHistory content evidence, including action counts, action categories, status-like row counts, timestamp coverage, and raw-key counts. It intentionally omits raw detail text and keeps parser/model/workflow changes disabled.
- Current branch validation: focused container validation passed for content-certification and scoped route propagation tests with `2 passed`.
- Current branch evidence on `agent/ticket-history-content-runtime-fix`: runtime validation found the content-certification query needed qualified `h.raw` references in joined SQL; the query now qualifies TicketHistory raw JSON fields and has regression coverage.

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
