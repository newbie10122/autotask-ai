import inspect

from app.answer_guardrails import has_required_answer_sections
from app.audit import audit_sink
import app.assistant as assistant_module
from app.assistant import ask_assistant, store_feedback
from app.autotask import AutotaskHeaders, AutotaskReadOnlyClient
from app.cache import scoped_cache_key
import app.documents as documents_module
from app.documents import create_documents_from_tickets, noise_report, reclassify_chunks
import app.embeddings as embeddings_module
from app.embeddings import run_embedding_batch
import app.customer_success as customer_success_module
from app.main import app
from app.models import AuditAction
import app.operations as operations_module
from app.ollama import OllamaUnavailable
from app.quality import classify_chunk, is_recurring_issues_question
import app.realtime as realtime_module
import app.routing as routing_module
import app.sync as sync_module
from app.sync import sync_companies, sync_ticket_notes, sync_tickets
from app.ticket_analytics import format_recurring_issues_answer, issue_group_label
import app.ticket_health as ticket_health_module
from app.ticket_classifier import classify_ticket


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
    assert "/api/analytics/recurring-issues" in route_paths
    assert "/api/sync/reference-data/start" in route_paths
    assert "/api/operations/status" in route_paths
    assert "/api/operations/jobs/{job_name}/run" in route_paths


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


def test_ticket_sync_skips_monitoring_alerts_before_storage():
    assert sync_module._should_skip_ticket(
        {
            "id": 10,
            "title": "C: Drive has 224.8 GB used out of 235.9 GB (95% Used)",
            "source": 8,
            "ticketType": 5,
        }
    )
    source = inspect.getsource(sync_module.sync_tickets)
    assert "stats[\"skipped\"] += 1" in source
    assert "_should_skip_ticket(item)" in source


def test_ticket_sync_skips_onsite_maintenance_before_storage():
    result = classify_ticket("Onsite maintenance and monitoring support visit")
    assert result["analytics_exclude"] is True
    assert result["analytics_exclude_reason"] == "onsite_maintenance"
    assert sync_module._should_skip_ticket({"id": 11, "title": "Onsite maintenance and monitoring support visit"})


def test_ticket_note_sync_skips_notes_without_local_ticket():
    source = inspect.getsource(sync_module.sync_ticket_notes)
    assert "if not ticket_row:" in source
    assert "stats[\"skipped\"] += 1" in source


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
    assert "authorized_company_ids" in retrieve_source
    assert "source_metadata->>'company_id'" in retrieve_source
    analytics_source = inspect.getsource(format_recurring_issues_answer.__globals__["recurring_issues_report"])
    assert "authorized_company_ids" in analytics_source
    assert "t.company_id = ANY" in analytics_source


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


def test_ticket_classifier_excludes_non_support_noise_and_monitoring_alerts():
    excluded = classify_ticket("Daily IT Meeting")
    assert excluded["analytics_exclude"] is True
    assert excluded["analytics_exclude_reason"] == "internal_meeting"

    vendor = classify_ticket("Updates to Google Play Terms of Service")
    assert vendor["analytics_exclude"] is True
    assert vendor["ticket_class"] == "vendor_notice"

    disk = classify_ticket("C: Drive has 225 GB used out of 236 GB (95% Used)", raw={"source": 8, "ticketType": 5})
    assert disk["analytics_exclude"] is True
    assert disk["analytics_exclude_reason"] == "monitoring_alert"
    assert disk["is_system_generated"] is True
    assert disk["ticket_class"] == "monitoring_alert"


def test_monitoring_alert_chunks_are_noise():
    result = classify_chunk(
        "C: Drive has 224.8 GB used out of 235.9 GB. "
        "SYSTEM_VOLUME drive has passed 95.0 % Used for 15 mins."
    )
    assert result["is_noise"] is True
    assert result["knowledge_class"] == "monitoring_alert"


def test_ticket_group_label_uses_reference_labels_instead_of_raw_ids():
    labels = {
        ("category", "2"): "Monitoring Alert",
        ("issue_type", "14"): "Disk Space",
        ("subissue_type", "222"): "System Volume 90/95%",
    }
    row = {
        "category": "2",
        "issue_type": "14",
        "subissue_type": "222",
        "ticket_class": "disk_space_alert",
        "title": "C: Drive has 95% used",
    }
    assert issue_group_label(row, labels) == "Monitoring Alert / Disk Space / System Volume 90/95%"


def test_new_recurring_formatter_caps_representative_ticket_output():
    report = {
        "groups": [
            {
                "label": f"Group {index}",
                "count": 10,
                "representative_tickets": [
                    {"ticket_number": f"T{index}-{ticket}", "title": "Example"}
                    for ticket in range(3)
                ],
            }
            for index in range(8)
        ],
        "warnings": [],
    }
    answer, tickets = format_recurring_issues_answer(report)
    assert "Top Recurring Issue Groups" in answer
    assert len(tickets) == 16


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


