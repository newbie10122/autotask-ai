# Autotask AI Implementation Status

**Updated:** 2026-07-22
**Management target:** 99% verified roadmap completion  
**Current state:** `partial`  
**Active milestone:** Milestone 1 — Security, identity, isolation, and answer trust

## Status confidence

The repository has a substantial implemented MVP foundation, but no roadmap milestone is yet marked `verified_complete` under `AGENTS.md`. Current verified completion cannot be represented honestly as a percentage until acceptance evidence, the capability certification matrix, and Quality Streak records are established.

## Implemented foundation

- Canonical `main` is `8e031d1`, which merged PR `newbie10122/autotask-ai#121` (`Guide status source candidates to schema probe`).
- Latest GitHub Actions CI evidence is PR `newbie10122/autotask-ai#121` run `29964318197`, workflow `CI`, job `Validate Autotask AI`, passed before merge. Local validation for PR #121 passed focused source-candidate validation with `1 passed`, `git diff --check`, and full repository validation with `164` API tests plus `13` Playwright tests.
- Second Brain projection PR `newbie10122/helix-second-brain#13` is open at head `977d6be` after recording Autotask AI progress through PR #121 and the status source-candidate schema guidance evidence; local `python3 tools/validate_knowledge.py` passed with `116` Markdown files, `116` unique IDs, and `271` internal links.
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
- Conversational UI branch `agent/ask-progress-phases` makes Ask Assistant request state explicit with visible phases for scoped ticket search, evidence preparation, local CPU model waiting, and answer rendering, plus terminal text that distinguishes active requests from timeout/error/done states.
- Conversational behavior branch `agent/ticket-history-only-no-llm` makes Ticket History Only deterministic and local-evidence-only; it skips the local chat model while keeping generated prose explicit to General + Ticket History and Deep Dive.
- Conversational UI branch `agent/ask-mode-ready-status` makes Ask Assistant ready text mode-specific so Ticket History Only no longer advertises local CPU model wait time.
- Milestone 1 admin-read audit branch `agent/m1-audit-scope-closeout` records durable success audit events for admin reads of the audit log and pending curated-memory queue, including actor, roles, global scope, and safe count metadata.
- Milestone 1 audit inspection PR #72 adds bounded Admin-only audit-log filters and records success audits for Operations inspection read routes with actor, roles, global scope, and compact safe count/state metadata.
- Milestone 2 related-data catch-up cadence branch `agent/m2-related-data-catchup-cadence` increases bounded estate TimeEntries/TicketHistory gap batch defaults to `100` and exposes estimated bounded runs remaining in the Operations related-data work plan.
- PR #75 carries open-ticket TimeEntries gap-check context into field certification so checked-empty labor evidence is distinguished from unchecked tickets before labor is certified.
- Milestone 2 scoped labor lineage branch `agent/m2-scoped-labor-lineage` applies authorized company scope to labor coverage summary/status/target queries and to field-certification labor context fetches.
- Milestone 2 SLA lineage branch `agent/m2-sla-lineage-certification` adds scoped SLA ID/met/due-target/pause lineage evidence and keeps SLA certification partial when due target timestamps are incomplete.
- Milestone 2 status-duration/waiting lineage branch `agent/m2-status-duration-waiting-lineage` adds aggregate-only TicketHistory source-shape inventory, current waiting-state snapshot taxonomy, and a no-proxy-duration contract so current status timestamps are not treated as historical waiting duration evidence.
- PR #83 adds aggregate-only scoped customer/technician response lineage from local ticket-note author identifiers and normalized/raw note timestamps; runtime evidence shows note author IDs and raw `createDateTime` timestamps are present, while the normalized timestamp column will populate on future sync/upsert/backfill.
- PR #85 adds aggregate-only scoped reference-field lineage for current priority, category/issue/subissue, queue, and status fields and feeds priority/category/queue reference completeness into field certification.
- PR #87 adds read-only scheduler automation certification to Operations status, including required-job recent scheduler-run evidence, stale running-run detection, and safe no-raw-error reporting.
- PR #89 adds read-only stale running-run provenance to scheduler automation certification and the Operations UI without cleanup or raw error/config/checkpoint output.
- PR #91 adds an Admin-only local archive action for stale orphaned scheduler run metadata. It only archives running rows older than 30 minutes with no active lock and newer completed evidence for the same job.
- PR #95 adds read-only scheduler recovery-streak evidence to Operations status and the Operations UI. It inspects the latest three scheduler-triggered runs for each required scheduler job without running jobs or exposing raw errors.
- PR #97 records local pause/resume provenance in Operations settings/status and success audits: action, actor, reason, timestamp, and policy flags proving local metadata only, no job execution, and no Autotask writes.
- PR #99 preserves bootstrap reference-label provenance during reference sync, reports reference label counts by source, and displays bootstrap/inferred/source counts in the UI.
- PR #101 separates meaningful local reference labels from authoritative Autotask-sourced labels in reference lineage, field certification, and Operations field-certification cards.
- PR #103 adds aggregate-only raw candidate label-key evidence to reference lineage and field certification, including the corrected category raw source key `ticketCategory`.
- PR #105 adds a read-only reference metadata source contract for authoritative reference-label certification.
- PR #107 adds an Admin-only manual bounded read-only reference metadata source probe.
- Post-merge bounded read-only runtime probe on canonical `main` `9e17d22` returned `/ready` `HTTP 200`, `live_autotask_probe_ran=true`, `autotask_writes_allowed=false`, `MaxRecords=1` per candidate entity, and one available candidate, `TicketCategories`. `TicketPriorities`, `Priorities`, `TicketIssueTypes`, `TicketSubIssueTypes`, `Queues`, `TicketQueues`, and `TicketStatuses` were unavailable by those entity names. The result is availability evidence only; it does not authorize automatic reference sync, model/workflow changes, or Autotask writes.
- PR #111 adds read-only `TicketCategories` metadata ingestion to the reference-data sync path. Post-merge local runtime executed the reference-data sync once, processed/upserted `14` `TicketCategories` metadata rows with `metadata_sync.ok=true`, `autotask_writes_allowed=false`, and no metadata-sync errors; category reference lineage then showed `100.0%` authoritative label coverage, while issue/subissue, priority, queue, status-duration, and waiting blockers remain.
- PR #114 adds read-only `Tickets/entityInformation/fields` picklist ingestion for priority, category, issue type, subissue type, queue, and status labels. Post-merge local runtime executed the reference-data sync once, upserted `231` ticket picklist rows across `issueType`, `priority`, `queueID`, `status`, `subIssueType`, and `ticketCategory`, and field certification now reports all six reference fields at `100.0%` authoritative label coverage with zero metadata-source gaps. Remaining blockers are `ticket_status_history`, `status_duration`, `waiting_states`, and queue-at-creation/history lineage.
- Branch `agent/m2-status-history-source-lineage-next` adds field-certification remaining-blocker diagnostics and Operations UI visibility. Local runtime evidence after API rebuild showed one automation-improvable coverage blocker (`ticket_status_history`) and three source/lineage blockers (`status_duration`, `waiting_states`, and `queue`) with no jobs run and no Autotask writes.
- Branch `agent/m2-ticket-history-schema-probe` adds an Admin-only bounded read-only TicketHistory schema probe. Local runtime evidence found the TicketHistory schema exposes `action`, `date`, `detail`, `id`, `resourceID`, and queryable `ticketID`; it does not expose structured old/new status transition fields.
- PR #121 carries the new TicketHistory schema probe into the status-transition source-candidates report so operators can see the governed route and evidence required before adding any sync path.
- Operations visibility branch `agent/operations-automation-visibility` exposes scheduler heartbeat, next due job, TimeEntries/TicketHistory totals, and recent related-data job movement in the Operations UI.
- Predictive ticket review branch `agent/predictive-ticket-review-ranking` adds a scoped review-only ticket-health queue with Bayesian-smoothed historical completion signals, local-feedback calibration, reason codes, confidence, and low-sample abstention.
- Predictive calibrated-ranking branch `agent/predictive-ranking-calibrated-score` exposes a review-only model version, calibrated delay probability, calibration adjustments, and calibrated rank contribution in the predictive review queue and Ticket Health UI.
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
- Status-probe error-isolation branch `agent/status-probe-error-isolation` fixes the manual status-history probe so repeated unavailable entities do not trip the read-only client's consecutive-error breaker across candidates; every candidate is attempted independently and reported.
- Status-probe entity-filters branch `agent/status-probe-entity-filters` makes the manual probe use per-entity read-only filters and report each filter used. `TicketHistory` now probes by `ticketID`, matching the existing read-only sync path, while candidate status-history entities still probe by `id`.
- Status-probe sample-ticket branch `agent/status-probe-ticket-history-sample` makes the `TicketHistory` availability probe use one real local `autotask_tickets.autotask_id` with `ticketID eq <local ticket>` and `MaxRecords=1`, falling back to `ticketID >= 0` only when no local ticket exists.
- Post-merge bounded read-only runtime probe on canonical `main` `9cc33aaf6ed3987d45a43e96713a7c39609bdcfc` found `TicketStatusHistory`, `TicketStatusHistories`, and `TicketChangeHistory` unavailable by those entity names, while `TicketHistory` was reachable with a sampled row and next page using `ticketID eq <local ticket>`. The status-duration/waiting blocker is now confirmed as TicketHistory row content/parser shape, not basic TicketHistory reachability.
- TicketHistory content-certification is merged through PRs #58 and #59. Canonical `main` runtime validation on `bcc1b433b4a0124c833f131d28227a57eb6e1df2` returned `ok=true` for `/api/ticket-health/ticket-history-content-certification` after qualifying joined `h.raw` JSON references. The aggregate-only evidence found `30186` TicketHistory rows, `100%` timestamp coverage, `1` status-like row, and no `field`/`oldValue`/`newValue` raw keys, without exposing raw history detail text or enabling parser/model/workflow changes.
- Post-merge Milestone 2 evidence on canonical `main` `27b0bd7e502a0b9ef74b60238f0e9f362ece422b`: PR #81 field certification executed locally through the API container against existing Postgres and returned `partial_field_certification` with blockers `ticket_status_history`, `status_duration`, and `waiting_states`. The aggregate-only TicketHistory source-shape inventory found `38648` scoped local rows, `4804` tickets represented, `100%` timestamp coverage, `0` structured status-transition rows, `1` status-like parser-incompatible row, `164` duplicate timestamp groups, and `33489` non-monotonic timestamp rows by local ID order. The current waiting-state snapshot taxonomy reported `67726` tickets, `67625` mapped tickets, and `101` unknown/unmapped tickets; historical waiting-duration remains unavailable.
- Post-merge PR #83 response-lineage runtime evidence: local read-only field certification returned blockers `ticket_status_history`, `status_duration`, and `waiting_states`. The response lineage report found `675531` scoped ticket notes, `8091` customer-attributed notes, `667440` technician-attributed notes, `0` ambiguous notes, `100%` raw-backed timestamp coverage for both customer and technician response notes, and `0` normalized timestamp rows until future sync/upsert/backfill refreshes the normalized column. Response lineage is available as local read-only evidence.
- Post-merge PR #85 reference-lineage runtime evidence: local read-only reference lineage returned `partial_reference_lineage`, tickets `67726`, and three partial targets. Priority has `67726` present rows, queue has `67665` present rows, and category/issue/subissue has `187528` present rows across the three fields, but each has `0%` meaningful mapped-label coverage because current local reference labels are inferred placeholders. Field certification remains `partial_field_certification` with blockers `ticket_status_history`, `status_duration`, `waiting_states`, `priority`, `category`, and `queue`.
- Post-merge PR #87 scheduler automation runtime evidence: local read-only scheduler certification returned `partial_scheduler_automation_evidence`, scheduler `healthy`, `9` required jobs, `9` certified jobs, `0` partial jobs, `0` missing jobs, `2` running jobs, and blocker `stale_running_jobs` because one old running row is older than 30 minutes. Required scheduled jobs had recent scheduler-completed runs, including `recent_sync` (`86` scheduler runs/`86` completed in 24h), `open_ticket_history_gaps` (`86` runs/`85` completed), `open_ticket_time_entry_gaps` (`85`/`85`), `ticket_history_gaps` (`23`/`23`), `ticket_time_entry_gaps` (`23`/`23`), `sync_reference_data` (`4`/`4`), `classify_tickets` (`46` runs/`44` completed), `reclassify_chunks` (`24`/`24`), and `nightly_pipeline` (`1`/`1`).
- Post-merge PR #89 stale-run provenance runtime evidence: local read-only scheduler certification returned `1` stale running row, `classify_tickets` run `4143`, no active lock, newer completed run `4391`, and stale state `orphaned_running_row_candidate`. This explains the blocker as likely stale local run metadata, not evidence that the scheduler is failing to run classification.
- Post-merge PR #91 cleanup capability evidence: `archive_stale_orphaned_run()` is local metadata only and returns policy flags proving it does not run jobs or allow Autotask writes. The archive SQL requires `running`, older than 30 minutes, no active lock, and newer completed run evidence before updating a row to `stale_orphaned`; PR #91 did not execute cleanup against the live database.
- Post-merge cleanup execution evidence on PR #93: local Admin route `POST /api/operations/jobs/4143/archive-stale` returned `ok=true`, `archived=true`, policy `local_metadata_only=true`, `runs_jobs=false`, and `autotask_writes_allowed=false`. Follow-up local scheduler certification returned `certification_state=scheduler_automation_available`, `ok=true`, `9` required jobs, `9` certified jobs, `0` running jobs, `0` stale running jobs, no blockers, and `0` stale provenance rows. Local Nginx `/ready` and UI root returned `HTTP 200`.
- Post-merge PR #95 scheduler recovery-streak runtime evidence: after local API/web rebuild and the next scheduler tick, read-only scheduler certification returned `certification_state=scheduler_automation_available`, scheduler `healthy`, `9` required jobs, `9` certified jobs, `0` running jobs, `0` stale running jobs, and recovery streak `scheduler_recovery_streak_available` with `9` clean-streak jobs, `0` partial-streak jobs, and `3` required clean runs per job. The recovery-streak policy reports `read_only=true`, `runs_jobs=false`, `autotask_writes_allowed=false`, and `returns_raw_error_text=false`.

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

