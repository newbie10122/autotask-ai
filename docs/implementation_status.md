# Autotask AI Implementation Status

**Updated:** 2026-07-22
**Management target:** 99% verified roadmap completion  
**Current state:** `partial`  
**Active milestone:** Milestone 1 — Security, identity, isolation, and answer trust

## Status confidence

The repository has a substantial implemented MVP foundation, but no roadmap milestone is yet marked `verified_complete` under `AGENTS.md`. Current verified completion cannot be represented honestly as a percentage until acceptance evidence, the capability certification matrix, and Quality Streak records are established.

## Implemented foundation

- Canonical `main` is `be7cc143af44b21e2bf9929737d8071d4ff41920`, which merged PR `newbie10122/autotask-ai#51`.
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
- Milestone 1 browser accessibility branch `agent/m1-browser-accessibility-smoke` adds Playwright axe smoke coverage for serious/critical accessibility violations and login accessible-name behavior.
- Milestone 1 keyboard/focus branch `agent/m1-keyboard-focus-smoke` adds explicit focus-visible styling and Playwright keyboard traversal evidence for navigation, auth, and ask workflow controls.
- Milestone 1 source-sufficiency branch `agent/m1-source-sufficiency-verifier` adds ticket-history source-overlap checks for non-resolution factual claims.
- Milestone 1 active scoped-cache branch `agent/m1-active-scoped-cache-consumer` moves the operations-status cache consumer onto the scoped cache-key contract.
- Milestone 1 production-auth preflight branch `agent/m1-production-auth-preflight` adds CI-validated production auth boundary checks.
- Milestone 1 bootstrap/admin-user branch `agent/m1-bootstrap-admin-user` adds a local operator command for creating or updating hashed app users without storing plaintext passwords.
- Milestone 1 adversarial verifier branch `agent/m1-adversarial-verifier-breadth` broadens conversational answer-safety checks for ticket-source metadata, cross-ticket evidence mismatch, and weak/no-evidence fallback language.
- Milestone 1 generated-answer verifier branch `agent/m1-generated-answer-verifier-evidence` exercises generated assistant answers through redaction, source metadata, verifier fallback, and audit behavior.
- Milestone 1 answer-safety Quality Streak branch `agent/m1-answer-safety-quality-streak` adds a repeatable three-run conversational answer-safety streak harness.
- Milestone 1 summary-cache scope branch `agent/m1-summary-cache-scope-contracts` moves ticket-health and customer-success summary cache keys onto the scoped cache contract.
- Milestone 1 ticket-health/customer-success/routing scope branch `agent/m1-scope-certification-ticket-health-routing` adds optional company-scope filters and fail-closed detail/feedback behavior for local capability functions.
- Milestone 1 realtime scope branch `agent/m1-realtime-scope-certification` adds authorized-company filtering for ticket-history realtime events and hides global job events from scoped callers.
- Milestone 1 scoped local capability routes branch `agent/m1-scoped-local-capability-routes` exposes scoped read-only ticket-health, customer-success, routing, and realtime GET routes with route-matrix and scope-propagation tests.
- Milestone 1 scoped local feedback routes branch `agent/m1-scoped-local-feedback-routes` exposes local-only ticket-health, customer-success, and routing feedback POST routes for Technician/Admin users with company-scope propagation and ReadOnly denial.
- Milestone 1 cache/export consumer certification branch `agent/m1-cache-export-consumer-certification` asserts current active cache consumers use scoped cache contracts and no export/download routes exist.
- Milestone 1 security/isolation Quality Streak branch `agent/m1-security-isolation-quality-streak` adds a repeatable three-run harness for auth, route RBAC, audit, scope, scoped-cache, realtime, feedback, and verifier evidence.
- Conversational UI branch `agent/ask-ticket-detail-modal` makes Ask Assistant ticket evidence inspectable by turning `Based on Tickets` entries into scoped ticket-detail modal links.
- Conversational UI branch `agent/answer-ticket-links` makes ticket IDs inside rendered assistant answer text open the same scoped ticket-detail modal.
- Operations visibility branch `agent/operations-automation-visibility` exposes scheduler heartbeat, next due job, TimeEntries/TicketHistory totals, and recent related-data job movement in the Operations UI.
- Predictive ticket review branch `agent/predictive-ticket-review-ranking` adds a scoped review-only ticket-health queue with Bayesian-smoothed historical completion signals, local-feedback calibration, reason codes, confidence, and low-sample abstention.
- Predictive review UI branch `agent/predictive-review-ui` adds a Ticket Health screen for predictive queue summary, ranked/abstained counts, confidence, sample size, reason codes, and ticket-detail drilldown.
- Predictive evaluation branch `agent/predictive-evaluation-baseline` adds a scoped holdout report comparing a simple priority baseline against the Bayesian statistical delay signal.
- Predictive threshold sweep branch `agent/predictive-threshold-sweep` adds read-only threshold sweep and F1 evidence to the predictive holdout report.

## Verified gaps blocking production readiness

- Route authentication/RBAC is implemented as an opt-in foundation and sensitive mutating/admin-inspection API routes now have a tested authority matrix. A production-auth preflight now requires app-route auth or an explicit external-auth boundary, but live production enforcement remains approval-gated.
- Audit logging is database-backed for foundation, denial, and first material success events, but identity/company-scope linkage is not yet complete across every workflow.
- Assistant retrieval, recurring-issue analytics, query rows, query sources, feedback, pending memory candidates, answer verification, static web controls, active operations-status cache consumption, ticket-health/customer-success summary cache keys, ticket-health/customer-success/routing local capability functions, scoped read-only local capability routes, scoped local feedback routes, realtime ticket-history events, browser RBAC smoke coverage, first browser accessibility smoke coverage, and keyboard/focus smoke coverage have scope/RBAC plumbing, but scope is not yet fully certified with production-auth deployment evidence.
- Prompt-injection scanning and deterministic answer verification have tests for citations, scope, secrets, injection, required sections, guidance labels, verifier-failure audit, unsupported ticket-history resolution claims, and first non-resolution ticket-history source sufficiency checks; broader adversarial verifier evidence remains open.
- Answer-safety and security/isolation have candidate three-run local Quality Streak harnesses and local 3/3 evidence, but live production-auth deployment evidence remains open; the validation harness has three browser-enabled clean evidence points recorded in `docs/CI_VALIDATION.md`.
- Governed memory approval/version/rollback workflow is incomplete.
- Ticket-health related-data synchronization is automated and now visibly inspectable in the Operations UI. Runtime evidence on 2026-07-22 showed the scheduler healthy, recent scheduled jobs completing, and local counts at `tickets=67726`, `time_entries=49950`, and `ticket_history=29760`; historical estate coverage still requires continued bounded scheduled sweeps and field/source-lineage certification.
- Predictive evaluation currently shows that the default Bayesian delay signal has high aggregate accuracy but zero delayed-ticket recall on the local 100-ticket holdout: `accuracy=0.94`, `recall=0.0`, `f1=0.0`. The advisory best-F1 threshold in that same report is `0.05`, with `precision=0.068`, `recall=0.833`, and `f1=0.125`; this is evidence for human review only and does not authorize automatic threshold, model, routing, escalation, or workflow changes.
- Predictive calibration branch `agent/predictive-calibration-policy` extends the same read-only evaluation report with target/label semantics, Brier score, calibration bands, PR/ROC secondary metrics, threshold coverage/abstention, sanitized client/category concentration, a human-review threshold policy, and a local read-only shadow-evaluation contract.
- Predictive leakage/bias branch `agent/predictive-leakage-bias-review` extends the evaluation report with explicit temporal leakage review, model comparison, and sanitized stratified metrics for company/category buckets.
- Predictive source-lineage branch `agent/predictive-source-lineage` adds a `source_lineage` section to the evaluation report that marks created/completed timestamps and company scope as locally available while explicitly treating queue/priority current fields and category labels as not fully certified for prediction.
- Milestone 2 field-certification branch `agent/m2-field-certification` adds scoped field-certification evidence to the API and predictive evaluation. Local runtime evidence returned `certification_state=partial_field_certification`, summary `certified=2`, `partial=1`, `source_limited=2`, and blockers `ticket_status_history`, `status_duration`, and `waiting_states`; no sync job, Autotask write, model threshold change, or workflow change was run or added.
- Predictive model-variants branch `agent/predictive-model-variants` broadens the read-only holdout report with global-prior, queue-only, priority-only, and queue+priority Bayesian variants alongside the simple priority baseline. Local runtime evidence on the 100-ticket holdout showed all variants still have default recall `0.0`; queue+priority remains the strongest secondary signal by ROC AUC `0.613` and PR AUC `0.115`, but no model selection or threshold/workflow change is authorized.
- Status-transition certification branch `agent/status-transition-certification` adds a scoped parser summary for local TicketHistory action/detail rows and feeds it into field certification. Local runtime evidence found `0` parsed status transitions and `0` timestamped status transitions in the inspected local TicketHistory sample, so status-duration and waiting-state analytics remain source-limited until a usable read-only status-transition source is found or backfilled.
- Operations field-certification UI branch `agent/operations-field-certification-ui` surfaces `/api/ticket-health/field-certification` in the Operations screen with certification state, blockers, parser counts, and target cards so operators can see why status-duration/waiting are not yet fully certified.
- Status-transition source-candidates branch `agent/status-transition-source-candidates` adds a scoped, read-only `/api/ticket-health/status-transition-sources` report and embeds the same source-candidate contract in field certification. It classifies local TicketHistory, current status, proxy timestamps, and unprobed candidate Autotask status-history entities without running a live Autotask probe or authorizing any sync/write/model workflow change.
- Status-history entity probe branch `agent/status-history-entity-probe` adds an Admin-only manual `POST /api/autotask/probe/status-transition-sources` endpoint that uses the read-only Autotask client with `MaxRecords=1` per candidate entity, per-entity error isolation, and success-audit metadata. It does not schedule probes, write to Autotask, or authorize automatic sync-path/model/workflow changes.

