from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .audit import audit_sink
from .assistant import ask_assistant, pending_memory, store_feedback
from .autotask import AutotaskReadOnlyClient
from .config import settings
from .db import database_available, init_schema
from .documents import create_documents_from_tickets
from .embeddings import run_embedding_batch
from .models import AuditAction, AuditLogEntry, LoginRequest, Role
from .sync import sync_companies, sync_recent, sync_runs, sync_status as get_sync_status, sync_ticket_notes, sync_tickets

app = FastAPI(title="Autotask AI API", version="0.1.0")


class SyncRequest(BaseModel):
    limit: int | None = Field(default=None, ge=1, le=500)
    full_sync: bool = False


class AskRequest(BaseModel):
    question: str = Field(min_length=3)
    mode: Literal["ticket_history_only", "general_plus_ticket_history", "deep_dive"] = "ticket_history_only"
    limit: int = Field(default=5, ge=1, le=12)


class FeedbackRequest(BaseModel):
    answer_id: int
    rating: Literal["Good", "Bad", "Needs Edit", "Save as Known Fix"]
    notes: str | None = None


@app.on_event("startup")
def startup() -> None:
    try:
        init_schema()
    except Exception:
        pass


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict:
    return {
        "status": "ready",
        "database": "available" if database_available() else "unavailable",
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
        "autotask_base_url": settings.autotask_base_url,
        "autotask_username": settings.autotask_username,
        "autotask_page_size": settings.autotask_page_size,
        "ollama_base_url": settings.ollama_base_url,
        "ollama_chat_model": settings.ollama_chat_model,
        "ollama_embedding_model": settings.ollama_embedding_model,
        "answer_target_seconds": settings.answer_target_seconds,
        "roles": [role.value for role in Role],
    }


@app.get("/audit-log")
def audit_log() -> dict:
    return {"entries": [entry.model_dump(mode="json") for entry in audit_sink.list_recent()]}


@app.get("/api/autotask/threshold")
def autotask_threshold() -> dict:
    audit_sink.record(AuditLogEntry(actor="system", action=AuditAction.admin_action, target="autotask.threshold"))
    payload = AutotaskReadOnlyClient().threshold_information()
    return {"ok": True, "base_url": settings.autotask_base_url, "username": settings.autotask_username, "threshold": payload}


@app.post("/api/autotask/test/companies")
def autotask_test_companies() -> dict:
    payload = AutotaskReadOnlyClient().query_entity("Companies", filters=[{"op": "gte", "field": "id", "value": 0}])
    items = payload.get("items") or payload.get("records") or []
    return {"ok": True, "entity": "Companies", "count": len(items[: settings.autotask_page_size])}


@app.post("/api/autotask/test/tickets")
def autotask_test_tickets() -> dict:
    payload = AutotaskReadOnlyClient().query_entity("Tickets", filters=[{"op": "gte", "field": "id", "value": 0}])
    items = payload.get("items") or payload.get("records") or []
    return {"ok": True, "entity": "Tickets", "count": len(items[: settings.autotask_page_size])}


@app.post("/api/autotask/test/ticket-notes")
def autotask_test_ticket_notes() -> dict:
    payload = AutotaskReadOnlyClient().query_entity("TicketNotes", filters=[{"op": "gte", "field": "id", "value": 0}])
    items = payload.get("items") or payload.get("records") or []
    return {"ok": True, "entity": "TicketNotes", "count": len(items[: settings.autotask_page_size])}


@app.post("/autotask/test-connection")
def autotask_test_connection() -> dict:
    audit_sink.record(AuditLogEntry(actor="system", action=AuditAction.admin_action, target="autotask.test_connection"))
    return AutotaskReadOnlyClient().test_connection()


@app.get("/sync/status")
def sync_status() -> dict:
    try:
        status = get_sync_status()
    except Exception as exc:
        status = {"error": str(exc)}
    status.update({"api_calls_tracked": True, "resumable": True})
    return status


@app.post("/api/sync/companies/start")
def start_companies_sync(payload: SyncRequest | None = None) -> dict:
    return sync_companies(limit=(payload.limit if payload else None), full_sync=bool(payload and payload.full_sync))


@app.post("/api/sync/tickets/start")
def start_tickets_sync(payload: SyncRequest | None = None) -> dict:
    return sync_tickets(limit=(payload.limit if payload else None), full_sync=bool(payload and payload.full_sync))


@app.post("/api/sync/ticket-notes/start")
def start_ticket_notes_sync(payload: SyncRequest | None = None) -> dict:
    return sync_ticket_notes(limit=(payload.limit if payload else None), full_sync=bool(payload and payload.full_sync))


@app.post("/api/sync/recent/start")
def start_recent_sync(payload: SyncRequest | None = None) -> dict:
    return sync_recent(limit=(payload.limit if payload else None))


@app.get("/api/sync/status")
def api_sync_status() -> dict:
    return sync_status()


@app.get("/api/sync/runs")
def api_sync_runs() -> dict:
    return {"runs": sync_runs()}


@app.post("/api/documents/build")
def build_documents(payload: SyncRequest | None = None) -> dict:
    return create_documents_from_tickets(limit=(payload.limit if payload else None))


@app.post("/api/embeddings/run")
def run_embeddings(payload: SyncRequest | None = None) -> dict:
    return run_embedding_batch(limit=(payload.limit if payload else None))


@app.post("/api/assistant/ask")
def assistant_ask(payload: AskRequest) -> dict:
    audit_sink.record(AuditLogEntry(actor="system", action=AuditAction.assistant_answer, target="assistant.ask"))
    return ask_assistant(payload.question, mode=payload.mode, limit=payload.limit)


@app.post("/api/assistant/feedback")
def assistant_feedback(payload: FeedbackRequest) -> dict:
    audit_sink.record(AuditLogEntry(actor="system", action=AuditAction.feedback, target=str(payload.answer_id)))
    return store_feedback(payload.answer_id, payload.rating, payload.notes)


@app.get("/api/admin/curated-memory")
def admin_curated_memory() -> dict:
    return {"items": pending_memory()}