1. Merge this docs-only projection reconciliation after CI passes.
2. Continue the next safe Milestone 2 source-lineage slice now that TicketHistory schema evidence is recorded and surfaced in the status-source report.
3. Continue production-auth deployment evidence only when explicitly approved for that protected action.
4. Add targeted capability Quality Streak evidence without marking milestones complete prematurely.

## Current receipt — PR #121 Second Brain projection reconciliation

- **Slice:** Record PR #121 merge evidence and Second Brain projection head after status source-candidate schema guidance.
- **State:** `partial_foundation`; documentation/projection evidence only.
- **Files changed:** canonical control docs only.
- **Implemented:** Project docs now identify canonical `main` at `8e031d1`, PR #121 CI run `29964318197`, and Second Brain PR #13 head `977d6be`.
- **Validation:** `git diff --check` passed; full `./scripts/validate-ci.sh` passed with `164` API tests and `13` Playwright tests. GitHub CI is still required before merge.
- **Read-only/authority evidence:** No application code, migrations, runtime configuration, production deployment, sync jobs, model workflow, or Autotask writes changed.
- **Second Brain state:** `pull-request-open`; existing projection PR `newbie10122/helix-second-brain#13` is open at head `977d6be` and records PR #121 status source-candidate schema guidance evidence with local knowledge validation passing: `116` Markdown files, `116` unique IDs, and `271` internal links.
- **Rollback:** Revert this docs-only reconciliation commit; canonical PR #121 application behavior and Second Brain PR #13 branch remain unchanged.

## Current receipt — Milestone 2 status source-candidate schema guidance

- **Slice:** Carry the TicketHistory schema probe into the status-transition source-candidates report.
- **State:** `partial_foundation`; this is source-discovery guidance and does not certify status-duration or waiting-duration analytics.
- **Files changed:** `apps/api/app/ticket_health.py`, focused API tests, and project status docs.
- **Implemented:** `/api/ticket-health/status-transition-sources` now includes a `ticket_history_schema_metadata` candidate with `candidate_route=/api/autotask/probe/ticket-history-schema`, the evidence required for certification, and read-only next-step guidance. The existing candidate status-history entity guidance now points to both the bounded status-transition source probe and the TicketHistory schema probe before any sync path is added.
- **Runtime evidence:** Local API rebuild returned `/ready` `HTTP 200`. `/api/ticket-health/status-transition-sources` returned the new `ticket_history_schema_metadata` candidate and the updated status-history entity next step.
- **Validation:** Focused status-transition source-candidate validation passed with `1 passed`; `git diff --check` passed; full `./scripts/validate-ci.sh` passed with `164` API tests and `13` Playwright tests. This branch still requires GitHub CI before merge.
- **Read-only/authority evidence:** The report update reads local aggregate evidence only and does not run probes, query TicketHistory rows, run sync jobs, write to Autotask, deploy production code, or change model/routing/assignment behavior.
- **Rollback:** Revert this branch commit; the TicketHistory schema probe endpoint remains available from PR #119, but the source-candidates report no longer points to it.

## Current receipt — Milestone 2 TicketHistory schema probe

- **Slice:** Add a governed Admin-only read-only probe for Autotask `TicketHistory` entity schema metadata.
- **State:** `partial_foundation`; this strengthens source-lineage evidence but does not certify status-duration or waiting-duration analytics.
- **Files changed:** `apps/api/app/autotask.py`, `apps/api/app/main.py`, API tests, and project status docs.
- **Implemented:** `AutotaskReadOnlyClient.probe_ticket_history_schema()` reads `/V1.0/TicketHistory/entityInformation/fields`, returns sanitized field names/types/queryability/read-only flags, classifies timestamp fields, unstructured transition text fields, and structured status-transition fields, and exposes policy flags proving no raw TicketHistory rows are returned. `POST /api/autotask/probe/ticket-history-schema` is Admin-only and records safe success-audit metadata.
- **Runtime evidence:** Local API rebuild returned `/ready` `HTTP 200`. The live probe returned `ok=true`, `live_autotask_probe_ran=true`, `autotask_writes_allowed=false`, `field_count=6`, `queryable_fields=['ticketID']`, `timestamp_fields=['date']`, `unstructured_transition_text_fields=['action','detail']`, `structured_status_transition_fields=[]`, and `has_structured_status_transition_fields=false`.
- **Validation:** PR #119 CI run `29963679064` passed; focused client schema-probe validation passed with `1 passed`; focused route matrix/success-audit validation passed with `2 passed`; full `./scripts/validate-ci.sh` passed with `164` API tests and `13` Playwright tests; `git diff --check` passed.
- **Read-only/authority evidence:** The probe reads schema metadata only. It does not query TicketHistory rows, run sync jobs, write to Autotask, deploy production code, change model thresholds/workflows, or change routing/assignment.
- **Rollback:** Revert this branch commit to remove the probe route and client method; existing status-transition source probes and field-certification reports remain available.

## Current receipt — Milestone 2 remaining blocker diagnostics

