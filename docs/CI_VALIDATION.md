# CI Validation

Milestone 0 CI is centered on one local command:

```bash
./scripts/validate-ci.sh
```

The same command runs in GitHub Actions at `.github/workflows/ci.yml`.

## What It Checks

- Redacted Docker Compose validation through `scripts/compose-config-redacted.sh`.
- Migration filename ordering using the `NNN_description.sql` sequence.
- API Docker image build.
- Python syntax compilation for `apps/api/app` and `workers`.
- Full Python test suite with `pytest -q`.
- Static JavaScript syntax extracted from `apps/web/index.html`.

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
