# Next Codex Prompt

Use `docs/CODEX_HARNESS_PROMPT.md` as the governing harness prompt.

## Immediate run objective

Complete the current Milestone 0 CI reconciliation:

1. Confirm branch `agent/m0-ci-validation` is based on canonical `origin/main` commit `792eca2c943e4276cc3b8e93093d5dc193c6174f`.
2. Preserve local CI source commit `dc18106` through backup branch `backup/dc18106-ci-harness`.
3. Commit the governed CI reconciliation as `Add governed CI validation harness`.
4. Push `agent/m0-ci-validation` and open a draft PR to `main`.
5. Inspect the actual GitHub Actions run for the PR head.
6. Record GitHub CI as passed, failed, or externally blocked. Do not mark Milestone 0 `verified_complete` until remote CI and canonical acceptance evidence support it.
7. After the PR state materially changes, update the existing governed Autotask AI Second Brain projection per `AGENTS.override.md`; do not create an unrelated Second Brain PR.
8. Continue to the next eligible safe slice without routine user questions or notifications.

Next eligible safe work after CI PR creation:

- Authentication and RBAC test-first design.
- Durable identity-linked audit design.
- Fail-closed client/company isolation tests.
- Prompt-injection scanning and independent answer-verifier contract tests.

Do not perform production deployment, access secrets, expand customer-data scope, make irreversible migrations, or implement any Autotask write capability.