- **Slice:** Make field-certification blockers explain whether scheduled automation can still improve coverage or whether the blocker is source/lineage limited.
- **State:** `partial_foundation`; this improves operator visibility only. Milestone 2 remains partial because historical TicketHistory estate coverage, timestamped status transitions, historical waiting duration, and queue-at-creation/history lineage are not certified.
- **Files changed:** `apps/api/app/ticket_health.py`, focused API tests, Operations UI rendering, Playwright Operations smoke, and project status docs.
- **Implemented:** `/api/ticket-health/field-certification` now returns `remaining_blocker_diagnostics` at top level and under `source_reports`. Each blocker includes a reason, safe next action, evidence counts, and read-only policy. Operations renders those diagnostics below the field-certification summary.
- **Runtime evidence:** Local API rebuild returned `/ready` `HTTP 200`. Field certification returned `partial_field_certification` with blockers `ticket_status_history`, `status_duration`, `waiting_states`, and `queue`. Diagnostics reported `coverage_backfill=1`, `source_shape_limited=1`, `snapshot_only_duration_limited=1`, `historical_lineage_limited=1`, `automation_can_improve_coverage=1`, and `source_or_lineage_limited=3`.
- **Validation:** PR #117 CI run `29962878273` passed; focused API validation passed with `6 passed`; focused Operations Playwright validation passed with `1 passed`; static web JavaScript syntax passed; full `./scripts/validate-ci.sh` passed with `163` API tests and `13` Playwright tests; `git diff --check` passed.
- **Read-only/authority evidence:** The change only reports local diagnostics and renders them in the local UI. It does not run jobs, write to Autotask, deploy production code, change model thresholds/workflows, or change routing/assignment.
- **Rollback:** Revert this branch commit to remove the diagnostic fields and UI cards; field-certification targets and existing source reports remain available from prior behavior.
- **Second Brain state:** `pull-request-open`; projection PR `newbie10122/helix-second-brain#13` has since advanced to head `977d6be` and records PR #121 status source-candidate schema guidance evidence with local knowledge validation passing: `116` Markdown files, `116` unique IDs, and `271` internal links.

## Current receipt — Milestone 2 ticket picklist metadata sync runtime evidence

- **Slice:** Record post-merge runtime execution for the read-only ticket picklist metadata sync added by PR #114.
- **State:** `partial_foundation`; reference-label source certification is now complete for priority, category, issue type, subissue type, queue, and status, but Milestone 2 remains partial because historical TicketHistory coverage, status-duration, waiting-duration, and queue-at-creation/history lineage remain incomplete.
- **Files changed:** Project status docs only.
- **Implemented by PR #114:** `AutotaskReadOnlyClient.ticket_entity_fields()` reads `/V1.0/Tickets/entityInformation/fields`. `sync_autotask_reference_metadata()` maps supported ticket picklist fields into local reference fields and upserts picklist `value`/`label` pairs as `source='autotask_metadata'`, with raw metadata scoped to the field/picklist item. The `metadata_sync` report includes `ticket_picklist_fields` and `ticket_picklist_upserted`.
- **Runtime evidence:** Local API rebuild returned `/ready` `HTTP 200`. `POST /api/sync/reference-data/start` returned `ok=true`, total `upserted=470`, `metadata_sync.ok=true`, `attempted_entities=['TicketCategories']`, `available_entities=['TicketCategories']`, `ticket_picklist_fields=['issueType','priority','queueID','status','subIssueType','ticketCategory']`, `ticket_picklist_upserted=231`, `metadata_sync.processed=245`, no metadata-sync errors, `read_only=true`, and `autotask_writes_allowed=false`.
- **Field-certification evidence:** `/api/ticket-health/field-certification` remained `partial_field_certification`, with summary `certified=6`, `partial=2`, `source_limited=2`; blockers are `ticket_status_history`, `status_duration`, `waiting_states`, and `queue`. Reference lineage summary is `certified=3`, metadata contract `fields_requiring_metadata_source=0`, and priority/category/issue_type/subissue_type/queue/status each report `100.0%` authoritative label coverage. Queue remains partial because queue-at-creation/history lineage is not certified, not because labels are missing.
- **Validation:** PR #114 CI run `29961689594` passed; PR #115 CI run `29961993981` passed; focused reference-data/probe/contract validation passed with `6 passed`; full validation passed with `163` API tests and `13` Playwright tests; `git diff --check` passed. This docs-only projection-reconciliation branch requires docs whitespace validation and CI before merge.
- **Read-only/authority evidence:** The runtime sync used read-only Autotask metadata endpoints and did not write to Autotask, change model threshold/workflow behavior, change routing/assignment, or deploy production code.
- **Rollback:** Revert the docs-only runtime evidence commit to remove the receipt. To remove local picklist metadata rows, a separately reviewed local database cleanup would be required; do not perform that cleanup as part of documentation rollback.
- **Second Brain state:** `pull-request-open`; projection PR `newbie10122/helix-second-brain#13` has since advanced to head `99eda3e` and records PR #117 field blocker diagnostics evidence with local knowledge validation passing: `114` Markdown files, `114` unique IDs, and `260` internal links.

## Historical receipt — Milestone 2 reference metadata source-contract merge evidence

- **Slice:** Record reference metadata source-contract merge evidence after PR #105 and Second Brain PR #13 update.
- **State:** `partial_foundation`; the app can now state which metadata source is still required before priority/category/queue/status labels become authoritative, but it does not fetch that source or certify completeness.
- **Files changed:** Project status docs only.
- **Implemented by PR #105:** Reference lineage now embeds `metadata_source_contract`, and `/api/ticket-health/reference-metadata-source-contract` exposes the same scoped read-only contract. The report lists present rows, authoritative-label gaps, local source-authority counts, checked raw candidate label keys, unverified candidate metadata entity names, and the required local reference source class.
- **Runtime evidence:** Local API rebuild returned Nginx `/ready` `HTTP 200`; `/api/ticket-health/reference-metadata-source-contract` returned `authoritative_reference_metadata_required`, `6` fields requiring metadata source, `0` fields with candidate raw labels, and policy flags blocking live probes, sync authorization, model workflow changes, and Autotask writes. `/api/ticket-health/field-certification` embeds the same metadata-source contract state.
- **Validation:** PR #105 CI run `29957655373` passed; focused reference metadata contract tests passed with `2 passed`; focused scoped route/route-matrix tests passed with `2 passed`; full repository validation passed with `159` API tests and `13` Playwright tests; `git diff --check` passed. PR #106 documentation reconciliation CI run `29958067967` also passed before merge.
- **Read-only/authority evidence:** This docs-only branch does not run reference sync, live Autotask probes, sync jobs, production deployment, model threshold/workflow changes, routing/assignment changes, or Autotask writes.
- **Rollback:** Revert this docs-only commit; application behavior remains the PR #105 behavior on canonical main.
- **Second Brain state:** `pull-request-open`; existing projection PR `newbie10122/helix-second-brain#13` remains open at head `dda245b` and records PR #105 reference metadata source-contract evidence with local knowledge validation passing.

## Historical receipt — Milestone 2 reference-label source-candidate merge evidence

- **Slice:** Record reference-label source-candidate merge evidence after PR #103 and Second Brain PR #13 update.
- **State:** `partial_foundation`; local ticket payloads can prove whether raw display-label candidate keys exist, but authoritative reference-label completeness remains open.
- **Files changed:** Project status docs only.
- **Implemented by PR #103:** Reference lineage now reports bounded aggregate source candidates for priority, category, issue type, subissue type, queue, and status without returning raw labels. It also corrects category raw value lineage to `ticketCategory`, matching the sync mapping.
- **Runtime evidence:** Local API rebuild returned Nginx `/ready` `HTTP 200`; `/api/ticket-health/field-certification` returned source-candidate state `raw_label_candidates_unavailable` with `5000` sampled tickets, `6` fields, `0` fields with candidate labels, and corrected category raw key `ticketCategory`.
- **Validation:** PR #103 CI run `29956218766` passed; focused API validation passed with `7 passed`; full repository validation passed with `158` API tests and `13` Playwright tests; `git diff --check` passed. PR #104 documentation reconciliation CI run `29957094931` also passed before merge.
- **Read-only/authority evidence:** This docs-only branch does not run reference sync, sync jobs, live Autotask probes, production deployment, model threshold/workflow changes, routing/assignment changes, or Autotask writes.
- **Rollback:** Revert PR #104; application behavior remains the PR #103 behavior on canonical main.
- **Second Brain state:** `pull-request-open`; existing projection PR `newbie10122/helix-second-brain#13` remains open at head `1068a9d` and records PR #103 reference-label source-candidate evidence with local knowledge validation passing.

## Historical receipt — Milestone 2 reference-lineage source-authority merge evidence

- **Slice:** Record reference-lineage source-authority merge evidence after PR #101 and Second Brain PR #13 update.
- **State:** `partial_foundation`; source authority is clearer, but authoritative Autotask reference-label completeness remains open until Autotask-sourced labels cover the relevant local ticket values.
- **Files changed:** Project status docs only.
- **Implemented by PR #101:** Reference lineage reports aggregate source-authority buckets, authoritative/bootstrap/inferred label rows, and authoritative label coverage. Field certification carries those counts into priority/category/queue targets, and the Operations UI displays authoritative label coverage when available.
- **Runtime evidence:** Local API/web rebuild returned Nginx `/ready` `HTTP 200`, UI root `HTTP 200`, and `/api/ticket-health/field-certification` showed priority, category, and queue still `partial` with `0.0%` authoritative label coverage and inferred label rows separated from authoritative rows.
- **Validation:** PR #101 CI run `29954546273` passed; focused API validation passed with `7 passed`; focused Operations browser validation passed with `1 passed`; full repository validation passed with `158` API tests and `13` Playwright tests; `git diff --check` passed. This docs-only reconciliation requires docs whitespace validation and CI before merge.
- **Read-only/authority evidence:** This docs-only branch does not run reference sync, run sync jobs, call Autotask, allow Autotask writes, deploy production code, change model threshold/workflow behavior, or change routing/assignment.
- **Rollback:** Revert this docs-only commit; application behavior remains the PR #101 behavior on canonical main.
- **Second Brain state:** `pull-request-open`; existing projection PR `newbie10122/helix-second-brain#13` remains open at head `93ad3a6` and records PR #101 reference-lineage source-authority evidence with local knowledge validation passing.

