# Next Codex Prompt

Use `docs/CODEX_HARNESS_PROMPT.md` as the governing harness prompt.

## Current canonical state

- Repository: `newbie10122/autotask-ai`
- Canonical `main`: `0e2f122db69d6ce367e82f792de4ff5c6ad97fe1`
- Latest merged PR: `newbie10122/autotask-ai#40`, `Show predictive ticket review in UI`
- Latest PR #40 CI: GitHub Actions run `29881507179`, workflow `CI`, passed before merge
- Latest local governed validation: focused container tests passed with `3 passed` on branch `agent/predictive-evaluation-baseline`; run full `./scripts/validate-ci.sh && git diff --check` before opening the PR.
- Current working branch objective: `agent/predictive-evaluation-baseline` adds a read-only holdout evaluation report comparing a simple priority baseline with the Bayesian queue/priority delay signal.
- Application auth remains opt-in: `APP_ROUTE_AUTH_REQUIRED=false` by default
- Autotask authority remains read-only; no Autotask write capability is approved

## Runtime evidence to preserve

- Local API and scheduler were rebuilt from canonical source after PR #10.
- `/api/operations/status` returned `global_pause=false` and no Autotask threshold error.
- Local synchronized ticket classification is complete for current tickets: `67726/67726`, `0` unclassified.
- TimeEntries/TicketHistory automation is active: recent sync includes TimeEntries, open-ticket gap jobs run every 15 minutes, and estate gap jobs run hourly.
- Current observed counts from read-only local operations checks after PR #38 local rebuild on 2026-07-22: `tickets=67726`, `ticket_notes=675531`, `time_entries=49147`, `ticket_history=29341`.
- Recent related-data movement included successful `open_ticket_history_gaps`, `ticket_history_gaps`, and `ticket_time_entry_gaps` runs with zero failures.
- The Operations UI now shows this evidence without requiring raw JSON inspection.
- Scheduler heartbeat/restart provenance is repaired on canonical `main`: runtime evidence after PR #11 showed `scheduler.state=healthy` with fresh heartbeat and completed gap-job evidence.

## Immediate run objective

Continue from a clean branch based on canonical `origin/main`.

1. Finish validation and merge branch `agent/predictive-evaluation-baseline` after GitHub CI passes.
2. Update the existing Second Brain projection PR with predictive evaluation baseline evidence.
3. Continue Milestone 1 closeout, Milestone 2 certification, and Milestone 7 evaluation work: live production-auth evidence where approved, bounded related-data catch-up certification, status-duration/SLA source-lineage work, predictive holdout baselines, bias/concentration review, and remaining capability Quality Streak receipts.

## Milestone status

- Milestone 0 remains `partial`; CI is merged and passing, but capability certification matrix and Quality Streak evidence are incomplete.
- Milestone 1 remains active and release-blocking.
- Milestone 2 is `partial_foundation`; TimeEntries/TicketHistory automation exists, but historical coverage and field certification are incomplete.
- Milestone 7 is `partial_foundation` on the current branch only; review-only statistical ranking exists but evaluation/bias/certification evidence is incomplete.
- Do not mark any milestone `verified_complete` without the formal acceptance evidence in `docs/acceptance_criteria.md`.

## Next eligible safe slices

- Durable audit identity/scope linkage across assistant, feedback, analytics, operations, sync, memory, denied requests, and verifier failures.
- Company-scope contracts for ticket health, customer success, routing, realtime, cache keys, and future exports.
- Deterministic answer verifier expansion for unsupported claims, source sufficiency, guidance labeling, weak evidence, secrets, injection, malformed output, timeout/failure, and fallback behavior.
- Source-sufficiency certification for deterministic and generated answer paths.
- Live production-auth deployment evidence.
- Remaining cache-consumer certification.
- Predictive ranking holdout baseline, leakage controls, and bias/concentration review.

## Second Brain state

Existing projection branch: `agent/autotask-ai-governed-roadmap-projection`.
Existing PR: `newbie10122/helix-second-brain#6`.
Latest pushed projection head `73a5576` records PR #38, canonical commit, Operations automation visibility, Ask Assistant status clarity, ticket-detail modal links, answer-body ticket links, prior Milestone 1 certification slices, restored scheduler automation, heartbeat repair, runtime counts, classification completion, and remaining gaps. Local validation passed with `python3 tools/validate_knowledge.py`.

Update the existing projection after the next material Autotask AI slice. Do not create duplicate projection PRs, and do not mark Second Brain state `merged` until PR #6 is actually merged.
