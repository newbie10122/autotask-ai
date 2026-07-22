# Autotask AI Known Risks

**Updated:** 2026-07-22

## Critical and high risks

### R1 — Authentication/RBAC foundation is not production-enforced end to end

**Severity:** Critical for production
**State:** Partially mitigated
**Impact:** Branch `agent/m1-auth-rbac-foundation` replaces placeholder token behavior with hashed passwords, signed expiring tokens, optional route enforcement, and admin denial tests. Branch `agent/m1-route-authority-audit-matrix` adds admin gates and a route inventory contract for sensitive routes. Branches `agent/m1-browser-rbac-smoke`, `agent/m1-browser-accessibility-smoke`, and `agent/m1-keyboard-focus-smoke` add first real-browser UI RBAC, axe accessibility, and keyboard/focus smoke coverage. Branch `agent/m1-production-auth-preflight` adds CI-validated deploy-time auth-boundary checks. Branch `agent/m1-bootstrap-admin-user` adds a local hashed app-user bootstrap command, but live production app-route auth remains approval-gated.
**Mitigation:** Finish live production-auth deployment receipt and three-run security evidence before production enforcement.
**Approval gate:** Production authentication changes require security review and controlled deployment.

### R2 — Client/company isolation is not yet proven fail-closed

**Severity:** Critical
**State:** Partially mitigated
**Impact:** Retrieval, analytics, citations, or future caches could expose one client’s information to an unauthorized user.
**Existing controls:** Branch `agent/m1-company-scope-foundation` adds user-company scope storage, fail-closed assistant/analytics route scope checks, and scoped retrieval/recurring-analytics filters when app route auth is enabled.
**Next mitigation:** Carry effective scope through remaining cache consumers, verifier checks, ticket-health/customer-success/routing APIs, and broader cross-client negative tests.

### R3 — Independent answer verification and prompt-injection defense are incomplete

**Severity:** High
**State:** Partially mitigated
**Impact:** Retrieved untrusted content could influence answers or unsupported claims could appear with insufficient evidence.
**Existing controls:** Branch `agent/m1-auth-rbac-foundation` adds deterministic prompt-injection detection, unsafe source filtering before model prompt assembly, and citation-subset verification for generated answers. Branch `agent/m1-source-sufficiency-verifier` adds first fail-closed source-overlap checks for ticket-history claims beyond explicit resolution/fix claims.
**Next mitigation:** Broaden adversarial source-sufficiency cases, independent verifier receipts, and three-run adversarial evidence.

### R4 — Audit evidence is not fully durable and identity-linked

**Severity:** High
**State:** Partially mitigated
**Impact:** Security and operational actions may not be reconstructable after restart unless every material path writes identity-linked audit records.
**Existing controls:** Branch `agent/m1-durable-audit-scope-foundation` adds durable `audit_log` persistence, outcome/scope fields, and authorization-denial audit events with no-DB fallback. Branch `agent/m1-success-audit-scope-linkage` adds centralized success records for material admin actions, recurring analytics, assistant ask, and feedback. PR #68 adds success audit records for admin reads of the audit log and pending curated-memory queue. PR #72 adds bounded audit-log filtering and success audits for Operations read inspections.
**Next mitigation:** Link audit records across remaining workflows and include verifier-failure receipts in the certification matrix before treating audit coverage as complete.

### R5 — Quality Streak evidence not yet established

**Severity:** High
**State:** Partially mitigated
**Impact:** Local and GitHub CI validation now exist for the governed CI branch, but three-run Quality Streak evidence and a fuller certification matrix are not yet established.
**Mitigation:** Build certification matrix plus three-consecutive-clean-run receipts without overstating existing capability certification.

## Medium risks

### R6 — CPU-only model latency and quality

**Severity:** Medium
**State:** Partially mitigated
**Impact:** Slow or weak generation may reduce technician usefulness.
**Existing controls:** Retrieval-first design, deterministic analytics, context limits, normal/deep-dive modes, timeouts, and evidence fallback.
**Next mitigation:** Benchmarks, scoped Redis caching, verifier metrics, and model/provider configuration controls.

### R7 — Incomplete operational Autotask data

