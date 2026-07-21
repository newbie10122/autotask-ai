# Next Codex Prompt

Use `docs/CODEX_HARNESS_PROMPT.md` as the governing harness prompt.

## Current canonical state

- Repository: `newbie10122/autotask-ai`
- Canonical `main`: `5919c397aa9c76087cea51e9b99b230c15cdbb43`
- Latest merged PR: `newbie10122/autotask-ai#24`, `Add app user bootstrap tooling`
- Latest PR #24 CI: GitHub Actions run `29865632284`, workflow `CI`, job `Validate Autotask AI`, passed before merge
- Latest local governed validation: `./scripts/validate-ci.sh && git diff --check` passed with production-auth preflight, full pytest `99 passed`, and Playwright browser smoke `6 passed` on branch `agent/m1-adversarial-verifier-breadth`.
- Current working branch objective: `agent/m1-adversarial-verifier-breadth` broadens conversational answer verifier checks for metadata ticket IDs, cross-ticket evidence mismatch, and weak no-evidence fallback language.
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
- Scheduler heartbeat/restart provenance is repaired on canonical `main`: runtime evidence after PR #11 showed `scheduler.state=healthy` with fresh heartbeat and completed gap-job evidence.

## Immediate run objective

Continue from a clean branch based on canonical `origin/main`.

1. Merge branch `agent/m1-adversarial-verifier-breadth` after GitHub CI passes.
2. Update the existing Second Brain projection PR with the adversarial conversational verifier evidence.
3. Continue Milestone 1 closeout with live production-auth deployment evidence, broader adversarial verifier evidence, remaining scope/cache certification, and capability Quality Streak receipts.

## Milestone status

- Milestone 0 remains `partial`; CI is merged and passing, but capability certification matrix and Quality Streak evidence are incomplete.
- Milestone 1 remains active and release-blocking.
- Milestone 2 is `partial_foundation`; TimeEntries/TicketHistory automation exists, but historical coverage and field certification are incomplete.
- Do not mark any milestone `verified_complete` without the formal acceptance evidence in `docs/acceptance_criteria.md`.

## Next eligible safe slices

- Durable audit identity/scope linkage across assistant, feedback, analytics, operations, sync, memory, denied requests, and verifier failures.
- Company-scope contracts for ticket health, customer success, routing, realtime, cache keys, and future exports.
- Deterministic answer verifier expansion for unsupported claims, source sufficiency, guidance labeling, weak evidence, secrets, injection, malformed output, timeout/failure, and fallback behavior.
- Source-sufficiency certification for deterministic and generated answer paths.
- Live production-auth deployment evidence.
- Remaining cache-consumer certification.

## Second Brain state

Existing projection branch: `agent/autotask-ai-governed-roadmap-projection`.
Existing PR: `newbie10122/helix-second-brain#6`.
Latest pushed projection head `f1a24d7` records PR #24, canonical commit, bootstrap app-user tooling, production-auth preflight validation, active scoped-cache consumer validation, source-sufficiency verifier checks, keyboard/focus browser smoke, browser accessibility smoke, capability certification matrix, validation-harness streak tracking, browser UI RBAC, unsupported-claim verifier breadth, cache/export contracts, verifier-failure audit, success audit actor/scope linkage, route authority/static UI contracts, restored scheduler automation, heartbeat repair, runtime counts, classification completion, and remaining gaps. Local validation passed with `python3 tools/validate_knowledge.py`.

Update the existing projection after the next material Autotask AI slice. Do not create duplicate projection PRs, and do not mark Second Brain state `merged` until PR #6 is actually merged.
