# Autotask AI Acceptance Criteria

These criteria govern milestone completion together with `AGENTS.md` and `docs/PRODUCT_ROADMAP.md`.

## Universal completion criteria

A milestone may be marked `verified_complete` only when:

- its objective and scope are documented at at least 95% confidence;
- code, configuration, schema, documentation, and UI agree;
- applicable unit, integration, negative, authorization, isolation, redaction, prompt-injection, migration, restart, recovery, idempotency, and rollback tests pass;
- material RAG, memory, security, authorization, migration, deployment, and write-capability changes have an independent verifier receipt;
- no unresolved critical security, privacy, client-isolation, data-integrity, or read-only-authority risk remains;
- performance and resource behavior are measured where applicable;
- the affected capability has three consecutive clean certification runs where required;
- `docs/implementation_status.md`, `docs/known_risks.md`, and `docs/codex_next_prompt.md` are current;
- the Second Brain synchronization state and evidence are recorded.

## Milestone 0

- Canonical roadmap and control files exist and are internally consistent.
- Obsolete roadmap PRs are closed or explicitly superseded.
- CI automatically runs the agreed validation suite on pull requests, pushes to `main`, and manual dispatch.
- CI uses read-only repository permissions and a bounded 30-minute job timeout.
- CI delegates command logic to `scripts/validate-ci.sh` instead of duplicating validation steps in workflow YAML.
- The CI validation script runs redacted Compose validation through `scripts/compose-config-redacted.sh` and does not print raw `.env` values.
- The CI validation script verifies migration filename ordering, builds the API image, compiles API/worker Python, runs the full Python test suite, and checks static web JavaScript syntax.
- CI validation uses `.env.example` and must not require live Autotask credentials for ordinary PR validation.
- CI validation does not start sync jobs, deploy production services, or write to Autotask.
- CI failures block completion claims.
- A capability certification and Quality Streak record format exists in `docs/CI_VALIDATION.md`.
- Repository hygiene tests pin the CI workflow, validation script, redacted Compose usage, migration ordering check, JavaScript syntax check, and receipt format.
- Repository receipts include exact commands, results, commits, risks, rollback, and Second Brain state.
- Local reconciled evidence on branch `agent/m0-ci-validation`: `./scripts/validate-ci.sh` passed with redacted Compose validation, 6 ordered migrations, API image build, Python compile, `53 passed`, and static web JavaScript syntax. GitHub Actions PR evidence remains pending and must be recorded before Milestone 0 can be marked `verified_complete`.

## Milestone 1

- Login rejects invalid credentials and disabled users.
- Passwords are securely hashed and never logged.
- Sessions/tokens expire and are securely configured.
- Admin, Technician, and ReadOnly permissions are enforced at API and UI boundaries.
- Unauthorized requests fail closed and are audited.
- Audit records survive restart and link actor, action, target, scope, and outcome.
- Every retrieval and analytics request has explicit authorized company/client scope.
- Cross-client source, cache, citation, and analytics access is denied by negative tests.
- Retrieved untrusted content is scanned for prompt injection and prohibited secrets.
- Material answers pass an independent verifier or fail closed.
- Three consecutive clean identity/isolation/verifier certification runs exist.

## Milestone 2

- Required ticket-health fields are inventoried with Autotask source names and availability.
- Time entries and approved operational fields synchronize read-only with checkpoints.
- Sync is idempotent, resumable, bounded, rate/threshold aware, and restart safe.
- Client scope and source lineage are retained.
- Missing/unmapped fields are visible and not silently guessed.
- Three consecutive clean sync/recovery runs exist.

## Milestone 3

- Ticket age, labor, last action, waiting state, resource count, response count, SLA risk, stalled state, and high-labor outliers are calculated deterministically where data permits.
- Every result shows scope, freshness, evidence, and assumptions.
- Filters, APIs, assistant routes, and UI agree.
- Empty, loading, stale, error, keyboard, responsive, and reduced-motion states are tested.
- Representative real-data calculations are independently checked.

## Milestone 4

- Redis health and safe fallback behavior are implemented.
- Cache keys contain authorization scope and all relevant version inputs.
- Invalidation prevents stale data after sync, permissions, model, embedding, prompt, document, and memory changes.
- Cache outage does not break core read-only behavior.
- Benchmarks show measurable benefit without leakage or correctness regression.
- Three consecutive clean cache/isolation/recovery runs exist.

## Milestone 5

- Real-time subscriptions are authenticated and client scoped.
- Reconnect, replay, duplicate, rate-limit, and outage behavior are tested.
- Events contain only necessary data.
- Event infrastructure failure degrades safely.

## Milestone 6

- Technician suggestions and drafts cite authorized evidence and label inference.
- Weak evidence abstains or clearly qualifies.
- Drafts are review-only and never written to Autotask.
- Prompt-injection, secret leakage, cross-client, timeout, and verifier-failure cases fail safely.
- Technician acceptance/correction metrics are captured.

## Milestone 7

- Prediction targets, labels, training/evaluation data, and leakage controls are documented.
- Predictions show evidence, sample size, freshness, confidence, limitations, and reason codes.
- Holdout evaluation beats a defined simple baseline.
- Calibration and abstention are measured.
- Bias and client/category concentration risks are reviewed.

## Milestone 8

- Routing remains recommendation-only.
- Recommendations include workload, skill, history, customer familiarity, and reason codes.
- Accuracy, acceptance, concentration, and fairness metrics are recorded.
- No assignment write route or hidden write path exists.

## Milestone 9

- Customer-success insights are authorized, fresh, evidence linked, and explainable.
- Evidence is separated from inference and business recommendation.
- Account-facing drafts remain review-only.
- Cross-client aggregation is prohibited unless explicitly authorized.

## Milestone 10

- All release-target milestones are `verified_complete`.
- Full CI and Quality Streak evidence is current.
- Backup/restore, restart, dependency-outage, deployment, and rollback drills pass.
- Monitoring, alerting, retention, capacity, and runbooks are verified.
- Policy-to-runtime review passes.
- No critical blocker or release-critical unknown remains.
- The residual 1% backlog is documented as noncritical and explicitly deferred.
- The sanitized Second Brain projection is current with exact source evidence.
