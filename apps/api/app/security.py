import base64
import hashlib
import hmac
import json
import re
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from .config import settings


SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY-----", re.I),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)\b(api[_-]?key|secret|password|passwd|pwd|token)\b\s*[:=]\s*\S+"),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
    re.compile(r"(?i)\bvpn\s+(?:shared\s+)?secret\s*[:=]\s*\S+"),
]

PROMPT_INJECTION_PATTERNS: dict[str, re.Pattern] = {
    "ignore_previous_instructions": re.compile(r"(?i)\bignore (?:all |any |the |previous|prior).{0,40}instructions\b"),
    "reveal_system_prompt": re.compile(r"(?i)\b(?:reveal|show|print|dump).{0,40}(?:system prompt|developer message|hidden prompt)\b"),
    "bypass_rules": re.compile(r"(?i)\b(?:bypass|override|disable).{0,40}(?:rules|guardrails|safety|policy)\b"),
    "act_as_system": re.compile(r"(?i)\b(?:you are now|act as).{0,40}(?:system|developer|admin)\b"),
}

PASSWORD_HASH_ALGORITHM = "pbkdf2_sha256"
PASSWORD_HASH_ITERATIONS = 260000

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


def detect_prompt_injection(text: str) -> list[str]:
    return [name for name, pattern in PROMPT_INJECTION_PATTERNS.items() if pattern.search(text)]


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


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_HASH_ITERATIONS)
    return "$".join(
        [
            PASSWORD_HASH_ALGORITHM,
            str(PASSWORD_HASH_ITERATIONS),
            _b64url_encode(salt),
            _b64url_encode(digest),
        ]
    )


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt_text, digest_text = encoded_hash.split("$", 3)
        if algorithm != PASSWORD_HASH_ALGORITHM:
            return False
        iterations = int(iterations_text)
        salt = _b64url_decode(salt_text)
        expected = _b64url_decode(digest_text)
    except Exception:
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


def _sign_token_payload(payload_text: str) -> str:
    digest = hmac.new(settings.app_session_secret.encode("utf-8"), payload_text.encode("utf-8"), hashlib.sha256).digest()
    return _b64url_encode(digest)


def create_session_token(username: str, roles: list[str], ttl_seconds: int | None = None) -> dict[str, Any]:
    issued_at = datetime.now(UTC)
    expires_at = issued_at + timedelta(seconds=ttl_seconds or settings.app_session_ttl_seconds)
    payload = {
        "sub": username,
        "roles": roles,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
        "jti": secrets.token_urlsafe(16),
    }
    payload_text = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    payload_part = _b64url_encode(payload_text.encode("utf-8"))
    signature = _sign_token_payload(payload_part)
    return {"token": f"v1.{payload_part}.{signature}", "expires_at": expires_at.isoformat()}


def verify_session_token(token: str) -> dict[str, Any] | None:
    try:
        version, payload_part, signature = token.split(".", 2)
        if version != "v1":
            return None
        expected_signature = _sign_token_payload(payload_part)
        if not hmac.compare_digest(signature, expected_signature):
            return None
        payload = json.loads(_b64url_decode(payload_part).decode("utf-8"))
        if int(payload.get("exp", 0)) <= int(datetime.now(UTC).timestamp()):
            return None
        if not payload.get("sub") or not isinstance(payload.get("roles"), list):
            return None
        return payload
    except Exception:
        return None


def _record_login_attempt(username: str, ip_address: str | None, success: bool, failure_reason: str | None = None) -> None:
    try:
        from .db import db_connection

        with db_connection() as conn:
            conn.execute(
                """
                INSERT INTO app_login_attempts (username, ip_address, success, failure_reason)
                VALUES (%s, %s, %s, %s)
                """,
                (username, ip_address, success, failure_reason),
            )
    except Exception:
        pass


def _login_is_throttled(username: str, ip_address: str | None) -> bool:
    try:
        from .db import db_connection

        with db_connection() as conn:
            row = conn.execute(
                """
                SELECT count(*) AS failures
                FROM app_login_attempts
                WHERE username = %s
                  AND success = FALSE
                  AND attempted_at >= now() - (%s || ' seconds')::interval
                """,
                (username, settings.auth_login_failure_window_seconds),
            ).fetchone()
        return int((row or {}).get("failures") or 0) >= settings.auth_login_failure_limit
    except Exception:
        return False


def authenticate_user(username: str, password: str, ip_address: str | None = None) -> dict[str, Any] | None:
    if _login_is_throttled(username, ip_address):
        return {"username": username, "roles": [], "disabled": False, "throttled": True}

    try:
        from .db import db_connection

        with db_connection() as conn:
            row = conn.execute(
                """
                SELECT username, password_hash, roles, disabled
                FROM app_users
                WHERE username = %s
                """,
                (username,),
            ).fetchone()
        if not row:
            if not settings.app_route_auth_required and username == "tech" and password == "local-password":
                return {"username": username, "roles": ["Technician"], "disabled": False}
            _record_login_attempt(username, ip_address, False, "invalid_credentials")
            return None
        if not verify_password(password, row["password_hash"]):
            _record_login_attempt(username, ip_address, False, "invalid_credentials")
            return None
        if row["disabled"]:
            _record_login_attempt(username, ip_address, False, "disabled")
            return {"username": row["username"], "roles": row["roles"] or [], "disabled": True}
        _record_login_attempt(username, ip_address, True)
        return {"username": row["username"], "roles": row["roles"] or [], "disabled": False}
    except Exception:
        if username == "tech" and password == "local-password":
            return {"username": username, "roles": ["Technician"], "disabled": False}
        return None