## Milestone table

| Milestone | State | Next evidence required |
|---|---|---|
| 0. Governance and continuous validation | partial | Certification matrix added and validation-harness streak recorded; capability Quality Streaks remain open |
| 1. Security, identity, isolation, answer trust | active | Complete durable audit, full route/UI RBAC, company scope wiring, verifier breadth, and three-run evidence |
| 2. Complete operational Autotask data | partial_foundation | TimeEntries/TicketHistory jobs restored and visible; continue bounded catch-up and field certification |
| 3. Ticket Health Analytics | not_started | Deterministic APIs/UI with evidence |
| 4. Redis and CPU performance | not_started | Scoped cache design and benchmarks |
| 5. Real-time technician updates | not_started | Authorized event architecture |
| 6. Technician Performance Assistant | partial_foundation | Current RAG exists; guided/draft workflows not certified |
| 7. Predictive Service Intelligence | partial_foundation | Review-only statistical ticket ranking plus initial holdout/threshold/calibration/leakage/bias/source-lineage evidence exists; broader model evaluation, Milestone 2 field certification, and production certification remain open |
| 8. Routing recommendations | not_started | Resource/workload data and evaluation |
| 9. Customer Success Intelligence | not_started | Certified internal capabilities |
| 10. Production certification/99% closeout | not_started | All target milestones and evidence |

## Active execution queue

1. Validate and merge `agent/status-history-entity-probe`, then update the existing Second Brain projection.
2. If an Admin intentionally runs the bounded read-only probe and a status-transition entity is available, design a review-only sync candidate; otherwise proceed to the next Milestone 1 audit/scope closeout slice.
3. Continue production-auth deployment evidence only when explicitly approved for that protected action.
4. Add remaining production-auth deployment evidence and targeted capability Quality Streak evidence without marking milestones complete prematurely.

Parallel-safe work after roadmap merge:

- Agent A: CI and repository validation.
- Agent B: authentication/RBAC design and negative tests.
- Agent C: client-scope data model and retrieval isolation analysis/tests.
- Agent D: prompt-injection and independent verifier contract/tests.
- Independent verifier: review threat model, overlap, integration order, and acceptance coverage.

Shared schema and integration changes must be serialized by the coordinator.

## Critical blockers

None currently identified for documentation and non-production implementation work. Production deployment, customer-data scope expansion, irreversible migrations, and any Autotask write capability remain approval-gated.

## Latest receipt — Operations field-certification UI evidence

- **Slice:** Surface field-certification evidence in the Operations UI on branch `agent/operations-field-certification-ui` from canonical `main` `df85cae244e9f3d4aa1ec01b409088666c730835`.
- **State:** `partial_foundation`; the UI now makes certification blockers visible, but underlying status-duration/waiting certification remains source-limited.
- **Files changed:** `apps/web/index.html`, `apps/web/tests/helpers.js`, `apps/web/tests/operations-automation.spec.js`, and project status docs.
- **Implemented:** Operations now loads `/api/ticket-health/field-certification` alongside automation status and renders field-certification state, blockers, parsed/timestamped status-transition counts, and target cards for certification status, coverage, and predictive-use policy.
- **Validation:** focused browser validation passed for `apps/web/tests/operations-automation.spec.js` with `1 passed`, static web JavaScript syntax validation passed, and full governed validation passed with production-auth preflight, redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `126 passed`, static web JavaScript syntax validation, Playwright browser smoke `11 passed`, and clean `git diff --check`.
- **Read-only evidence:** No sync jobs, production deployment, live credential changes, local feedback writes, Autotask writes, model threshold changes, routing, escalation, notification, assignment, status, priority, or workflow changes were run or added.
- **Rollback:** Revert this branch commit; Operations UI falls back to PR #50 without the field-certification panel.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Status-transition parser certification evidence

- **Slice:** Add scoped TicketHistory transition parser certification on branch `agent/status-transition-certification` from canonical `main` `10e3b35517c5bec87f22461fbd3a0a7d0b769b5f`.
- **State:** `partial_foundation`; field certification now includes parser evidence, but status-duration and waiting-state certification remain source-limited because local TicketHistory rows do not currently parse into status transitions.
- **Files changed:** `apps/api/app/ticket_health.py`, `apps/api/tests/test_ingestion_rag.py`, and project status docs.
- **Implemented:** `ticket_history_transition_parse_summary()` computes scoped parse counts, status-transition counts, timestamped status-transition counts, parsed categories, and source-limited state without exposing raw TicketHistory samples. `field_certification_report()` now requires parsed and timestamped status transitions before status-duration/waiting can leave source-limited status.
- **Validation:** focused container validation passed for field-certification/parser tests with `2 passed`, runtime local Postgres field-certification smoke passed, and full governed validation passed with production-auth preflight, redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `126 passed`, static web JavaScript syntax validation, Playwright browser smoke `11 passed`, and clean `git diff --check`.
- **Runtime evidence:** Local field certification returned blockers `ticket_status_history`, `status_duration`, and `waiting_states`; parser evidence returned `parsed_status_transitions=0`, `timestamped_status_transitions=0`, and `source_limited=true`.
- **Read-only evidence:** No sync jobs, production deployment, live credential changes, local feedback writes, Autotask writes, model threshold changes, routing, escalation, notification, assignment, status, priority, or workflow changes were run or added.
- **Rollback:** Revert this branch commit; field certification falls back to PR #49 behavior without parser-summary gating.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Predictive model-variant evaluation evidence

