# Next Codex Prompt

Use `docs/CODEX_HARNESS_PROMPT.md` as the governing harness prompt.

## Current canonical state

- Repository: `newbie10122/autotask-ai`
- Canonical `main`: `c688c6d622e60e866ee63302a1f577f498635741`
- Latest merged PR: `newbie10122/autotask-ai#42`, `Add predictive threshold sweep`
- Latest PR #42 CI: GitHub Actions run `29882172665`, workflow `CI`, job `Validate Autotask AI`, passed before merge
- Latest local governed runtime checks on 2026-07-22: `/ready` returned ready, operations status returned scheduler `healthy`, `global_pause=false`, and local counts `tickets=67726`, `time_entries=49636`, `ticket_history=29582`
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

1. Reconcile any stale control documents before selecting new work.
2. Build the next read-only predictive evaluation slice:
   - define prediction target and label semantics;
   - add calibration bands/deciles and Brier score;
   - add PR/ROC secondary evidence where practical;
   - report confusion at selected thresholds and coverage/abstention;
   - add sanitized client/category concentration analysis;
   - add a human-review threshold policy artifact;
   - add local bounded shadow evaluation that never writes to Autotask, sends notifications, or changes ranking/routing/workflow behavior.
3. Validate with focused tests plus the broadest safe affected harness.
4. Open a PR, watch exact-head CI, merge only after CI passes, update local main, then update the existing Second Brain projection PR.

## Milestone status

- Milestone 0 remains `partial`; CI and certification tracking exist, but no milestone is `verified_complete`.
- Milestone 1 remains active and release-blocking; local auth/RBAC/audit/scope/answer-safety foundations and local streak harnesses exist, but live production-auth deployment evidence remains open.
- Milestone 2 is `partial_foundation`; TimeEntries/TicketHistory automation exists and is visible, but historical coverage, source-lineage, field certification, and sync/recovery streak evidence remain incomplete.
- Milestone 7 is `partial_foundation`; review-only statistical ranking, UI, holdout evaluation, and threshold sweep exist, but the default signal currently misses delayed tickets in the local holdout and requires calibration, leakage, concentration, human-review policy, shadow evaluation, and production certification.
- Do not mark any milestone `verified_complete` without the formal acceptance evidence in `docs/acceptance_criteria.md`.

## Next eligible safe slices

- Predictive target/label semantics, calibration, concentration, threshold policy, and shadow evaluation.
- Durable audit identity/scope linkage across remaining workflows.
- Milestone 2 field/source-lineage certification for status-duration, SLA, waiting state, TimeEntries, and TicketHistory.
- Deterministic Ticket Health completion using existing local TimeEntries/TicketHistory coverage.
- Production-auth deployment evidence only when explicitly approved for that protected action.

## Second Brain state

Existing projection branch: `agent/autotask-ai-governed-roadmap-projection`.
Existing PR: `newbie10122/helix-second-brain#6`.
Latest pushed projection head `8a7919e89b5f171a84d3be3913b4c54a971e6925` records PR #42, canonical commit `c688c6d622e60e866ee63302a1f577f498635741`, predictive threshold evidence, prior predictive ranking/evaluation/UI work, operations automation visibility, Ask Assistant ticket-detail links, prior Milestone 1 certification slices, restored scheduler automation, heartbeat repair, runtime counts, classification completion, and remaining gaps. Local validation passed with `python3 tools/validate_knowledge.py`.

Update the existing projection after the next material Autotask AI slice. Do not create duplicate projection PRs, and do not mark Second Brain state `merged` until PR #6 is actually merged.
