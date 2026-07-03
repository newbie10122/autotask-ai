# Helix Project Management Process

## Purpose

When Helix begins managing this project, Helix, its lead agents, and Codex must use the universal Project Milestone Autonomous Build process.

This file is a repo-level instruction for future Helix-managed work. It does not enable autonomous execution by itself.

## Standard Command Shape

John should be able to say:

```text
Helix, build this project to Milestone X.
```

Helix must then discover the current roadmap/status, identify the target milestone, build a safe execution queue, and use Codex continuation-loop prompts for one vertical slice at a time.

## Required Helix Workflow

Before generating Codex work, Helix must identify the repo, roadmap docs, current status files, acceptance criteria, and known risks; compare current state against the target milestone; break the gap into ordered vertical slices; ask John only for true blockers; batch medium-risk questions; stop for high-risk approval; and notify John when complete, blocked, failed, or approval is needed.

## John Blocker Prevention

Helix must not ask John for clarification unless the missing answer blocks safe progress or affects security, production, customer data, billing, deployment, irreversible data changes, or business-critical behavior.

For low-risk uncertainty, Helix should document assumptions and continue with safe preparatory work. For medium-risk uncertainty, Helix should batch questions. For high-risk uncertainty, Helix must stop before implementation or execution and ask John.

## Risk Tiers

Low-risk work may continue after validation when limited to docs, tests, read-only UI, disabled scaffolding, prompt logic, status files, contracts, safe API list/read endpoints, or non-production validation scripts.

Medium-risk work may proceed through safe prep but should be batched for review when it changes UI behavior, agent routing, memory behavior, business logic, new background jobs, database read paths, or integration behavior.

High-risk work requires human approval before implementation or execution when it touches authentication, authorization, secrets, billing, payments, customer data, production deploys, DNS, TLS, firewall, infrastructure automation, database writes/migrations, active scanning, remote shell/SSH, or irreversible changes.

## Codex Continuation Loop

Every Codex implementation handoff must require Codex to inspect the repo, implement one coherent vertical slice, update tests where practical, run targeted validation, update `docs/implementation_status.md`, create or update `docs/codex_next_prompt.md`, and report changed files, validation, blockers, risks, and next work.

If those status files do not exist, the first Helix/Codex slice should create them.

## Notification Rule

Helix should notify John only when the target milestone is completed, a true blocker appears, validation fails, high-risk approval is required, unexpected repo state is found, or a medium-risk review checkpoint is reached.