- **Slice:** Add read-only predictive model-variant comparison on branch `agent/predictive-model-variants` from canonical `main` `60923182c007fb9337bc7fc956c3cfbf4086c242`.
- **State:** `partial_foundation`; predictive evaluation now compares additional variants, but no model is selected and Milestone 7 remains blocked by weak default delayed-ticket recall, Milestone 2 status-duration/waiting blockers, three-run evidence, and production certification.
- **Files changed:** `apps/api/app/ticket_health.py`, `apps/api/tests/test_ingestion_rag.py`, and project status docs.
- **Implemented:** `/api/ticket-health/predictive-evaluation` now returns `model_variants` with simple priority baseline, global prior, queue-only, priority-only, and queue+priority Bayesian variants. Each variant includes metrics, Brier/AUC where probability evidence exists, advisory threshold sweep, features, lineage status, `review_only=true`, and `selection_allowed=false`.
- **Validation:** focused container validation passed for variant/model-comparison tests with `3 passed`; runtime local Postgres evaluation passed for 50-ticket and 100-ticket samples; full governed validation passed with production-auth preflight, redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `125 passed`, static web JavaScript syntax validation, Playwright browser smoke `11 passed`, and clean `git diff --check`.
- **Runtime evidence:** On `/api/ticket-health/predictive-evaluation?limit=100&delayed_days_threshold=7`, all variants retained default recall `0.0` and F1 `0.0`; global-prior and priority-only Brier score `0.057`, queue-only Brier `0.056`, queue+priority Brier `0.056`, queue+priority ROC AUC `0.613`, and queue+priority PR AUC `0.115`.
- **Read-only evidence:** No sync jobs, production deployment, live credential changes, local feedback writes, Autotask writes, model selection, model threshold changes, routing, escalation, notification, assignment, status, priority, or workflow changes were run or added.
- **Rollback:** Revert this branch commit; predictive evaluation falls back to PR #48 behavior with field-certification evidence and the original baseline/statistical comparison.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Milestone 2 field-certification evidence

- **Slice:** Add scoped Milestone 2 field-certification evidence on branch `agent/m2-field-certification` from canonical `main` `99937d5113b0cc78270bf9a718f1cb4692ba2b28`.
- **State:** `partial_foundation`; the app now exposes scoped certification status for TicketHistory, status-duration, TimeEntries/labor, SLA, and waiting-state lineage, but Milestone 2 is not complete because TicketHistory/status-duration/waiting evidence remains partial or source-limited.
- **Files changed:** `apps/api/app/main.py`, `apps/api/app/ticket_health.py`, `apps/api/tests/test_api.py`, `apps/api/tests/test_ingestion_rag.py`, and project status docs.
- **Implemented:** `/api/ticket-health/field-certification` returns scoped local field-certification targets, blockers, summarized source reports, and a predictive-use policy. `/api/ticket-health/predictive-evaluation` now includes `field_certification` and carries Milestone 2 excluded fields into `source_lineage` without changing model thresholds, rankings, workflows, or Autotask data.
- **Validation:** focused container validation passed for field-certification/predictive-source-lineage tests with `2 passed`, scoped route authority/scope propagation tests with `2 passed`, runtime local Postgres report execution succeeded, and full governed validation passed with production-auth preflight, redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `124 passed`, static web JavaScript syntax validation, Playwright browser smoke `11 passed`, and clean `git diff --check`.
- **Runtime evidence:** Local read-only report returned `certification_state=partial_field_certification`, summary `certified=2`, `partial=1`, `source_limited=2`, blockers `ticket_status_history`, `status_duration`, and `waiting_states`; predictive evaluation returned the same field-certification state and excluded blockers in source lineage.
- **Read-only evidence:** No sync jobs, production deployment, live credential changes, local feedback writes, Autotask writes, model threshold changes, routing, escalation, notification, assignment, status, priority, or workflow changes were run or added.
- **Rollback:** Revert this branch commit; predictive evaluation falls back to PR #47 behavior with source-lineage evidence but no field-certification rollup.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Predictive source-lineage evidence

- **Slice:** Add predictive source-lineage evidence on branch `agent/predictive-source-lineage` from canonical `main` `a2a2a3c98245307438d8d26005aecd6403fce0f6`.
- **State:** `partial_foundation`; the evaluation report now identifies which local fields are certified enough for the current evaluation and which remain current-field proxies, but no threshold/model/routing/workflow behavior is changed and Milestone 7 still requires broader model evaluation, Milestone 2 field certification, and production certification.
- **Files changed:** `apps/api/app/ticket_health.py`, `apps/api/tests/test_ingestion_rag.py`, and project status docs.
- **Implemented:** `/api/ticket-health/predictive-evaluation` now returns `source_lineage` with per-field source, use, lineage status, and prediction-certification state. Created/completed timestamps and company scope are marked locally available; queue, priority, and category-derived fields remain not fully certified for prediction because historical queue/priority-at-creation and reference completeness are still open.
- **Validation:** focused container validation passed for `apps/api/tests/test_ingestion_rag.py` with `60 passed`. Full governed validation passed with production-auth preflight, redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `123 passed`, static web JavaScript syntax validation, Playwright browser smoke `11 passed`, and `git diff --check`.
- **Runtime evidence:** After rebuilding the local API from this branch, `/ready` returned ready. The predictive evaluation endpoint returned `source_lineage.certification_state=partial_source_lineage`, marked `created_at_autotask`, `completed_at_autotask`, and `company_id` as locally available/certified for the current evaluation, and marked queue, priority, and category-derived fields as not fully certified for prediction.
- **Read-only evidence:** No sync jobs, production deployment, live credential changes, local feedback writes, or Autotask write capability were run or added.
- **Rollback:** Revert this branch commit; predictive evaluation falls back to the PR #45 leakage/bias report.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Predictive leakage and bias review evidence

- **Slice:** Add predictive temporal leakage review, model comparison, and sanitized stratified bias evidence on branch `agent/predictive-leakage-bias-review` from canonical `main` `afb0bb1b9c4d26505b16078c547ec9b4f07ad66a`.
- **State:** `partial_foundation`; the evaluation report now exposes broader review evidence, but no threshold/model/routing/workflow behavior is changed and Milestone 7 still requires broader model evaluation, source-lineage certification, and production certification.
- **Files changed:** `apps/api/app/ticket_health.py`, `apps/api/tests/test_ingestion_rag.py`, and project status docs.
- **Implemented:** `/api/ticket-health/predictive-evaluation` now returns `leakage_review`, `model_comparison`, and `stratified_metrics` sections. Leakage review documents the temporal split and known source-lineage limitations. Model comparison reports deterministic baseline versus Bayesian signal deltas and blocks model selection without human review. Stratified metrics show sanitized top company/category bucket metrics without exposing customer names, raw category labels, or raw company IDs.
- **Validation:** focused container validation passed for `apps/api/tests/test_ingestion_rag.py` with `59 passed`. Full governed validation passed with production-auth preflight, redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `122 passed`, static web JavaScript syntax validation, Playwright browser smoke `11 passed`, and `git diff --check`.
- **Runtime evidence:** After rebuilding the local API from this branch, `/ready` returned ready. The predictive evaluation endpoint returned `model_comparison.current_finding=statistical_signal_not_better_on_f1_or_recall`, baseline and Bayesian statistical F1/recall deltas of `0`, leakage review with `training_rows_after_or_during_holdout_included=0`, sanitized top company bucket share `0.67` with actual delayed rate `0.075`, and sanitized top category bucket share `0.99` with actual delayed rate `0.051`.
- **Read-only evidence:** No sync jobs, production deployment, live credential changes, local feedback writes, or Autotask write capability were run or added. The evidence remains local, review-only, and non-operational.
- **Rollback:** Revert this branch commit; predictive evaluation falls back to the PR #44 calibration-policy report.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Predictive calibration and human-review policy