**Severity:** Medium
**State:** Partially mitigated
**Impact:** Ticket-health, prediction, and routing calculations may be incomplete or misleading.
**Existing controls:** PR `newbie10122/autotask-ai#10` restored read-only TimeEntries and TicketHistory automation, including recent-sync TimeEntries, open-ticket gap repair, estate-wide gap sweeps, and operations coverage reporting. Branch `agent/m2-related-data-catchup-cadence` raises bounded estate TimeEntries/TicketHistory gap batch defaults to `100`, upgrades persisted old-default `25` values only, and exposes estimated bounded catch-up runs in Operations.
**Next mitigation:** Complete field inventory, source-lineage certification, SLA/status/waiting fields, freshness policy, restart/recovery tests, and explicit distinctions among synchronized, checked-empty, unchecked, failed, unavailable, and authorization-filtered data.

### R18 — Scheduler heartbeat can drift from actual job execution

**Severity:** Medium
**State:** Partially mitigated
**Impact:** Operations status can report a stale scheduler heartbeat even while jobs continue completing, weakening readiness evidence and making pause/restart diagnosis harder.
**Evidence:** After PR #10, `recent_sync`, `open_ticket_history_gaps`, and `open_ticket_time_entry_gaps` completed, but `scheduler_heartbeats.heartbeat_at` remained at the rebuild-time tick and operations status showed `scheduler.state=stale`.
**Existing controls:** The scheduler worker now records heartbeat at tick start, tick finish, and failure. Focused tests assert the worker heartbeat contract, and live runtime validation showed `scheduler.state=healthy` after restart with a fresh `heartbeat_at` and completed gap-job evidence.
**Next mitigation:** Add pause/resume actor/reason provenance and include heartbeat restart checks in Quality Streak certification.

### R8 — Historical backfill resource and API pressure

**Severity:** Medium
**State:** Partially mitigated
**Impact:** Large pulls may exceed Autotask thresholds, disk capacity, or CPU budgets.
**Existing controls:** Conservative disabled defaults, locks, threshold checks, disk checks, checkpoints, and batch settings. Estate TimeEntries/TicketHistory gap batches remain bounded by existing setting limits and now surface estimated catch-up run counts before operators trust coverage.
**Next mitigation:** Measured backfill plans, capacity budgets, recovery drills, and bounded scheduling.

### R9 — Cache leakage or staleness

**Severity:** Medium
**State:** Partially mitigated
**Impact:** Redis could reuse data across clients or after source/model/permission changes.
**Mitigation:** Scope/version-aware keys, short TTLs, explicit invalidation, outage fallback, and isolation tests before enabling answer caching. The active operations-status cache consumer now uses scoped cache keys; remaining and future cache consumers still require certification.

### R10 — Parallel agent merge conflict or inconsistent architecture

**Severity:** Medium
**State:** Controlled by contract
**Impact:** Agents may overlap files, duplicate work, or pass isolated tests while integrated behavior fails.
**Mitigation:** Coordinator ownership, isolated worktrees/branches, non-overlapping files, dependency-ordered integration, and independent verification.

### R11 — Memory promotion without sufficient provenance

**Severity:** Medium
**State:** Open
**Impact:** A weak or unsafe known-fix candidate could influence future retrieval.
**Mitigation:** Keep all candidates pending; implement source links, classification review, verifier, admin approval, versioning, supersession, and rollback.

### R12 — Roadmap/status drift

**Severity:** Medium
**State:** Mitigating
**Impact:** Written progress could disagree with code, tests, or deployment reality.
**Mitigation:** Canonical control files, evidence-linked receipts, CI, independent verification, and sanitized Second Brain projection. Current reconciliation target is canonical `main` `7e68107a82ea49938c74ad184972b45611815789` through PR #73; Second Brain PR #13 is open at head `b1bf8505ea7e1eb0ff0f623799abc746997f5582` with local knowledge validation passing.

### R16 — CI runner environment differences

**Severity:** Medium
**State:** Partially mitigated
**Impact:** The first GitHub-hosted CI run passed, but future runners may still differ in Docker Compose, Node, network, cache, or resource limits.
**Mitigation:** Keep CI credentials-free, bounded, and deterministic; treat future GitHub CI failures as blockers to completion claims until repaired.

### R17 — Host test tooling is incomplete

**Severity:** Low
**State:** Mitigated by containerized CI validator
**Impact:** Host `pytest` is not installed, so direct `cd apps/api && pytest` cannot run outside the container on this machine.
**Mitigation:** `scripts/validate-ci.sh` runs pytest inside the API image with the repository mounted; install host test tooling only if a future local workflow requires non-container pytest.

