# Autotask AI Known Risks

**Updated:** 2026-07-21

## Critical and high risks

### R1 — Placeholder authentication

**Severity:** Critical for production  
**State:** Open  
**Impact:** Any nonempty credentials may be accepted by the current placeholder flow; role assignment is not trustworthy.  
**Mitigation:** Milestone 1 real authentication, secure sessions, disabled-user handling, throttling, and RBAC.  
**Approval gate:** Production authentication changes require security review and controlled deployment.

### R2 — Client/company isolation is not yet proven fail-closed

**Severity:** Critical  
**State:** Open  
**Impact:** Retrieval, analytics, citations, or future caches could expose one client’s information to an unauthorized user.  
**Mitigation:** Explicit authorization scope on every data path, negative tests, independent verification, and Quality Streak evidence.

### R3 — Independent answer verification and prompt-injection defense are incomplete

**Severity:** High  
**State:** Open  
**Impact:** Retrieved untrusted content could influence answers or unsupported claims could appear with insufficient evidence.  
**Mitigation:** Pre-context injection scanning, post-answer verification, fail-closed handling, and adversarial tests.

### R4 — Audit evidence is not fully durable and identity-linked

**Severity:** High  
**State:** Open  
**Impact:** Security and operational actions may not be reconstructable after restart.  
**Mitigation:** Database-backed immutable audit records with actor, scope, target, outcome, source references, and denied actions.

### R5 — Quality Streak evidence not yet established

**Severity:** High  
**State:** Partially mitigated  
**Impact:** Local and GitHub CI validation now exist for the governed CI branch, but three-run Quality Streak evidence and a fuller certification matrix are not yet established.
**Mitigation:** Merge the governed CI PR after review, then build certification matrix plus three-consecutive-clean-run receipts without overstating existing capability certification.

## Medium risks

### R6 — CPU-only model latency and quality

**Severity:** Medium  
**State:** Partially mitigated  
**Impact:** Slow or weak generation may reduce technician usefulness.  
**Existing controls:** Retrieval-first design, deterministic analytics, context limits, normal/deep-dive modes, timeouts, and evidence fallback.  
**Next mitigation:** Benchmarks, scoped Redis caching, verifier metrics, and model/provider configuration controls.

### R7 — Incomplete operational Autotask data

**Severity:** Medium  
**State:** Open  
**Impact:** Ticket-health, prediction, and routing calculations may be incomplete or misleading.  
**Mitigation:** Field inventory, resumable time-entry/status/SLA synchronization, freshness reporting, and explicit unavailable-field handling.

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

No critical blockage currently prevents documentation, CI, test, security-design, or other non-production work. High-risk production execution and protected actions remain approval-gated but do not block safe preparatory engineering.