- **Slice:** Add predictive calibration, sanitized concentration, human-review threshold policy, and read-only shadow-evaluation evidence on branch `agent/predictive-calibration-policy` from canonical `main` `14a3784fa8b109495a7b2abc14b860e5113bb873`.
- **State:** `partial_foundation`; the evaluation report now carries stronger evidence for human review, but no threshold/model/routing/workflow behavior is changed and Milestone 7 still requires leakage review, broader bias review, model comparison, and production certification.
- **Files changed:** `apps/api/app/ticket_health.py`, `apps/api/tests/test_ingestion_rag.py`, and project status docs.
- **Implemented:** `/api/ticket-health/predictive-evaluation` now returns target/label semantics, Brier score, calibration bands, PR/ROC secondary metrics, coverage and abstention rates, sanitized company/category concentration buckets, a human-review threshold policy, and a local read-only shadow-evaluation contract. Dynamic warnings call out zero default recall and low-precision best-F1 thresholds when observed.
- **Validation:** focused container validation passed for `apps/api/tests/test_ingestion_rag.py` with `56 passed`; scoped route propagation test passed for `test_scoped_local_capability_routes_pass_company_scope`. Full governed validation passed with production-auth preflight, redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `119 passed`, static web JavaScript syntax validation, Playwright browser smoke `11 passed`, and `git diff --check`.
- **Runtime evidence:** After rebuilding the local API from this branch, `/ready` returned ready. The first immediate `/ready` probe during API recreation returned a transient Nginx `502` while the upstream container was restarting; subsequent readiness was `200` and API logs showed startup complete. The predictive evaluation endpoint returned target semantics, coverage `1.0`, abstention rate `0.0`, Brier score `0.056`, ROC AUC `0.613`, PR AUC `0.115`, sanitized largest company bucket share `0.67`, sanitized largest category bucket share `0.99`, and warnings for zero default recall and low-precision best-F1 threshold.
- **Read-only evidence:** No sync jobs, production deployment, live credential changes, local feedback writes, or Autotask write capability were run or added. The shadow-evaluation contract explicitly reports no Autotask writes, notifications, threshold changes, or workflow changes.
- **Rollback:** Revert this branch commit; predictive evaluation falls back to the PR #42 threshold-sweep report.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Predictive threshold sweep

- **Slice:** Add predictive evaluation threshold-sweep evidence on branch `agent/predictive-threshold-sweep`; merged as PR `newbie10122/autotask-ai#42` into canonical `main` `c688c6d622e60e866ee63302a1f577f498635741`.
- **State:** `partial_foundation`; the evaluation report can now compare candidate Bayesian delay thresholds by precision, recall, and F1, but no threshold changes are applied automatically and Milestone 7 still requires bias/concentration review and production certification.
- **Files changed:** `apps/api/app/ticket_health.py`, `apps/api/tests/test_ingestion_rag.py`, and project status docs.
- **Implemented:** Predictive evaluation metrics now include F1, and `/api/ticket-health/predictive-evaluation` returns `threshold_sweep` plus `best_threshold_by_f1` as advisory evidence. The sweep is explicitly review-only and does not tune weights or alter ranking behavior.
- **Validation:** focused container tests passed with `2 passed`: binary metric F1 and threshold sweep ordering. GitHub Actions run `29882172665` passed workflow `CI`, job `Validate Autotask AI`, for PR #42 before merge. Local runtime evaluation on 2026-07-22 returned holdout size `100`, training groups `32`, default statistical `accuracy=0.94`, `recall=0.0`, `f1=0.0`, and advisory best-F1 threshold `0.05` with `precision=0.068`, `recall=0.833`, and `f1=0.125`.
- **Read-only evidence:** No sync jobs, production deployment, live credential changes, local feedback writes, or Autotask write capability were run or added.
- **Rollback:** Revert this branch commit; predictive evaluation remains available without F1/threshold-sweep evidence.
- **Second Brain state:** `pull-request-open`; existing projection PR `newbie10122/helix-second-brain#6` was updated through PR #42 at branch head `8a7919e89b5f171a84d3be3913b4c54a971e6925` with local `python3 tools/validate_knowledge.py` passing. It is not marked merged.

## Previous receipt — Predictive evaluation baseline

- **Slice:** Add a read-only predictive holdout evaluation report on branch `agent/predictive-evaluation-baseline` from canonical `main` `0e2f122db69d6ce367e82f792de4ff5c6ad97fe1`.
- **State:** `partial_foundation`; predictive ranking now has initial local holdout metrics, but Milestone 7 still requires broader target/label documentation, bias/concentration review, leakage review, and production certification.
- **Files changed:** `apps/api/app/ticket_health.py`, `apps/api/app/main.py`, `apps/api/tests/test_api.py`, `apps/api/tests/test_ingestion_rag.py`, and project status docs.
- **Implemented:** `/api/ticket-health/predictive-evaluation` compares a simple priority baseline with the Bayesian queue/priority delay signal over recent completed-ticket holdout rows. Training data is limited to tickets completed before the holdout window, low-sample statistical rows abstain, and the report returns accuracy, precision, recall, sample counts, and leakage/bias warnings.
- **Validation:** focused container tests passed with `3 passed`: route authority matrix, scoped route propagation, and binary classification metric calculations.
- **Read-only evidence:** No sync jobs, production deployment, live credential changes, local feedback writes, or Autotask write capability were run or added; the report reads local completed-ticket history only and does not tune weights automatically.
- **Rollback:** Revert this branch commit; predictive review ranking remains available, but the evaluation report route is removed.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Predictive review UI

- **Slice:** Surface review-only predictive ticket ranking in the web UI on branch `agent/predictive-review-ui` from canonical `main` `ab65f9390ac3ad69f44648a564b6830dfd906bf5`.
- **State:** `partial_foundation`; technicians can now inspect predictive ranking and abstention evidence in the browser, but Milestone 7 still requires holdout evaluation, leakage controls, bias/concentration review, and production certification.
- **Files changed:** `apps/web/index.html`, `apps/web/styles.css`, `apps/web/tests/helpers.js`, `apps/web/tests/accessibility.spec.js`, `apps/web/tests/ticket-health.spec.js`, and project status docs.
- **Implemented:** The static web app now has a Ticket Health navigation section that loads `/api/ticket-health/review-queue`, shows review candidate, predictive-ranked, and abstention counts, displays review-only guidance, lists ticket risk/priority/predictive score/confidence/sample/reasons, and lets ticket numbers open the existing scoped local detail modal.
- **Validation:** `npm run test:web -- ticket-health.spec.js` passed with `1 passed`; `npm run test:web` passed with `11 passed`.
- **Read-only evidence:** No sync jobs, production deployment, live credential changes, local feedback writes, or Autotask write capability were run or added; the UI renders local read-only review-queue evidence and existing local ticket detail evidence.
- **Rollback:** Revert this branch commit; the predictive review queue remains available by API, but the static UI no longer shows the Ticket Health predictive table.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Predictive ticket review ranking