## Low and deferred risks

### R13 — Real-time event complexity

**Severity:** Low until Milestone 5
**Mitigation:** Build after authorization and cache/event infrastructure; require reconnect, replay, rate-limit, and outage tests.

### R14 — Prediction and routing bias

**Severity:** Deferred but material
**State:** Partially mitigated; evaluation caveat found.
**Impact:** Aggregate accuracy can look strong while the current signal misses delayed tickets, and lower thresholds can improve recall only by accepting substantial false positives. This could mislead technicians if presented as an automatic or trusted predictor.
**Evidence:** On canonical `main` `c688c6d622e60e866ee63302a1f577f498635741`, the local 100-ticket holdout for `/api/ticket-health/predictive-evaluation?limit=100&delayed_days_threshold=7` returned default statistical `accuracy=0.94`, `precision=null`, `recall=0.0`, and `f1=0.0`; the advisory best-F1 threshold `0.05` returned `accuracy=0.3`, `precision=0.068`, `recall=0.833`, and `f1=0.125`.
**Mitigation:** Keep predictive ranking and threshold-sweep output review-only. Do not auto-select the highest-F1 threshold and do not deploy threshold, model, routing, escalation, notification, assignment, or workflow changes from this evidence. Branch `agent/predictive-ranking-calibrated-score` exposes a review-only model version, calibrated delay probability, transparent adjustments, and rank contribution in Ticket Health without authorizing threshold/model/workflow changes. Branch `agent/predictive-calibration-policy` adds target/label semantics, Brier score, calibration bands, PR/ROC secondary metrics, threshold coverage/abstention, sanitized client/category concentration, a human-review threshold policy, and a read-only shadow-evaluation contract. Branch `agent/predictive-leakage-bias-review` adds temporal leakage review, model comparison, and sanitized stratified company/category bucket metrics. Branch `agent/predictive-source-lineage` marks current model input lineage and explicitly keeps current queue/priority/category fields uncertified for prediction. Branch `agent/m2-field-certification` adds scoped field-certification evidence and carries current Milestone 2 blockers into predictive source lineage; runtime evidence remains `partial_field_certification` with TicketHistory/status-duration/waiting blockers. Branch `agent/predictive-model-variants` compares additional read-only variants and confirms the default-threshold zero-recall problem remains across simple priority, global-prior, queue-only, priority-only, and queue+priority signals. Milestone 2 status-duration/waiting certification, three-run evaluation evidence, and production certification remain required before predictive claims are trusted.

### R16 — TicketHistory status-duration source limitation

**Severity:** Medium
**State:** Confirmed source limitation
**Impact:** Local TicketHistory may be present for tickets while still lacking parseable status-transition events. Treating those rows as exact status-duration evidence would overstate waiting/customer/vendor/technician duration accuracy.
**Evidence:** Branch `agent/status-transition-certification` adds scoped parser certification and local runtime evidence returned `parsed_status_transitions=0`, `timestamped_status_transitions=0`, and `source_limited=true` for the inspected TicketHistory sample. Branch `agent/status-transition-source-candidates` adds a scoped source-candidate report that classifies local TicketHistory, current status, proxy timestamps, and unprobed candidate Autotask status-history entities without running a live Autotask probe. Branch `agent/status-history-entity-probe` adds an Admin-only manual bounded read-only probe for candidate status-transition entities.
**Mitigation:** Keep status-duration and waiting-state analytics source-limited until parser-compatible status transitions are backfilled or another read-only Autotask source exposes timestamped status changes. Do not feed these fields into predictive models or certified ticket-health calculations until Milestone 2 source-lineage evidence improves. Any candidate status-history entity must pass the bounded read-only availability probe before a sync path is added.

### R15 — Future Autotask writeback

**Severity:** Prohibited future risk
**State:** Not authorized
**Mitigation:** No write implementation under the current roadmap. Any future capability requires explicit approval, kill switch, idempotency, read-after-write verification, compensation/rollback, negative tests, and a separate Quality Streak.

## Critical-blockage status

No critical blockage currently prevents documentation, CI, test, security-design, or other non-production work. High-risk production execution and protected actions remain approval-gated but do not block safe preparatory engineering. Second Brain PR #13 is open at head `b1bf8505ea7e1eb0ff0f623799abc746997f5582` with local validation passing; pending merge there does not block independent Autotask AI engineering.