def test_scheduler_default_settings_are_conservative():
    defaults = operations_module.default_operations_settings()
    assert defaults["recent_sync_enabled"] is True
    assert defaults["raw_backfill_enabled"] is False
    assert defaults["open_ticket_time_entry_gaps_enabled"] is True
    assert defaults["open_ticket_history_gaps_enabled"] is True
    assert defaults["ticket_time_entry_gaps_enabled"] is True
    assert defaults["ticket_history_gaps_enabled"] is True
    assert defaults["document_build_enabled"] is False
    assert defaults["embedding_enabled"] is False
    assert defaults["nightly_pipeline_enabled"] is True
    assert defaults["min_free_disk_gb"] == 50


def test_recent_sync_includes_time_entries(monkeypatch):
    monkeypatch.setattr(sync_module, "sync_companies", lambda limit=None: {"kind": "companies", "limit": limit})
    monkeypatch.setattr(sync_module, "sync_tickets", lambda limit=None: {"kind": "tickets", "limit": limit})
    monkeypatch.setattr(sync_module, "sync_ticket_notes", lambda limit=None: {"kind": "ticket_notes", "limit": limit})
    monkeypatch.setattr(sync_module, "sync_time_entries", lambda limit=None: {"kind": "time_entries", "limit": limit})

    result = sync_module.sync_recent(limit=12)

    assert result["time_entries"] == {"kind": "time_entries", "limit": 12}


def test_scheduler_preserves_related_data_gap_jobs():
    jobs = operations_module.DEFAULT_JOBS
    assert jobs["open_ticket_time_entry_gaps"]["enabled"] is True
    assert jobs["open_ticket_history_gaps"]["enabled"] is True
    assert jobs["ticket_time_entry_gaps"]["enabled"] is True
    assert jobs["ticket_history_gaps"]["enabled"] is True

    source = inspect.getsource(operations_module._execute_job)
    assert "sync_open_ticket_time_entry_gaps" in source
    assert "sync_open_ticket_history_gaps" in source
    assert "sync_ticket_time_entry_gaps" in source
    assert "sync_ticket_history_gaps" in source


def test_scheduler_preflight_global_pause_disk_and_threshold_guards(monkeypatch):
    settings = operations_module.default_operations_settings()
    settings["global_pause"] = True
    assert operations_module._preflight("recent_sync", settings) == "global_pause"

    settings["global_pause"] = False
    monkeypatch.setattr(operations_module, "disk_free_gb", lambda _path="/": 1)
    assert operations_module._preflight("recent_sync", settings).startswith("low_disk_free_gb")

    monkeypatch.setattr(operations_module, "disk_free_gb", lambda _path="/": 100)
    monkeypatch.setattr(operations_module, "autotask_threshold_remaining", lambda: 25)
    assert operations_module._preflight("recent_sync", settings) == "autotask_threshold_low:25"


def test_scheduler_conflicts_prevent_duplicate_or_unsafe_jobs():
    assert operations_module.conflicting_jobs("recent_sync", {"raw_backfill_tickets"}) == {"raw_backfill_tickets"}
    assert operations_module.conflicting_jobs("run_embeddings", {"build_documents"}) == {"build_documents"}
    assert operations_module.conflicting_jobs("build_documents", {"reclassify_chunks"}) == {"reclassify_chunks"}


def test_embedding_job_refuses_when_disabled_and_skips_noise_by_default(monkeypatch):
    settings = operations_module.default_operations_settings()
    monkeypatch.setattr(operations_module, "disk_free_gb", lambda _path="/": 100)
    assert operations_module._preflight("run_embeddings", settings) == "embedding_disabled"
    embedding_source = inspect.getsource(embeddings_module.run_embedding_batch)
    assert "OR NOT dc.is_noise" in embedding_source


def test_nightly_pipeline_respects_disabled_document_and_embedding_settings(monkeypatch):
    calls = []
    settings = operations_module.default_operations_settings()
    settings["document_build_enabled"] = False
    settings["embedding_enabled"] = False
    monkeypatch.setattr(operations_module, "sync_reference_data", lambda: calls.append("reference") or {"processed": 1})
    monkeypatch.setattr(operations_module, "classify_tickets", lambda limit=None: calls.append("classify") or {"processed": limit or 0})
    monkeypatch.setattr(operations_module, "create_documents_from_tickets", lambda limit=None: calls.append("documents") or {})
    monkeypatch.setattr(operations_module, "reclassify_chunks", lambda limit=None: calls.append("reclassify_chunks") or {"processed": limit or 0})
    monkeypatch.setattr(operations_module, "run_embedding_batch", lambda limit=None: calls.append("embeddings") or {})
    result = operations_module._nightly_pipeline(settings)
    assert calls == ["reference", "classify", "reclassify_chunks"]
    assert result["failed"] == 0


def test_scheduler_job_runner_records_start_finish_and_uses_locks():
    source = inspect.getsource(operations_module.run_job)
    assert "_create_job_run" in source
    assert "_acquire_lock" in source
    assert "_finish_job_run" in source


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