- **Slice:** Add review-only statistical ticket ranking on branch `agent/predictive-ticket-review-ranking` from canonical `main` `844d0330ad703d1744fc4837ce042c13122b52e9`.
- **State:** `partial_foundation`; ticket review ranking now includes Bayesian-smoothed local historical signals and abstention, but Milestone 7 still requires documented prediction targets, holdout evaluation, bias/concentration review, and production certification.
- **Files changed:** `apps/api/app/ticket_health.py`, `apps/api/app/main.py`, `apps/api/tests/test_api.py`, `apps/api/tests/test_ingestion_rag.py`, and project status docs.
- **Implemented:** `ticket_health_review_queue()` now uses scoped completed-ticket history by queue/priority, applies Bayesian delay-rate smoothing, folds in local feedback calibration, emits `predictive_signal` with confidence/sample size/reason codes/limitations, and abstains when scoped sample size is too low. A new scoped read route `/api/ticket-health/review-queue` exposes the review queue and records success audit metadata.
- **Validation:** focused container tests passed with `4 passed`: route authority matrix, scoped route propagation, low-sample abstention, and Bayesian history/feedback score movement.
- **Read-only evidence:** No sync jobs, production deployment, live credential changes, local feedback writes, or Autotask write capability were run or added; predictions are local review guidance only and do not update Autotask tickets.
- **Rollback:** Revert this branch commit; ticket-health summary/detail and existing review helpers return to deterministic heuristic behavior without the statistical predictive signal route.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Operations automation visibility

- **Slice:** Make scheduled automation movement visible on branch `agent/operations-automation-visibility` from canonical `main` `96a3e9503b0195af8157324afb6824a04aeb03e0`.
- **State:** `partial_foundation`; operators can now see whether TimeEntries/TicketHistory automation is running and moving data, but Milestone 2 still requires historical catch-up certification and source-lineage/field availability closure.
- **Files changed:** `apps/web/index.html`, `apps/web/styles.css`, `apps/web/tests/helpers.js`, `apps/web/tests/operations-automation.spec.js`, and project status docs.
- **Implemented:** Operations now displays local TimeEntries and TicketHistory totals, scheduler health, scheduler heartbeat age, next due job, and recent related-data automation cards for open-ticket/estate TicketHistory, TimeEntries, recent sync, classification, document, and embedding jobs.
- **Runtime evidence:** Read-only local checks on 2026-07-22 showed `scheduler.state=healthy`, `global_pause=false`, heartbeat age about 18 seconds, counts `tickets=67726`, `ticket_notes=675531`, `time_entries=49054`, `ticket_history=29340`, and recent successful related-data runs including `open_ticket_history_gaps` pulled `685` with `2` inserted and `683` updated, `ticket_history_gaps` pulled `566` with `200` inserted and `366` updated, and `ticket_time_entry_gaps` pulled/inserted `40`.
- **Validation:** `npm run test:web -- operations-automation.spec.js` passed with `1 passed`; `npm run test:web` passed with `10 passed`; full `./scripts/validate-ci.sh && git diff --check` passed with production-auth preflight, redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `112 passed`, static web JavaScript syntax validation, Playwright browser smoke `10 passed`, and whitespace checks.
- **Read-only evidence:** No sync jobs were manually triggered, no production deployment or live credential changes were made, and no Autotask write capability was run or added; the UI renders existing local operations/status/job-run evidence only.
- **Rollback:** Revert this branch commit; scheduled jobs keep running, but the Operations page returns to the previous generic counts/tables without the automation-health summary.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Ask Assistant answer ticket links

- **Slice:** Make ticket IDs inside assistant answer text clickable on branch `agent/answer-ticket-links` from canonical `main` `65a42bbdc4fa6689ad2fb67fea00d3aa0a375783`.
- **State:** `partial`; answer evidence is easier to inspect in the UI, but live production-auth deployment evidence remains open.
- **Files changed:** `apps/web/index.html`, `apps/web/tests/ask-status.spec.js`, and project status docs.
- **Implemented:** Rendered assistant answer paragraphs and bullet lines now detect `T########.####` ticket IDs and turn them into buttons that open the existing scoped local ticket-health detail modal.
- **Validation:** `npm run test:web` passed with `9 passed`.
- **Read-only evidence:** No sync jobs, production deployment, live credential changes, local feedback writes, or Autotask write capability were run or added; the links read existing local scoped API evidence only.
- **Rollback:** Revert this branch commit; answer-body ticket IDs return to plain text while the `Based on Tickets` modal remains intact.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Ask Assistant ticket detail modal

- **Slice:** Make assistant ticket evidence inspectable on branch `agent/ask-ticket-detail-modal` from canonical `main` `695d58b22e4f764e0f07e282d44aaffb3c46fb13`.
- **State:** `partial`; Ask Assistant ticket evidence is easier to inspect in the UI, but live production-auth deployment evidence remains open.
- **Files changed:** `apps/web/index.html`, `apps/web/styles.css`, `apps/web/tests/helpers.js`, `apps/web/tests/ask-status.spec.js`, and project status docs.
- **Implemented:** `Based on Tickets` entries now render as clickable buttons that fetch existing scoped local ticket-health details by ticket number and open a modal with summary, status-duration, recent history, recent labor, and warnings. The modal states that evidence is local and no Autotask data was changed.
- **Validation:** `npm run test:web` passed with `8 passed`. Full `./scripts/validate-ci.sh` passed with production-auth preflight, redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `112 passed`, static web JavaScript syntax validation, Playwright browser smoke `8 passed`, and `git diff --check`.
- **Read-only evidence:** No sync jobs, production deployment, live credential changes, local feedback writes, or Autotask write capability were run or added; the modal reads existing local scoped API evidence only.
- **Rollback:** Revert this branch commit; the Ask Assistant returns to plain text `Based on Tickets` entries.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Milestone 1 security/isolation Quality Streak

- **Slice:** Add repeatable Milestone 1 security/isolation Quality Streak harness on branch `agent/m1-security-isolation-quality-streak` from canonical `main` `a58b10a91b101d21cd84742e5ff72abc45c44a3b`.
- **State:** `partial`; security/isolation now has repeatable local 3/3 streak evidence, but live production-auth deployment evidence remains open.
- **Files changed:** `scripts/security-isolation-quality-streak.sh`, `apps/api/tests/test_repo_hygiene.py`, and project status docs.
- **Implemented:** Added `scripts/security-isolation-quality-streak.sh` to run the existing auth, route RBAC, audit, company-scope propagation, scoped local capability route, local feedback role-gate, scoped-cache, export/download absence, realtime scope, and verifier fail-closed subset three consecutive times inside the API container. Repository-hygiene coverage verifies the script exists, is executable, uses no-deps Docker test runs, and avoids shell tracing.
- **Validation:** Focused repository-hygiene test command passed with `14 passed`. `./scripts/security-isolation-quality-streak.sh` passed 3/3 runs, each with `46 passed`.
- **Read-only evidence:** No sync jobs, production deployment, live credential changes, local feedback writes, or Autotask write capability were run or added; tests use synthetic local evidence only.
- **Rollback:** Revert this branch commit; no schema/runtime configuration change is included.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Milestone 1 cache/export consumer certification

