# Codex Continuation Workflow Contract

Codex should not be asked to complete large multi-phase work in one long-running prompt. Each Codex run must complete one safe vertical slice, validate it, and leave a clean handoff for the next run.

## Required Operating Pattern

Every Codex implementation prompt for this repo must instruct Codex to inspect the relevant repo files before editing, select the largest safe coherent vertical slice, make real changes unless already satisfied, add or update tests where practical, run targeted validation first, update `docs/implementation_status.md`, create or update `docs/codex_next_prompt.md`, and stop only after leaving a usable diff, validation notes, and a next-step handoff.

## Standard Handoff Files

- `docs/implementation_status.md`
- `docs/codex_next_prompt.md`
- `docs/acceptance_criteria.md`
- `docs/known_risks.md`

If these files do not exist, the first Codex run for a milestone should create them.

## Anti-Patterns

Do not ask Codex to run 40 phases, continue forever, spend a fixed amount of time, make broad changes without acceptance criteria, or submit only a plan when implementation is requested.

## Standard Codex Run Template

```text
You are operating as a senior engineer in this repo.

Goal:
Complete one coherent vertical implementation slice that materially advances the project.

Do not perform only analysis. Inspect the repo, implement changes, validate them, and leave a clean handoff for the next Codex run.

Execution rules:
1. Read existing docs, tests, routes, config, and related code before editing.
2. Choose the largest safe vertical slice that can be completed in this run.
3. Make real code changes unless the repo already fully satisfies the acceptance criteria.
4. Add or update tests where practical.
5. Run targeted validation first, then broader validation if practical.
6. Update docs/implementation_status.md.
7. Create or update docs/codex_next_prompt.md with the exact next prompt to continue the work.
8. Include changed files, tests run, test results, remaining risks, and next recommended slice.
9. Do not mark the milestone complete unless validation supports it.
10. If blocked, document the blocker and still complete any safe preparatory work.

Required final state:
- Non-empty git diff, unless no change is truly needed.
- Clear validation results.
- Updated implementation status.
- Next Codex prompt ready to paste.

Milestone:
[PASTE THE SPECIFIC MILESTONE HERE]

Acceptance criteria:
[PASTE TESTABLE CRITERIA HERE]
```