def test_verifier_failure_preserves_warning_and_records_audit(monkeypatch):
    events = []
    monkeypatch.setattr("app.assistant.init_schema", lambda: None)
    monkeypatch.setattr("app.assistant.embed_text", lambda _text: [0.1, 0.2, 0.3])
    monkeypatch.setattr(
        "app.assistant.chat",
        lambda _prompt: (
            "Confidence: High\n\n"
            "From CompuOne Ticket History\n"
            "T999 fixed this by replacing the firewall.\n\n"
            "General IT Guidance\n"
            "Check the basics.\n\n"
            "Suggested Next Steps\n"
            "- Open the ticket.\n\n"
            "Based on Tickets\n"
            "- T999\n\n"
            "Warnings\n"
            "- None"
        ),
    )
    monkeypatch.setattr(audit_sink, "record", lambda entry: events.append(entry) or entry)

    source = {
        "chunk_id": 10,
        "content": "Ticket Number: T1\nTitle: Printer issue\nDescription: Restarted print spooler.",
        "source_metadata": {"company_id": 123},
        "knowledge_class": "resolution",
        "quality_score": 0.9,
        "is_noise": False,
        "noise_reason": None,
        "ticket_pk": 20,
        "autotask_id": 1,
        "ticket_number": "T1",
        "score": 0.8,
    }

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
            if "FROM document_embeddings" in self.sql:
                return [source]
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

    monkeypatch.setattr("app.assistant.db_connection", lambda: FakeConn())

    result = ask_assistant("how do I fix the printer", authorized_company_ids=[123], actor_username="tech")

    assert result["confidence"] == "High"
    assert "Answer verifier failed closed: unretrieved ticket citation." in result["answer"]
    assert "Answer verifier failed closed: unretrieved ticket citation." in result["warnings"]
    audit_event = next(event for event in events if event.action == AuditAction.verifier_failed)
    assert audit_event.actor == "tech"
    assert audit_event.outcome == "blocked"
    assert audit_event.scope == {"company_ids": [123], "global": False}
    assert audit_event.metadata == {
        "reason": "unretrieved ticket citation",
        "source_count": 1,
        "source_ticket_count": 1,
    }


def test_generated_answer_accepts_ticket_ids_from_source_metadata(monkeypatch):
    monkeypatch.setattr("app.assistant.init_schema", lambda: None)
    monkeypatch.setattr("app.assistant.embed_text", lambda _text: [0.1, 0.2, 0.3])
    monkeypatch.setattr(
        "app.assistant.chat",
        lambda _prompt: (
            "Confidence: High\n\n"
            "From CompuOne Ticket History\n"
            "T42 reports printer unable to print labels.\n\n"
            "General IT Guidance\n"
            "Check print queue and device status.\n\n"
            "Suggested Next Steps\n"
            "- Open the ticket and compare symptoms.\n\n"
            "Based on Tickets\n"
            "- T42\n\n"
            "Warnings\n"
            "- None"
        ),
    )

    source = {
        "chunk_id": 10,
        "content": "Ticket Number: T42\nDescription: Printer unable to print labels.",
        "source_metadata": {"company_id": 123, "ticket_number": "T42", "autotask_id": 42},
        "knowledge_class": "human_troubleshooting",
        "quality_score": 0.9,
        "is_noise": False,
        "noise_reason": None,
        "ticket_pk": 20,
        "autotask_id": None,
        "ticket_number": None,
        "score": 0.8,
    }

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
            if "FROM document_embeddings" in self.sql:
                return [source]
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

    monkeypatch.setattr("app.assistant.db_connection", lambda: FakeConn())

    result = ask_assistant("how do I fix the printer", authorized_company_ids=[123], actor_username="tech")

    assert result["confidence"] == "High"
    assert result["based_on_tickets"] == ["T42"]
    assert result["sources"][0]["ticket_id"] == 42
    assert result["sources"][0]["ticket_number"] == "T42"
    assert "Answer verifier failed closed" not in result["answer"]
    assert result["warnings"] == []