- **Slice:** Certify current active cache and export/download route state on branch `agent/m1-cache-export-consumer-certification` from canonical `main` `e05ac0c34b7457bf690fd06793c90c164239eb69`.
- **State:** `partial`; current active cache consumers are covered by scoped cache contracts and export/download routes remain absent, but production-auth deployment evidence and broader capability Quality Streak records remain open.
- **Files changed:** `apps/api/tests/test_ingestion_rag.py` and project status docs.
- **Implemented:** Added a repository-level test proving current active cache consumers in operations, ticket-health, and customer-success use scoped cache machinery and do not directly import the unscoped cache-key helper. The same test verifies no export/download API routes exist.
- **Validation:** Focused API/RAG test command passed with `49 passed`. Full `./scripts/validate-ci.sh` passed with production-auth preflight, redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `112 passed`, static web JavaScript syntax validation, Playwright browser smoke `6 passed`, and `git diff --check`.
- **Read-only evidence:** No sync jobs, production deployment, live credential changes, local feedback writes, or Autotask write capability were run or added.
- **Rollback:** Revert this branch commit; implementation behavior is unchanged, but the explicit certification test is removed.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Milestone 1 scoped local feedback routes

- **Slice:** Expose local-only scoped feedback routes on branch `agent/m1-scoped-local-feedback-routes` from canonical `main` `d6b49c9e4832ce1ce86819ce844085c2f1b8a268`.
- **State:** `partial`; local ticket-health, customer-success, and routing feedback POST routes now have role and company-scope contracts, but production-auth deployment evidence and broader capability Quality Streak records remain open.
- **Files changed:** `apps/api/app/main.py`, `apps/api/app/ticket_health.py`, `apps/api/tests/test_api.py`, `apps/api/tests/test_ingestion_rag.py`, and project status docs.
- **Implemented:** Added Technician/Admin local feedback POST routes for ticket-health, customer-success, and routing. ReadOnly users are denied. Feedback calls pass authorized company scope; ticket-health feedback now filters ticket lookup by authorized company scope before writing local review evidence.
- **Validation:** Focused API/RAG test command passed with `79 passed`. Full `./scripts/validate-ci.sh` passed with production-auth preflight, redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `111 passed`, static web JavaScript syntax validation, Playwright browser smoke `6 passed`, and `git diff --check`.
- **Read-only evidence:** No sync jobs, production deployment, live credential changes, or Autotask write capability were run or added. These routes write local review records only.
- **Rollback:** Revert this branch commit; local feedback helpers remain internally available, but the POST route surface is removed.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Milestone 1 scoped local capability routes

- **Slice:** Expose scoped read-only local capability routes on branch `agent/m1-scoped-local-capability-routes` from canonical `main` `d2b325e1405caa070079dd60c464798ea45e2954`.
- **State:** `partial`; ticket-health, customer-success, routing, and realtime GET routes now have first-class company-scope route contracts, but local feedback POST exposure, production-auth deployment evidence, and broader capability Quality Streak records remain open.
- **Files changed:** `apps/api/app/main.py`, `apps/api/tests/test_api.py`, and project status docs.
- **Implemented:** Added authenticated/company-scoped GET routes for ticket-health summary/detail, customer-success summary/detail, routing skill profiles/recommendations, and realtime events. Summary routes pass scoped cache context; route tests assert route inventory classification and authorized-company propagation.
- **Validation:** Focused API test command passed with `30 passed`. Full `./scripts/validate-ci.sh` passed with production-auth preflight, redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `110 passed`, static web JavaScript syntax validation, Playwright browser smoke `6 passed`, and `git diff --check`.
- **Read-only evidence:** No sync jobs, production deployment, live credential changes, local feedback writes, or Autotask write capability were run or added.
- **Rollback:** Revert this branch commit; local capability functions remain available internally but the new route surface is removed.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Milestone 1 realtime scope certification

- **Slice:** Add authorized-company filtering for realtime ticket-history events on branch `agent/m1-realtime-scope-certification` from canonical `main` `18fe54ff1b3d686c7fa573548c7a558d8e39a7aa`.
- **State:** `partial`; realtime event helpers now carry scope for local ticket-history events, but production-auth deployment evidence, first-class route exposure decisions, and broader capability Quality Streak records remain open.
- **Files changed:** `apps/api/app/realtime.py`, `apps/api/tests/test_ingestion_rag.py`, and project status docs.
- **Implemented:** `recent_realtime_events()` and `realtime_event_stream()` accept optional authorized company scope. Company-scoped calls filter ticket-history events by ticket company and hide global scheduler job events unless explicitly allowed.
- **Validation:** Focused API/RAG test command passed with `48 passed`. Full `./scripts/validate-ci.sh` passed with production-auth preflight, redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `108 passed`, static web JavaScript syntax validation, Playwright browser smoke `6 passed`, and `git diff --check`.
- **Read-only evidence:** No sync jobs, production deployment, live credential changes, or Autotask write capability were run or added; changes only filter local realtime read evidence.
- **Rollback:** Revert this branch commit; realtime helpers return to prior global event behavior.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Milestone 1 ticket-health/customer-success/routing scope certification

- **Slice:** Add company-scope filters and fail-closed detail/feedback behavior for ticket-health, customer-success, and routing local capability functions on branch `agent/m1-scope-certification-ticket-health-routing` from canonical `main` `14a545e356fff7dca6ba1a946f0cc5837e025f1d`.
- **State:** `partial`; local capability functions now accept and apply company scope, but production-auth deployment evidence, first-class route exposure decisions, and broader capability Quality Streak records remain open.
- **Files changed:** `apps/api/app/ticket_health.py`, `apps/api/app/customer_success.py`, `apps/api/app/routing.py`, `apps/api/tests/test_ingestion_rag.py`, and project status docs.
- **Implemented:** `ticket_health_summary()`, ticket-health review/detail lookup helpers, `customer_success_summary()`, customer-success detail/review/feedback helpers, `technician_skill_profiles()`, `ticket_routing_recommendation()`, and local routing feedback now accept optional authorized company scope. Scoped calls add SQL company filters; out-of-scope customer detail/feedback and ticket/routing lookups fail closed as not found.
- **Validation:** Focused API/RAG test command passed with `47 passed`. Full `./scripts/validate-ci.sh` passed with production-auth preflight, redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `107 passed`, static web JavaScript syntax validation, Playwright browser smoke `6 passed`, and `git diff --check`.
- **Read-only evidence:** No sync jobs, production deployment, live credential changes, or Autotask write capability were run or added; changes only filter local read/feedback evidence.
- **Rollback:** Revert this branch commit; local capability functions return to prior global-scope behavior.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Milestone 1 summary cache scope contracts

- **Slice:** Move ticket-health and customer-success summary cache consumers onto scoped cache contracts on branch `agent/m1-summary-cache-scope-contracts` from canonical `main` `2b5485c00dcb940650b3076d44ccbfb8a7d9381d`.
- **State:** `partial`; active summary cache consumers now have scope/role-aware key contracts, but production-auth deployment evidence and broader capability Quality Streak records remain open.
- **Files changed:** `apps/api/app/ticket_health.py`, `apps/api/app/customer_success.py`, `apps/api/tests/test_ingestion_rag.py`, and project status docs.
- **Implemented:** `ticket_health_summary_cache_key()` and `customer_success_summary_cache_key()` now delegate to `scoped_cache_key()` with authority class, roles, explicit scope, version, and TTL config. Summary functions accept optional cache context and mark cache metadata as scoped.
- **Validation:** Focused cache contract tests passed with `5 passed`. Full `./scripts/validate-ci.sh` passed with production-auth preflight, redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `104 passed`, static web JavaScript syntax validation, Playwright browser smoke `6 passed`, and `git diff --check`.
- **Read-only evidence:** No sync jobs, production deployment, live credential changes, or Autotask write capability were run or added; tests are synthetic cache-key checks only.
- **Rollback:** Revert this branch commit; summary caches fall back to prior unscoped key behavior.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Milestone 1 answer-safety Quality Streak harness

