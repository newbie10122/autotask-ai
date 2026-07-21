from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .answer_guardrails import has_required_answer_sections
from .security import detect_prompt_injection, find_sensitive_content, redact_private_entities


TICKET_TOKEN_PATTERN = re.compile(r"\bT\d+(?:\.\d+)?\b")
FIX_CLAIM_PATTERN = re.compile(
    r"\b("
    r"fix(?:ed|es)?|resolv(?:ed|es|ing)|repair(?:ed|s)?|"
    r"replac(?:ed|e|ing)|restart(?:ed|ing)?|reinstall(?:ed|ing)?|"
    r"updat(?:ed|e|ing)|reset(?:ting)?|reboot(?:ed|ing)?"
    r")\b",
    re.IGNORECASE,
)
TOKEN_PATTERN = re.compile(r"[a-z0-9]{3,}")
STOPWORDS = {
    "and",
    "are",
    "but",
    "can",
    "for",
    "from",
    "have",
    "into",
    "not",
    "the",
    "this",
    "that",
    "then",
    "they",
    "was",
    "were",
    "with",
    "your",
}
WEAK_HISTORY_PHRASES = (
    "i do not have enough matching",
    "no related ticket",
    "no matching ticket",
)


@dataclass
class AnswerVerificationResult:
    ok: bool
    fail_closed_reason: str = ""
    warnings: list[str] = field(default_factory=list)
    citation_ticket_ids: list[str] = field(default_factory=list)
    unsupported_claims: list[str] = field(default_factory=list)
    insufficient_source_claims: list[str] = field(default_factory=list)
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


def _tokens(value: str) -> set[str]:
    return {token for token in TOKEN_PATTERN.findall(value.lower()) if token not in STOPWORDS}


def _ticket_history_lines(answer: str) -> list[str]:
    lines: list[str] = []
    in_ticket_history = False
    for raw_line in answer.splitlines():
        line = raw_line.strip()
        if line == "From CompuOne Ticket History":
            in_ticket_history = True
            continue
        if in_ticket_history and line in {
            "General IT Guidance",
            "Suggested Next Steps",
            "Based on Tickets",
            "Warnings",
        }:
            break
        if in_ticket_history and line and not line.startswith("Confidence:"):
            lines.append(line.removeprefix("- ").strip())
    return lines


def _unsupported_ticket_history_claims(answer: str, sources: list[dict[str, Any]]) -> list[str]:
    source_tokens = _tokens("\n".join(str(source.get("content") or "") for source in sources))
    unsupported: list[str] = []
    for line in _ticket_history_lines(answer):
        if not FIX_CLAIM_PATTERN.search(line):
            continue
        claim_tokens = _tokens(line)
        overlap = claim_tokens & source_tokens
        if not sources or len(overlap) < 2:
            unsupported.append(redact_private_entities(line))
    return unsupported


def _sources_for_claim(line: str, sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cited_tickets = set(TICKET_TOKEN_PATTERN.findall(line))
    if not cited_tickets:
        return sources
    return [
        source
        for source in sources
        if cited_tickets
        & {
            str(source.get("ticket_number") or ""),
            str(source.get("autotask_id") or ""),
            str(source.get("ticket_id") or ""),
        }
    ]


def _source_sufficiency_violations(answer: str, sources: list[dict[str, Any]]) -> list[str]:
    violations: list[str] = []
    for line in _ticket_history_lines(answer):
        normalized = line.lower()
        if any(phrase in normalized for phrase in WEAK_HISTORY_PHRASES):
            continue
        claim_tokens = _tokens(TICKET_TOKEN_PATTERN.sub(" ", line))
        if len(claim_tokens) < 3:
            continue
        candidate_sources = _sources_for_claim(line, sources)
        source_tokens = _tokens("\n".join(str(source.get("content") or "") for source in candidate_sources))
        if not candidate_sources or len(claim_tokens & source_tokens) < 2:
            violations.append(redact_private_entities(line))
    return violations


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
    unsupported_claims = _unsupported_ticket_history_claims(answer, sources)
    insufficient_source_claims = _source_sufficiency_violations(answer, sources)
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
    if unsupported_claims:
        warnings.append("Answer included unsupported ticket-history resolution claim(s).")
    if insufficient_source_claims:
        warnings.append("Answer included ticket-history claim(s) with insufficient retrieved source evidence.")
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
    elif unsupported_claims:
        fail_closed_reason = "unsupported ticket-history claim"
    elif insufficient_source_claims:
        fail_closed_reason = "insufficient ticket-history source evidence"
    elif not has_required_answer_sections(answer):
        fail_closed_reason = "missing required answer sections"
    elif not general_guidance_labeled:
        fail_closed_reason = "unlabeled general guidance"

    return AnswerVerificationResult(
        ok=not fail_closed_reason,
        fail_closed_reason=fail_closed_reason,
        warnings=warnings,
        citation_ticket_ids=cited_tickets,
        unsupported_claims=unsupported_claims,
        insufficient_source_claims=insufficient_source_claims,
        secret_findings=secret_findings,
        prompt_injection_findings=injection_findings,
        scope_violations=scope_violations,
        general_guidance_labeled=general_guidance_labeled,
    )