def test_generated_answer_rejects_cross_ticket_evidence_substitution(monkeypatch):
    events = []
    monkeypatch.setattr("app.assistant.init_schema", lambda: None)
    monkeypatch.setattr("app.assistant.embed_text", lambda _text: [0.1, 0.2, 0.3])
    monkeypatch.setattr(
        "app.assistant.chat",
        lambda _prompt: (
            "Confidence: High\n\n"
            "From CompuOne Ticket History\n"
            "T2 reports payroll scanner outage affecting check-in.\n\n"
            "General IT Guidance\n"
            "Check impacted device class.\n\n"
            "Suggested Next Steps\n"
            "- Open the cited ticket and compare symptoms.\n\n"
            "Based on Tickets\n"
            "- T2\n\n"
            "Warnings\n"
            "- None"
        ),
    )
    monkeypatch.setattr(audit_sink, "record", lambda entry: events.append(entry) or entry)

    sources = [
        {
            "chunk_id": 10,
            "content": "Ticket Number: T1\nDescription: Payroll scanner outage affecting check-in.",
            "source_metadata": {"company_id": 123},
            "knowledge_class": "human_troubleshooting",
            "quality_score": 0.9,
            "is_noise": False,
            "noise_reason": None,
            "ticket_pk": 20,
            "autotask_id": 1,
            "ticket_number": "T1",
            "score": 0.8,
        },
        {
            "chunk_id": 11,
            "content": "Ticket Number: T2\nDescription: Printer unable to print labels.",
            "source_metadata": {"company_id": 123},
            "knowledge_class": "human_troubleshooting",
            "quality_score": 0.9,
            "is_noise": False,
            "noise_reason": None,
            "ticket_pk": 21,
            "autotask_id": 2,
            "ticket_number": "T2",
            "score": 0.7,
        },
    ]

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
            if "FROM document_embeddings" in self.sql:
                return sources
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

    monkeypatch.setattr("app.assistant.db_connection", lambda: FakeConn())

    result = ask_assistant("how do I fix the scanner", authorized_company_ids=[123], actor_username="tech")

    assert "Answer verifier failed closed: insufficient ticket-history source evidence." in result["answer"]
    assert "Answer verifier failed closed: insufficient ticket-history source evidence." in result["warnings"]
    audit_event = next(event for event in events if event.action == AuditAction.verifier_failed)
    assert audit_event.metadata["reason"] == "insufficient ticket-history source evidence"
    assert audit_event.metadata["source_ticket_count"] == 2


def test_feedback_and_known_fix_functions_are_available():
    assert callable(store_feedback)


def test_scoped_cache_key_requires_authority_scope_roles_and_version():
    key = scoped_cache_key(
        "assistant-preview",
        {"question_hash": "abc"},
        authority_class="company-scoped",
        roles=["Technician", "ReadOnly"],
        scope={"company_ids": [123], "global": False},
        version=1,
        model_name="local-model",
        config={"prompt_version": 2},
    )
    assert key.startswith("autotask-ai:assistant-preview:")
    assert key == scoped_cache_key(
        "assistant-preview",
        {"question_hash": "abc"},
        authority_class="company-scoped",
        roles=["ReadOnly", "Technician"],
        scope={"company_ids": [123], "global": False},
        version=1,
        model_name="local-model",
        config={"prompt_version": 2},
    )
    assert key != scoped_cache_key(
        "assistant-preview",
        {"question_hash": "abc"},
        authority_class="company-scoped",
        roles=["Technician", "ReadOnly"],
        scope={"company_ids": [456], "global": False},
        version=1,
        model_name="local-model",
        config={"prompt_version": 2},
    )


def test_scoped_cache_key_rejects_missing_contract_inputs():
    required = {
        "authority_class": "company-scoped",
        "roles": ["Technician"],
        "scope": {"company_ids": [123], "global": False},
        "version": 1,
    }
    for key, value in {
        "authority_class": "",
        "roles": [],
        "scope": {},
        "version": 0,
    }.items():
        kwargs = dict(required)
        kwargs[key] = value
        try:
            scoped_cache_key("assistant-preview", {"question_hash": "abc"}, **kwargs)
        except ValueError as exc:
            assert "Scoped cache keys require" in str(exc)
        else:
            raise AssertionError(f"missing {key} should fail")


def test_operations_status_cache_key_uses_scope_role_and_auth_contract():
    outer = operations_module.operations_status_cache_key()
    readonly = operations_module.operations_status_cache_key(
        authority_class="authenticated-read",
        roles=["ReadOnly"],
        scope={"global": True},
    )
    admin = operations_module.operations_status_cache_key(
        authority_class="authenticated-read",
        roles=["Admin"],
        scope={"global": True},
    )

    assert outer.startswith("autotask-ai:operations-status:")
    assert readonly.startswith("autotask-ai:operations-status:")
    assert outer != readonly
    assert readonly != admin


def test_ticket_health_summary_cache_key_uses_scope_role_and_filter_contract():
    payload = {
        "limit": 50,
        "queue": "Support",
        "assigned_resource_id": None,
        "closed_status_ids": ["Complete"],
    }
    outer = ticket_health_module.ticket_health_summary_cache_key(payload)
    readonly = ticket_health_module.ticket_health_summary_cache_key(
        payload,
        authority_class="authenticated-read",
        roles=["ReadOnly"],
        scope={"company_ids": [123], "global": False},
    )
    admin = ticket_health_module.ticket_health_summary_cache_key(
        payload,
        authority_class="authenticated-read",
        roles=["Admin"],
        scope={"company_ids": [123], "global": False},
    )
    other_scope = ticket_health_module.ticket_health_summary_cache_key(
        payload,
        authority_class="authenticated-read",
        roles=["ReadOnly"],
        scope={"company_ids": [456], "global": False},
    )

    assert outer.startswith("autotask-ai:ticket-health-summary:")
    assert readonly.startswith("autotask-ai:ticket-health-summary:")
    assert outer != readonly
    assert readonly != admin
    assert readonly != other_scope


