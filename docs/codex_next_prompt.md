# Next Codex Prompt

Use `docs/CODEX_HARNESS_PROMPT.md` as the governing harness prompt.

## Immediate run objective

Continue Milestone 1 from branch `agent/m1-durable-audit-scope-foundation`:

1. Push/open a draft PR for the durable-audit foundation if it is not already open.
2. Confirm the latest GitHub Actions result for that PR head.
3. Update the existing governed Autotask AI Second Brain projection PR after the Autotask AI PR exists or materially changes.
4. Continue immediately to full company-scope propagation.
5. Do not mark Milestone 1 `verified_complete` until full API/UI RBAC, persistent audit, fail-closed client isolation, independent verifier breadth, and three-run Quality Streak evidence all pass.

Current foundation evidence:

- PBKDF2 password hashing, signed expiring tokens, `/auth/me`, optional bearer-token middleware, disabled-user rejection, invalid-login rejection, and admin-operation role denial tests exist.
- Pre-prompt prompt-injection/secret source filtering and citation-subset answer verification tests exist.
- `_retrieve_sources` has an `authorized_company_ids` filter contract, but authenticated actor-to-company scope is not wired end to end.
- `./scripts/validate-ci.sh` passed on the M1 branch with 7 ordered migrations and full pytest `65 passed`.
- Initial PR #4 run `29854738844` failed from a non-hermetic admin-route test that expected a live `postgres` hostname, and the amended branch fixes that test.
- Durable audit branch adds DB-backed `audit_log` persistence, outcome/scope fields, missing-token denial events, insufficient-role denial events, and no-Postgres API tests.
- `./scripts/validate-ci.sh` passed on the durable-audit branch with 8 ordered migrations and full pytest `67 passed`.

Next eligible safe work:

- User-company scope tables, helpers, and fail-closed dependencies.
- Assistant, recurring analytics, query source, feedback, memory, future cache/export scope propagation.
- UI auth/RBAC states and API denial coverage for all roles.
- Verifier expansion for unsupported claims, scope violations, guidance labeling, secrets, injection, weak evidence, and fallback behavior.

Do not perform production deployment, access secrets, expand customer-data scope, make irreversible migrations, or implement any Autotask write capability.
