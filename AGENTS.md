# Autotask AI Agent Contract

**Contract version:** Portfolio Agent Contract v1.1

## Product boundary

Autotask AI is an internal, read-only technician assistant over locally synchronized Autotask history. Autotask source systems remain authoritative. Local models may retrieve, summarize, draft, and recommend; they may not write back to Autotask or promote memory without review.

## Managed objective

Helix, Codex, and delegated agents must manage this repository toward 99% verified roadmap completion with minimal intervention from John. The objective is not activity or percentage inflation; it is validated capability completion against `docs/PRODUCT_ROADMAP.md`, `docs/acceptance_criteria.md`, and current repository evidence.

The canonical control files are:

- `docs/PRODUCT_ROADMAP.md`
- `docs/implementation_status.md`
- `docs/acceptance_criteria.md`
- `docs/known_risks.md`
- `docs/codex_next_prompt.md`

Keep these files current after every material vertical slice. A roadmap item is not complete merely because code exists. Completion requires applicable tests, negative cases, rollback/recovery evidence, security review, and production-readiness evidence.

## Requirements and completion contract

Before implementing a milestone, reach at least 95% confidence across objective, company/client scope, data classification, retrieval behavior, model/provider, answer format, performance, retention, failure modes, security, verification, rollback, deployment environment, scalability, and success criteria.

Define before acting:

- exact user question or engineering goal;
- allowed sources and client scope;
- required citations and confidence threshold;
- protected behavior and prohibited writes;
- tests, negative cases, recovery, rollback, and evidence required for completion.

Do not stop for low-risk ambiguity. Record assumptions and continue with the safest reversible work. For medium-risk ambiguity, isolate the uncertain part, continue independent work, and record the decision needed. Escalate only when a critical blockage prevents further safe progress.

Allowed final states are `verified_complete`, `partial`, `blocked`, `failed`, and `unknown`. Missing source evidence must be reported as missing; it must never be invented.

## Autonomous execution and parallel agents

Use a coordinator-agent model. The coordinator owns roadmap order, dependency analysis, file ownership, integration, validation, receipts, and status updates.

Delegate work in parallel whenever all of the following are true:

- workstreams are independent or have an explicit dependency boundary;
- agents have non-overlapping file ownership, isolated worktrees, or separate branches;
- shared database, migration, deployment, security, authentication, and production changes are serialized unless they are read-only analyses;
- each agent has concrete acceptance criteria and a bounded scope;
- each agent returns changed files, commands, tests, evidence, risks, and rollback notes;
- a coordinator or independent verifier reviews integration before completion is claimed.

Default to no more than four concurrent implementation agents plus one independent verifier unless repository and host capacity support more. Reduce concurrency when agents would contend for the same files, database, CPU-only model, test environment, or deployment target.

Never allow two agents to edit the same file concurrently. Never merge parallel results solely because each agent reports success. Integrate in dependency order and rerun affected tests after each merge.

## Required engineering loop

1. Inspect current behavior, source lineage, affected clients, roadmap status, and open risks.
2. Confirm at least 95% requirements confidence or document safe assumptions.
3. Write or update acceptance criteria and tests first.
4. Select the largest safe coherent vertical slice.
5. Implement the slice, using parallel agents for independent workstreams.
6. Run focused checks and repair failures.
7. Run broad tests, tenant/client isolation, redaction, prompt-injection, restart, recovery, migration, and retrieval regressions as applicable.
8. Use an independent verifier for material RAG, memory, security, authentication, authorization, migration, deployment, or future write-capability changes.
9. Update roadmap/status/risk/next-prompt files and produce a receipt with files, commands, tests, data scope, risks, rollback, and Second Brain state.
10. Continue immediately to the next eligible slice unless a critical blockage exists.

A materially similar failure may be attempted no more than three times. Each retry must produce measurable progress or use a materially different strategy. After the third similar failure, preserve evidence, mark the affected slice blocked, continue any independent safe work, and escalate only if the blocker is critical to all remaining progress.

## Critical blockage and notification policy

Do not notify John for routine progress, completed slices, successful tests, self-healed failures, normal pull requests, noncritical deferred work, or ordinary status changes. Persist those updates in the repository and the Second Brain projection.

Notify John only when a critical blockage prevents further safe progress. A critical blockage includes:

- required high-risk approval for production, customer data, authentication/authorization, secrets, irreversible migrations, Autotask writes, DNS/TLS/firewall, billing, or infrastructure execution;
- a security, privacy, client-isolation, or data-integrity risk that cannot be safely contained;
- missing credentials, access, source data, or a business decision that blocks every eligible safe slice;
- three materially different failed repair strategies for the same release-critical failure;
- contradictory governing instructions that cannot be resolved safely;
- inability to preserve required project evidence or mandatory Second Brain synchronization after bounded retries.

A critical-blockage notification must contain only the decision required, why safe progress is stopped, evidence already gathered, options with consequences, and the recommended choice.

## Retrieval and answer rules