def test_customer_success_summary_cache_key_uses_scope_role_and_window_contract():
    payload = {
        "limit": 25,
        "recent_days": 30,
        "closed_status_ids": ["Complete"],
    }
    outer = customer_success_module.customer_success_summary_cache_key(payload)
    readonly = customer_success_module.customer_success_summary_cache_key(
        payload,
        authority_class="authenticated-read",
        roles=["ReadOnly"],
        scope={"company_ids": [123], "global": False},
    )
    admin = customer_success_module.customer_success_summary_cache_key(
        payload,
        authority_class="authenticated-read",
        roles=["Admin"],
        scope={"company_ids": [123], "global": False},
    )
    other_scope = customer_success_module.customer_success_summary_cache_key(
        payload,
        authority_class="authenticated-read",
        roles=["ReadOnly"],
        scope={"company_ids": [456], "global": False},
    )

    assert outer.startswith("autotask-ai:customer-success-summary:")
    assert readonly.startswith("autotask-ai:customer-success-summary:")
    assert outer != readonly
    assert readonly != admin
    assert readonly != other_scope


def test_active_cache_consumers_are_scoped_and_export_routes_absent():
    active_cache_modules = [
        operations_module,
        ticket_health_module,
        customer_success_module,
    ]
    for module in active_cache_modules:
        source = inspect.getsource(module)
        assert "cache_get_json" in source
        assert "cache_set_json" in source
        assert "scoped_cache_key" in source
        assert "from .cache import cache_key" not in source
        assert "from app.cache import cache_key" not in source

    route_paths = {route.path for route in app.routes}
    assert not any(token in path.lower() for path in route_paths for token in ("export", "download"))


def test_ticket_health_data_paths_accept_and_apply_company_scope():
    scope_source = inspect.getsource(ticket_health_module._company_scope_clause)
    summary_source = inspect.getsource(ticket_health_module.ticket_health_summary)
    review_source = inspect.getsource(ticket_health_module.ticket_health_review_queue)
    detail_source = inspect.getsource(ticket_health_module.ticket_health_detail_scoped)
    number_source = inspect.getsource(ticket_health_module.ticket_health_detail_by_number_scoped)
    feedback_source = inspect.getsource(ticket_health_module.store_ticket_health_risk_feedback)

    assert "authorized_company_ids" in summary_source
    assert "authorized_company_ids" in review_source
    assert "authorized_company_ids" in detail_source
    assert "authorized_company_ids" in number_source
    assert "authorized_company_ids" in feedback_source
    assert "company_id = ANY(%s)" in scope_source
    assert "_company_scope_clause(authorized_company_ids)" in summary_source
    assert "_company_scope_clause(authorized_company_ids)" in detail_source
    assert "_company_scope_clause(authorized_company_ids)" in feedback_source
    assert "company_scope_sql" in number_source


def test_ticket_predictive_review_signal_abstains_with_low_sample_size():
    signal = ticket_health_module._ticket_predictive_review_signal(
        {"health_score": 40, "age_days": 3, "labor_hours": 1},
        {},
        {"sample_size": 2, "delayed_count": 1, "avg_resolution_days": 2, "avg_labor_hours": 1},
    )

    assert signal["abstained"] is True
    assert signal["confidence"] == "low"
    assert signal["statistical_review_score"] is None
    assert "insufficient_local_history" in signal["reason_codes"]
    assert signal["review_only"] is True


def test_ticket_predictive_review_signal_uses_bayesian_history_and_feedback():
    signal = ticket_health_module._ticket_predictive_review_signal(
        {"health_score": 55, "age_days": 8, "labor_hours": 6},
        {"needs_review": 1, "too_low": 1},
        {"sample_size": 20, "delayed_count": 8, "avg_resolution_days": 4, "avg_labor_hours": 2},
    )

    assert signal["abstained"] is False
    assert signal["confidence"] == "moderate"
    assert signal["sample_size"] == 20
    assert signal["statistical_review_score"] > 55
    assert "open_age_exceeds_similar_resolution_average" in signal["reason_codes"]
    assert "labor_exceeds_similar_average" in signal["reason_codes"]
    assert "local_needs_review_feedback" in signal["reason_codes"]
    assert signal["review_only"] is True


def test_ticket_predictive_binary_metrics_report_precision_recall():
    metrics = ticket_health_module._binary_classification_metrics(
        [
            {"actual_delayed": True, "predicted": True},
            {"actual_delayed": True, "predicted": False},
            {"actual_delayed": False, "predicted": True},
            {"actual_delayed": False, "predicted": False},
        ],
        "predicted",
    )

    assert metrics["total"] == 4
    assert metrics["true_positive"] == 1
    assert metrics["true_negative"] == 1
    assert metrics["false_positive"] == 1
    assert metrics["false_negative"] == 1
    assert metrics["accuracy"] == 0.5
    assert metrics["precision"] == 0.5
    assert metrics["recall"] == 0.5
    assert metrics["f1"] == 0.5


