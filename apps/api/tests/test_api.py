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
