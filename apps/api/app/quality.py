from __future__ import annotations

import re


NOISE_CLASSES = {
    "system_notification",
    "completion_email",
    "survey_email",
    "autoresponder",
    "unsubscribe_or_footer",
    "low_value_noise",
}

FIX_PATTERNS = (
    r"\bresolved\b",
    r"\bfixed\b",
    r"\brestarted\b",
    r"\breinstalled\b",
    r"\bupdated\b",
    r"\bcleared\b",
    r"\bchanged\b",
    r"\breplaced\b",
    r"\bsolution\b",
    r"\bworkaround\b",
)

CLASS_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "survey_email",
        (
            "ticket survey",
            "help us serve you better",
            "i no longer wish to receive these surveys",
            "unsubscribesurvey",
        ),
    ),
    (
        "completion_email",
        (
            "your ticket is complete",
            "ticket is complete",
            "this ticket has been completed",
        ),
    ),
    (
        "system_notification",
        (
            "replies to this email will be added as a note",
            "you are receiving this message because a ticket was created",
            "notification e-mail",
            "ticket note created or edited",
            "initiated by",
        ),
    ),
    (
        "autoresponder",
        (
            "*** please enter replies above this line ***",
            "out of office",
            "automatic reply",
            "auto-reply",
            "autoresponder",
        ),
    ),
    (
        "unsubscribe_or_footer",
        (
            "unsubscribe",
            "privacy policy",
            "confidentiality notice",
            "this e-mail and any attachments",
        ),
    ),
)


def classify_chunk(content: str) -> dict[str, object]:
    text = content or ""
    lowered = text.lower()
    for knowledge_class, phrases in CLASS_RULES:
        for phrase in phrases:
            if phrase in lowered:
                return {
                    "knowledge_class": knowledge_class,
                    "quality_score": 0.05,
                    "is_noise": True,
                    "noise_reason": phrase,
                }

    email_header_lines = len(re.findall(r"(?im)^(from|to|sent|subject|cc):\s+", text))
    substantive_words = re.findall(r"\b[a-zA-Z]{4,}\b", text)
    fix_language = any(re.search(pattern, lowered) for pattern in FIX_PATTERNS)
    has_customer_language = any(word in lowered for word in ("please", "error", "issue", "problem", "cannot", "can't", "failed"))

    if email_header_lines >= 3 and len(substantive_words) < 80 and not fix_language:
        return {
            "knowledge_class": "low_value_noise",
            "quality_score": 0.15,
            "is_noise": True,
            "noise_reason": "email headers without troubleshooting content",
        }
    if len(substantive_words) < 12 and not fix_language:
        return {
            "knowledge_class": "low_value_noise",
            "quality_score": 0.2,
            "is_noise": True,
            "noise_reason": "too little substantive troubleshooting content",
        }
    if fix_language:
        return {"knowledge_class": "resolution", "quality_score": 1.0, "is_noise": False, "noise_reason": None}
    if has_customer_language:
        return {"knowledge_class": "customer_reply", "quality_score": 0.7, "is_noise": False, "noise_reason": None}
    if "note body:" in lowered or "description:" in lowered:
        return {"knowledge_class": "human_troubleshooting", "quality_score": 0.85, "is_noise": False, "noise_reason": None}
    return {"knowledge_class": "unknown", "quality_score": 0.5, "is_noise": False, "noise_reason": None}


def is_recurring_issues_question(question: str) -> bool:
    lowered = question.lower()
    return any(
        phrase in lowered
        for phrase in (
            "most common recurring issues",
            "common recurring issues",
            "recurring support issues",
            "common issues",
            "top problems",
            "what keeps happening",
            "frequent tickets",
            "most common",
        )
    )
