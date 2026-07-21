# Autotask AI Known Risks

**Updated:** 2026-07-21

## Critical and high risks

### R1 — Authentication/RBAC foundation is not production-enforced end to end

**Severity:** Critical for production
**State:** Partially mitigated
**Impact:** Branch `agent/m1-auth-rbac-foundation` replaces placeholder token behavior with hashed passwords, signed expiring tokens, optional route enforcement, and admin denial tests. Branch `agent/m1-route-authority-audit-matrix` adds admin gates and a route inventory contract for sensitive routes, but production defaults still keep app-route auth off behind Nginx Basic Auth and real-browser UI evidence is not complete.
**Mitigation:** Finish success-path audit actor/scope linkage, bootstrap/admin-user operations, real-browser UI RBAC/accessibility evidence, and three-run security evidence before production enforcement.
**Approval gate:** Production authentication changes require security review and controlled deployment.

### R2 — Client/company isolation is not yet proven fail-closed

**Severity:** Critical
**State:** Partially mitigated
**Impact:** Retrieval, analytics, citations, or future caches could expose one client’s information to an unauthorized user.
**Existing controls:** Branch `agent/m1-company-scope-foundation` adds user-company scope storage, fail-closed assistant/analytics route scope checks, and scoped retrieval/recurring-analytics filters when app route auth is enabled.
**Next mitigation:** Carry effective scope through future cache/export paths, verifier checks, ticket-health/customer-success/routing APIs, and broader cross-client negative tests.

### R3 — Independent answer verification and prompt-injection defense are incomplete

**Severity:** High
**State:** Partially mitigated
**Impact:** Retrieved untrusted content could influence answers or unsupported claims could appear with insufficient evidence.
**Existing controls:** Branch `agent/m1-auth-rbac-foundation` adds deterministic prompt-injection detection, unsafe source filtering before model prompt assembly, and citation-subset verification for generated answers.
**Next mitigation:** Add scope-aware verifier inputs, unsupported-claim checks, denial audit records, independent verifier receipts, and three-run adversarial evidence.

### R4 — Audit evidence is not fully durable and identity-linked

**Severity:** High
**State:** Partially mitigated
**Impact:** Security and operational actions may not be reconstructable after restart unless every material path writes identity-linked audit records.
**Existing controls:** Branch `agent/m1-durable-audit-scope-foundation` adds durable `audit_log` persistence, outcome/scope fields, and authorization-denial audit events with no-DB fallback. Branch `agent/m1-success-audit-scope-linkage` adds centralized success records for material admin actions, recurring analytics, assistant ask, and feedback.
**Next mitigation:** Link audit records across remaining workflows and add verifier-failure audit records before treating audit coverage as complete.

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
**Existing controls:** PR `newbie10122/autotask-ai#10` restored read-only TimeEntries and TicketHistory automation, including recent-sync TimeEntries, open-ticket gap repair, estate-wide gap sweeps, and operations coverage reporting.
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
**Existing controls:** Conservative disabled defaults, locks, threshold checks, disk checks, checkpoints, and batch settings.
**Next mitigation:** Measured backfill plans, capacity budgets, recovery drills, and bounded scheduling.

### R9 — Cache leakage or staleness

**Severity:** Medium
**State:** Future risk
**Impact:** Redis could reuse data across clients or after source/model/permission changes.
**Mitigation:** Scope/version-aware keys, short TTLs, explicit invalidation, outage fallback, and isolation tests before enabling answer caching.

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
**Mitigation:** Canonical control files, evidence-linked receipts, CI, independent verification, and sanitized Second Brain projection.

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
**Mitigation:** Explainable baselines, holdout evaluation, calibration, reason codes, abstention, fairness/concentration review, and recommendation-only authority.

### R15 — Future Autotask writeback

**Severity:** Prohibited future risk
**State:** Not authorized
**Mitigation:** No write implementation under the current roadmap. Any future capability requires explicit approval, kill switch, idempotency, read-after-write verification, compensation/rollback, negative tests, and a separate Quality Streak.

## Critical-blockage status

No critical blockage currently prevents documentation, CI, test, security-design, or other non-production work. High-risk production execution and protected actions remain approval-gated but do not block safe preparatory engineering. Second Brain PR #6 has an updated Autotask AI projection with local validation passing; remote validation status must remain tracked there but does not block independent Autotask AI engineering.