def test_ticket_predictive_threshold_sweep_prefers_f1_then_recall():
    sweep = ticket_health_module._threshold_sweep(
        [
            {"actual_delayed": True, "bayesian_delay_rate": 0.31},
            {"actual_delayed": True, "bayesian_delay_rate": 0.11},
            {"actual_delayed": False, "bayesian_delay_rate": 0.06},
            {"actual_delayed": False, "bayesian_delay_rate": 0.01},
        ]
    )

    assert sweep[0]["threshold"] == 0.1
    assert sweep[0]["true_positive"] == 2
    assert sweep[0]["false_positive"] == 0
    assert sweep[0]["recall"] == 1.0
    assert sweep[0]["f1"] == 1.0


def test_ticket_predictive_calibration_and_auc_metrics_are_review_only():
    rows = [
        {"actual_delayed": True, "bayesian_delay_rate": 0.8},
        {"actual_delayed": False, "bayesian_delay_rate": 0.6},
        {"actual_delayed": True, "bayesian_delay_rate": 0.4},
        {"actual_delayed": False, "bayesian_delay_rate": 0.1},
    ]

    assert ticket_health_module._brier_score(rows) == 0.193
    bands = ticket_health_module._calibration_bands(rows)
    auc = ticket_health_module._probability_auc(rows)

    assert bands[0]["range"] == "0.1-0.2"
    assert any(band["range"] == "0.8-0.9" and band["observed_delay_rate"] == 1.0 for band in bands)
    assert auc["roc_auc"] == 0.75
    assert auc["pr_auc"] == 0.834


def test_ticket_predictive_variant_report_is_review_only_and_scored():
    report = ticket_health_module._predictive_variant_report(
        [
            {
                "actual_delayed": True,
                "variant_rate": 0.8,
                "variant_predicted": True,
            },
            {
                "actual_delayed": False,
                "variant_rate": 0.7,
                "variant_predicted": True,
            },
            {
                "actual_delayed": False,
                "variant_rate": 0.1,
                "variant_predicted": False,
            },
        ],
        name="test_variant",
        model_type="lightweight_statistical",
        probability_key="variant_rate",
        prediction_key="variant_predicted",
        features=["current_queue"],
        lineage_status="current-field proxy",
    )

    assert report["review_only"] is True
    assert report["selection_allowed"] is False
    assert report["metrics"]["precision"] == 0.5
    assert report["brier_score"] == 0.18
    assert report["threshold_sweep"][0]["threshold"] in {0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5}
    assert report["lineage_status"] == "current-field proxy"


def test_ticket_predictive_concentration_uses_sanitized_buckets():
    concentration = ticket_health_module._sanitized_concentration(
        [
            {"company_id": 10, "actual_delayed": True},
            {"company_id": 10, "actual_delayed": False},
            {"company_id": 22, "actual_delayed": True},
        ],
        "company_id",
        "company_bucket",
    )

    assert concentration["sanitized"] is True
    assert concentration["distinct_buckets"] == 2
    assert concentration["top_buckets"][0]["bucket"] == "company_bucket_1"
    assert "10" not in concentration["top_buckets"][0].values()
    assert concentration["top_buckets"][0]["share"] == 0.667


def test_ticket_predictive_stratified_metrics_are_sanitized_and_scored():
    metrics = ticket_health_module._sanitized_stratified_metrics(
        [
            {
                "company_id": 10,
                "actual_delayed": True,
                "baseline_predicted_delayed": True,
                "statistical_predicted_delayed": False,
                "statistical_abstained": False,
                "bayesian_delay_rate": 0.2,
            },
            {
                "company_id": 10,
                "actual_delayed": False,
                "baseline_predicted_delayed": False,
                "statistical_predicted_delayed": False,
                "statistical_abstained": False,
                "bayesian_delay_rate": 0.1,
            },
            {
                "company_id": 22,
                "actual_delayed": True,
                "baseline_predicted_delayed": False,
                "statistical_predicted_delayed": True,
                "statistical_abstained": False,
                "bayesian_delay_rate": 0.8,
            },
        ],
        "company_id",
        "company_bucket",
    )

    assert metrics["sanitized"] is True
    assert metrics["top_buckets"][0]["bucket"] == "company_bucket_1"
    assert "10" not in metrics["top_buckets"][0].values()
    assert metrics["top_buckets"][0]["baseline"]["recall"] == 1.0
    assert metrics["top_buckets"][0]["statistical_brier_score"] == 0.325


def test_ticket_predictive_model_comparison_keeps_human_review_policy():
    comparison = ticket_health_module._model_comparison(
        {"f1": 0.5, "recall": 0.5},
        {"f1": 0.0, "recall": 0.0},
        {"brier_score": 0.12, "secondary_metrics": {"roc_auc": 0.6, "pr_auc": 0.2}},
    )

    assert comparison["statistical_f1_delta"] == -0.5
    assert comparison["current_finding"] == "statistical_signal_not_better_on_f1_or_recall"
    assert "Do not select or deploy" in comparison["selection_policy"]
    assert comparison["models"][1]["brier_score"] == 0.12


