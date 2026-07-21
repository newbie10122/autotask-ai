# CI Validation

Milestone 0 CI is centered on one local command:

```bash
./scripts/validate-ci.sh
```

The same command runs in GitHub Actions at `.github/workflows/ci.yml`.

## What It Checks

- Redacted Docker Compose validation through `scripts/compose-config-redacted.sh`.
- Production-auth preflight validation against `.env.example`.
- Migration filename ordering using the `NNN_description.sql` sequence.
- API Docker image build.
- Python syntax compilation for `apps/api/app` and `workers`.
- Full Python test suite with `pytest -q`.
- Static JavaScript syntax extracted from `apps/web/index.html`.
- Playwright Chromium browser UI RBAC smoke tests for anonymous, Admin, and ReadOnly role-control states plus serious/critical accessibility and keyboard/focus smoke checks.

The CI path uses `.env.example` and must not require real Autotask credentials. It does not start a sync, does not run live Autotask pulls, and does not write to Autotask.

## Capability Certification Receipt

Use this receipt format when certifying a roadmap capability:

```text
Capability:
Commit:
Scope:
Data classification:
Autotask write-back:
Files changed:
Migrations:
Tests run:
Validation evidence:
Security/read-only evidence:
Client-isolation evidence:
Rollback path:
Remaining risks:
Next action:
```

`Autotask write-back` must be `none` unless John has explicitly approved otherwise.

## Current Validation Streak

This section records validation-harness evidence only. It does not certify production deployment, production authentication enforcement, live customer-data expansion, or any Autotask write capability.

| Run | Commit / PR | Command | Result | Notes |
|---|---|---|---|---|
| 1 | `agent/m1-browser-rbac-smoke` pre-merge | `./scripts/validate-ci.sh && git diff --check` | pass: Python `88 passed`; Playwright `3 passed`; diff clean | First browser-enabled local validation |
| 2 | PR `newbie10122/autotask-ai#17` | GitHub Actions run `29862324198` | pass | First browser-enabled remote CI validation |
| 3 | `agent/m0-quality-streak-matrix` | `./scripts/validate-ci.sh && git diff --check` | pass: Python `88 passed`; Playwright `3 passed`; diff clean | Third browser-enabled validation-harness evidence point |

The validation harness has three clean browser-enabled evidence points. Capability-specific Quality Streaks remain governed by `AGENTS.md` and require the relevant negative, recovery, isolation, and rollback evidence.

## Answer-Safety Quality Streak

Use this command for repeatable conversational answer-safety certification evidence:

```bash
./scripts/answer-safety-quality-streak.sh
```

The script runs the guardrail and RAG conversational test subset three consecutive times inside the API container. It covers prompt-injection detection, secret filtering, ticket citation checks, source sufficiency, generated-answer verifier fallback, verifier-failure audit, metadata ticket IDs, cross-ticket evidence mismatch, weak no-evidence fallback language, required answer sections, and redaction preserving answer headers.

This is a candidate answer-safety Quality Streak harness. It does not certify production authentication enforcement, production deployment, live model quality, live customer-data expansion, or any Autotask write capability.