## Historical receipt — Milestone 2 reference-lineage source-authority evidence

- **Slice:** Distinguish authoritative Autotask reference labels from bootstrap/inferred local labels on branch `agent/m2-reference-lineage-source-authority` from canonical `main` `4bd7460`.
- **State:** `partial_foundation`; source authority is clearer, but authoritative reference-label completeness remains open until Autotask-sourced labels cover the relevant local ticket values.
- **Files changed:** `apps/api/app/ticket_health.py`, `apps/api/tests/test_ingestion_rag.py`, `apps/web/index.html`, `apps/web/tests/helpers.js`, `apps/web/tests/operations-automation.spec.js`, and project status docs.
- **Implemented:** Reference lineage now reports aggregate source-authority buckets, authoritative/bootstrap/inferred label rows, and authoritative label coverage. Field certification carries those counts into priority/category/queue targets, and the Operations UI displays authoritative label coverage when available.
- **Runtime evidence:** Local API/web rebuild returned Nginx `/ready` `HTTP 200`, UI root `HTTP 200`, and `/api/ticket-health/field-certification` showed priority, category, and queue still `partial` with `0.0%` authoritative label coverage and inferred label rows separated from authoritative rows.
- **Validation:** Focused API validation passed with `7 passed`; focused Operations browser validation passed with `1 passed`; full repository validation passed with `158` API tests and `13` Playwright tests; `git diff --check` passed. GitHub CI is still required before merge.
- **Read-only/authority evidence:** This branch only changes local aggregate certification/reporting and UI display. It does not run reference sync, sync jobs, live Autotask probes, production deployment, model threshold/workflow changes, routing/assignment changes, or Autotask writes.
- **Rollback:** Revert this branch commit; reference lineage returns to meaningful-label coverage without separate source-authority buckets.
- **Second Brain state:** `pull-request-open`; existing projection PR `newbie10122/helix-second-brain#13` records this PR #101 evidence at head `93ad3a6`.

## Historical receipt — Milestone 2 reference-label provenance merge evidence

- **Slice:** Record reference-label provenance merge evidence after PR #99 and Second Brain PR #13 update.
- **State:** `partial_foundation`; source counts are clearer and bootstrap labels are no longer downgraded to inferred, but authoritative Autotask reference-label completeness remains open.
- **Files changed:** Project status docs only.
- **Implemented by PR #99:** Reference sync preserves `source=bootstrap` for known bootstrap values when ticket-observed values are upserted, keeps unknown values `source=inferred`, returns `reference_data_status().by_source`, and displays source counts in the web app.
- **Runtime evidence:** Local runtime smoke after API/web rebuild returned Nginx `/ready` `HTTP 200`, UI root `HTTP 200`, and `/api/reference-data/status` source counts for inferred, Autotask, Autotask metadata, and bootstrap rows.
- **Validation:** PR #99 CI run `29953209879` passed; focused reference provenance tests passed with `3 passed`; focused browser validation passed with `3 passed`; full repository validation passed with `158` API tests and `13` Playwright tests; `git diff --check` passed. This docs-only reconciliation requires docs whitespace validation and CI before merge.
- **Read-only/authority evidence:** This docs-only branch does not run reference sync, run sync jobs, call Autotask, allow Autotask writes, deploy production code, change model threshold/workflow behavior, or change routing/assignment.
- **Rollback:** Revert this docs-only commit; application behavior remains the PR #99 behavior on canonical main.
- **Second Brain state:** `pull-request-open`; existing projection PR `newbie10122/helix-second-brain#13` remains open at head `3c3a78bd93420932ed1a0bd8b0cb7490416bb61c` and records PR #99 reference-label provenance evidence with local knowledge validation passing.

## Historical receipt — Milestone 2 reference-label provenance

- **Slice:** Preserve and expose reference-label provenance on branch `agent/m2-reference-label-provenance` from canonical `main` `d8e70b95139143283b435f958dd377cd362f17ca`.
- **State:** `partial_foundation`; source counts are clearer and bootstrap labels are no longer downgraded to inferred, but authoritative Autotask reference-label completeness remains open.
- **Files changed:** `apps/api/app/ticket_analytics.py`, `apps/api/tests/test_ingestion_rag.py`, `apps/web/index.html`, `apps/web/tests/helpers.js`, `apps/web/tests/rbac.spec.js`, and project status docs.
- **Implemented:** Reference sync now preserves `source=bootstrap` for known bootstrap values when ticket-observed values are upserted, keeps unknown values `source=inferred`, returns `reference_data_status().by_source`, and displays source counts in the web app.
- **Validation:** Focused reference provenance tests passed with `3 passed`.
- **Read-only/authority evidence:** This branch only changes local reference metadata provenance and display. It does not run reference sync, sync jobs, live Autotask probes, production deployment, model threshold/workflow changes, routing/assignment changes, or Autotask writes.
- **Rollback:** Revert this branch commit; reference sync returns to previous source labeling and the UI hides source counts.
- **Second Brain state:** `pull-request-open`; existing projection PR `newbie10122/helix-second-brain#13` records this PR #99 evidence at head `3c3a78bd93420932ed1a0bd8b0cb7490416bb61c`.

## Historical receipt — Milestone 2 scheduler pause/resume provenance merge evidence

- **Slice:** Record scheduler pause/resume provenance merge evidence after PR #97 and Second Brain PR #13 update.
- **State:** `partial_foundation`; local scheduler visibility is stronger, but production restart/recovery certification and broader field/source-lineage completion remain open.
- **Files changed:** Project status docs only.
- **Implemented by PR #97:** Pause/resume writes local provenance fields alongside `global_pause`, exposes `pause_provenance` in Operations status, records safe metadata in success audit events, and displays the latest pause/resume actor in the Operations UI.
- **Validation:** PR #97 CI run `29952434655` passed; focused pause/provenance API tests passed with `2 passed`; focused Admin route audit tests passed with `2 passed`; focused Operations browser smoke passed with `1 passed`; full repository validation passed with `156` API tests and `13` Playwright tests; `git diff --check` passed. This docs-only reconciliation requires docs whitespace validation and CI before merge.
- **Read-only/authority evidence:** This docs-only branch does not run jobs, allow Autotask writes, deploy production code, change model threshold/workflow behavior, change routing/assignment, run sync jobs, or run reference-data sync.
- **Rollback:** Revert this docs-only commit; application behavior remains the PR #97 behavior on canonical main.
- **Second Brain state:** `pull-request-open`; existing projection PR `newbie10122/helix-second-brain#13` remains open at head `e4ed5db2a68c414950a4e6e1ecc68ecf7d00fdb9` and records PR #97 pause/resume provenance evidence with local knowledge validation passing.

## Historical receipt — Milestone 2 scheduler recovery-streak merge evidence

- **Slice:** Record scheduler recovery-streak merge evidence after PR #95 and Second Brain PR #13 update.
- **State:** `partial_foundation`; local runtime evidence now shows scheduler automation and recovery streaks available, but production certification and broader field/source-lineage completion remain open.
- **Files changed:** Project status docs only.
- **Implemented by PR #95:** `scheduler_automation_certification_report()` now includes a `recovery_streak` section that inspects the latest three scheduler-triggered runs per required job, counts clean/problematic runs, reports per-job streak status, and keeps raw error text out of the response. Operations UI displays the recovery-streak state and clean-job count.
- **Runtime evidence:** Local scheduler certification returned scheduler `healthy`, `scheduler_automation_available`, `9` required jobs, `9` certified jobs, `0` running jobs, `0` stale running jobs, recovery streak `scheduler_recovery_streak_available`, `9` clean-streak jobs, `0` partial-streak jobs, and `3` required clean runs per job.
- **Validation:** PR #95 CI run `29951300057` passed; focused scheduler recovery tests passed with `3 passed`; focused Operations browser smoke passed with `1 passed`; Nginx `/ready` and UI root returned `HTTP 200`; full repository validation passed with `155` API tests and `13` Playwright tests; `git diff --check` passed. This docs-only reconciliation requires docs whitespace validation and CI before merge.
- **Read-only/authority evidence:** This docs-only branch does not run jobs, expose raw error text, allow Autotask writes, deploy production code, change model threshold/workflow behavior, change routing/assignment, or run reference-data sync.
- **Rollback:** Revert this docs-only commit; application behavior remains the PR #95 behavior on canonical main.
- **Second Brain state:** `pull-request-open`; existing projection PR `newbie10122/helix-second-brain#13` remains open at head `1c1c63857fcb4907529c5eb7997f3fe0bb27f561` and records PR #95 recovery-streak evidence with local knowledge validation passing.

## Historical receipt — Milestone 2 stale scheduler-run cleanup execution merge evidence

