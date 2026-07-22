from pathlib import Path
import subprocess

from fastapi.testclient import TestClient

from app.audit import audit_sink
from app.config import settings
from app.main import app
from app.models import AuditAction, AuditLogEntry, Role
from app.security import create_session_token, hash_password, verify_password
import app.user_admin as user_admin


client = TestClient(app)
ROOT = Path(__file__).resolve().parents[3]


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_endpoint():
    response = client.get("/ready")
    assert response.status_code == 200
    assert "status" in response.json()
    assert "app_route_auth_required" in response.json()


def test_auth_model_records_login_audit_event():
    audit_sink.entries.clear()
    response = client.post("/auth/login", json={"username": "tech", "password": "local-password"})
    assert response.status_code == 200
    assert response.json()["user"]["roles"] == ["Technician"]
    assert response.json()["token"] != "local-development-placeholder-token"
    assert audit_sink.entries[-1].action == "login"


def test_password_hashing_verifies_and_rejects_wrong_password():
    encoded = hash_password("correct horse battery staple")

    assert encoded.startswith("pbkdf2_sha256$")
    assert verify_password("correct horse battery staple", encoded)
    assert not verify_password("wrong password", encoded)
    assert "correct horse battery staple" not in encoded


def test_bootstrap_app_user_validates_roles_and_password_length():
    assert user_admin.normalize_roles([Role.admin.value, Role.admin.value]) == [Role.admin.value]
    try:
        user_admin.normalize_roles(["Owner"])
    except ValueError as exc:
        assert "Unsupported role" in str(exc)
    else:
        raise AssertionError("unsupported role should fail")

    try:
        user_admin.upsert_app_user("admin", "short", [Role.admin.value])
    except ValueError as exc:
        assert "at least" in str(exc)
    else:
        raise AssertionError("short bootstrap password should fail")


def test_bootstrap_app_user_upserts_hash_only_and_returns_safe_metadata(monkeypatch):
    captured = {}

    class FakeConnection:
        def execute(self, sql, params):
            captured["sql"] = sql
            captured["params"] = params
            return self

        def fetchone(self):
            return {"username": "admin", "roles": [Role.admin.value], "disabled": False}

    class FakeConnectionContext:
        def __enter__(self):
            return FakeConnection()

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(user_admin, "db_connection", lambda: FakeConnectionContext())

    result = user_admin.upsert_app_user(" admin ", "correct horse battery staple", [Role.admin.value])

    assert result == {"username": "admin", "roles": [Role.admin.value], "disabled": False}
    assert "ON CONFLICT (username)" in captured["sql"]
    assert captured["params"][0] == "admin"
    assert captured["params"][1] != "correct horse battery staple"
    assert captured["params"][1].startswith("pbkdf2_sha256$")


