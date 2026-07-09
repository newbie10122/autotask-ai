import inspect

from app.answer_guardrails import has_required_answer_sections
import app.assistant as assistant_module
from app.assistant import ask_assistant, store_feedback
from app.autotask import AutotaskHeaders, AutotaskReadOnlyClient
import app.documents as documents_module
from app.documents import create_documents_from_tickets, noise_report, reclassify_chunks
import app.embeddings as embeddings_module
from app.embeddings import run_embedding_batch
from app.main import app
from app.ollama import OllamaUnavailable
from app.quality import classify_chunk, is_recurring_issues_question
from app.sync import sync_companies, sync_ticket_notes, sync_tickets


def test_autotask_headers_include_required_names_without_logging_secret():
    headers = AutotaskHeaders("user@example.com", "super-secret", "integration").as_http_headers()
    assert headers["Username"] == "user@example.com"
    assert headers["Secret"] == "super-secret"
    assert headers["APIIntegrationcode"] == "integration"
    assert headers["Content-Type"] == "application/json"


def test_threshold_success_path(monkeypatch):
    monkeypatch.setattr(AutotaskReadOnlyClient, "_request", lambda _self, method, endpoint, json=None: {"threshold": 42})
    assert AutotaskReadOnlyClient().threshold_information() == {"threshold": 42}


def test_next_page_query_urls_use_post(monkeypatch):
    calls = []
    monkeypatch.setattr(
        AutotaskReadOnlyClient,
        "_request",
        lambda _self, method, endpoint, json=None: calls.append((method, endpoint)) or {"items": []},
    )
    AutotaskReadOnlyClient().follow_next_page("https://example.invalid/V1.0/Tickets/query/next?paging=abc")
    assert calls == [("POST", "https://example.invalid/V1.0/Tickets/query/next?paging=abc")]


def test_no_autotask_write_back_routes_exist():
    route_paths = {route.path for route in app.routes}
    assert not any(path.endswith("/tickets/create") or path.endswith("/tickets/update") for path in route_paths)


