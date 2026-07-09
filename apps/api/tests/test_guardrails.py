from app.answer_guardrails import build_guarded_answer, has_required_answer_sections
from app.autotask import AutotaskReadOnlyClient
from app.security import find_sensitive_content, redact_private_entities


def test_answer_format_guardrails_include_required_sections():
    answer = build_guarded_answer(
        ticket_history="Resolved by restarting the print spooler.",
        general_guidance="Check service state and event logs.",
        next_steps=["Verify the service stays running."],
        tickets=["TICKET-1001"],
        confidence=0.87,
    )
    assert has_required_answer_sections(answer)
    assert "Confidence: 0.87" in answer
    assert "TICKET-1001" in answer


def test_weak_ticket_evidence_message_is_used():
    answer = build_guarded_answer("thin match", "general", [], [], 0.2)
    assert "I do not have enough matching CompuOne ticket history." in answer


def test_sensitive_content_scanner_detects_obvious_secrets():
    assert find_sensitive_content("password=Summer2026!")


def test_private_entity_redaction_filters_client_and_people_names():
    text = (
        "Company: California Protons Therapy Center\n"
        "Note Resource: Mike Kirby\n"
        "Suggested Next Steps: Schedule a remote session with Mike Kirby."
    )
    redacted = redact_private_entities(text)
    assert "California Protons Therapy Center" not in redacted
    assert "Mike Kirby" not in redacted
    assert "Company: [CLIENT]" in redacted
    assert "Note Resource: [PERSON]" in redacted
    assert "with [NAME]" in redacted


def test_autotask_write_calls_are_not_enabled():
    client = AutotaskReadOnlyClient()
    for method_name in ("create_ticket", "update_ticket", "delete_ticket"):
        method = getattr(client, method_name)
        try:
            method({})
        except NotImplementedError as exc:
            assert "disabled" in str(exc)
        else:
            raise AssertionError(f"{method_name} should not be implemented")
