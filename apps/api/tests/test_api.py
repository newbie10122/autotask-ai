from fastapi.testclient import TestClient

from app.audit import audit_sink
from app.config import settings
from app.main import app
from app.models import AuditAction, AuditLogEntry, Role
from app.security import create_session_token, hash_password, verify_password


client = TestClient(app)


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


def test_admin_route_requires_admin_role_when_route_auth_enabled(monkeypatch):
    monkeypatch.setattr(settings, "app_route_auth_required", True)
    monkeypatch.setattr("app.main.update_operations_settings", lambda payload: payload)
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
        ("POST", "/api/assistant/ask"),
        ("POST", "/api/assistant/feedback"),
    }
    admin_only = {
        ("GET", "/audit-log"),
        ("GET", "/api/autotask/threshold"),
        ("POST", "/api/autotask/test/companies"),
        ("POST", "/api/autotask/test/tickets"),
        ("POST", "/api/autotask/test/ticket-notes"),
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
        ("GET", "/api/admin/curated-memory"),
    }

    matrix = public_or_auth_utility | authenticated_read | company_scoped | admin_only
    assert route_keys - matrix == set()
    assert admin_only <= route_keys
    assert company_scoped <= route_keys


def test_admin_success_actions_record_actor_scope_and_safe_metadata(monkeypatch):
    events = []
    monkeypatch.setattr(settings, "app_route_auth_required", True)
    monkeypatch.setattr(audit_sink, "record", lambda entry: events.append(entry) or entry)
    monkeypatch.setattr("app.main.update_operations_settings", lambda payload: payload)
    monkeypatch.setattr("app.main.run_job", lambda job_name, triggered_by, force: {"ok": True, "job_name": job_name})
    monkeypatch.setattr("app.main.classify_tickets", lambda limit=None: {"ok": True, "limit": limit})
    monkeypatch.setattr("app.main.sync_reference_data", lambda: {"ok": True})
    monkeypatch.setattr("app.main.create_documents_from_tickets", lambda limit=None: {"ok": True, "limit": limit})
    monkeypatch.setattr("app.main.run_embedding_batch", lambda limit=None: {"ok": True, "limit": limit})

    class FakeAutotaskClient:
        def threshold_information(self):
            return {"remaining": 100}

    monkeypatch.setattr("app.main.AutotaskReadOnlyClient", lambda: FakeAutotaskClient())
    token = create_session_token("admin", [Role.admin.value])["token"]
    headers = {"Authorization": f"Bearer {token}"}
    routes = [
        ("GET", "/api/autotask/threshold", None, "autotask.threshold"),
        ("POST", "/api/sync/reference-data/start", None, "sync.reference_data.start"),
        ("POST", "/api/documents/build", {"limit": 5}, "documents.build"),
        ("POST", "/api/embeddings/run", {"limit": 5}, "embeddings.run"),
        ("POST", "/api/analytics/classify-tickets", {"limit": 5}, "analytics.classify_tickets"),
        ("POST", "/api/operations/settings", {"settings": {"global_pause": True}}, "operations.settings.update"),
        ("POST", "/api/operations/jobs/recent_sync/run", None, "operations.job.run"),
        ("POST", "/api/operations/pause", None, "operations.pause"),
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
