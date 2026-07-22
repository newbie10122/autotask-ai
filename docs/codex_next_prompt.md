# Next Codex Prompt

Use `docs/CODEX_HARNESS_PROMPT.md` as the governing harness prompt.

## Current canonical state

- Repository: `newbie10122/autotask-ai`
- Canonical `main`: `14a3784fa8b109495a7b2abc14b860e5113bb873`
- Latest merged PR: `newbie10122/autotask-ai#43`, `Reconcile PR42 control docs`
- Latest PR #43 CI: GitHub Actions run `29884920721`, workflow `CI`, job `Validate Autotask AI`, passed before merge
- Latest local governed runtime checks on 2026-07-22: `/ready` returned ready, operations status returned scheduler `healthy`, `global_pause=false`, and local counts `tickets=67726`, `time_entries=49636`, `ticket_history=29582`
- Current branch validation: `agent/predictive-calibration-policy` passed full governed validation with `119` API tests, `11` Playwright tests, and clean `git diff --check`; runtime predictive evaluation after local API rebuild returned Brier `0.056`, ROC AUC `0.613`, PR AUC `0.115`, coverage `1.0`, abstention rate `0.0`, largest sanitized company bucket share `0.67`, and largest sanitized category bucket share `0.99`
- Application auth remains opt-in: `APP_ROUTE_AUTH_REQUIRED=false` by default
- Autotask authority remains read-only; no Autotask write capability is approved

## Runtime evidence to preserve

- TimeEntries/TicketHistory automation is active through scheduled read-only jobs: recent sync includes TimeEntries, open-ticket gap jobs run every 15 minutes, and estate gap jobs run hourly.
- The latest read-only operations check showed recent scheduler-owned jobs completing successfully, including nightly pipeline, recent sync, open-ticket TimeEntries/TicketHistory gap jobs, document build, classification, and reclassification runs with zero reported failures in the inspected recent runs.
- Local synchronized ticket classification is complete for current tickets: `67726/67726`, `0` unclassified.
- Scheduler heartbeat/restart provenance is repaired on canonical `main`; Operations UI now exposes scheduler heartbeat, next due job, related-data movement, TimeEntries totals, and TicketHistory totals.
- Current predictive evaluation for `/api/ticket-health/predictive-evaluation?limit=100&delayed_days_threshold=7` returned holdout size `100`, training groups `32`, default statistical `accuracy=0.94`, `precision=null`, `recall=0.0`, and `f1=0.0`. Advisory best-F1 threshold `0.05` returned `accuracy=0.3`, `precision=0.068`, `recall=0.833`, and `f1=0.125`.

## Immediate run objective

Continue from a clean branch based on canonical `origin/main`.

1. Validate and merge branch `agent/predictive-calibration-policy` after GitHub CI passes.
2. Update the existing Second Brain projection PR with predictive calibration-policy evidence.
3. Continue predictive work with leakage review, model/simple-baseline comparison, and broader sanitized bias/concentration review.
4. Keep all predictive behavior review-only; do not auto-select thresholds or change routing, escalation, notification, assignment, status, priority, or workflow behavior.

## Milestone status

- Milestone 0 remains `partial`; CI and certification tracking exist, but no milestone is `verified_complete`.
- Milestone 1 remains active and release-blocking; local auth/RBAC/audit/scope/answer-safety foundations and local streak harnesses exist, but live production-auth deployment evidence remains open.
- Milestone 2 is `partial_foundation`; TimeEntries/TicketHistory automation exists and is visible, but historical coverage, source-lineage, field certification, and sync/recovery streak evidence remain incomplete.
- Milestone 7 is `partial_foundation`; review-only statistical ranking, UI, holdout evaluation, threshold sweep, and branch-level calibration/policy evidence exist, but the default signal currently misses delayed tickets in the local holdout and still requires leakage review, broader bias review, model comparison, and production certification.
- Do not mark any milestone `verified_complete` without the formal acceptance evidence in `docs/acceptance_criteria.md`.

## Next eligible safe slices

- Predictive leakage review, model/simple-baseline comparison, and broader sanitized bias/concentration review.
- Durable audit identity/scope linkage across remaining workflows.
- Milestone 2 field/source-lineage certification for status-duration, SLA, waiting state, TimeEntries, and TicketHistory.
- Deterministic Ticket Health completion using existing local TimeEntries/TicketHistory coverage.
- Production-auth deployment evidence only when explicitly approved for that protected action.

## Second Brain state

Existing projection branch: `agent/autotask-ai-governed-roadmap-projection`.
Existing PR: `newbie10122/helix-second-brain#6`.
Latest pushed projection head `8eb7ab53699d6ec0a66a45415c9dc66398981443` records PR #43, canonical commit `14a3784fa8b109495a7b2abc14b860e5113bb873`, control-doc reconciliation, predictive threshold evidence, prior predictive ranking/evaluation/UI work, operations automation visibility, Ask Assistant ticket-detail links, prior Milestone 1 certification slices, restored scheduler automation, heartbeat repair, runtime counts, classification completion, and remaining gaps. Local validation passed with `python3 tools/validate_knowledge.py`.

Update the existing projection after the next material Autotask AI slice. Do not create duplicate projection PRs, and do not mark Second Brain state `merged` until PR #6 is actually merged.