- **Slice:** Add repeatable conversational answer-safety Quality Streak harness on branch `agent/m1-answer-safety-quality-streak` from canonical `main` `5f308551234d37b2622eb5d31ecb6e2e6680a6c4`.
- **State:** `partial`; answer-safety now has a repeatable 3/3 local streak harness, but production capability certification still requires broader live/deployment context and remaining Milestone 1 evidence.
- **Files changed:** `scripts/answer-safety-quality-streak.sh`, `docs/CI_VALIDATION.md`, `apps/api/tests/test_repo_hygiene.py`, and project status docs.
- **Implemented:** `scripts/answer-safety-quality-streak.sh` runs the guardrail and RAG conversational subset three consecutive times inside the API container. Repository-hygiene coverage verifies the script exists, is executable, uses no-deps container tests, covers guardrail/RAG tests, and avoids sync behavior.
- **Validation:** `./scripts/answer-safety-quality-streak.sh` passed 3/3 runs, each with `20 passed`. Full `./scripts/validate-ci.sh` passed with production-auth preflight, redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `102 passed`, static web JavaScript syntax validation, Playwright browser smoke `6 passed`, and `git diff --check`.
- **Read-only evidence:** No sync jobs, production deployment, live credential changes, or Autotask write capability were run or added; tests use synthetic local evidence only.
- **Rollback:** Revert this branch commit; no schema/runtime configuration change is included.
- **Second Brain state:** `updated`; existing projection PR #6 records PR #27 at commit `72eea2c`.

## Previous receipt — Milestone 1 generated-answer conversational verifier evidence

- **Slice:** Add generated-answer verifier evidence on branch `agent/m1-generated-answer-verifier-evidence` from canonical `main` `01a3ec7610bda4c8b07059798f63da7adbdf303d`.
- **State:** `partial`; generated conversational answer paths are better verified, but live production-auth deployment evidence, remaining scope/cache certification, and Quality Streak records remain open.
- **Files changed:** `apps/api/app/assistant.py`, `apps/api/app/security.py`, `apps/api/tests/test_ingestion_rag.py`, `apps/api/tests/test_guardrails.py`, and project status docs.
- **Implemented:** The assistant now carries ticket IDs from source metadata through source limiting, fallback summaries, `based_on_tickets`, and returned source payloads. Generated-answer tests prove metadata-only ticket evidence can pass verification, cross-ticket evidence substitution fails closed through the real `ask_assistant()` path with verifier audit, and private-entity redaction no longer crosses line breaks and damages answer section headers.
- **Validation:** Focused generated-answer/redaction tests passed with `4 passed`. Full `./scripts/validate-ci.sh` passed with production-auth preflight, redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `102 passed`, static web JavaScript syntax validation, Playwright browser smoke `6 passed`, and `git diff --check`.
- **Read-only evidence:** No sync jobs, production deployment, live credential changes, or Autotask write capability were run or added; tests use synthetic local evidence only.
- **Rollback:** Revert this branch commit; no schema/runtime configuration change is included.
- **Second Brain state:** `updated`; existing projection PR #6 records PR #26 at commit `6ba46c3`.

## Previous receipt — Milestone 1 adversarial conversational verifier breadth

- **Slice:** Broaden conversational answer verifier evidence on branch `agent/m1-adversarial-verifier-breadth` from canonical `main` `5919c397aa9c76087cea51e9b99b230c15cdbb43`.
- **State:** `partial`; conversational answer evidence is stronger, but broader adversarial verifier evidence, live production-auth deployment evidence, remaining scope/cache certification, and Quality Streak records remain open.
- **Files changed:** `apps/api/app/answer_safety.py`, `apps/api/tests/test_guardrails.py`, and project status docs.
- **Implemented:** The verifier now recognizes cited ticket IDs stored inside `source_metadata`, continues to reject cross-ticket evidence substitution, and allows explicit no-history/no-source fallback language without treating it as an unsupported factual claim.
- **Validation:** Focused guardrail tests passed with `17 passed`. Full `./scripts/validate-ci.sh` passed with production-auth preflight, redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `99 passed`, static web JavaScript syntax validation, Playwright browser smoke `6 passed`, and `git diff --check`.
- **Read-only evidence:** No sync jobs, production deployment, live credential changes, or Autotask write capability were run or added; tests use synthetic local evidence only.
- **Rollback:** Revert this branch commit; no schema/runtime configuration change is included.
- **Second Brain state:** `updated`; existing projection PR #6 records PR #25 at commit `e2654e2`.

## Previous receipt — Milestone 1 bootstrap/admin-user operations

- **Slice:** Add local bootstrap/admin-user operations on branch `agent/m1-bootstrap-admin-user` from canonical `main` `44c080169baa31ece7cc15f4684130149cf69b53`.
- **State:** `partial`; local app-user bootstrap is safer and repeatable, but live production auth enforcement, deployment receipt, broader adversarial verifier evidence, and Quality Streak records remain open.
- **Files changed:** `apps/api/app/user_admin.py`, `scripts/bootstrap-app-user.sh`, `apps/api/tests/test_api.py`, `README.md`, and project status docs.
- **Implemented:** Operators can set `BOOTSTRAP_APP_PASSWORD` and run `scripts/bootstrap-app-user.sh --username admin --role Admin` to create or update a local app user. The command validates supported roles, enforces a minimum bootstrap password length, stores only the PBKDF2 password hash, supports disabling a user, and returns safe metadata only.
- **Validation:** Focused API tests passed with `28 passed`. Full `./scripts/validate-ci.sh` passed with production-auth preflight, redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `96 passed`, static web JavaScript syntax validation, Playwright browser smoke `6 passed`, and `git diff --check`.
- **Read-only evidence:** No sync jobs, production deployment, live credential changes, or Autotask write capability were run or added; tests are hermetic and mock the database upsert.
- **Rollback:** Revert this branch commit; the deployment README loses the bootstrap command and no schema/runtime state changes are included.
- **Second Brain state:** `updated`; existing projection PR #6 records PR #24 at commit `f1a24d7`.

## Previous receipt — Milestone 1 production-auth preflight

- **Slice:** Add CI-validated production-auth preflight on branch `agent/m1-production-auth-preflight` from canonical `main` `064f82debc47cd16a6c9ba8fefd535719d3d173c`.
- **State:** `partial`; deploy-time auth evidence is stronger, but live production auth enforcement remains approval-gated and Milestone 1 still requires bootstrap/admin-user operations, broader adversarial verifier evidence, and Quality Streak records.
- **Files changed:** `.env.example`, `README.md`, `scripts/production-auth-preflight.sh`, `scripts/validate-ci.sh`, `docs/CI_VALIDATION.md`, `apps/api/tests/test_repo_hygiene.py`, and project status docs.
- **Implemented:** CI now runs `scripts/production-auth-preflight.sh .env.example`. The preflight passes production only when `APP_ROUTE_AUTH_REQUIRED=true` or an explicit external-auth boundary is documented with `EXTERNAL_AUTH_CONFIRMED=true` and `EXTERNAL_AUTH_DESCRIPTION`. README deployment steps now call out the preflight before deploy.
- **Validation:** `scripts/production-auth-preflight.sh .env.example` passed; focused repository-hygiene tests passed with `14 passed`. Full `./scripts/validate-ci.sh` passed with production-auth preflight, redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `93 passed`, static web JavaScript syntax validation, Playwright browser smoke `6 passed`, and `git diff --check`.
- **Read-only evidence:** No sync jobs, production deployment, or Autotask write capability were run or added.
- **Rollback:** Revert this branch commit; deploy instructions and CI return to the prior auth-boundary checks.
- **Second Brain state:** `updated`; existing projection PR #6 records PR #23 at commit `a4f4789`.