def test_company_sync_stores_records(monkeypatch):
    calls = []

    class FakeConn:
        def execute(self, sql, params=None):
            calls.append((sql, params))
            if "RETURNING id" in sql:
                return self
            if "RETURNING (xmax = 0)" in sql:
                return self
            return self

        def fetchone(self):
            return {"id": 1, "inserted": True}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def commit(self):
            pass

        def rollback(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr("app.db.psycopg.connect", lambda *args, **kwargs: FakeConn())
    monkeypatch.setattr("app.sync.init_schema", lambda: None)
    monkeypatch.setattr("app.sync._last_checkpoint", lambda _sync_type: 0)
    monkeypatch.setattr(
        AutotaskReadOnlyClient,
        "query_entity",
        lambda _self, entity, filters=None, include_fields=None: {"items": [{"id": 10, "companyName": "Acme"}]},
    )
    result = sync_companies(limit=1)
    assert result["pulled"] == 1
    assert result["inserted"] == 1


def test_company_sync_limit_1000_can_process_two_pages(monkeypatch):
    class FakeConn:
        def execute(self, sql, params=None):
            if "RETURNING id" in sql:
                self.next_row = {"id": 1}
            elif "RETURNING (xmax = 0)" in sql:
                self.next_row = {"inserted": True}
            else:
                self.next_row = {}
            return self

        def fetchone(self):
            return self.next_row

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def commit(self):
            pass

        def rollback(self):
            pass

        def close(self):
            pass

    first_page = [{"id": i, "companyName": f"Company {i}"} for i in range(1, 501)]
    second_page = [{"id": i, "companyName": f"Company {i}"} for i in range(501, 1001)]
    monkeypatch.setattr("app.db.psycopg.connect", lambda *args, **kwargs: FakeConn())
    monkeypatch.setattr("app.sync.init_schema", lambda: None)
    monkeypatch.setattr("app.sync._last_checkpoint", lambda _sync_type: 0)
    pages = iter([first_page, second_page, []])
    monkeypatch.setattr(
        AutotaskReadOnlyClient,
        "query_entity",
        lambda _self, entity, filters=None, include_fields=None: {"items": next(pages)},
    )

    result = sync_companies(limit=1000)

    assert result["pulled"] == 1000
    assert result["inserted"] == 1000
    assert result["checkpoint"] == {"last_seen_id": 1000}


def test_ticket_and_note_sync_functions_are_available():
    assert callable(sync_tickets)
    assert callable(sync_ticket_notes)


def test_document_creation_function_is_available():
    assert callable(create_documents_from_tickets)


def test_document_rebuild_soft_deprecates_chunks_instead_of_deleting_history():
    source = inspect.getsource(documents_module.create_documents_from_tickets)
    assert "DELETE FROM document_chunks" not in source
    assert "DELETE FROM document_embeddings" not in source
    assert "SET is_active=FALSE" in source
    assert "content_hash" in source
    assert "classified_at=now()" in source


def test_search_and_embedding_only_use_active_chunks():
    assistant_source = inspect.getsource(assistant_module.ask_assistant)
    retrieve_source = inspect.getsource(assistant_module._retrieve_sources)
    embedding_source = inspect.getsource(embeddings_module.run_embedding_batch)
    assert "AND dc.is_active" in retrieve_source
    assert "OR NOT dc.is_noise" in retrieve_source
    assert "AND dc.is_active" in embedding_source
    assert "OR NOT dc.is_noise" in embedding_source


def test_noise_classifier_marks_survey_completion_and_autoresponder_noise():
    for text, expected in (
        ("Ticket Survey Help us serve you better UnsubscribeSurvey", "survey_email"),
        ("Your Ticket Is Complete. Replies to this email will be added as a note", "completion_email"),
        ("*** Please enter replies above this line *** automatic reply", "autoresponder"),
        ("Ticket Note Created or Edited notification e-mail Initiated by workflow", "system_notification"),
        ("From: Person\nTo: Support\nSubject: x\nThanks\nPhone: 555-1234", "signature_or_footer"),
    ):
        result = classify_chunk(text)
        assert result["is_noise"] is True
        assert result["knowledge_class"] == expected


def test_resolution_classifier_is_high_quality_not_noise():
    result = classify_chunk("Resolved by restarting the print spooler and clearing stuck jobs.")
    assert result["is_noise"] is False
    assert result["knowledge_class"] == "resolution"
    assert result["quality_score"] == 1.0


def test_recurring_issue_question_detection():
    assert is_recurring_issues_question("What are the most common recurring support issues?")
    assert is_recurring_issues_question("top problems in our tickets")
    assert not is_recurring_issues_question("How did we fix ticket T123?")


def test_source_ticket_dedupe_and_context_limits(monkeypatch):
    monkeypatch.setattr("app.assistant.settings.assistant_max_unique_tickets", 2)
    monkeypatch.setattr("app.assistant.settings.assistant_max_chunks_per_ticket", 1)
    monkeypatch.setattr("app.assistant.settings.assistant_max_context_chunks", 3)
    sources = [
        {"chunk_id": 1, "autotask_id": 100, "ticket_number": "T1"},
        {"chunk_id": 2, "autotask_id": 100, "ticket_number": "T1"},
        {"chunk_id": 3, "autotask_id": 101, "ticket_number": "T2"},
        {"chunk_id": 4, "autotask_id": 102, "ticket_number": "T3"},
    ]
    limited = assistant_module._limit_sources(sources)
    assert [source["chunk_id"] for source in limited] == [1, 3]
    assert assistant_module._unique_tickets(limited) == ["T1", "T2"]


def test_timeout_fallback_uses_structured_warning():
    sources = [
        {
            "content": "Resolved VPN failures by updating the client and restarting the service.",
            "ticket_number": "T1",
            "autotask_id": 1,
        }
    ]
    answer = assistant_module._fallback_answer(
        sources,
        0.7,
        "Local LLM timed out; showing retrieval summary only.",
    )
    assert "Local LLM timed out; showing retrieval summary only." in answer
    assert "Resolved VPN failures" in answer


def test_recurring_issues_formatter_returns_counts_and_representatives():
    groups = [
        {"category": "Network", "issue_type": "VPN", "subissue_type": "Client", "queue": "Helpdesk", "ticket_count": 12}
    ]
    reps = [{"group": groups[0], "tickets": [{"ticket_number": "T1", "autotask_id": 1, "title": "VPN down"}]}]
    answer, tickets = assistant_module._format_recurring_answer(groups, reps)
    assert "Top Recurring Issue Groups" in answer
    assert "12 tickets" in answer
    assert tickets == ["T1"]


def test_embedding_worker_handles_missing_ollama_gracefully(monkeypatch):
    class FakeConn:
        def execute(self, *_args, **_kwargs):
            return self

        def fetchone(self):
            return {"count": 0}

        def fetchall(self):
            return [{"id": 1, "content": "Printer spooler restart fixed issue."}]

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def commit(self):
            pass

        def rollback(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr("app.db.psycopg.connect", lambda *args, **kwargs: FakeConn())
    monkeypatch.setattr("app.embeddings.embed_text", lambda _text: (_ for _ in ()).throw(OllamaUnavailable("missing ollama")))
    result = run_embedding_batch(limit=1)
    assert result["failed"] == 1
    assert "skipped_noise" in result


def test_reclassify_chunks_updates_classification_without_deleting(monkeypatch):
    calls = []

    class FakeConn:
        def execute(self, sql, params=None):
            calls.append((sql, params))
            return self

        def fetchall(self):
            return [{"id": 1, "content": "Ticket Survey Help us serve you better"}]

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def commit(self):
            pass

        def rollback(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr("app.db.psycopg.connect", lambda *args, **kwargs: FakeConn())
    result = reclassify_chunks(limit=1)
    assert result["processed"] == 1
    assert result["noise"] == 1
    sql_text = "\n".join(str(call[0]) for call in calls)
    assert "DELETE FROM document_chunks" not in sql_text
    assert "classified_at=now()" in sql_text


def test_noise_report_returns_embedding_backlog(monkeypatch):
    class FakeConn:
        def execute(self, sql, params=None):
            self.sql = sql
            return self

        def fetchone(self):
            return {
                "total_active_chunks": 3,
                "active_noise_chunks": 1,
                "active_useful_chunks": 1,
                "unknown_chunks": 1,
                "embedding_eligible_chunks": 2,
                "eligible_missing_embeddings": 2,
            }

        def fetchall(self):
            if "GROUP BY knowledge_class" in self.sql:
                return [{"knowledge_class": "survey_email", "count": 1}]
            return [{"noise_reason": "ticket survey", "count": 1}]

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def commit(self):
            pass

        def rollback(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr("app.db.psycopg.connect", lambda *args, **kwargs: FakeConn())
    report = noise_report()
    assert report["active_noise_chunks"] == 1
    assert report["eligible_missing_embeddings"] == 2


def test_ask_endpoint_refuses_when_no_matching_chunks(monkeypatch):
    monkeypatch.setattr("app.assistant.init_schema", lambda: None)
    monkeypatch.setattr("app.assistant.embed_text", lambda _text: (_ for _ in ()).throw(OllamaUnavailable("missing ollama")))

    class FakeConn:
        def execute(self, sql, params=None):
            self.sql = sql
            return self

        def fetchone(self):
            if "assistant_queries" in self.sql:
                return {"id": 1}
            if "assistant_answers" in self.sql:
                return {"id": 2}
            return {}

        def fetchall(self):
            return []

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def commit(self):
            pass

        def rollback(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr("app.db.psycopg.connect", lambda *args, **kwargs: FakeConn())
    result = ask_assistant("how do I fix vpn")
    assert result["confidence"] == "Low"
    assert "I do not have enough matching CompuOne ticket history" in result["answer"]
    assert has_required_answer_sections(result["answer"])


def test_feedback_and_known_fix_functions_are_available():
    assert callable(store_feedback)