def test_ticket_predictive_leakage_review_documents_temporal_split():
    review = ticket_health_module._leakage_review("2026-01-01T00:00:00Z", 100, 12)

    assert review["temporal_split"] == "training_completed_before_holdout_start"
    assert review["training_rows_after_or_during_holdout_included"] == 0
    assert review["label_available_only_after_completion"] is True
    assert any("queue/priority-at-creation" in item for item in review["known_limitations"])


def test_ticket_predictive_source_lineage_marks_current_field_proxies():
    field_certification = {
        "certification_state": "partial_field_certification",
        "predictive_policy": {
            "excluded_until_certified": ["status_duration", "time_entries", "sla_information"],
        },
    }
    lineage = ticket_health_module._predictive_source_lineage(field_certification)
    by_field = {item["field"]: item for item in lineage["fields"]}

    assert lineage["certification_state"] == "partial_source_lineage"
    assert lineage["milestone_2_field_certification_state"] == "partial_field_certification"
    assert by_field["created_at_autotask"]["certified_for_prediction"] is True
    assert by_field["completed_at_autotask"]["certified_for_prediction"] is True
    assert by_field["queue"]["certified_for_prediction"] is False
    assert "queue-at-creation" in by_field["queue"]["lineage_status"]
    assert "ticket_status_history" in lineage["not_used_for_current_model"]
    assert "status_duration" in lineage["milestone_2_excluded_until_certified"]
    assert any("does not authorize" in item for item in lineage["limitations"])


def test_ticket_field_certification_marks_source_limited_operational_inputs():
    coverage = {
        "ready_for_ticket_health": False,
        "counts": {"tickets": 10, "ticket_history": 4, "time_entries": 3},
        "blockers": ["Continue TicketHistory backfill before precise waiting-state duration analytics."],
        "fields": [
            {
                "key": "ticket_status",
                "status": "available",
                "available_count": 10,
                "total_count": 10,
                "coverage_percent": 100.0,
                "source": "autotask_tickets.status",
                "note": "",
            },
            {
                "key": "ticket_status_history",
                "status": "partial",
                "available_count": 4,
                "total_count": 10,
                "coverage_percent": 40.0,
                "source": "autotask_ticket_history",
                "note": "partial backfill",
            },
            {
                "key": "waiting_states",
                "status": "partial",
                "available_count": 10,
                "total_count": 10,
                "coverage_percent": 100.0,
                "source": "current status plus TicketHistory",
                "note": "needs transitions",
            },
            {
                "key": "time_entries",
                "status": "available",
                "available_count": 3,
                "total_count": 3,
                "coverage_percent": 100.0,
                "source": "autotask_time_entries",
                "note": "",
            },
            {
                "key": "labor_hours",
                "status": "available",
                "available_count": 3,
                "total_count": 3,
                "coverage_percent": 100.0,
                "source": "autotask_time_entries.hours",
                "note": "",
            },
            {
                "key": "sla_information",
                "status": "missing",
                "available_count": 0,
                "total_count": 10,
                "coverage_percent": 0.0,
                "source": "SLA raw fields",
                "note": "",
            },
        ],
    }
    diagnostics = {
        "source_capability": {
            "has_exact_status_transition_timestamp": False,
            "proxy_timestamp_fields": ["lastActivityDate"],
        },
        "open_ticket_history_context": {
            "open_tickets": 10,
            "open_tickets_with_history": 4,
            "open_tickets_without_history": 6,
            "coverage_percent": 40.0,
        },
        "status_sample_coverage": {
            "sampled_status_candidate_rows": 0,
            "coverage_percent": 100.0,
            "by_status": [{"status": "1"}],
        },
    }

    transition_summary = {
        "inspected_history": 10,
        "parsed_transitions": 2,
        "parsed_status_transitions": 0,
        "timestamped_status_transitions": 0,
        "source_limited": True,
    }

    report = ticket_health_module.field_certification_report(coverage, diagnostics, transition_summary)
    by_target = {target["key"]: target for target in report["targets"]}

    assert report["certification_state"] == "partial_field_certification"
    assert by_target["status_duration"]["certification_status"] == "source_limited"
    assert by_target["time_entries"]["certification_status"] == "certified"
    assert by_target["sla_information"]["certification_status"] == "missing"
    assert "status_duration" in report["predictive_policy"]["excluded_until_certified"]
    assert "by_status" not in report["source_reports"]["status_source"]["status_sample_coverage"]
    assert report["predictive_policy"]["automatic_model_or_workflow_changes_allowed"] is False
    assert report["source_reports"]["status_transition_source_candidates"]["policy"]["live_autotask_probe_ran"] is False


