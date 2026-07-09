import re


SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY-----", re.I),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)\b(api[_-]?key|secret|password|passwd|pwd|token)\b\s*[:=]\s*\S+"),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
    re.compile(r"(?i)\bvpn\s+(?:shared\s+)?secret\s*[:=]\s*\S+"),
]

CLIENT_LABEL_PATTERN = re.compile(
    r"(?im)^((?:Company|Client|Customer|Account)\s*:\s*)(.+)$",
)
PERSON_LABEL_PATTERN = re.compile(
    r"(?im)^((?:Note Resource|Resource|Assigned Resource|Requester|Contact|User)\s*:\s*)(.+)$",
)
PROPER_NAME_PATTERN = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b")

PROPER_NAME_ALLOWLIST = {
    "Admin Operations",
    "Autotask AI",
    "Basic Auth",
    "CompuOne Ticket History",
    "Deep Dive",
    "From CompuOne",
    "General IT",
    "General IT Guidance",
    "Local CPU",
    "Microsoft Teams",
    "Microsoft Windows",
    "Note Resource",
    "Office 365",
    "Suggested Next",
    "Suggested Next Steps",
    "Ticket History",
}

PROPER_NAME_ALLOWED_WORDS = {
    "Access",
    "Active",
    "Admin",
    "Answer",
    "API",
    "Auth",
    "Autotask",
    "Based",
    "Basic",
    "CPU",
    "Chrome",
    "CompuOne",
    "Confidence",
    "Deep",
    "Description",
    "Dive",
    "DNS",
    "Email",
    "Evidence",
    "Exchange",
    "From",
    "General",
    "Guidance",
    "History",
    "Local",
    "Microsoft",
    "Nginx",
    "Office",
    "Operations",
    "Outlook",
    "Postgres",
    "Printer",
    "RAG",
    "Scan",
    "SharePoint",
    "Suggested",
    "Teams",
    "Ticket",
    "Tickets",
    "VPN",
    "Warnings",
    "Windows",
}


def find_sensitive_content(text: str) -> list[str]:
    findings: list[str] = []
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            findings.append(pattern.pattern)
    return findings


def redact_sensitive_content(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def _redact_proper_name(match: re.Match) -> str:
    value = match.group(0)
    words = set(value.split())
    if value in PROPER_NAME_ALLOWLIST or words <= PROPER_NAME_ALLOWED_WORDS:
        return value
    return "[NAME]"


def redact_private_entities(text: str) -> str:
    redacted = redact_sensitive_content(text)
    redacted = CLIENT_LABEL_PATTERN.sub(r"\1[CLIENT]", redacted)
    redacted = PERSON_LABEL_PATTERN.sub(r"\1[PERSON]", redacted)
    redacted = PROPER_NAME_PATTERN.sub(_redact_proper_name, redacted)
    return redacted