- **Slice:** Record stale scheduler-run cleanup execution merge evidence after PR #93 and Second Brain PR #13 update.
- **State:** `partial_foundation`; canonical docs now reflect PR #93 and Second Brain projection head `7cd186cb9777025770ce5bc27cbe7e77e2408a16`.
- **Files changed:** Project status docs only.
- **Validation:** Full validation and GitHub Actions passed for PR #93 before merge; this reconciliation requires docs whitespace validation and CI before merge.
- **Read-only/authority evidence:** No job cleanup, sync jobs, production deployment, live Autotask probe, model threshold/workflow change, reference-data sync, routing/assignment change, or Autotask write capability was run or added by this docs-only branch.
- **Rollback:** Revert this docs-only commit; application behavior and local cleanup execution evidence remain the PR #93 behavior on canonical main.
- **Second Brain state:** `pull-request-open`; existing projection PR `newbie10122/helix-second-brain#13` remains open at head `7cd186cb9777025770ce5bc27cbe7e77e2408a16` and records PR #93 cleanup-execution evidence with local knowledge validation passing.

## Historical receipt — Milestone 2 stale scheduler-run cleanup execution evidence

- **Slice:** Record guarded local stale scheduler-run cleanup execution after PR #92; merged as PR #93 into canonical `main` `c1caa13d9b9785fce242b4a6ef2df8294857dceb`.
- **State:** `partial_foundation`; the stale local scheduler metadata blocker was cleared and scheduler automation certification now reports available, but three-run scheduler/restart/recovery evidence and production certification remain open.
- **Files changed:** Project status docs only.
- **Runtime evidence:** Local route `POST /api/operations/jobs/4143/archive-stale` returned `ok=true`, `archived=true`, and run `4143` status `stale_orphaned` with current step `archived_stale_orphaned`.
- **Post-cleanup verification:** Local read-only scheduler certification returned `certification_state=scheduler_automation_available`, `ok=true`, `9` required jobs, `9` certified jobs, `0` partial jobs, `0` missing jobs, `0` running jobs, `0` stale running jobs, no blockers, and `0` stale provenance rows. Operations API returned `HTTP 200`, scheduler state `healthy`, and the same scheduler automation summary. Nginx `/ready` and UI root returned `HTTP 200`.
- **Validation:** Focused docs whitespace validation passed; full repository validation passed with `154` API tests and `13` Playwright tests; GitHub Actions run `29950143994` passed. The runtime action did not require application code changes.
- **Read-only/authority evidence:** The executed action was local scheduler metadata cleanup only. It did not run sync jobs, reference-data sync, live Autotask probe, production deployment, model threshold/workflow change, routing/assignment change, or any Autotask write.
- **Rollback:** The code rollback is not applicable because this branch is docs-only; the local metadata row can be inspected historically as `stale_orphaned` and future guarded cleanup remains controlled by PR #91 behavior.
- **Second Brain state:** `pull-request-open`; existing projection PR `newbie10122/helix-second-brain#13` records this PR #93 evidence at head `7cd186cb9777025770ce5bc27cbe7e77e2408a16`.

## Historical receipt — Milestone 2 stale scheduler-run cleanup merge evidence

- **Slice:** Record stale scheduler-run cleanup merge evidence after PR #91 and Second Brain PR #13 update.
- **State:** `partial_foundation`; canonical docs now reflect PR #91 and Second Brain projection head `8235559d0dff9ba8225ebea3164123d8263db7d3`.
- **Files changed:** Project status docs only.
- **Validation:** Full validation and GitHub Actions passed for PR #91 before merge; this reconciliation requires docs whitespace validation and CI before merge.
- **Read-only/authority evidence:** No job cleanup, sync jobs, production deployment, live Autotask probe, model threshold/workflow change, reference-data sync, routing/assignment change, or Autotask write capability was run or added by this docs-only branch.
- **Rollback:** Revert this docs-only commit; application behavior remains the PR #91 behavior on canonical main.
- **Second Brain state:** `pull-request-open`; existing projection PR `newbie10122/helix-second-brain#13` remains open at head `8235559d0dff9ba8225ebea3164123d8263db7d3` and records PR #91 stale scheduler cleanup capability evidence with local knowledge validation passing.

## Historical receipt — Milestone 2 stale scheduler-run cleanup

- **Slice:** Add Admin-only local stale scheduler-run archive action on branch `agent/m2-stale-run-cleanup`; merged as PR #91 into canonical `main` `216e803296698febd0c869bacbce671dd5f60e50`.
- **State:** `partial_foundation`; the app can intentionally clear proven stale local scheduler metadata, but this branch does not run cleanup against the live database or mark sync/recovery certification complete.
- **Files changed:** `apps/api/app/operations.py`, `apps/api/app/main.py`, `apps/api/tests/test_api.py`, `apps/api/tests/test_ingestion_rag.py`, `apps/web/index.html`, `apps/web/tests/helpers.js`, `apps/web/tests/operations-automation.spec.js`, and project status docs.
- **Implemented:** `archive_stale_orphaned_run()` updates local `job_runs` rows to `stale_orphaned` only when the row is running, older than 30 minutes, has no active lock, and has a newer completed run for the same job. The Operations UI shows an Admin-only Archive action for `orphaned_running_row_candidate` cards.
- **Validation:** Focused scheduler/archive tests passed with `3 passed`; focused route/audit tests passed with `4 passed`; focused Operations browser smoke passed with `1 passed`; full repository validation passed with `154 passed`; Playwright browser smoke passed with `13 passed`; `git diff --check` passed; GitHub Actions run `29948960498` passed.
- **Read-only/authority evidence:** No sync jobs, reference-data sync, live Autotask probe, production deployment, model workflow change, routing/assignment change, or Autotask write capability was run or added. The only mutation introduced is local scheduler metadata archival behind Admin route authority.
- **Rollback:** Revert this branch commit; stale scheduler-run provenance remains visible but cannot be archived from the app.
- **Second Brain state:** `pull-request-open`; existing projection PR `newbie10122/helix-second-brain#13` records this PR #91 evidence at head `8235559d0dff9ba8225ebea3164123d8263db7d3`.

## Historical receipt — Milestone 2 stale running-run provenance merge evidence

- **Slice:** Record stale running-run provenance merge evidence after PR #89 and Second Brain PR #13 update.
- **State:** `partial_foundation`; canonical docs now reflect PR #89 and Second Brain projection head `06dacfb4fee52ee48edf11ba39bd07f1059c9ec9`.
- **Files changed:** Project status docs only.
- **Validation:** Full validation and GitHub Actions passed for PR #89 before merge; this reconciliation requires docs whitespace validation and CI before merge.
- **Read-only evidence:** No job cleanup, sync jobs, production deployment, live Autotask probe, model threshold/workflow change, reference-data sync, or Autotask write capability was run or added.
- **Rollback:** Revert this docs-only commit; application behavior remains the PR #89 behavior on canonical main.
- **Second Brain state:** `pull-request-open`; existing projection PR `newbie10122/helix-second-brain#13` remains open at head `06dacfb4fee52ee48edf11ba39bd07f1059c9ec9` and records PR #89 stale-run provenance evidence with local knowledge validation passing.

## Historical receipt — Milestone 2 stale running-run provenance

- **Slice:** Add read-only stale running-run provenance on branch `agent/m2-stale-run-provenance`; merged as PR #89 into canonical `main` `1827b5dd9ecfb55316a6716d671d9c22212f78a7`.
- **State:** `partial_foundation`; the app can now explain stale running rows, but it does not clean them up or mark sync/recovery certification complete.
- **Files changed:** `apps/api/app/operations.py`, `apps/api/tests/test_ingestion_rag.py`, `apps/web/index.html`, `apps/web/tests/helpers.js`, `apps/web/tests/operations-automation.spec.js`, and project status docs.
- **Implemented:** `scheduler_automation_certification_report()` now includes sanitized `stale_running_provenance` rows with run ID, job name, started time, age, trigger, current step, active-lock presence, newer completed run evidence, and a classified stale state. Operations UI now shows scheduler certification state, stale-run count, and stale-run provenance cards.
- **Runtime evidence:** Local read-only smoke reported `partial_scheduler_automation_evidence`, `1` stale running row, `classify_tickets` run `4143`, no active lock, newer completed run `4391`, and stale state `orphaned_running_row_candidate`.
- **Validation:** Focused scheduler automation tests passed with `2 passed`; focused Operations browser smoke passed with `1 passed`; full repository validation passed with `153 passed`; Playwright browser smoke passed with `13 passed`; `git diff --check` passed; GitHub Actions run `29948149588` passed.
- **Read-only evidence:** No job cleanup, sync jobs, production deployment, live Autotask probe, model threshold/workflow change, reference-data sync, or Autotask write capability was run or added.
- **Rollback:** Revert this branch commit; scheduler automation certification returns to stale-run counts without detailed provenance, and the Operations UI hides stale provenance cards.
- **Second Brain state:** `pull-request-open`; existing projection PR `newbie10122/helix-second-brain#13` records this PR #89 evidence at head `06dacfb4fee52ee48edf11ba39bd07f1059c9ec9`.

## Historical receipt — Milestone 2 scheduler automation evidence

