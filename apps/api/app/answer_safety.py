from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .answer_guardrails import has_required_answer_sections
from .security import detect_prompt_injection, find_sensitive_content, redact_private_entities


TICKET_TOKEN_PATTERN = re.compile(r"\bT\d+(?:\.\d+)?\b")


@dataclass
class AnswerVerificationResult:
    ok: bool
    fail_closed_reason: str = ""
    warnings: list[str] = field(default_factory=list)
    citation_ticket_ids: list[str] = field(default_factory=list)
    unsupported_claims: list[str] = field(default_factory=list)
    secret_findings: list[str] = field(default_factory=list)
    prompt_injection_findings: list[str] = field(default_factory=list)
    scope_violations: list[str] = field(default_factory=list)
    general_guidance_labeled: bool = True


def source_ticket_ids(sources: list[dict[str, Any]]) -> set[str]:
    ids: set[str] = set()
    for source in sources:
        for key in ("ticket_number", "autotask_id", "ticket_id"):
            value = source.get(key)
            if value:
                ids.add(str(value))
    return ids


def filter_safe_sources(sources: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    safe_sources: list[dict[str, Any]] = []
    warnings: list[str] = []
    for source in sources:
        content = str(source.get("content") or "")
        injection_findings = detect_prompt_injection(content)
        secret_findings = find_sensitive_content(content)
        ticket = source.get("ticket_number") or source.get("autotask_id") or source.get("chunk_id")
        if injection_findings:
            warnings.append(f"Excluded source {ticket}: prompt injection indicators detected.")
            continue
        if secret_findings:
            warnings.append(f"Excluded source {ticket}: sensitive content indicators detected.")
            continue
        cleaned = dict(source)
        cleaned["content"] = redact_private_entities(content)
        safe_sources.append(cleaned)
    return safe_sources, warnings


def verify_answer(
    answer: str,
    sources: list[dict[str, Any]],
    authorized_company_ids: list[int] | None = None,
) -> AnswerVerificationResult:
    secret_findings = find_sensitive_content(answer)
    injection_findings = detect_prompt_injection(answer)
    cited_tickets = sorted(set(TICKET_TOKEN_PATTERN.findall(answer)))
    allowed_tickets = source_ticket_ids(sources)
    unknown_tickets = [ticket for ticket in cited_tickets if ticket not in allowed_tickets]
    scope_violations: list[str] = []
    if authorized_company_ids is not None:
        allowed_companies = {int(company_id) for company_id in authorized_company_ids}
        for source in sources:
            metadata = source.get("source_metadata") or {}
            company_id = source.get("company_id") or metadata.get("company_id")
            if company_id is not None and int(company_id) not in allowed_companies:
                source_id = source.get("ticket_number") or source.get("autotask_id") or source.get("chunk_id")
                scope_violations.append(str(source_id))
    general_guidance_labeled = "General IT Guidance" in answer
    warnings: list[str] = []
    if secret_findings:
        warnings.append("Sensitive content was detected in the answer.")
    if injection_findings:
        warnings.append("Prompt-injection language was detected in the answer.")
    if unknown_tickets:
        warnings.append(f"Answer cited unretrieved ticket(s): {', '.join(unknown_tickets)}.")
    if scope_violations:
        warnings.append(f"Answer used out-of-scope source(s): {', '.join(scope_violations)}.")
    if not has_required_answer_sections(answer):
        warnings.append("Answer is missing required sections.")
    if not general_guidance_labeled:
        warnings.append("General guidance is not clearly labeled.")

    fail_closed_reason = ""
    if unknown_tickets:
        fail_closed_reason = "unretrieved ticket citation"
    elif scope_violations:
        fail_closed_reason = "out-of-scope source"
    elif secret_findings:
        fail_closed_reason = "sensitive content in answer"
    elif injection_findings:
        fail_closed_reason = "prompt injection text in answer"
    elif not has_required_answer_sections(answer):
        fail_closed_reason = "missing required answer sections"
    elif not general_guidance_labeled:
        fail_closed_reason = "unlabeled general guidance"

    return AnswerVerificationResult(
        ok=not fail_closed_reason,
        fail_closed_reason=fail_closed_reason,
        warnings=warnings,
        citation_ticket_ids=cited_tickets,
        secret_findings=secret_findings,
        prompt_injection_findings=injection_findings,
        scope_violations=scope_violations,
        general_guidance_labeled=general_guidance_labeled,
    )
