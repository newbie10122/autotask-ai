from .models import REQUIRED_ANSWER_SECTIONS
from .security import redact_sensitive_content

WEAK_EVIDENCE_MESSAGE = "I do not have enough matching CompuOne ticket history."


def build_guarded_answer(
    ticket_history: str,
    general_guidance: str,
    next_steps: list[str],
    tickets: list[str],
    confidence: float,
) -> str:
    safe_history = redact_sensitive_content(ticket_history)
    safe_guidance = redact_sensitive_content(general_guidance)
    if confidence < 0.35 or not tickets:
        safe_history = WEAK_EVIDENCE_MESSAGE

    steps = "\n".join(f"- {step}" for step in next_steps) or "- Review available ticket evidence."
    ticket_lines = "\n".join(f"- {ticket}" for ticket in tickets) or "- None"
    return (
        f"Confidence: {confidence:.2f}\n\n"
        f"{REQUIRED_ANSWER_SECTIONS[0]}\n{safe_history}\n\n"
        f"{REQUIRED_ANSWER_SECTIONS[1]}\n{safe_guidance}\n\n"
        f"{REQUIRED_ANSWER_SECTIONS[2]}\n{steps}\n\n"
        f"{REQUIRED_ANSWER_SECTIONS[3]}\n{ticket_lines}"
    )


def has_required_answer_sections(answer: str) -> bool:
    return all(section in answer for section in REQUIRED_ANSWER_SECTIONS)