- **Slice:** Add read-only scheduler automation certification on branch `agent/m2-sync-recovery-evidence`; merged as PR #87 into canonical `main` `2a3841b83ef336462eb162ec64bbe1531f776f9e`.
- **State:** `partial_foundation`; all required scheduled jobs have recent scheduler-completed evidence, but one stale running job row prevents a full sync/recovery streak claim.
- **Files changed:** `apps/api/app/operations.py`, `apps/api/tests/test_ingestion_rag.py`, and project status docs.
- **Implemented:** `scheduler_automation_certification_report()` summarizes required scheduled jobs, enabled state, cadence, latest run status, scheduler-triggered run counts for 24h and 7d, stale running-run counts, blockers, and safe policy metadata. `operations_status()` now includes `scheduler_automation`, and the operations-status scoped cache version was bumped.
- **Runtime evidence:** Local read-only scheduler certification returned scheduler `healthy`, `9` required jobs, `9` certified jobs, `0` partial jobs, `0` missing jobs, `2` running jobs, blocker `stale_running_jobs`, and recent scheduler-completed runs for recent sync, open-ticket TimeEntries/TicketHistory gaps, estate TimeEntries/TicketHistory gaps, sync-reference-data, classification, reclassification, and nightly pipeline.
- **Validation:** Focused container validation passed with `86 passed`. API/worker Python compilation and full pytest passed with `152 passed`; Playwright browser smoke passed with `13 passed`. Real local Postgres smoke for `scheduler_automation_certification_report()` passed.
- **Read-only evidence:** No sync jobs, production deployment, live Autotask probe, model threshold/workflow change, reference-data sync, or Autotask write capability was run or added.
- **Rollback:** Revert this branch commit; Operations status returns to the prior scheduler/status payload without explicit scheduler automation certification.
- **Second Brain state:** `pull-request-open`; existing projection PR `newbie10122/helix-second-brain#13` remains open at head `709c1e736a223b6f5759bdb0d47a7a702999c228` and records this PR #87 scheduler automation evidence with local knowledge validation passing.

## Historical receipt — Milestone 2 reference-field lineage

- **Slice:** Add scoped priority/category/queue reference-field lineage on branch `agent/m2-reference-field-lineage`; merged as PR #85 into canonical `main` `d295d6a6ad1168f3cbd2deb717422936ef5c34aa`.
- **State:** `partial_foundation`; current local priority, category/issue/subissue, and queue values are present, but the local reference-value rows are inferred placeholders and therefore not fully certified as meaningful/authoritative labels.
- **Files changed:** `apps/api/app/ticket_health.py`, `apps/api/tests/test_ingestion_rag.py`, and project status docs.
- **Implemented:** `reference_field_lineage_report()` returns aggregate-only scoped field presence, raw-value coverage, distinct-value counts, local reference coverage, meaningful-label coverage, source counts, and bucketed top-value evidence for priority, category, issue type, subissue type, queue, and status. `field_certification_report()` now includes priority, category, and queue reference-lineage targets plus `source_reports.reference_lineage`, keeping those inputs excluded from model training until certified.
- **Runtime evidence:** Local read-only reference lineage found `67726` tickets, priority present rows `67726`, queue present rows `67665`, and category/issue/subissue present rows `187528` across those three fields. Priority, category, and queue reference targets are `partial` with `0%` meaningful mapped-label coverage because all current local labels are inferred placeholders. Field certification blockers are `ticket_status_history`, `status_duration`, `waiting_states`, `priority`, `category`, and `queue`.
- **Validation:** Focused container validation passed with `85 passed`. API/worker Python compilation and full pytest passed with `151 passed`; Playwright browser smoke passed with `13 passed`. Real local Postgres smoke for `reference_field_lineage_report()` and `field_certification_report()` passed.
- **Read-only evidence:** No sync jobs, production deployment, live Autotask probe, model threshold/workflow change, reference-data sync, or Autotask write capability was run or added.
- **Rollback:** Revert this branch commit; field certification returns to the prior target set without explicit priority/category/queue reference-lineage targets.
- **Second Brain state:** `pull-request-open`; existing projection PR `newbie10122/helix-second-brain#13` recorded this PR #85 reference-lineage evidence with local knowledge validation passing and has since advanced to the current head documented in the Second Brain state section.

## Historical receipt — Milestone 2 customer/technician response lineage

- **Slice:** Add scoped customer/technician response-lineage certification on branch `agent/m2-response-lineage-certification`; merged as PR #83 into canonical `main` `15ca2bada4aa81bdd1c29cfd4f503ad7b4f6eb1a`.
- **State:** `partial_foundation`; local ticket-note author identifiers and raw `createDateTime` timestamps are present, while normalized ticket-note timestamps need future sync/upsert/backfill refresh before the normalized column alone can carry the evidence.
- **Files changed:** `apps/api/app/ticket_health.py`, `apps/api/tests/test_ingestion_rag.py`, and project status docs.
- **Implemented:** `response_lineage_report()` returns aggregate-only scoped counts for customer-attributed notes, technician-attributed notes, normalized/raw timestamp coverage, ambiguous author attribution, open-ticket response coverage, author-source fields, safe note-type aggregates, and a no-raw-note-text/no-note-body-attribution policy. Ticket-note ingestion now recognizes Autotask `createDateTime` in addition to `createdDateTime` and `createDate`. `field_certification_report()` now includes `customer_responses` and `technician_responses` targets plus `source_reports.response_lineage`, keeping the evidence review-only.
- **Runtime evidence:** Local read-only field certification found `675531` scoped ticket notes, `8091` customer-attributed notes, `667440` technician-attributed notes, `0` ambiguous notes, `8091` timestamped customer notes, `667440` timestamped technician notes, `100%` raw-backed timestamp coverage, and `0` normalized timestamp rows; response lineage state is `response_lineage_available`.
- **Validation:** Focused container validation passed with `84 passed`. API/worker Python compilation and full pytest passed with `150 passed`; static web JavaScript syntax, Playwright browser smoke `13 passed`, and clean `git diff --check` passed.
- **Read-only evidence:** No sync jobs, production deployment, live Autotask probe, model threshold/workflow change, or Autotask write capability was run or added.
- **Rollback:** Revert this branch commit; field certification returns to the prior target set without explicit customer/technician response lineage targets.
- **Second Brain state:** `pull-request-open`; existing projection PR `newbie10122/helix-second-brain#13` records this PR #83 response-lineage evidence with local knowledge validation passing and has since advanced to the current head documented in the Second Brain state section.

## Historical receipt — Milestone 2 status-duration and waiting source-lineage

- **Slice:** Certify status-duration and waiting-state source limitations on branch `agent/m2-status-duration-waiting-lineage` from canonical `main` `16aee8b0ccb1393ca52be2e86790f94220052150`; merged as PR #81 into canonical `main` `27b0bd7e502a0b9ef74b60238f0e9f362ece422b`.
- **State:** `partial_foundation`; current waiting-state snapshot taxonomy is available from scoped local current status/reference labels, but historical status-duration and waiting-duration remain `source_limited` because local TicketHistory has no structured timestamped status-transition rows.
- **Files changed:** `apps/api/app/ticket_health.py`, `apps/api/tests/test_ingestion_rag.py`, and project status docs.
- **Implemented:** `status_duration_summary()` no longer turns current ticket proxy timestamps into lower-bound waiting duration when no parsed status transitions exist. `ticket_history_source_shape_inventory()` adds aggregate-only, scoped TicketHistory shape counts for timestamp coverage, structured status-transition availability, parser-incompatible status-like rows, duplicate timestamps, non-monotonic timestamps, raw-key frequency, safe action identifiers, and sanitized shape signatures. `current_waiting_state_snapshot_report()` adds versioned current-status taxonomy buckets while leaving unknown/unmapped statuses unknown and avoiding ticket prose.
- **Runtime evidence:** Local read-only field certification found `38648` TicketHistory rows, `100%` timestamp coverage, `0` structured status-transition rows, `1` status-like parser-incompatible row, and current waiting snapshot summary `67726` tickets with `101` unknown/unmapped; blockers remain `ticket_status_history`, `status_duration`, and `waiting_states`.
- **Validation:** Focused container validation passed: `docker compose run --rm -T --no-deps -v "$PWD":/workspace -w /workspace api pytest apps/api/tests/test_ingestion_rag.py -q` returned `81 passed`. API/worker Python compilation and full pytest passed with `147 passed`; static web JavaScript syntax, Playwright browser smoke `13 passed`, and clean `git diff --check` passed.
- **Read-only evidence:** No sync jobs, production deployment, live Autotask probe, model threshold/workflow change, or Autotask write capability was run or added.
- **Rollback:** Revert this branch commit; no migration is included and field certification returns to the prior parser/source-candidate-only status-duration evidence.
- **Second Brain state:** `pull-request-open`; existing projection PR `newbie10122/helix-second-brain#13` recorded this PR #81 evidence with local knowledge validation passing and has since advanced to the current head documented in the Second Brain state section.

## Historical receipt — Milestone 2 SLA lineage certification

- **Slice:** Add scoped SLA lineage evidence to field certification on branch `agent/m2-sla-lineage-certification` from canonical `main` `b2b9faa65963f1dad280195150bb5128cc0d855c`; merged as PR #79 into canonical `main` `b504622a828379434e91a41f40c0247cd5dbebf9`.
- **State:** `partial`; SLA evidence is more explicit and scoped, but Milestone 2 still requires full sync/recovery streak evidence, status-duration/waiting certification, and production certification.
- **Files changed:** `apps/api/app/ticket_health.py`, `apps/api/tests/test_ingestion_rag.py`, and project status docs.
- **Implemented:** `sla_lineage_report()` reports scoped local counts for SLA identifiers, met flags, generic due dates, first-response due targets, resolution-plan due targets, resolved due targets, pause context, by-status SLA coverage, warnings, and scope application. Field certification now embeds the SLA lineage report and keeps SLA certification `partial` when SLA identifiers/met flags exist without complete due/response/resolution target timestamps.
- **Validation:** Focused container validation passed: `docker compose run --rm -T --no-deps -v "$PWD":/workspace -w /workspace api pytest apps/api/tests/test_ingestion_rag.py -q` returned `77 passed`. Full API compile/pytest validation passed with `143 passed`; static web JavaScript syntax, direct Playwright browser smoke `13 passed`, and clean `git diff --check` passed; PR #79 CI run `29938144886` passed before merge.
- **Read-only evidence:** No sync jobs, production deployment, live Autotask probe, model workflow change, or Autotask write capability was run or added.
- **Rollback:** Revert this branch commit; no migration is included and SLA field certification returns to the prior aggregate field row.
- **Second Brain state:** `pull-request-open`; existing projection PR `newbie10122/helix-second-brain#13` remains open at head `ed311a9166088aebce7cf1ece1d30a76017e1697` and records this PR #79 evidence with local knowledge validation passing.

