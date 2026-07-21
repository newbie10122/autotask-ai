# Capability Certification Matrix

**Updated:** 2026-07-21  
**Canonical main:** `2b5485c00dcb940650b3076d44ccbfb8a7d9381d`
**Autotask write-back:** none

This matrix is a certification tracker, not a production-readiness claim. A capability may only move to `verified_complete` when its acceptance criteria, negative tests, rollback/recovery evidence, and applicable three-run Quality Streak are present.

| Capability | State | Current evidence | Quality Streak | Remaining certification work |
|---|---|---|---|---|
| CI validation harness | partial | Redacted Compose, production-auth preflight, migration ordering, API build, compile, full pytest, static JS, Playwright browser UI RBAC smoke, first axe accessibility smoke, and keyboard/focus smoke are wired into `./scripts/validate-ci.sh`; PR #27 remote CI passed before this branch. | 3/3 validation-harness runs recorded in `docs/CI_VALIDATION.md`; not a production capability streak. | Keep receipts current after dependency or validation changes; capability-specific Quality Streaks remain separate. |
| Authentication and route RBAC | partial | PRs #4, #12, #17, #19, #20, PR #23, and branch `agent/m1-bootstrap-admin-user` cover signed tokens, admin route gates, route matrix, denial audit, browser RBAC smoke, accessibility smoke, keyboard/focus smoke, deploy-time auth-boundary preflight, and local hashed app-user bootstrap. | Not established. | Live production auth enforcement, deployment receipts, and broader security Quality Streak evidence remain open. |
| Durable audit logging | partial | PRs #5, #13, and #14 cover durable audit storage, authorization-denial events, success actor/scope events, and verifier-failure audit. | Not established. | Broader workflow audit coverage and certification receipts remain open. |
| Company/client isolation | partial | PRs #6, #7, #8, #12, and #15 plus branches `agent/m1-active-scoped-cache-consumer`, `agent/m1-summary-cache-scope-contracts`, `agent/m1-scope-certification-ticket-health-routing`, and `agent/m1-realtime-scope-certification` cover company scope tables, scoped assistant/analytics retrieval, scope snapshots, verifier scope rejection, route matrix, scoped cache/export contracts, active operations-status scoped cache, ticket-health/customer-success summary scoped cache keys, local ticket-health/customer-success/routing company-scope filters, and scoped realtime ticket-history events. | Not established. | Production-auth deployment evidence, first-class route exposure decisions, and broader capability Quality Streak evidence remain open. |
| Answer safety and verification | partial | PRs #4, #8, #14, #16, #21, #25, #26, and branch `agent/m1-answer-safety-quality-streak` cover prompt-injection/secret filtering, citation checks, out-of-scope source rejection, verifier-failure audit, preserved fail-closed reasons, unsupported resolution-claim checks, non-resolution source sufficiency, metadata ticket IDs, cross-ticket mismatch rejection, weak no-evidence fallback language, generated-answer verifier paths, redaction preserving required answer sections, and a repeatable local answer-safety streak harness. | 3/3 local answer-safety streak passed on branch `agent/m1-answer-safety-quality-streak`; production capability certification remains partial. | Production/deployment context and broader capability receipts remain open. |
| Read-only TimeEntries/TicketHistory sync | partial_foundation | PR #10 restored recent TimeEntries sync, open-ticket gap jobs, estate-wide sweeps, operations coverage, and scheduler automation; PR #11 repaired scheduler heartbeat freshness. | Not established. | Historical estate catch-up, SLA/status-duration source-lineage certification, restart/recovery receipts, and field completeness evidence remain open. |
| Browser UI RBAC/accessibility | partial | PR #17 adds Playwright Chromium smoke tests for anonymous, Admin, and ReadOnly UI role states. PR #19 adds shared browser helpers, axe serious/critical checks, login accessible-name checks, and a visible Ask mode label. PR #20 adds explicit focus-visible styling and keyboard traversal evidence. | Not established. | Production-auth deployment evidence and broader responsive/reduced-motion evidence remain open. |

## Current Production Certification Summary

- No milestone is `verified_complete`.
- No Autotask write capability is implemented or approved.
- The validation harness is stronger and has three clean browser-enabled evidence points; answer-safety has a local 3/3 streak harness, but production capability certification remains incomplete.
- Next work should target live production-auth deployment evidence, first-class route exposure decisions for scoped local capabilities, and capability-specific Quality Streaks.
