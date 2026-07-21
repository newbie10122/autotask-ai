# Capability Certification Matrix

**Updated:** 2026-07-21  
**Canonical main:** `82d30d34032a42ff505de9ef6c88500c9a39b526`  
**Autotask write-back:** none

This matrix is a certification tracker, not a production-readiness claim. A capability may only move to `verified_complete` when its acceptance criteria, negative tests, rollback/recovery evidence, and applicable three-run Quality Streak are present.

| Capability | State | Current evidence | Quality Streak | Remaining certification work |
|---|---|---|---|---|
| CI validation harness | partial | Redacted Compose, migration ordering, API build, compile, full pytest, static JS, and Playwright browser UI RBAC smoke are wired into `./scripts/validate-ci.sh`; PR #17 remote CI passed. | 3/3 validation-harness runs recorded in `docs/CI_VALIDATION.md`; not a production capability streak. | Keep receipts current after dependency or validation changes; capability-specific Quality Streaks remain separate. |
| Authentication and route RBAC | partial | PRs #4, #12, and #17 cover signed tokens, admin route gates, route matrix, denial audit, and browser RBAC smoke. | Not established. | Production auth enablement remains off by default; bootstrap/admin-user operations and broader accessibility evidence remain open. |
| Durable audit logging | partial | PRs #5, #13, and #14 cover durable audit storage, authorization-denial events, success actor/scope events, and verifier-failure audit. | Not established. | Broader workflow audit coverage and certification receipts remain open. |
| Company/client isolation | partial | PRs #6, #7, #8, #12, and #15 cover company scope tables, scoped assistant/analytics retrieval, scope snapshots, verifier scope rejection, route matrix, and scoped cache/export contracts. | Not established. | Broader ticket-health/customer-success/routing scope certification and active scoped cache consumer validation remain open. |
| Answer safety and verification | partial | PRs #4, #8, #14, and #16 cover prompt-injection/secret filtering, citation checks, out-of-scope source rejection, verifier-failure audit, preserved fail-closed reasons, and first unsupported resolution-claim checks. | Not established. | Broader source-sufficiency checks, deterministic-path receipts, and adversarial three-run evidence remain open. |
| Read-only TimeEntries/TicketHistory sync | partial_foundation | PR #10 restored recent TimeEntries sync, open-ticket gap jobs, estate-wide sweeps, operations coverage, and scheduler automation; PR #11 repaired scheduler heartbeat freshness. | Not established. | Historical estate catch-up, SLA/status-duration source-lineage certification, restart/recovery receipts, and field completeness evidence remain open. |
| Browser UI RBAC | partial | PR #17 adds Playwright Chromium smoke tests for anonymous, Admin, and ReadOnly UI role states. | Not established. | Broader accessibility checks, keyboard/focus evidence, and production-auth deployment evidence remain open. |

## Current Production Certification Summary

- No milestone is `verified_complete`.
- No Autotask write capability is implemented or approved.
- The validation harness is stronger and has three clean browser-enabled evidence points, but production capability Quality Streaks remain incomplete.
- Next work should target broader accessibility evidence, source-sufficiency certification, and capability-specific Quality Streaks.
