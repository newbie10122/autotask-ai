# Autotask AI Second Brain Synchronization Override

Read and obey the root `AGENTS.md` completely. This override adds mandatory portfolio-knowledge synchronization without weakening Autotask scope, privacy, security, evidence, approval, connector, notification, or write-authority controls.

## Assigned Second Brain area

This repository may update only `projects/autotask-ai/**`, source-linked append-only material events under `events/<year>/`, and affected concise portfolio projections. Do not alter another project family unless a verified cross-project dependency is explicitly in scope.

## Mandatory synchronization triggers

After project-local roadmap, implementation status, acceptance criteria, decisions, risks, blockers, tests, connector/retrieval evidence, and receipts are current, prepare a sanitized Second Brain update for any material:

- roadmap or milestone change;
- verified completion or regression;
- synchronization, retrieval, embedding, model, or memory-candidate change;
- security, privacy, client-isolation, authentication, authorization, or audit change;
- connector, deployment, pilot, production, or rollback event;
- critical blocker, material failure, repair, or risk change;
- exact next-action or delivery-order change.

Routine code edits that do not change project state may be marked `not-required` in the project receipt.

## Required status and roadmap projection

The Autotask AI projection must include:

- roadmap source, branch/commit, and freshness date;
- verified completed milestones;
- active milestone and exact vertical slice;
- next eligible milestone and dependency order;
- blocked, deferred, and approval-gated work;
- verified successes and material failures/repairs;
- residual risks and evidence gaps;
- data freshness, client-scope, local-model, production, and write-authority boundaries;
- CI and Quality Streak evidence;
- exact next action;
- source commits, pull requests, test receipts, and rollback references.

Project-local evidence remains authoritative. The Second Brain is a sanitized projection only and must never be used to inflate completion beyond repository evidence.

## Git and review path

Use a dedicated branch and pull request in `newbie10122/helix-second-brain`. Never push directly to its `main`, self-merge, or claim synchronization complete before merge. Validate the exact clean branch head with:

```bash
python tools/validate_knowledge.py
```

Every project completion receipt must state exactly one Second Brain state:

- `not-required`
- `prepared`
- `pull-request-open`
- `merged`
- `blocked`
- `failed`

Include the branch, pull request, source commit, validation result, or exact blocker.

## Autonomous handling and notifications

Do not interrupt John for normal Second Brain preparation, validation, pull requests, merge waiting, or noncritical repair work. Keep the synchronization state visible in `docs/implementation_status.md` and continue independent safe engineering work.

Retry a synchronization or validation failure with no more than three materially different strategies. Notify John only when inability to preserve or submit the required sanitized project state becomes a critical blockage to all further safe progress.

Never copy credentials, tokens, raw Autotask/customer records, tickets, contacts, contracts, financial data, private infrastructure details, or unnecessary personal information. Preserve material failures without status inflation.
