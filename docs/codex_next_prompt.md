# Next Codex Prompt

Use `docs/CODEX_HARNESS_PROMPT.md` as the governing harness prompt.

## Immediate run objective

Complete the current Milestone 0 CI PR and certification handoff:

1. Review draft PR `newbie10122/autotask-ai#3` from `agent/m0-ci-validation` to `main`.
2. Confirm latest GitHub Actions result for the PR head. Run `29849731532` passed for implementation commit `c092bfa6f1f958f46f0512fa3817d5911d8f3b3f`; later receipt commits may trigger a newer run that must also be checked.
3. Do not mark Milestone 0 `verified_complete` until the PR is merged and fuller certification matrix/Quality Streak evidence is recorded.
4. After the PR is merged or materially changes, update the existing governed Autotask AI Second Brain projection per `AGENTS.override.md`; do not create an unrelated Second Brain PR.
5. Continue to the next eligible safe slice without routine user questions or notifications.

Next eligible safe work after CI PR creation:

- Authentication and RBAC test-first design.
- Durable identity-linked audit design.
- Fail-closed client/company isolation tests.
- Prompt-injection scanning and independent answer-verifier contract tests.

Do not perform production deployment, access secrets, expand customer-data scope, make irreversible migrations, or implement any Autotask write capability.
