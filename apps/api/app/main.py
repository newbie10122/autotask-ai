from fastapi import FastAPI, HTTPException

from .audit import audit_sink
from .autotask import AutotaskReadOnlyClient
from .config import settings
from .models import AuditAction, AuditLogEntry, LoginRequest, Role

app = FastAPI(title="Autotask AI API", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict:
    return {
        "status": "ready",
        "database": "configured" if settings.database_url else "missing",
        "autotask": "configured" if settings.autotask_username else "missing",
    }


@app.post("/auth/login")
def login(payload: LoginRequest) -> dict:
    if not payload.username or not payload.password:
        raise HTTPException(status_code=400, detail="Username and password are required.")
    audit_sink.record(AuditLogEntry(actor=payload.username, action=AuditAction.login))
    return {
        "token": "local-development-placeholder-token",
        "user": {"username": payload.username, "roles": [Role.technician]},
    }


@app.post("/auth/logout")
def logout() -> dict:
    return {"ok": True}


@app.get("/settings")
def get_settings() -> dict:
    return {
        "app_env": settings.app_env,
        "autotask_page_size": settings.autotask_page_size,
        "answer_target_seconds": settings.answer_target_seconds,
        "roles": [role.value for role in Role],
    }


@app.get("/audit-log")
def audit_log() -> dict:
    return {"entries": [entry.model_dump(mode="json") for entry in audit_sink.list_recent()]}


@app.post("/autotask/test-connection")
def autotask_test_connection() -> dict:
    audit_sink.record(AuditLogEntry(actor="system", action=AuditAction.admin_action, target="autotask.test_connection"))
    return AutotaskReadOnlyClient().test_connection()


@app.get("/sync/status")
def sync_status() -> dict:
    return {
        "historical_sync": "not_started",
        "recent_sync": "scheduled_every_15_minutes",
        "last_run": None,
        "api_calls_tracked": True,
        "resumable": True,
    }

