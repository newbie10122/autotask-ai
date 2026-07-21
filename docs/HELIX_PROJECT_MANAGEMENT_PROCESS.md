# Helix Project Management Process

## Purpose

Helix, lead agents, Codex, and delegated agents must manage Autotask AI toward 99% verified roadmap completion with minimal intervention from John.

This process authorizes bounded autonomous engineering only within `AGENTS.md`, `AGENTS.override.md`, repository permissions, security controls, and explicit read-only Autotask authority. It does not authorize production execution, customer-data expansion, secrets access, irreversible changes, or Autotask writes without the approvals required by `AGENTS.md`.

## Standard command

John should be able to say:

```text
Manage Autotask AI to 99% verified roadmap completion.
```

Helix must then discover current repository truth, reconcile roadmap and status, create a dependency-aware execution queue, delegate independent work in parallel when safe, validate integration, update project evidence, and continue until the target is verified or a critical blockage prevents all further safe progress.

## Canonical control files

- `AGENTS.md`
- `AGENTS.override.md`
- `docs/PRODUCT_ROADMAP.md`
- `docs/implementation_status.md`
- `docs/acceptance_criteria.md`
- `docs/known_risks.md`
- `docs/codex_next_prompt.md`

Project-local code, tests, commits, and receipts are authoritative. Status prose may not overrule failing or missing evidence.

## Required workflow

1. Inspect the repository, current branch, open pull requests, recent commits, roadmap, status, acceptance criteria, risks, tests, deployment docs, and Second Brain state.
2. Compare actual implementation and validation evidence against the roadmap.
3. Reach at least 95% confidence for the next milestone or record conservative assumptions that permit reversible work.
4. Build a dependency graph and mark slices `eligible`, `parallel-safe`, `serialized`, `approval-gated`, or `blocked`.
5. Dispatch parallel-safe slices to isolated agents with explicit file ownership and acceptance criteria.
6. Serialize shared migrations, authentication, authorization, production, deployment, and overlapping-file work.
7. Integrate in dependency order, run focused and broad validation, and use an independent verifier for material changes.
8. Update all canonical control files and prepare the sanitized Second Brain projection after material state changes.
9. Continue to the next eligible slice without asking John for routine confirmation.
10. Stop and notify John only when a critical blockage defined in `AGENTS.md` prevents further safe progress.

## Parallel agent rules

Use up to four implementation agents plus one independent verifier by default. Increase or reduce concurrency based on repository, CPU, test, database, and deployment contention.

Each delegated task must specify:

- objective and roadmap milestone;
- files or directories owned by the agent;
- dependencies and prohibited files;
- acceptance criteria and negative tests;
- validation commands;
- risk tier and rollback expectation;
- required receipt format.

Agents must use isolated worktrees or branches when editing in parallel. No two agents may edit the same file concurrently. Read-only analysis agents may run in parallel with implementation agents if they do not mutate shared state.

## Risk handling

Low-risk and reversible work should continue autonomously after validation. Medium-risk work may be implemented behind flags, disabled defaults, test-only paths, or non-production scaffolding when this preserves safety and rollback. High-risk execution remains approval-gated.

When one slice is blocked, continue any independent eligible slice. A blocker becomes critical only when it prevents all further safe progress or requires a protected decision/action listed in `AGENTS.md`.

## Bounded repair

A materially similar failure receives no more than three attempts. Each attempt must use a different strategy or produce measurable progress. After the third similar failure:

- preserve commands, logs, and evidence;
- mark the slice blocked;
- document viable options and recommendation;
- continue independent work;
- notify John only if the blocker is critical to all remaining safe work.

## Notification rule

Do not notify John for normal progress, successful milestones, normal PR creation, self-healed failures, routine validation results, or noncritical deferred work. Write these to repository receipts and the Second Brain projection.

A critical-blockage notification must be concise and include only the decision required, evidence, safe options, consequences, and the recommended option.

## Completion rule

Do not call the project 99% complete until:

- all release-critical roadmap milestones are `verified_complete`;
- no unresolved critical security, privacy, client-isolation, data-integrity, or read-only-authority risk remains;
- applicable CI and three-run Quality Streak evidence exists;
- rollback/recovery evidence exists for material capabilities;
- the implementation status and roadmap are current;
- the Second Brain synchronization state and evidence are recorded.
