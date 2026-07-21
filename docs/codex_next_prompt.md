# Next Codex Prompt

Use `docs/CODEX_HARNESS_PROMPT.md` as the governing harness prompt.

## Current canonical state

- Repository: `newbie10122/autotask-ai`
- Canonical `main`: `7ca491b82d1ac1085efbbede3d3ccc1a9fe35057`
- Latest merged PR: `newbie10122/autotask-ai#10`, `Restore related-data scheduler automation`
- Latest PR #10 CI: GitHub Actions run `29857699615`, workflow `CI`, job `Validate Autotask AI`, passed for head `07fe5c98361e933254a537e8bc24b0b0f49bab1a`
- Latest local governed validation: `./scripts/validate-ci.sh` passed with full pytest `74 passed`
- Application auth remains opt-in: `APP_ROUTE_AUTH_REQUIRED=false` by default
- Autotask authority remains read-only; no Autotask write capability is approved

## Runtime evidence to preserve

- Local API and scheduler were rebuilt from canonical source after PR #10.
- `/api/operations/status` returned `global_pause=false` and no Autotask threshold error.
- Local synchronized ticket classification is complete for current tickets: `67726/67726`, `0` unclassified.
- TimeEntries/TicketHistory automation is active: recent sync includes TimeEntries, open-ticket gap jobs run every 15 minutes, and estate gap jobs run hourly.
- Current observed counts: `time_entries=46899`, `ticket_history=28207`.
- Open-ticket labor coverage: `90/146` with TimeEntries, `56` checked-empty, `0` unchecked.
- Open-ticket TicketHistory coverage: `146/146`.
- Scheduler jobs continued to complete after pause was cleared, but `scheduler_heartbeats` stopped updating after rebuild and operations status reported heartbeat `state=stale`; repair heartbeat/restart provenance before using it as readiness evidence.

## Immediate run objective

Continue from a clean branch based on canonical `origin/main`.

1. Finish reconciling stale control documents against PR #10 and current runtime evidence.
2. Repair scheduler heartbeat/restart provenance so heartbeat freshness agrees with completed scheduled ticks.
3. Validate scheduler heartbeat, pause/resume state, bounded job cadence, and clear skipped/blocked/failed/idle distinctions.
4. Continue Milestone 1 closeout with route authority matrix, comprehensive API denial tests, durable audit actor/scope coverage, company-isolation negatives, verifier breadth, and UI browser/RBAC evidence.

## Milestone status

- Milestone 0 remains `partial`; CI is merged and passing, but capability certification matrix and Quality Streak evidence are incomplete.
- Milestone 1 remains active and release-blocking.
- Milestone 2 is `partial_foundation`; TimeEntries/TicketHistory automation exists, but historical coverage and field certification are incomplete.
- Do not mark any milestone `verified_complete` without the formal acceptance evidence in `docs/acceptance_criteria.md`.

## Next eligible safe slices

- Scheduler heartbeat/restart provenance and pause audit clarity.
- Route authority matrix plus API auth/RBAC denial coverage for every route.
- Durable audit identity/scope linkage across assistant, feedback, analytics, operations, sync, memory, denied requests, and verifier failures.
- Company-scope contracts for ticket health, customer success, routing, realtime, cache keys, and future exports.
- Deterministic answer verifier expansion for unsupported claims, source sufficiency, guidance labeling, weak evidence, secrets, injection, malformed output, timeout/failure, and fallback behavior.
- Real-browser UI auth/RBAC and accessibility checks.

## Second Brain state

Existing projection branch: `agent/autotask-ai-governed-roadmap-projection`.
Existing PR: `newbie10122/helix-second-brain#6`.
Latest pushed projection head `a8a9981` records PR #10, canonical commit, restored scheduler automation, runtime counts, classification completion, and remaining gaps. Local validation passed with `python3 tools/validate_knowledge.py`.

Update the existing projection after the next material Autotask AI slice. Do not create duplicate projection PRs, and do not mark Second Brain state `merged` until PR #6 is actually merged.
