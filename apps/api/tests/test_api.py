from fastapi.testclient import TestClient

from app.audit import audit_sink
from app.main import app


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
    assert audit_sink.entries[-1].action == "login"