## Historical receipt — Milestone 2 scoped labor lineage

- **Slice:** Apply authorized company scope to labor coverage lineage on branch `agent/m2-scoped-labor-lineage` from canonical `main` `f2212e93ad80259b6b5bba5eb121071d15c6fd5c`; merged as PR #77 into canonical `main` `c9a8accf4d5a7a4a8e8e8e1c9fc807fd77b75df4`.
- **State:** `partial`; scoped labor evidence is stronger, but Milestone 2 still requires full sync/recovery streak evidence, status-duration/waiting certification, SLA lineage, and production certification.
- **Files changed:** `apps/api/app/ticket_health.py`, `apps/api/tests/test_ingestion_rag.py`, and project status docs.
- **Implemented:** `labor_coverage_report()` now accepts `authorized_company_ids`, applies the existing company-scope SQL helper to open-ticket labor summary, by-status, and next-target queries, returns whether company scope was applied, and field certification now fetches labor coverage with the same authorized company scope as the surrounding certification reports.
- **Validation:** Focused container validation passed: `docker compose run --rm -T --no-deps -v "$PWD":/workspace -w /workspace api pytest apps/api/tests/test_ingestion_rag.py -q` returned `75 passed`. Full API compile/pytest validation passed with `141 passed`; static web JavaScript syntax, direct Playwright browser smoke `13 passed`, and clean `git diff --check` passed. The local full `./scripts/validate-ci.sh` path was blocked at `npx playwright install --with-deps chromium` by unreachable Ubuntu mirrors; PR #77 CI run `29937143017` passed before merge.
- **Read-only evidence:** No sync jobs, production deployment, live Autotask probe, model workflow change, or Autotask write capability was run or added.
- **Rollback:** Revert this branch commit; no migration is included and labor coverage returns to global open-ticket reporting inside field certification.
- **Second Brain state:** `pull-request-open`; existing projection PR `newbie10122/helix-second-brain#13` remains open at head `9ebafae751455669da145675e1215bdbe15b1a4f` and records this PR #77 evidence with local knowledge validation passing.

## Historical receipt — Milestone 2 labor gap lineage

- **Slice:** Carry TimeEntries gap-check lineage into field certification on branch `agent/m2-labor-gap-lineage` from canonical `main` `dff08b09de8bc4c1e12f111ef19ba0aa8a661d1b`; merged as PR #75 into canonical `main` `b03f4f35b2d032af58e7447444be6550136f9410`.
- **State:** `partial`; labor evidence is more accurately classified, but Milestone 2 still requires full sync/recovery streak evidence, status-duration/waiting certification, SLA lineage, and production certification.
- **Files changed:** `apps/api/app/ticket_health.py`, `apps/api/tests/test_ingestion_rag.py`, and project status docs.
- **Implemented:** `/api/ticket-health/field-certification` now includes `labor_gap_context` from open-ticket TimeEntries gap checks and exposes checked, checked-empty, and unchecked open-ticket labor counts on the TimeEntries target. Checked-empty TimeEntries are treated as confirmed zero-result reads, while unchecked open tickets keep TimeEntries/labor certification `partial`.
- **Validation:** Focused container validation passed: `docker compose run --rm -T --no-deps -v "$PWD":/workspace -w /workspace api pytest apps/api/tests/test_ingestion_rag.py -q` returned `73 passed`. Full governed validation passed with production-auth preflight, redacted Compose validation, migration ordering, API image build, API/worker Python compilation, full pytest `139 passed`, static web JavaScript syntax, Playwright browser smoke `13 passed`, and clean `git diff --check`; PR #75 CI run `29933463319` passed before merge.
- **Read-only evidence:** No sync jobs, production deployment, live Autotask probe, model workflow change, or Autotask write capability was run or added.
- **Rollback:** Revert this branch commit; no migration is included and field certification returns to prior row-count-only labor classification.
- **Second Brain state:** `pull-request-open`; existing projection PR `newbie10122/helix-second-brain#13` remains open at head `efde35985ce30cc3955f27488ba16336ef5e2cdf` and records this PR #75 evidence with local knowledge validation passing.

## Historical receipt — Milestone 1 audit inspection coverage

- **Slice:** Add bounded audit-log filtering and Operations read inspection audits on branch `agent/audit-log-filtering` from canonical `main` `ffd53e9dbe26bcbf20f7c8669d8c895a6381f6bd`; merged as PR #72 into canonical `main` `63201015556cdee0df5e250c88213bc465765aee`.
- **State:** `partial`; durable audit inspection coverage is stronger, but full workflow audit certification, live production-auth deployment evidence, and capability-specific Quality Streak evidence remain open.
- **Files changed:** `apps/api/app/audit.py`, `apps/api/app/main.py`, `apps/api/tests/test_api.py`, and project status docs.
- **Implemented:** `GET /audit-log` remains Admin-only and now accepts bounded `actor`, `action`, `outcome`, `target`, and `limit` filters, returns the applied filter contract, and records the read with safe filter/limit metadata. Operations read routes for status, settings, jobs, and job runs now record identity-linked success audit events with compact scheduler state/count metadata when inspected.
- **Validation:** Initial focused container command without the governed `/workspace` mount found no tests because the API image workdir only contains the copied app. Rerun with the validator mount pattern passed: `docker compose run --rm -T --no-deps -v "$PWD":/workspace -w /workspace api pytest apps/api/tests/test_api.py -q` returned `34 passed`. Full governed validation passed with production-auth preflight, redacted Compose validation, migration ordering, API image build, API/worker Python compilation, full pytest `138 passed`, static web JavaScript syntax, Playwright browser smoke `13 passed`, and clean `git diff --check`; PR #72 CI run `29931726891` passed before merge.
- **Read-only evidence:** No sync jobs, production deployment, live Autotask probe, model workflow change, or Autotask write capability was run or added.
- **Rollback:** Revert this branch commit; no migration is included and audit-log reads/Operations reads return to prior behavior.
- **Verifier:** Read-only sidecar recommended Operations inspection read audit coverage as the highest-value safe Milestone 1 slice; coordinator integrated it with the audit-log filtering slice.
- **Second Brain state:** `pull-request-open`; projection PR `newbie10122/helix-second-brain#13` records this audit inspection update and later PR #75 labor lineage evidence at head `efde35985ce30cc3955f27488ba16336ef5e2cdf` with local knowledge validation passing.

Parallel-safe work after roadmap merge:

- Agent A: CI and repository validation.
- Agent B: authentication/RBAC design and negative tests.
- Agent C: client-scope data model and retrieval isolation analysis/tests.
- Agent D: prompt-injection and independent verifier contract/tests.
- Independent verifier: review threat model, overlap, integration order, and acceptance coverage.

Shared schema and integration changes must be serialized by the coordinator.

## Critical blockers

None currently identified for documentation and non-production implementation work. Production deployment, customer-data scope expansion, irreversible migrations, and any Autotask write capability remain approval-gated.

## Latest receipt — Predictive calibrated review-ranking signal

- **Slice:** Expose calibrated review-only predictive ranking signal on branch `agent/predictive-ranking-calibrated-score` from canonical `main` `5469e3949fb2c750fceb91059342ec078ae27c31`.
- **State:** `partial_foundation`; predictive ranking remains review-only and no threshold/model/workflow change is authorized.
- **Implemented:** Predictive review signals now include model version `bayesian_queue_priority_feedback_v1_review_only`, calibrated delay probability, transparent calibration adjustments, and calibrated rank contribution. Ticket Health UI displays calibrated probability/contribution in the existing Reasons cell while keeping low-sample abstention.
- **Validation:** focused container validation passed for predictive review signal contracts with `2 passed`; focused Ticket Health Playwright validation passed with `1 passed`.
- **Read-only evidence:** No sync jobs, production deployment, live credential changes, local feedback writes, Autotask writes, model threshold changes, routing, escalation, notification, assignment, status, priority, or workflow changes were run or added.
- **Rollback:** Revert this branch commit; predictive review queue returns to raw Bayesian delay-rate scoring without calibrated probability fields.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Historical receipt — Milestone 2 related-data catch-up cadence

- **Slice:** Improve bounded related-data estate catch-up cadence and visibility on branch `agent/m2-related-data-catchup-cadence` from canonical `main` `d831d8b0a2a173605fba927327a79330667546f9`.
- **State:** `partial_foundation`; scheduled TimeEntries/TicketHistory catch-up remains bounded and read-only, but estate-wide coverage is not complete.
- **Runtime observation:** Local Operations status on 2026-07-22 returned scheduler `healthy`, `global_pause=false`, counts `tickets=67726`, `time_entries=50751`, `ticket_history=30186`, open-ticket TicketHistory coverage `100%`, open-ticket labor unchecked `0`, estate TimeEntries backlog `32082`, and estate TicketHistory backlog `64047`.
- **Implemented:** Estate TimeEntries and TicketHistory gap batch defaults move from `25` to `100` within the existing configured upper bound, and existing persisted settings still equal to the old default `25` are upgraded while operator-customized values are preserved. `/api/operations/status` related-data work-plan items now include `estimated_runs_to_check`. Operations UI renders backlog, unchecked count, bounded limit, and estimated runs next to recent related-data job movement.
- **Validation:** focused container validation passed for scheduler defaults, related-data gap job preservation, and bounded catch-up run estimates with `3 passed`; focused Operations Playwright validation passed with `1 passed`.
- **Read-only evidence:** No sync jobs, production deployment, live credential changes, local feedback writes, Autotask writes, model threshold changes, routing, escalation, notification, assignment, status, priority, or workflow changes were run or added.
- **Rollback:** Revert this branch commit; estate gap jobs return to prior `25` defaults and Operations hides estimated catch-up runs.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Historical receipt — Milestone 1 admin-read audit closeout

