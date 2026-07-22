# Next Codex Prompt

Use `docs/CODEX_HARNESS_PROMPT.md` as the governing harness prompt.

## Current canonical state

- Repository: `newbie10122/autotask-ai`
- Canonical `main`: `8571084b4744f482960937531611004a0dc6d67e`
- Latest merged PR: `newbie10122/autotask-ai#53`, `Add bounded status history entity probe`
- Latest PR #53 CI: GitHub Actions run `29889467648`, workflow `CI`, job `Validate Autotask AI`, passed before merge
- Latest local governed runtime checks on 2026-07-22: `/ready` returned ready, operations status returned scheduler `healthy`, `global_pause=false`, and local counts `tickets=67726`, `time_entries=49950`, `ticket_history=29760`
- Current branch validation: `agent/predictive-calibration-policy` passed full governed validation with `119` API tests, `11` Playwright tests, and clean `git diff --check`; runtime predictive evaluation after local API rebuild returned Brier `0.056`, ROC AUC `0.613`, PR AUC `0.115`, coverage `1.0`, abstention rate `0.0`, largest sanitized company bucket share `0.67`, and largest sanitized category bucket share `0.99`
- Current active branch validation: `agent/predictive-leakage-bias-review` passed full governed validation with `122` API tests, `11` Playwright tests, and clean `git diff --check`; runtime predictive evaluation after local API rebuild returned `statistical_signal_not_better_on_f1_or_recall`, F1/recall deltas `0`, leakage review with `training_rows_after_or_during_holdout_included=0`, sanitized top company bucket share `0.67`, and sanitized top category bucket share `0.99`
- Current active branch validation: `agent/predictive-source-lineage` passed full governed validation with `123` API tests, `11` Playwright tests, and clean `git diff --check`; runtime predictive evaluation after local API rebuild returned `source_lineage.certification_state=partial_source_lineage`, with queue, priority, and category-derived fields marked not fully certified for prediction
- Current active branch validation: `agent/m2-field-certification` passed focused validation for field-certification/predictive-source-lineage tests with `2 passed`, scoped route authority/scope propagation tests with `2 passed`, runtime local Postgres report execution, and full governed validation with `124` API tests, `11` Playwright browser tests, and clean `git diff --check`. Runtime field certification returned `partial_field_certification`, summary `certified=2`, `partial=1`, `source_limited=2`, and blockers `ticket_status_history`, `status_duration`, and `waiting_states`.
- Current active branch validation: `agent/predictive-model-variants` has focused variant/model-comparison tests passing with `3 passed`, runtime local Postgres evaluation passing for 50-ticket and 100-ticket samples, and full governed validation passing with `125` API tests, `11` Playwright browser tests, and clean `git diff --check`. The 100-ticket holdout showed all variants retain default recall `0.0`; queue+priority has ROC AUC `0.613` and PR AUC `0.115`.
- Current active branch validation: `agent/status-transition-certification` has focused field-certification/parser tests passing with `2 passed`, runtime local Postgres field-certification smoke passing, and full governed validation passing with `126` API tests, `11` Playwright browser tests, and clean `git diff --check`. Runtime parser evidence returned `parsed_status_transitions=0`, `timestamped_status_transitions=0`, and `source_limited=true`.
- Current active branch validation: `agent/operations-field-certification-ui` has focused Playwright Operations validation passing with `1 passed`, static web JavaScript syntax validation passing, and full governed validation passing with `126` API tests, `11` Playwright browser tests, and clean `git diff --check`.
- Current active branch validation: `agent/status-transition-source-candidates` has focused field-certification/source-candidate/parser tests passing with `3 passed`, scoped route authority/scope propagation tests passing with `2 passed`, and full governed validation passing with `127` API tests plus `11` Playwright browser tests. The branch adds scoped `/api/ticket-health/status-transition-sources` and embeds the same read-only source-candidate report in field certification without running a live Autotask probe or authorizing sync/write/model workflow changes.
- Current active branch validation: `agent/status-history-entity-probe` has focused bounded probe/client and company-sync compatibility tests passing with `3 passed`, and focused admin route matrix, route authority, and success-audit tests passing with `3 passed`. The branch adds Admin-only manual `POST /api/autotask/probe/status-transition-sources` using `MaxRecords=1` per candidate entity with no scheduling, no Autotask writes, and no automatic sync-path/model/workflow authorization.
- Current active branch validation: `agent/status-probe-error-isolation` has focused bounded probe/error-isolation tests passing with `2 passed`. The branch fixes the manual status-history probe so repeated unavailable entities do not trip the read-only client's consecutive-error breaker across candidates.
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

1. Validate and merge `agent/status-probe-error-isolation` if full governed validation and exact-head CI pass.
2. Rerun the bounded read-only status-transition probe. If an entity is available, design a review-only sync candidate; otherwise return to Milestone 1 audit/scope closeout.
3. Update the existing Second Brain projection PR after this material slice merges.

## Milestone status

- Milestone 0 remains `partial`; CI and certification tracking exist, but no milestone is `verified_complete`.
- Milestone 1 remains active and release-blocking; local auth/RBAC/audit/scope/answer-safety foundations and local streak harnesses exist, but live production-auth deployment evidence remains open.
- Milestone 2 is `partial_foundation`; TimeEntries/TicketHistory automation exists and is visible, but historical coverage, source-lineage, field certification, and sync/recovery streak evidence remain incomplete.
- Milestone 7 is `partial_foundation`; review-only statistical ranking, UI, holdout evaluation, threshold sweep, calibration/policy evidence, leakage/model/bias evidence, and branch-level source-lineage evidence exist, but the default signal currently misses delayed tickets in the local holdout and still requires broader model evaluation, Milestone 2 field certification, and production certification.
- Do not mark any milestone `verified_complete` without the formal acceptance evidence in `docs/acceptance_criteria.md`.

## Next eligible safe slices

- Predictive broader model evaluation and Milestone 2 field certification.
- Durable audit identity/scope linkage across remaining workflows.
- Milestone 2 field/source-lineage certification for status-duration, SLA, waiting state, TimeEntries, and TicketHistory.
- Deterministic Ticket Health completion using existing local TimeEntries/TicketHistory coverage.
- Production-auth deployment evidence only when explicitly approved for that protected action.

## Second Brain state

Existing projection branch: `agent/autotask-ai-governed-roadmap-projection`.
Existing PR: `newbie10122/helix-second-brain#6`.
Latest pushed projection head `f88d14aefeb8b0743dff663b6f1574a07b2feffa` records PR #47, canonical commit `99937d5113b0cc78270bf9a718f1cb4692ba2b28`, predictive source-lineage evidence, predictive leakage/model/bias evidence, predictive calibration-policy evidence, PR #43 control-doc reconciliation, predictive threshold evidence, prior predictive ranking/evaluation/UI work, operations automation visibility, Ask Assistant ticket-detail links, prior Milestone 1 certification slices, restored scheduler automation, heartbeat repair, runtime counts, classification completion, and remaining gaps. Local validation passed with `python3 tools/validate_knowledge.py`.

Update the existing projection after the next material Autotask AI slice. Do not create duplicate projection PRs, and do not mark Second Brain state `merged` until PR #6 is actually merged.