## Previous receipt — Milestone 1 active scoped-cache consumer

- **Slice:** Move the active operations-status cache consumer onto scoped cache keys on branch `agent/m1-active-scoped-cache-consumer` from canonical `main` `a2c3cd5037e4a3656114678c39c1e12a4e6e4ed1`.
- **State:** `partial`; one active global cache consumer is now scoped, but Milestone 1 still requires production auth enablement, remaining cache-consumer certification, broader adversarial verifier evidence, and Quality Streak records.
- **Files changed:** `apps/api/app/operations.py`, `apps/api/app/main.py`, `apps/api/tests/test_api.py`, `apps/api/tests/test_ingestion_rag.py`, and project status docs.
- **Implemented:** `operations_status()` now uses `operations_status_cache_key()`, which delegates to `scoped_cache_key()` with authority class, roles, explicit scope, positive version, and TTL config. `/api/operations/status` passes authenticated-read role context when app-route auth is enabled and uses the outer-auth scoped context otherwise. Operations-status invalidation now clears the namespace so scoped variants are invalidated together.
- **Validation:** Focused API/RAG tests passed with `65 passed`. Full `./scripts/validate-ci.sh` passed with redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `92 passed`, static web JavaScript syntax validation, Playwright browser smoke `6 passed`, and `git diff --check`.
- **Read-only evidence:** No sync jobs, production deployment, or Autotask write capability were run or added; tests are hermetic.
- **Rollback:** Revert this branch commit; operations status falls back to the prior global cache key behavior.
- **Second Brain state:** `updated`; existing projection PR #6 records PR #22 at commit `ff37f14`.

## Previous receipt — Milestone 1 source-sufficiency verifier

- **Slice:** Add deterministic ticket-history source-sufficiency checks on branch `agent/m1-source-sufficiency-verifier` from canonical `main` `52e77420dfd9790f40e1a2ab72423e37d3d393f8`.
- **State:** `partial`; answer-safety breadth is improved, but Milestone 1 still requires broader adversarial evidence, production auth enablement, active scoped cache consumer validation, and Quality Streak records.
- **Files changed:** `apps/api/app/answer_safety.py`, `apps/api/tests/test_guardrails.py`, and project status docs.
- **Implemented:** `verify_answer()` now records `insufficient_source_claims` and fails closed when a non-weak ticket-history claim lacks a matching retrieved source or has fewer than two meaningful token overlaps with the relevant source content. Ticket-specific claims are checked against matching ticket sources when ticket IDs are present.
- **Validation:** Focused guardrail tests passed with `14 passed`. Full `./scripts/validate-ci.sh` passed with redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `90 passed`, static web JavaScript syntax validation, Playwright browser smoke `6 passed`, and `git diff --check`.
- **Read-only evidence:** No sync jobs, production deployment, or Autotask write capability were run or added; tests use synthetic local evidence only.
- **Rollback:** Revert this branch commit; no schema or runtime configuration change is included.
- **Second Brain state:** `updated`; existing projection PR #6 records PR #21 at commit `47dca09`.

## Previous receipt — Milestone 1 keyboard/focus browser smoke

- **Slice:** Add keyboard/focus browser accessibility evidence on branch `agent/m1-keyboard-focus-smoke` from canonical `main` `6ea8a91e5a42aa6650a3f6fe05202227a11639c3`.
- **State:** `partial`; keyboard/focus browser evidence is stronger, but Milestone 1 still requires source-sufficiency certification, production auth enablement, active scoped cache consumer validation, and Quality Streak records.
- **Files changed:** `apps/web/styles.css`, `apps/web/tests/accessibility.spec.js`, and project status docs.
- **Implemented:** Navigation links, buttons, inputs, textareas, and selects now share an explicit focus-visible indicator. Playwright verifies keyboard Tab traversal through primary navigation, login controls, mode selection, question entry, and the Ask action with visible focus on each step.
- **Validation:** `npm run test:web` passed with `6 passed`. Full `./scripts/validate-ci.sh` passed with redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `88 passed`, static web JavaScript syntax validation, Playwright browser smoke `6 passed`, and `git diff --check`.
- **Read-only evidence:** No sync jobs, production deployment, or Autotask write capability were run or added; browser tests stub API calls.
- **Rollback:** Revert this branch commit; behavior change is limited to visible keyboard focus styling and stronger browser validation.
- **Second Brain state:** `updated`; existing projection PR #6 records PR #20 at commit `d6775f8`.

## Previous receipt — Milestone 1 browser accessibility smoke

- **Slice:** Add Playwright axe accessibility smoke coverage on branch `agent/m1-browser-accessibility-smoke` from canonical `main` `cd1a0b4e1f6dda9ba3eadd6fb44fe5934d1f1b65`.
- **State:** `partial`; browser accessibility evidence is broader, but Milestone 1 still requires keyboard/focus evidence, source-sufficiency certification, production auth enablement, active scoped cache consumer validation, and Quality Streak records.
- **Files changed:** `apps/web/index.html`, `apps/web/styles.css`, `apps/web/tests/accessibility.spec.js`, `apps/web/tests/helpers.js`, `apps/web/tests/rbac.spec.js`, `package.json`, `package-lock.json`, and project status docs.
- **Implemented:** Shared Playwright static-web/API-stub helpers now support browser tests. Axe checks assert no serious or critical dashboard accessibility violations, and login controls are verified by accessible name. The Ask mode selector now has a visible label.
- **Validation:** `npm run test:web` passed with `5 passed`. Full `./scripts/validate-ci.sh` passed with redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `88 passed`, static web JavaScript syntax validation, Playwright browser smoke `5 passed`, and `git diff --check`.
- **Read-only evidence:** No sync jobs, production deployment, or Autotask write capability were run or added; browser tests stub API calls.
- **Rollback:** Revert this branch commit; application behavior is unchanged except the Ask mode selector label and stronger browser validation.
- **Second Brain state:** `updated`; existing projection PR #6 records PR #19 at commit `f5ddb53`.

## Previous receipt — Certification matrix and validation-harness streak tracking

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

`pull-request-open` — branch `agent/autotask-ai-governed-roadmap-projection`, draft PR `newbie10122/helix-second-brain#6`, branch head `8a7919e89b5f171a84d3be3913b4c54a971e6925` records Autotask AI PR #42, canonical commit `c688c6d622e60e866ee63302a1f577f498635741`, predictive threshold evidence, prior predictive evaluation/ranking/UI work, operations automation visibility, Ask Assistant ticket-detail links, Milestone 1 certification slices, restored scheduler automation, heartbeat repair, runtime counts, classification completion, and remaining gaps. Local Second Brain validation passed with `python3 tools/validate_knowledge.py`. Remote validation status remains separately tracked on PR #6. Do not mark `merged` until PR #6 is merged.

## Exact next action

Complete the control-document reconciliation branch, validate it, open/merge the PR if CI passes, update the existing Second Brain projection, then begin the next safe predictive evaluation slice: target/label semantics, calibration/Brier/PR/ROC evidence, threshold confusion/coverage/abstention evidence, sanitized concentration analysis, human-review threshold policy, and local read-only shadow evaluation.
