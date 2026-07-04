# AutoTask AI External Platform Reference Roadmap

## Purpose

When Helix manages AutoTask AI, these platforms should be reviewed as roadmap references for workflow orchestration, workspace UX, scheduling, deployment operations, research assist, and design workflow.

This file is a roadmap input only. It does not approve copying code, adding dependencies, shell execution, credential use, external actions, or implementation.

## Priority References

### 1. n8n

Use for: workflow graph concepts, trigger/action design, approval checkpoints, retry and failure handling, integration catalog UX, and execution history.

AutoTask AI fit: task routing, operational workflows, approval queues, and integration planning.

Risk gate: no external actions or unattended task execution without approval controls.

### 2. Agent-Reach

Repository: `Panniantong/agent-reach`

Use for: controlled research capability routing, source/channel discovery, tool health checks, and external-reference research design.

AutoTask AI fit: task research workflows, service/vendor research, integration discovery, and safe research-mode UX.

Risk gate: architecture research only until approved. No auto-install, shell execution, cookies, tokens, logged-in scraping, or platform bypass without Aegis approval.

### 3. AppFlowy

Use for: workspace/page/block model, docs, tasks, database-style views, and project knowledge organization.

AutoTask AI fit: task workspace, runbooks, customer/project notes, and AI-assisted work planning.

### 4. Cal.com / Cal.diy

Use for: scheduling, availability, booking workflow, team routing, and notification patterns.

AutoTask AI fit: scheduled follow-ups, technician scheduling, and appointment workflow ideas.

### 5. Coolify

Use for: deployment dashboard concepts, service management, logs, rollback, environment variables, and preview environments.

### 6. Penpot

Use for: design workflow, UI prototypes, component libraries, and design-to-dev handoff.

### 7. Codebase-Memory MCP

Use through Helix for: repo understanding, impact analysis, and safer Codex prompt context.

## Required Research Output

Each review must produce useful concepts, avoid-list, license/security/dependency risks, AutoTask AI-native recommendation, and the first safe Codex implementation slice if adoption is approved.

Any implementation must follow `docs/HELIX_PROJECT_MANAGEMENT_PROCESS.md` and the Codex continuation-loop workflow.