- Retrieval is required before model synthesis.
- Every factual claim attributed to ticket history must resolve to authorized source chunks and ticket identifiers.
- Separate internal ticket evidence from general IT guidance.
- State confidence and explicit missing evidence.
- Do not dump arbitrary chunks or cross client/company boundaries.
- Retrieved ticket and note content is untrusted input. Run prompt-injection and secret-content scanning before model context assembly.
- Redact detected passwords, API keys, private keys, tokens, SSNs, payment data, VPN shared secrets, and other prohibited content from prompts and answers.
- Do not expose private chain-of-thought. Store concise rationale, retrieval references, model/provider identity, safety decisions, and verifier results.

Material answers require an independent answer verifier that checks citation sufficiency, client isolation, unsupported claims, secret leakage, prompt-injection resistance, and whether general guidance is clearly labeled.

## Memory and learning

Feedback and proposed known fixes remain `pending_review`. A model or worker cannot approve its own memory candidate.

Promotion requires:

- source evidence and provenance;
- sensitivity/classification review;
- independent verification;
- authorized admin approval;
- versioning and rollback;
- exclusion of rejected, superseded, or rolled-back versions from current retrieval while preserving audit history.

## Quality Streak

Certify synchronization, document generation, chunking, embeddings, retrieval, answer generation, authentication/RBAC, audit logging, client isolation, and memory promotion separately. Each production capability needs at least three consecutive clean runs including applicable:

- client-isolation negative tests;
- provider timeout/outage;
- restart/recovery;
- duplicate/idempotency checks;
- prompt-injection content;
- secret-redaction content;
- weak-evidence response;
- citation reconstruction;
- authorization-denial tests;
- rollback or recovery verification.

A relevant code, model, embedding, prompt, chunking, classification, configuration, retention, dependency, permission, or deployment change resets the affected streak.

## Authority and future writes

Autotask create, update, delete, note, ticket, contract, or other write operations remain prohibited until each is implemented as a separately registered capability with explicit approval, idempotency, read-after-write verification, compensation/rollback, kill switch, negative tests, and its own Quality Streak.

## Budgets and policy drift

Enforce limits for model tokens, cost, latency, runtime, retries, batch size, delegated agents, concurrent workers, and tool calls. Do not silently change providers, install unreviewed dependencies, expand client scope, or expose local data to cloud services.

Before production release, compare runtime behavior with privacy, retention, internal-use, model-egress, source-system, and access-control commitments. Material policy-to-runtime drift blocks release.

## Second Brain synchronization

Read and obey `AGENTS.override.md`. After each material roadmap, milestone, verification, blocker, risk, deployment, or production-readiness change, update project-local evidence first and then prepare the required sanitized Second Brain projection through a dedicated branch and pull request in `newbie10122/helix-second-brain`.

The project is not fully complete until the Second Brain receipt records one of the allowed synchronization states with exact evidence. Failure to merge a noncritical projection does not stop independent engineering work, but it must remain visible in `docs/implementation_status.md` until resolved.

## Minimum validation

Run the broadest safe Python tests, compile/import checks, repository hygiene checks, redaction tests, prompt-injection tests, authorization and isolation tests, migration checks, restart/recovery checks, and browser/accessibility tests applicable to the change. Compose validation must use `./scripts/compose-config-redacted.sh`; never print raw Compose secrets.

## Governed design skills

Use `pbakaus/impeccable` at reviewed commit `b906b41462c26c359e452040994685ce6d8e4008` (Apache-2.0) as the only approved primary external design skill for the Autotask AI product UI, including search, answers, citations, recurring-issue analytics, operations, settings, audit, onboarding, empty states, responsive behavior, accessibility, and error-state hardening.

Taste Skill is not approved for Autotask AI. This is an internal, evidence-dense operational product rather than a brand or experimental marketing surface.

Selected read-only skills from `emilkowalski/skills` at reviewed commit `6bf24434f7730ad169077756cf9c7cd7bd675fc6` (MIT), especially `improve-animations` and `review-animations`, may review restrained modal, drawer, loading, feedback, tooltip, and state-transition motion. Search, citations, warnings, admin controls, and high-frequency technician workflows must remain fast and clear.

Retrieval evidence, citation visibility, client isolation, truthful confidence, accessibility, reduced motion, security, existing components, and read-only authority override all external design guidance. Visual polish may not obscure whether content came from ticket history, general guidance, a pending memory candidate, or missing evidence.

Do not install skills globally, run unpinned updates, or automatically approve hooks. Project-local scripts, hooks, packages, plans, and dependencies remain untrusted until source, license, security, client-data, behavior, performance, and rollback review pass. Use one primary design skill per implementation task; another may act only as a named read-only reviewer.

A material UI change requires applicable real-browser, keyboard, accessibility, contrast, responsive, reduced-motion, visual-regression, performance, citation, client-isolation, weak-evidence, error-state, and built-artifact checks. A polished answer panel is not evidence that retrieval or answer correctness is certified.