def test_bootstrap_app_user_wrapper_requires_password_env():
    result = subprocess.run(
        ["scripts/bootstrap-app-user.sh", "--username", "admin"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "BOOTSTRAP_APP_PASSWORD" in result.stderr


def test_login_rejects_invalid_credentials(monkeypatch):
    monkeypatch.setattr("app.main.authenticate_user", lambda *_args, **_kwargs: None)

    response = client.post("/auth/login", json={"username": "tech", "password": "wrong"})

    assert response.status_code == 401
    assert "Invalid username or password" in response.json()["detail"]


def test_login_rejects_disabled_users(monkeypatch):
    monkeypatch.setattr(
        "app.main.authenticate_user",
        lambda *_args, **_kwargs: {"username": "tech", "roles": [Role.technician.value], "disabled": True},
    )

    response = client.post("/auth/login", json={"username": "tech", "password": "local-password"})

    assert response.status_code == 403
    assert "disabled" in response.json()["detail"].lower()


def test_auth_me_validates_signed_session_token():
    token = create_session_token("tech", [Role.technician.value])["token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["user"]["username"] == "tech"
    assert response.json()["user"]["roles"] == ["Technician"]


def test_auth_me_rejects_missing_or_tampered_token():
    missing = client.get("/auth/me")
    tampered = client.get("/auth/me", headers={"Authorization": "Bearer v1.invalid.token"})

    assert missing.status_code == 401
    assert tampered.status_code == 401


def test_route_auth_is_default_off_for_basic_auth_deployment(monkeypatch):
    monkeypatch.setattr(settings, "app_route_auth_required", False)

    response = client.get("/settings")

    assert response.status_code == 200


def test_route_auth_rejects_missing_token_when_enabled(monkeypatch):
    monkeypatch.setattr(settings, "app_route_auth_required", True)

    public_ready = client.get("/ready")
    protected = client.get("/settings")

    assert public_ready.status_code == 200
    assert protected.status_code == 401


def test_route_auth_denial_records_audit_event(monkeypatch):
    events = []
    monkeypatch.setattr(settings, "app_route_auth_required", True)
    monkeypatch.setattr(audit_sink, "record", lambda entry: events.append(entry) or entry)

    response = client.get("/settings")

    assert response.status_code == 401
    assert events[-1].action == "authorization_denied"
    assert events[-1].outcome == "denied"
    assert events[-1].target == "/settings"


def test_route_auth_accepts_bearer_token_when_enabled(monkeypatch):
    monkeypatch.setattr(settings, "app_route_auth_required", True)
    token = create_session_token("tech", [Role.technician.value])["token"]

    response = client.get("/settings", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200


def test_operations_status_passes_scoped_cache_context_when_route_auth_enabled(monkeypatch):
    monkeypatch.setattr(settings, "app_route_auth_required", True)
    captured = {}

    def fake_operations_status(cache_context=None):
        captured["cache_context"] = cache_context
        return {"ok": True, "cache": {"scoped": True}}

    monkeypatch.setattr("app.main.operations_status", fake_operations_status)
    token = create_session_token("reader", [Role.readonly.value])["token"]

    response = client.get("/api/operations/status", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert captured["cache_context"] == {
        "authority_class": "authenticated-read",
        "roles": [Role.readonly.value],
        "scope": {"global": True},
    }


def test_admin_route_requires_admin_role_when_route_auth_enabled(monkeypatch):
    monkeypatch.setattr(settings, "app_route_auth_required", True)
    monkeypatch.setattr("app.main.set_global_pause", lambda paused, actor, reason=None: {"ok": True, "settings": {"global_pause": paused}})
    readonly_token = create_session_token("reader", [Role.readonly.value])["token"]
    admin_token = create_session_token("admin", [Role.admin.value])["token"]

    denied = client.post("/api/operations/pause", headers={"Authorization": f"Bearer {readonly_token}"})
    allowed = client.post("/api/operations/pause", headers={"Authorization": f"Bearer {admin_token}"})

    assert denied.status_code == 403
    assert allowed.status_code == 200


def test_admin_route_matrix_denies_readonly_and_audits_each_denial(monkeypatch):
    events = []
    monkeypatch.setattr(settings, "app_route_auth_required", True)
    monkeypatch.setattr(audit_sink, "record", lambda entry: events.append(entry) or entry)
    token = create_session_token("reader", [Role.readonly.value])["token"]
    headers = {"Authorization": f"Bearer {token}"}
    admin_routes = [
        ("GET", "/audit-log", None),
        ("GET", "/api/autotask/threshold", None),
        ("POST", "/api/autotask/test/companies", None),
        ("POST", "/api/autotask/test/tickets", None),
        ("POST", "/api/autotask/test/ticket-notes", None),
        ("POST", "/api/autotask/probe/status-transition-sources", None),
        ("POST", "/autotask/test-connection", None),
        ("POST", "/api/sync/companies/start", {}),
        ("POST", "/api/sync/tickets/start", {}),
        ("POST", "/api/sync/ticket-notes/start", {}),
        ("POST", "/api/sync/recent/start", {}),
        ("POST", "/api/sync/reference-data/start", None),
        ("POST", "/api/documents/build", {}),
        ("POST", "/api/embeddings/run", {}),
        ("POST", "/api/analytics/classify-tickets", {}),
        ("POST", "/api/operations/settings", {"settings": {"global_pause": True}}),
        ("POST", "/api/operations/jobs/recent_sync/run", None),
        ("POST", "/api/operations/jobs/recent_sync/enable", None),
        ("POST", "/api/operations/jobs/recent_sync/disable", None),
        ("POST", "/api/operations/pause", None),
        ("POST", "/api/operations/resume", None),
        ("POST", "/api/operations/jobs/1/request-stop", None),
        ("POST", "/api/operations/jobs/1/archive-stale", None),
        ("GET", "/api/admin/curated-memory", None),
    ]

    for method, path, payload in admin_routes:
        response = client.request(method, path, headers=headers, json=payload)
        assert response.status_code == 403, path

    denials = [event for event in events if event.action == AuditAction.authorization_denied]
    assert len(denials) == len(admin_routes)
    assert {event.actor for event in denials} == {"reader"}
    assert {event.outcome for event in denials} == {"denied"}
    assert all(event.metadata["required_roles"] == [Role.admin.value] for event in denials)


def test_api_route_authority_matrix_classifies_every_route():
    route_keys = {
        (method, route.path)
        for route in app.routes
        for method in getattr(route, "methods", set())
        if method in {"GET", "POST"} and route.path.startswith(("/", "/api"))
    }
    public_or_auth_utility = {
        ("GET", "/health"),
        ("GET", "/ready"),
        ("POST", "/auth/login"),
        ("POST", "/auth/logout"),
        ("GET", "/auth/me"),
        ("GET", "/docs"),
        ("GET", "/docs/oauth2-redirect"),
        ("GET", "/openapi.json"),
        ("GET", "/redoc"),
    }
    authenticated_read = {
        ("GET", "/settings"),
        ("GET", "/sync/status"),
        ("GET", "/api/sync/status"),
        ("GET", "/api/sync/runs"),
        ("GET", "/api/knowledge/noise-report"),
        ("GET", "/api/reference-data/status"),
        ("GET", "/api/analytics/ticket-class-report"),
        ("GET", "/api/operations/status"),
        ("GET", "/api/operations/settings"),
        ("GET", "/api/operations/jobs"),
        ("GET", "/api/operations/jobs/runs"),
    }
    company_scoped = {
        ("GET", "/api/analytics/recurring-issues"),
        ("GET", "/api/ticket-health/summary"),
        ("GET", "/api/ticket-health/tickets/{ticket_id}"),
        ("GET", "/api/ticket-health/ticket-number/{ticket_number}"),
        ("GET", "/api/ticket-health/review-queue"),
        ("GET", "/api/ticket-health/predictive-evaluation"),
        ("GET", "/api/ticket-health/field-certification"),
        ("GET", "/api/ticket-health/status-transition-sources"),
        ("GET", "/api/ticket-health/reference-metadata-source-contract"),
        ("GET", "/api/ticket-health/ticket-history-content-certification"),
        ("GET", "/api/customer-success/summary"),
        ("GET", "/api/customer-success/companies/{company_id}"),
        ("GET", "/api/routing/technician-skill-profiles"),
        ("GET", "/api/routing/tickets/{ticket_id}/recommendation"),
        ("GET", "/api/realtime/events"),
        ("POST", "/api/ticket-health/feedback"),
        ("POST", "/api/customer-success/feedback"),
        ("POST", "/api/routing/feedback"),
        ("POST", "/api/assistant/ask"),
        ("POST", "/api/assistant/feedback"),
    }
    admin_only = {
        ("GET", "/audit-log"),
        ("GET", "/api/autotask/threshold"),
        ("POST", "/api/autotask/test/companies"),
        ("POST", "/api/autotask/test/tickets"),
        ("POST", "/api/autotask/test/ticket-notes"),
        ("POST", "/api/autotask/probe/status-transition-sources"),
        ("POST", "/api/autotask/probe/reference-metadata-sources"),
        ("POST", "/autotask/test-connection"),
        ("POST", "/api/sync/companies/start"),
        ("POST", "/api/sync/tickets/start"),
        ("POST", "/api/sync/ticket-notes/start"),
        ("POST", "/api/sync/recent/start"),
        ("POST", "/api/sync/reference-data/start"),
        ("POST", "/api/documents/build"),
        ("POST", "/api/embeddings/run"),
        ("POST", "/api/analytics/classify-tickets"),
        ("POST", "/api/operations/settings"),
        ("POST", "/api/operations/jobs/{job_name}/run"),
        ("POST", "/api/operations/jobs/{job_name}/enable"),
        ("POST", "/api/operations/jobs/{job_name}/disable"),
        ("POST", "/api/operations/pause"),
        ("POST", "/api/operations/resume"),
        ("POST", "/api/operations/jobs/{run_id}/request-stop"),
        ("POST", "/api/operations/jobs/{run_id}/archive-stale"),
        ("GET", "/api/admin/curated-memory"),
    }

    matrix = public_or_auth_utility | authenticated_read | company_scoped | admin_only
    assert route_keys - matrix == set()
    assert admin_only <= route_keys
    assert company_scoped <= route_keys


def test_no_export_or_download_routes_exist_without_authority_contract():
    export_like_routes = [
        route.path
        for route in app.routes
        if any(token in route.path.lower() for token in ("export", "download"))
    ]

    assert export_like_routes == []


def test_admin_success_actions_record_actor_scope_and_safe_metadata(monkeypatch):
    events = []
    monkeypatch.setattr(settings, "app_route_auth_required", True)
    monkeypatch.setattr(audit_sink, "record", lambda entry: events.append(entry) or entry)
    monkeypatch.setattr("app.main.update_operations_settings", lambda payload: payload)
    monkeypatch.setattr(
        "app.main.set_global_pause",
        lambda paused, actor, reason=None: {
            "ok": True,
            "settings": {"global_pause": paused},
            "pause_provenance": {
                "paused": paused,
                "reason": reason or ("manual_pause" if paused else "manual_resume"),
                "policy": {
                    "local_metadata_only": True,
                    "runs_jobs": False,
                    "autotask_writes_allowed": False,
                },
            },
        },
    )
    monkeypatch.setattr("app.main.run_job", lambda job_name, triggered_by, force: {"ok": True, "job_name": job_name})
    monkeypatch.setattr("app.main.archive_stale_orphaned_run", lambda run_id: {"ok": True, "archived": True, "run": {"id": run_id}})
    monkeypatch.setattr("app.main.classify_tickets", lambda limit=None: {"ok": True, "limit": limit})
    monkeypatch.setattr("app.main.sync_reference_data", lambda: {"ok": True})
    monkeypatch.setattr("app.main.create_documents_from_tickets", lambda limit=None: {"ok": True, "limit": limit})
    monkeypatch.setattr("app.main.run_embedding_batch", lambda limit=None: {"ok": True, "limit": limit})
    monkeypatch.setattr("app.main.pending_memory", lambda: [{"id": 1, "title": "Pending fix"}])

    class FakeAutotaskClient:
        def __init__(self, *args, **kwargs):
            pass

        def threshold_information(self):
            return {"remaining": 100}

        def probe_status_transition_sources(self):
            return {
                "ok": True,
                "candidate_entities": ["TicketStatusHistory"],
                "available_entities": ["TicketStatusHistory"],
                "max_records_per_entity": 1,
                "autotask_writes_allowed": False,
            }

        def probe_reference_metadata_sources(self):
            return {
                "ok": True,
                "candidate_entities": ["TicketPriorities"],
                "available_entities": ["TicketPriorities"],
                "max_records_per_entity": 1,
                "autotask_writes_allowed": False,
            }

    monkeypatch.setattr("app.main.AutotaskReadOnlyClient", FakeAutotaskClient)
    token = create_session_token("admin", [Role.admin.value])["token"]
    headers = {"Authorization": f"Bearer {token}"}
    routes = [
        ("GET", "/audit-log", None, "audit_log.read"),
        ("GET", "/api/autotask/threshold", None, "autotask.threshold"),
        (
            "POST",
            "/api/autotask/probe/status-transition-sources",
            None,
            "autotask.probe.status_transition_sources",
        ),
        (
            "POST",
            "/api/autotask/probe/reference-metadata-sources",
            None,
            "autotask.probe.reference_metadata_sources",
        ),
        ("POST", "/api/sync/reference-data/start", None, "sync.reference_data.start"),
        ("POST", "/api/documents/build", {"limit": 5}, "documents.build"),
        ("POST", "/api/embeddings/run", {"limit": 5}, "embeddings.run"),
        ("POST", "/api/analytics/classify-tickets", {"limit": 5}, "analytics.classify_tickets"),
        ("POST", "/api/operations/settings", {"settings": {"global_pause": True}}, "operations.settings.update"),
        ("POST", "/api/operations/jobs/recent_sync/run", None, "operations.job.run"),
        ("POST", "/api/operations/jobs/1/archive-stale", None, "operations.job.archive_stale"),
        ("POST", "/api/operations/pause", {"reason": "maintenance"}, "operations.pause"),
        ("POST", "/api/operations/resume", {"reason": "maintenance complete"}, "operations.resume"),
        ("GET", "/api/admin/curated-memory", None, "curated_memory.pending.read"),
    ]

    for method, path, payload, _target in routes:
        response = client.request(method, path, headers=headers, json=payload)
        assert response.status_code == 200, path

    success_events = [event for event in events if event.action == AuditAction.admin_action]
    assert {event.target for event in success_events} >= {target for *_prefix, target in routes}
    for event in success_events:
        assert event.actor == "admin"
        assert event.outcome == "success"
        assert event.scope == {"global": True}
        assert event.metadata["roles"] == [Role.admin.value]
    curated_read = next(event for event in success_events if event.target == "curated_memory.pending.read")
    assert curated_read.metadata["item_count"] == 1
    pause_event = next(event for event in success_events if event.target == "operations.pause")
    assert pause_event.metadata["paused"] is True
    assert pause_event.metadata["reason"] == "maintenance"
    assert pause_event.metadata["local_metadata_only"] is True
    assert pause_event.metadata["runs_jobs"] is False
    assert pause_event.metadata["autotask_writes_allowed"] is False
    resume_event = next(event for event in success_events if event.target == "operations.resume")
    assert resume_event.metadata["paused"] is False
    assert resume_event.metadata["reason"] == "maintenance complete"


def test_audit_log_supports_bounded_admin_filters_and_audits_read(monkeypatch):
    events = []
    monkeypatch.setattr(settings, "app_route_auth_required", True)
    monkeypatch.setattr("app.db.db_connection", lambda: (_ for _ in ()).throw(RuntimeError("database unavailable")))
    monkeypatch.setattr(audit_sink, "entries", [
        AuditLogEntry(actor="tech", action=AuditAction.search, target="analytics.recurring_issues", outcome="success"),
        AuditLogEntry(actor="reader", action=AuditAction.authorization_denied, target="api.secret", outcome="denied"),
        AuditLogEntry(actor="admin", action=AuditAction.admin_action, target="operations.pause", outcome="success"),
    ])

    def record_and_capture(entry):
        events.append(entry)
        audit_sink.entries.append(entry)
        return entry

    monkeypatch.setattr(audit_sink, "record", record_and_capture)
    token = create_session_token("admin", [Role.admin.value])["token"]

    response = client.get(
        "/audit-log?action=authorization_denied&outcome=denied&actor=reader&limit=5",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["filters"] == {"actor": "reader", "action": "authorization_denied", "outcome": "denied"}
    assert payload["limit"] == 5
    assert [entry["actor"] for entry in payload["entries"]] == ["reader"]
    assert payload["entries"][0]["target"] == "api.secret"
    audit_event = next(event for event in events if event.target == "audit_log.read")
    assert audit_event.actor == "admin"
    assert audit_event.scope == {"global": True}
    assert audit_event.metadata["limit"] == 5
    assert audit_event.metadata["filters"] == {
        "actor": "reader",
        "action": "authorization_denied",
        "outcome": "denied",
    }


def test_audit_log_rejects_unbounded_limit_when_route_auth_enabled(monkeypatch):
    monkeypatch.setattr(settings, "app_route_auth_required", True)
    token = create_session_token("admin", [Role.admin.value])["token"]

    response = client.get("/audit-log?limit=1000", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 422


def test_operations_read_routes_record_actor_scope_and_safe_metadata(monkeypatch):
    events = []
    monkeypatch.setattr(settings, "app_route_auth_required", True)
    monkeypatch.setattr(audit_sink, "record", lambda entry: events.append(entry) or entry)
    monkeypatch.setattr(
        "app.main.operations_status",
        lambda cache_context=None: {
            "ok": True,
            "scheduler": {"state": "healthy"},
            "counts": {"tickets": 7},
            "cache_context": cache_context,
        },
    )
    monkeypatch.setattr("app.main.operations_settings", lambda: {"global_pause": False, "sync_enabled": True})
    monkeypatch.setattr("app.main.operations_jobs", lambda: {"jobs": [{"name": "recent_sync"}, {"name": "ticket_history_gaps"}]})
    monkeypatch.setattr("app.main.job_runs", lambda limit=100: {"runs": [{"id": 1}, {"id": 2}], "limit": limit})
    token = create_session_token("reader", [Role.readonly.value])["token"]
    headers = {"Authorization": f"Bearer {token}"}

    routes = [
        ("/api/operations/status", "operations.status.read"),
        ("/api/operations/settings", "operations.settings.read"),
        ("/api/operations/jobs", "operations.jobs.read"),
        ("/api/operations/jobs/runs", "operations.job_runs.read"),
    ]

    for path, _target in routes:
        response = client.get(path, headers=headers)
        assert response.status_code == 200, path

    read_events = [event for event in events if event.action == AuditAction.search]
    assert {event.target for event in read_events} >= {target for _path, target in routes}
    for event in read_events:
        assert event.actor == "reader"
        assert event.outcome == "success"
        assert event.scope == {"global": True}
        assert event.metadata["roles"] == [Role.readonly.value]
    status_event = next(event for event in read_events if event.target == "operations.status.read")
    assert status_event.metadata["scheduler_state"] == "healthy"
    settings_event = next(event for event in read_events if event.target == "operations.settings.read")
    assert settings_event.metadata["setting_count"] == 2
    jobs_event = next(event for event in read_events if event.target == "operations.jobs.read")
    assert jobs_event.metadata["job_count"] == 2
    runs_event = next(event for event in read_events if event.target == "operations.job_runs.read")
    assert runs_event.metadata == {"roles": [Role.readonly.value], "run_count": 2, "limit": 100}


def test_assistant_ask_denies_authenticated_user_without_company_scope(monkeypatch):
    monkeypatch.setattr(settings, "app_route_auth_required", True)
    monkeypatch.setattr("app.main.authorized_company_ids_for_user", lambda _user: [])
    token = create_session_token("tech", [Role.technician.value])["token"]

    response = client.post(
        "/api/assistant/ask",
        json={"question": "printer not printing"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert "company scope" in response.json()["detail"]


def test_assistant_ask_passes_authorized_company_scope(monkeypatch):
    captured = {}
    monkeypatch.setattr(settings, "app_route_auth_required", True)
    monkeypatch.setattr("app.main.authorized_company_ids_for_user", lambda _user: [123])

    def fake_ask_assistant(question, mode, limit, include_noise, authorized_company_ids, actor_username):
        captured["authorized_company_ids"] = authorized_company_ids
        captured["actor_username"] = actor_username
        return {"ok": True}

    monkeypatch.setattr(
        "app.main.ask_assistant",
        fake_ask_assistant,
    )
    token = create_session_token("tech", [Role.technician.value])["token"]

    response = client.post(
        "/api/assistant/ask",
        json={"question": "printer not printing"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert captured["authorized_company_ids"] == [123]
    assert captured["actor_username"] == "tech"


def test_ticket_health_summary_route_passes_scope_and_cache_context(monkeypatch):
    captured = {}
    monkeypatch.setattr(settings, "app_route_auth_required", True)
    monkeypatch.setattr("app.main.authorized_company_ids_for_user", lambda _user: [123])

    def fake_ticket_health_summary(limit, queue, assigned_resource_id, cache_context, authorized_company_ids):
        captured["limit"] = limit
        captured["queue"] = queue
        captured["assigned_resource_id"] = assigned_resource_id
        captured["cache_context"] = cache_context
        captured["authorized_company_ids"] = authorized_company_ids
        return {"ok": True}

    monkeypatch.setattr("app.main.ticket_health_summary", fake_ticket_health_summary)
    token = create_session_token("tech", [Role.technician.value])["token"]

    response = client.get(
        "/api/ticket-health/summary?limit=12&queue=Support&assigned_resource_id=44",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert captured["limit"] == 12
    assert captured["queue"] == "Support"
    assert captured["assigned_resource_id"] == 44
    assert captured["authorized_company_ids"] == [123]
    assert captured["cache_context"] == {
        "authority_class": "authenticated-read",
        "roles": [Role.technician.value],
        "scope": {"global": False, "company_ids": [123]},
    }


def test_scoped_local_capability_routes_pass_company_scope(monkeypatch):
    captured = {}
    monkeypatch.setattr(settings, "app_route_auth_required", True)
    monkeypatch.setattr("app.main.authorized_company_ids_for_user", lambda _user: [123])

    def fake_customer_success_detail(company_id, recent_days, authorized_company_ids):
        captured["customer_success_detail"] = (company_id, recent_days, authorized_company_ids)
        return {"ok": True}

    def fake_ticket_routing_recommendation(ticket_id, limit, authorized_company_ids):
        captured["ticket_routing_recommendation"] = (ticket_id, limit, authorized_company_ids)
        return {"ok": True}

    def fake_recent_realtime_events(limit, authorized_company_ids):
        captured["recent_realtime_events"] = (limit, authorized_company_ids)
        return {"ok": True}

    def fake_ticket_health_review_queue(
        limit,
        queue,
        assigned_resource_id,
        risk_bucket,
        min_priority,
        needs_review_only,
        authorized_company_ids,
    ):
        captured["ticket_health_review_queue"] = (
            limit,
            queue,
            assigned_resource_id,
            risk_bucket,
            min_priority,
            needs_review_only,
            authorized_company_ids,
        )
        return {"ok": True}

    def fake_ticket_health_predictive_evaluation(limit, delayed_days_threshold, authorized_company_ids):
        captured["ticket_health_predictive_evaluation"] = (limit, delayed_days_threshold, authorized_company_ids)
        return {"ok": True}

    def fake_field_certification_report(authorized_company_ids):
        captured["field_certification_report"] = authorized_company_ids
        return {"ok": True}

    def fake_status_transition_source_candidates_report(authorized_company_ids):
        captured["status_transition_source_candidates_report"] = authorized_company_ids
        return {"ok": True}

    def fake_reference_metadata_source_contract_report(authorized_company_ids):
        captured["reference_metadata_source_contract_report"] = authorized_company_ids
        return {"ok": True}

    def fake_ticket_history_content_certification_report(authorized_company_ids):
        captured["ticket_history_content_certification_report"] = authorized_company_ids
        return {"ok": True}

    monkeypatch.setattr("app.main.customer_success_detail", fake_customer_success_detail)
    monkeypatch.setattr("app.main.ticket_routing_recommendation", fake_ticket_routing_recommendation)
    monkeypatch.setattr("app.main.recent_realtime_events", fake_recent_realtime_events)
    monkeypatch.setattr("app.main.ticket_health_review_queue", fake_ticket_health_review_queue)
    monkeypatch.setattr("app.main.ticket_health_predictive_evaluation", fake_ticket_health_predictive_evaluation)
    monkeypatch.setattr("app.main.field_certification_report", fake_field_certification_report)
    monkeypatch.setattr(
        "app.main.status_transition_source_candidates_report",
        fake_status_transition_source_candidates_report,
    )
    monkeypatch.setattr(
        "app.main.reference_metadata_source_contract_report",
        fake_reference_metadata_source_contract_report,
    )
    monkeypatch.setattr(
        "app.main.ticket_history_content_certification_report",
        fake_ticket_history_content_certification_report,
    )
    token = create_session_token("tech", [Role.technician.value])["token"]
    headers = {"Authorization": f"Bearer {token}"}

    assert client.get("/api/customer-success/companies/77?recent_days=14", headers=headers).status_code == 200
    assert client.get("/api/routing/tickets/88/recommendation?limit=4", headers=headers).status_code == 200
    assert client.get("/api/realtime/events?limit=9", headers=headers).status_code == 200
    assert (
        client.get(
            "/api/ticket-health/review-queue?limit=7&queue=Support&assigned_resource_id=44&risk_bucket=high&min_priority=20&needs_review_only=true",
            headers=headers,
        ).status_code
        == 200
    )
    assert client.get("/api/ticket-health/predictive-evaluation?limit=120&delayed_days_threshold=10", headers=headers).status_code == 200
    assert client.get("/api/ticket-health/field-certification", headers=headers).status_code == 200
    assert client.get("/api/ticket-health/status-transition-sources", headers=headers).status_code == 200
    assert client.get("/api/ticket-health/reference-metadata-source-contract", headers=headers).status_code == 200
    assert client.get("/api/ticket-health/ticket-history-content-certification", headers=headers).status_code == 200

    assert captured["customer_success_detail"] == (77, 14, [123])
    assert captured["ticket_routing_recommendation"] == (88, 4, [123])
    assert captured["recent_realtime_events"] == (9, [123])
    assert captured["ticket_health_review_queue"] == (7, "Support", 44, "high", 20, True, [123])
    assert captured["ticket_health_predictive_evaluation"] == (120, 10, [123])
    assert captured["field_certification_report"] == [123]
    assert captured["status_transition_source_candidates_report"] == [123]
    assert captured["reference_metadata_source_contract_report"] == [123]
    assert captured["ticket_history_content_certification_report"] == [123]


def test_local_feedback_routes_pass_scope_and_deny_readonly(monkeypatch):
    captured = {}
    monkeypatch.setattr(settings, "app_route_auth_required", True)
    monkeypatch.setattr("app.main.authorized_company_ids_for_user", lambda _user: [123])

    def fake_ticket_health_feedback(ticket_id, health_score, risk_bucket, outcome, notes, authorized_company_ids):
        captured["ticket_health"] = (ticket_id, health_score, risk_bucket, outcome, notes, authorized_company_ids)
        return {"ok": True}

    def fake_customer_feedback(company_id, risk_bucket, outcome, notes, authorized_company_ids):
        captured["customer_success"] = (company_id, risk_bucket, outcome, notes, authorized_company_ids)
        return {"ok": True}

    def fake_routing_feedback(ticket_id, recommended_resource_id, recommended_resource_name, outcome, notes, authorized_company_ids):
        captured["routing"] = (
            ticket_id,
            recommended_resource_id,
            recommended_resource_name,
            outcome,
            notes,
            authorized_company_ids,
        )
        return {"ok": True}

    monkeypatch.setattr("app.main.store_ticket_health_risk_feedback", fake_ticket_health_feedback)
    monkeypatch.setattr("app.main.store_customer_risk_feedback", fake_customer_feedback)
    monkeypatch.setattr("app.main.store_routing_feedback", fake_routing_feedback)
    tech_token = create_session_token("tech", [Role.technician.value])["token"]
    headers = {"Authorization": f"Bearer {tech_token}"}

    assert client.post(
        "/api/ticket-health/feedback",
        json={
            "ticket_id": 88,
            "health_score": 70,
            "risk_bucket": "high",
            "outcome": "accurate",
            "notes": "reviewed locally",
        },
        headers=headers,
    ).status_code == 200
    assert client.post(
        "/api/customer-success/feedback",
        json={"company_id": 77, "risk_bucket": "watch", "outcome": "dismissed", "notes": "local only"},
        headers=headers,
    ).status_code == 200
    assert client.post(
        "/api/routing/feedback",
        json={
            "ticket_id": 88,
            "recommended_resource_id": 44,
            "recommended_resource_name": "Tech",
            "outcome": "needs_review",
            "notes": "local only",
        },
        headers=headers,
    ).status_code == 200

    assert captured["ticket_health"] == (88, 70, "high", "accurate", "reviewed locally", [123])
    assert captured["customer_success"] == (77, "watch", "dismissed", "local only", [123])
    assert captured["routing"] == (88, 44, "Tech", "needs_review", "local only", [123])

    readonly_token = create_session_token("reader", [Role.readonly.value])["token"]
    denied = client.post(
        "/api/ticket-health/feedback",
        json={"ticket_id": 88, "outcome": "accurate"},
        headers={"Authorization": f"Bearer {readonly_token}"},
    )

    assert denied.status_code == 403


def test_admin_assistant_ask_uses_explicit_global_scope(monkeypatch):
    captured = {}
    monkeypatch.setattr(settings, "app_route_auth_required", True)

    def fake_ask_assistant(question, mode, limit, include_noise, authorized_company_ids, actor_username):
        captured["authorized_company_ids"] = authorized_company_ids
        captured["actor_username"] = actor_username
        return {"ok": True}

    monkeypatch.setattr(
        "app.main.ask_assistant",
        fake_ask_assistant,
    )
    token = create_session_token("admin", [Role.admin.value])["token"]

    response = client.post(
        "/api/assistant/ask",
        json={"question": "printer not printing"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert captured["authorized_company_ids"] is None
    assert captured["actor_username"] == "admin"


def test_feedback_passes_actor_and_scope_snapshot(monkeypatch):
    captured = {}
    monkeypatch.setattr(settings, "app_route_auth_required", True)
    monkeypatch.setattr("app.main.authorized_company_ids_for_user", lambda _user: [123])

    def fake_store_feedback(answer_id, rating, notes, actor_username, authorized_company_ids):
        captured.update(
            {
                "answer_id": answer_id,
                "rating": rating,
                "actor_username": actor_username,
                "authorized_company_ids": authorized_company_ids,
            }
        )
        return {"feedback_id": 1}

    monkeypatch.setattr("app.main.store_feedback", fake_store_feedback)
    token = create_session_token("tech", [Role.technician.value])["token"]

    response = client.post(
        "/api/assistant/feedback",
        json={"answer_id": 42, "rating": "Good"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert captured == {
        "answer_id": 42,
        "rating": "Good",
        "actor_username": "tech",
        "authorized_company_ids": [123],
    }


def test_assistant_and_feedback_success_audit_use_actor_and_effective_scope(monkeypatch):
    events = []
    monkeypatch.setattr(settings, "app_route_auth_required", True)
    monkeypatch.setattr("app.main.authorized_company_ids_for_user", lambda _user: [123])
    monkeypatch.setattr(audit_sink, "record", lambda entry: events.append(entry) or entry)
    monkeypatch.setattr("app.main.ask_assistant", lambda *_args, **_kwargs: {"answer_id": 42, "answer": "ok"})
    monkeypatch.setattr("app.main.store_feedback", lambda *_args, **_kwargs: {"feedback_id": 7})
    token = create_session_token("tech", [Role.technician.value])["token"]
    headers = {"Authorization": f"Bearer {token}"}

    ask_response = client.post(
        "/api/assistant/ask",
        json={"question": "printer not printing"},
        headers=headers,
    )
    feedback_response = client.post(
        "/api/assistant/feedback",
        json={"answer_id": 42, "rating": "Good"},
        headers=headers,
    )

    assert ask_response.status_code == 200
    assert feedback_response.status_code == 200
    assistant_event = next(event for event in events if event.action == AuditAction.assistant_answer)
    feedback_event = next(event for event in events if event.action == AuditAction.feedback)
    for event in (assistant_event, feedback_event):
        assert event.actor == "tech"
        assert event.outcome == "success"
        assert event.scope == {"global": False, "company_ids": [123]}
        assert event.metadata["roles"] == [Role.technician.value]
    assert feedback_event.metadata["rating"] == "Good"


def test_authorized_company_ids_for_user_reads_database_scope(monkeypatch):
    class FakeConn:
        def execute(self, sql, params=None):
            assert "FROM app_user_company_scopes" in sql
            assert params == ("tech",)
            return self

        def fetchall(self):
            return [{"company_id": 321}, {"company_id": 654}]

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr("app.main.db_connection", lambda: FakeConn())

    from app.main import authorized_company_ids_for_user

    assert authorized_company_ids_for_user({"username": "tech", "roles": [Role.technician.value]}) == [321, 654]


def test_audit_sink_persists_when_database_available(monkeypatch):
    calls = []

    class FakeConn:
        def execute(self, sql, params=None):
            calls.append((sql, params))
            return self

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

    audit_sink.record(
        AuditLogEntry(
            actor="tech",
            action=AuditAction.admin_action,
            target="/settings",
            outcome="success",
            scope={"company_ids": [1]},
            metadata={"safe": True},
        )
    )

    sql, params = calls[-1]
    assert "INSERT INTO audit_log" in sql
    assert params[0] == "tech"
    assert params[3] == "success"