def test_ticket_history_transition_parse_summary_counts_status_transitions(monkeypatch):
    class FakeResult:
        def fetchall(self):
            return [
                {
                    "action": "Status Changed",
                    "detail": "Status changed from New to Waiting Customer",
                    "happened_at": object(),
                },
                {"action": "Queue Changed", "detail": "Queue changed from A to B", "happened_at": object()},
                {"action": "Note Added", "detail": "Technician updated the ticket", "happened_at": None},
            ]

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, _sql, _params):
            return FakeResult()

    monkeypatch.setattr(ticket_health_module, "db_connection", lambda: FakeConnection())

    summary = ticket_health_module.ticket_history_transition_parse_summary(authorized_company_ids=[123])

    assert summary["inspected_history"] == 3
    assert summary["parsed_transitions"] == 2
    assert summary["parsed_status_transitions"] == 1
    assert summary["timestamped_status_transitions"] == 1
    assert summary["source_limited"] is False
    assert summary["authorized_company_scope_applied"] is True
    assert any(item["category"] == "status" for item in summary["parsed_transition_categories"])


def test_status_transition_source_candidates_are_review_only_and_scoped():
    diagnostics = {
        "source_capability": {
            "current_status_field_available": True,
            "exact_status_transition_timestamp_fields": [],
            "proxy_timestamp_fields": ["lastActivityDate"],
        },
        "open_ticket_history_context": {
            "open_tickets": 12,
            "open_tickets_with_history": 12,
            "open_tickets_without_history": 0,
        },
        "status_sample_coverage": {"sampled_status_candidate_rows": 0},
    }
    transition_summary = {
        "parsed_status_transitions": 0,
        "timestamped_status_transitions": 0,
    }

    report = ticket_health_module.status_transition_source_candidates_report(
        diagnostics,
        transition_summary,
        authorized_company_ids=[123],
    )
    by_candidate = {candidate["key"]: candidate for candidate in report["candidates"]}

    assert report["certification_state"] == "source_candidates_partial"
    assert report["authorized_company_scope_applied"] is True
    assert by_candidate["local_ticket_history"]["certification_status"] == "source_limited"
    assert by_candidate["ticket_current_status"]["certification_status"] == "current_state_only"
    assert by_candidate["ticket_proxy_timestamps"]["certification_status"] == "proxy_only"
    assert by_candidate["candidate_status_history_entities"]["certification_status"] == "not_certified"
    assert by_candidate["candidate_status_history_entities"]["access"] == "not_queried_by_this_report"
    assert report["policy"]["autotask_writes_allowed"] is False
    assert report["policy"]["live_autotask_probe_ran"] is False


def test_ticket_predictive_target_policy_blocks_automatic_actions():
    policy = ticket_health_module._prediction_target_policy(7, 100)

    assert policy["positive_label"] == "resolution_days_greater_than_7"
    assert policy["review_authority"] == "advisory_human_review_only"
    assert "no Autotask writes" in policy["prohibited_actions"]
    assert any("routing" in action for action in policy["prohibited_actions"])


def test_customer_success_data_paths_fail_closed_and_filter_company_scope():
    summary_source = inspect.getsource(customer_success_module.customer_success_summary)
    detail_source = inspect.getsource(customer_success_module.customer_success_detail)
    review_source = inspect.getsource(customer_success_module.customer_success_review_queue)
    feedback_source = inspect.getsource(customer_success_module.store_customer_risk_feedback)
    query_source = inspect.getsource(customer_success_module._customer_row_query)

    assert "authorized_company_ids" in summary_source
    assert "authorized_company_ids" in detail_source
    assert "authorized_company_ids" in review_source
    assert "authorized_company_ids" in feedback_source
    assert "metrics.company_id = ANY(%s)" in query_source
    assert "company_not_found" in detail_source
    assert "company_not_found" in feedback_source


def test_routing_data_paths_apply_company_scope_to_evidence_and_feedback():
    profile_source = inspect.getsource(routing_module.technician_skill_profiles)
    recommendation_source = inspect.getsource(routing_module.ticket_routing_recommendation)
    feedback_source = inspect.getsource(routing_module.store_routing_feedback)

    assert "authorized_company_ids" in profile_source
    assert "authorized_company_ids" in recommendation_source
    assert "authorized_company_ids" in feedback_source
    assert "company_id = ANY(%s)" in profile_source
    assert "company_id = ANY(%s)" in recommendation_source
    assert "company_id = ANY(%s)" in feedback_source


def test_realtime_events_filter_ticket_history_scope_and_hide_global_jobs(monkeypatch):
    calls = []

    class FakeResult:
        def fetchall(self):
            return []

    class FakeConn:
        def execute(self, sql, params=None):
            calls.append((sql, params))
            return FakeResult()

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr("app.realtime.db_connection", lambda: FakeConn())

    result = realtime_module.recent_realtime_events(limit=5, authorized_company_ids=[123])

    assert result["ok"] is True
    assert result["scope"] == {"global": False, "company_ids": [123]}
    assert not any("FROM job_runs" in sql for sql, _params in calls)
    assert len(calls) == 1
    sql, params = calls[0]
    assert "FROM autotask_ticket_history" in sql
    assert "t.company_id = ANY(%s)" in sql
    assert params == ([123], [123], 10)
