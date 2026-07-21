# Codex Continuation Workflow Contract

Codex must manage the project as a sequence of verified vertical slices, not as an unbounded prompt or a long list of shallow edits. One harness run may dispatch several independent slices in parallel, but every result must be integrated and verified through a single coordinator.

## Required operating pattern

Every Codex harness run must:

1. Read `AGENTS.md`, `AGENTS.override.md`, the product roadmap, implementation status, acceptance criteria, known risks, recent commits, open pull requests, tests, and deployment/runbook files.
2. Reconcile written status with actual code and validation evidence.
3. Reach at least 95% confidence for the next eligible work or record conservative assumptions.
4. Build a dependency graph and identify parallel-safe workstreams with explicit non-overlapping file ownership.
5. Dispatch up to four implementation agents plus one independent verifier by default when safe.
6. Complete real implementation work, not analysis only, unless the selected slice is explicitly a research or evidence milestone.
7. Run targeted validation for each workstream and broad integration validation after merging results.
8. Repair failures within the three-attempt rule in `AGENTS.md`.
9. Update the canonical control files and Second Brain synchronization state.
10. Continue to the next eligible slice without routine user confirmation.
11. Notify John only when a critical blockage prevents all further safe progress.

## Standard handoff files

- `docs/implementation_status.md`
- `docs/codex_next_prompt.md`
- `docs/acceptance_criteria.md`
- `docs/known_risks.md`

These files are mandatory and must remain consistent with `docs/PRODUCT_ROADMAP.md`.

## Parallel work rules

Parallel work is allowed only when:

- workstreams are independent or dependency-ordered;
- agents use isolated worktrees or branches;
- no two agents edit the same file concurrently;
- migrations, authentication/authorization, shared schemas, production deployment, and overlapping integrations are serialized;
- each agent has explicit acceptance criteria, prohibited scope, validation commands, and a receipt requirement;
- an independent verifier reviews material security, RAG, memory, migration, deployment, or authorization changes.

The coordinator must integrate one workstream at a time and rerun affected tests after each integration. Individual agent success is not sufficient evidence of integrated success.

## Anti-patterns

Do not:

- run forever or promise future background work;
- implement many roadmap phases shallowly;
- edit overlapping files in parallel;
- mark work complete from code inspection alone;
- bypass tests, approval gates, read-only authority, client isolation, or Second Brain requirements;
- ask John routine clarification questions that can be handled through conservative assumptions;
- send routine progress or success notifications.

## Required receipt

Every completed slice must record:

- milestone and exact slice;
- final state: `verified_complete`, `partial`, `blocked`, `failed`, or `unknown`;
- files changed and commits;
- tests and commands run with results;
- negative, isolation, redaction, recovery, and rollback evidence as applicable;
- delegated agents and file ownership;
- assumptions and residual risks;
- exact next eligible slice;
- Second Brain state and evidence.

## Standard single-slice prompt

```text
You are operating as a senior engineer in the Autotask AI repository.

Read and obey AGENTS.md and AGENTS.override.md before doing anything else.

Goal:
Complete the largest safe coherent vertical slice that materially advances the active milestone in docs/PRODUCT_ROADMAP.md.

Execution rules:
1. Inspect the roadmap, implementation status, acceptance criteria, known risks, recent commits, open PRs, tests, routes, schema, config, deployment docs, and current Second Brain state.
2. Reach at least 95% confidence or document conservative assumptions that allow reversible work.
3. Make real code or evidence changes unless the slice is already fully satisfied.
4. Add or update tests first where practical.
5. Use isolated parallel agents only for independent work with non-overlapping files; otherwise serialize.
6. Run targeted validation, integrate carefully, then run broad affected tests.
7. Use an independent verifier for material RAG, memory, security, authorization, migration, deployment, or future write-capability changes.
8. Retry materially similar failures no more than three times using different strategies.
9. Update docs/implementation_status.md, docs/acceptance_criteria.md, docs/known_risks.md, and docs/codex_next_prompt.md.
10. Prepare the sanitized Second Brain update required by AGENTS.override.md after material state changes.
11. Continue to the next eligible slice without routine user confirmation.
12. Notify John only if a critical blockage prevents all further safe progress.

Required final state:
- A verified vertical slice or a precisely evidenced blocked state.
- Clear validation and rollback/recovery evidence.
- Updated canonical control files.
- Exact next prompt and Second Brain state recorded.
```