- **Slice:** Record admin inspection read success audits on branch `agent/m1-audit-scope-closeout` from canonical `main` `725621de2356cd1337a8e17f68e7f02ff9616040`.
- **State:** `partial`; admin read audit coverage improved, but full durable-audit certification and production-auth deployment evidence remain open.
- **Files changed:** `apps/api/app/main.py`, `apps/api/tests/test_api.py`, and project status docs.
- **Implemented:** `GET /audit-log` now records a durable success audit event for `audit_log.read`, and `GET /api/admin/curated-memory` records `curated_memory.pending.read` with safe `item_count` metadata. Existing admin route authority remains unchanged.
- **Validation:** focused container validation passed for admin route matrix and admin success-audit coverage with `2 passed`.
- **Read-only evidence:** No sync jobs, production deployment, live credential changes, local feedback writes, Autotask writes, model threshold changes, routing, escalation, notification, assignment, status, priority, or workflow changes were run or added.
- **Rollback:** Revert this branch commit; admin read routes return to prior success-audit coverage.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Historical receipt — PR66 Ask mode ready-status evidence

- **Slice:** Record mode-specific Ask Assistant ready-status evidence on branch `agent/ask-mode-ready-status-docs` from canonical `main` `99f79d82b8803b7d12930228f95aa023ce647107`.
- **State:** `partial`; the UI now distinguishes modes before a request is submitted, but live production-auth deployment evidence and broader capability certification remain open.
- **Files changed:** Project status and certification documents only.
- **Implemented evidence:** PR #65 made Ask Assistant ready text mode-specific: Ticket History Only says it uses retrieved ticket evidence without the local CPU model, General + Ticket History says it can take up to a minute on the local CPU model, and Deep Dive says it can spend longer waiting on the local CPU model. PR #66 recorded this evidence in canonical project documents.
- **Validation:** Full governed validation passed with production-auth preflight, redacted Compose validation, migration ordering, API image build, API/worker Python compilation, full pytest `134 passed`, static web JavaScript syntax, Playwright browser smoke `13 passed`, and clean `git diff --check`; PR #66 GitHub Actions run `29892106293` passed before merge.
- **Read-only evidence:** No sync jobs, production deployment, live credential changes, local feedback writes, Autotask writes, model threshold changes, routing, escalation, notification, assignment, status, priority, or workflow changes were run or added.
- **Rollback:** Revert PR #66 for docs evidence only; revert PR #65 to return Ask Assistant to the prior generic ready text.
- **Second Brain state:** Existing projection PR #6 updated through PR #66 at head `8042a4b`; local knowledge validation passed.

## Historical receipt — Operations field-certification UI evidence

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

## Latest receipt — Ask mode ready status

- **Slice:** Show mode-specific Ask Assistant ready status on branch `agent/ask-mode-ready-status` from canonical `main` `14bc4f082fff2f1582ccfce456052bae4a6d6c1b`; merged as PR #65 into canonical `main` `99f79d82b8803b7d12930228f95aa023ce647107`.
- **State:** `partial`; mode semantics are clearer in the UI, but live production-auth deployment evidence remains open.
- **Files changed:** `apps/web/index.html`, `apps/web/tests/ask-status.spec.js`, and project status docs.
- **Implemented:** Ask Assistant ready text now reflects the selected mode: Ticket History Only says it uses retrieved evidence without the local CPU model, while General + Ticket History and Deep Dive tell operators the local model may be involved.
- **Validation:** Focused `npx playwright test apps/web/tests/ask-status.spec.js` passed with `5 passed`; full `./scripts/validate-ci.sh` passed with production-auth preflight, redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `134 passed`, static web JavaScript syntax validation, Playwright browser smoke `13 passed`, and `git diff --check`.
- **Runtime evidence:** Local web container was rebuilt; `/ready` returned ready and the served web bundle contains all three mode-specific ready messages.
- **Read-only evidence:** No backend API contract, sync job, production deployment, live credential, model tuning, routing, workflow, or Autotask write behavior was changed.
- **Rollback:** Revert this branch commit; the Ask Assistant returns to its prior static ready message.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Ticket History Only deterministic mode

- **Slice:** Make Ticket History Only skip the local LLM on branch `agent/ticket-history-only-no-llm` from canonical `main` `cc63a9e1434a0dc15a1c5bc25258f23d7b6549a1`; merged as PR #63 into canonical `main` `e05f32ed28b4446ad53bdd6911e782f9f3d22d6f`.
- **State:** `partial`; mode behavior is clearer and faster for deterministic evidence, but live production-auth deployment evidence remains open.
- **Files changed:** `apps/api/app/assistant.py`, `apps/api/tests/test_ingestion_rag.py`, `apps/web/index.html`, `apps/web/tests/ask-status.spec.js`, and project status docs.
- **Implemented:** `ticket_history_only` returns retrieved local ticket evidence without invoking `_chat_with_timeout`; generated-answer verifier tests now explicitly use generated modes. The Ask progress UI labels the model phase as skipped for Ticket History Only.
- **Validation:** Focused API mode tests passed with `2 passed`; focused `npx playwright test apps/web/tests/ask-status.spec.js` passed with `4 passed`; full `./scripts/validate-ci.sh` passed with production-auth preflight, redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `134 passed`, static web JavaScript syntax validation, Playwright browser smoke `12 passed`, and `git diff --check`.
- **Runtime evidence:** Local API/web containers were rebuilt; `/ready` returned ready and the static web bundle contains the Ticket History Only skip-label logic.
- **Read-only evidence:** No sync job, production deployment, live credential, model tuning, routing, escalation, notification, assignment, workflow, or Autotask write behavior was changed.
- **Rollback:** Revert this branch commit; Ticket History Only resumes the prior generated-answer path when evidence is strong.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Ask Assistant progress phases

- **Slice:** Show Ask Assistant request phases on branch `agent/ask-progress-phases` from canonical `main` `068473623df7134294c46cb9767eae8cc59a3b43`; merged as PR #61 into canonical `main` `98c047d290fa3ae89b1d196fbfcc91771e55de98`.
- **State:** `partial`; conversational request state is clearer, but live production-auth deployment evidence remains open.
- **Files changed:** `apps/web/index.html`, `apps/web/styles.css`, `apps/web/tests/ask-status.spec.js`, and project status docs.
- **Implemented:** Ask Assistant now shows visible request phases for scoped ticket search, evidence preparation, local CPU model waiting, and answer rendering. Running text says the request is active, while timeout/error/done text says no browser request remains active.
- **Validation:** Focused `npx playwright test apps/web/tests/ask-status.spec.js` passed with `4 passed`; full `./scripts/validate-ci.sh` passed with production-auth preflight, redacted Compose validation, 10 ordered migrations, API image build, API/worker Python compile, full pytest `133 passed`, static web JavaScript syntax validation, Playwright browser smoke `12 passed`, and `git diff --check`.
- **Read-only evidence:** No backend API contract, sync job, production deployment, live credential, local feedback, model, workflow, or Autotask write behavior was changed.
- **Rollback:** Revert this branch commit; Ask Assistant returns to the prior single-line running/timeout status while ticket-detail modal links remain intact.
- **Second Brain state:** `pending-update`; update existing projection PR #6 after this Autotask AI PR is merged.

## Previous receipt — Ask Assistant answer ticket links

- **Slice:** Make ticket IDs inside assistant answers inspectable on branch `agent/answer-ticket-links` from canonical `main` `4f7029b5ba818d3a413e2411a4fa94e06963f06b`.
- **State:** `partial`; assistant answer evidence is easier to inspect in the UI, but live production-auth deployment evidence remains open.
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

`pull-request-open` — projection PR `newbie10122/helix-second-brain#13` is open on branch `agent/autotask-ai-audit-inspection-projection` at head `977d6be`. It records Autotask AI progress through PR #121, including PR #75 labor gap lineage, PR #77 scoped labor lineage, PR #79 scoped SLA lineage, PR #81 status-duration/waiting source-limited evidence, PR #83 response-lineage evidence, PR #85 reference-field lineage evidence, PR #87 scheduler automation evidence, PR #89 stale-run provenance evidence, PR #91 stale scheduler cleanup capability evidence, PR #93 cleanup-execution evidence, PR #95 recovery-streak evidence, PR #97 pause/resume provenance evidence, PR #99 reference-label provenance evidence, PR #101 reference-lineage source-authority evidence, PR #103 reference-label source-candidate evidence, PR #105 reference metadata source-contract evidence, PR #107 reference metadata source-probe evidence, PR #109 reference metadata runtime-probe evidence, PR #112 TicketCategories metadata sync runtime evidence, PR #115 ticket picklist metadata sync runtime evidence, PR #117 field blocker diagnostics evidence, PR #119 TicketHistory schema probe evidence, and PR #121 status source-candidate schema guidance evidence. Local Second Brain validation passed with `python3 tools/validate_knowledge.py` using `116` Markdown files, `116` unique IDs, and `271` internal links.

## Exact next action

Commit and merge this docs-only projection reconciliation, then continue the next safe Milestone 2 source-lineage slice. Keep production-auth deployment evidence approval-gated and keep status-duration/waiting/response timing source-limited unless parser-compatible timestamps are backfilled or another read-only source is found.
