from typing import Literal

from collections.abc import Callable

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .audit import audit_sink
from .assistant import ask_assistant, pending_memory, store_feedback
from .autotask import AutotaskReadOnlyClient
from .config import settings
from .db import database_available, init_schema
from .documents import create_documents_from_tickets, noise_report
from .embeddings import run_embedding_batch
from .models import AuditAction, AuditLogEntry, LoginRequest, Role
from .operations import (
    job_runs,
    operations_jobs,
    operations_settings,
    operations_status,
    request_stop,
    run_job,
    set_job_enabled,
    update_operations_settings,
)
from .sync import sync_companies, sync_recent, sync_runs, sync_status as get_sync_status, sync_ticket_notes, sync_tickets
from .ticket_analytics import classify_tickets, recurring_issues_report, reference_data_status, sync_reference_data, ticket_class_report
from .security import authenticate_user, create_session_token, verify_session_token

app = FastAPI(title="Autotask AI API", version="0.1.0")

PUBLIC_AUTH_PATHS = {
    "/health",
    "/ready",
    "/auth/login",
    "/auth/logout",
    "/auth/me",
    "/docs",
    "/openapi.json",
    "/redoc",
}


class SyncRequest(BaseModel):
    limit: int | None = Field(default=None, ge=1, le=500)
    full_sync: bool = False


class AskRequest(BaseModel):
    question: str = Field(min_length=3)
    mode: Literal["ticket_history_only", "general_plus_ticket_history", "deep_dive"] = "ticket_history_only"
    limit: int = Field(default=5, ge=1, le=12)
    include_noise: bool = False


class FeedbackRequest(BaseModel):
    answer_id: int
    rating: Literal["Good", "Bad", "Needs Edit", "Save as Known Fix"]
    notes: str | None = None


class OperationsSettingsRequest(BaseModel):
    settings: dict[str, object] = Field(default_factory=dict)


def _bearer_token(request: Request) -> str | None:
    authorization = request.headers.get("authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


def _token_user(request: Request) -> dict | None:
    token = _bearer_token(request)
    if not token:
        return None
    payload = verify_session_token(token)
    if not payload:
        return None
    return {"username": payload["sub"], "roles": payload["roles"]}


def _record_auth_denial(request: Request, actor: str = "anonymous", reason: str = "missing_or_invalid_token") -> None:
    audit_sink.record(
        AuditLogEntry(
            actor=actor,
            action=AuditAction.authorization_denied,
            target=request.url.path,
            outcome="denied",
            metadata={"reason": reason, "method": request.method},
        )
    )


@app.middleware("http")
async def enforce_route_auth(request: Request, call_next: Callable) -> JSONResponse:
    if not settings.app_route_auth_required or request.url.path in PUBLIC_AUTH_PATHS:
        return await call_next(request)

    user = _token_user(request)
    if not user:
        _record_auth_denial(request)
        return JSONResponse(status_code=401, content={"detail": "Missing or invalid bearer token."})
    request.state.user = user
    return await call_next(request)


def current_user(request: Request) -> dict:
    user = getattr(request.state, "user", None) or _token_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Missing or invalid bearer token.")
    return user


def require_roles(*allowed_roles: Role):
    allowed = {role.value for role in allowed_roles}

    def dependency(request: Request) -> dict | None:
        if not settings.app_route_auth_required:
            return None
        user = current_user(request)
        if not allowed.intersection(set(user.get("roles") or [])):
            audit_sink.record(
                AuditLogEntry(
                    actor=user.get("username") or "unknown",
                    action=AuditAction.authorization_denied,
                    target=request.url.path,
                    outcome="denied",
                    metadata={"required_roles": sorted(allowed), "actual_roles": user.get("roles") or []},
                )
            )
            raise HTTPException(status_code=403, detail="Insufficient role for this action.")
        return user

    return dependency


def authorized_company_ids_for_user(user: dict) -> list[int] | None:
    roles = set(user.get("roles") or [])
    if Role.admin.value in roles:
        return None
    try:
        with db_connection() as conn:
            rows = conn.execute(
                """
                SELECT company_id
                FROM app_user_company_scopes
                WHERE username = %s
                ORDER BY company_id
                """,
                (user.get("username"),),
            ).fetchall()
        return [int(row["company_id"]) for row in rows]
    except Exception:
        return []


def require_company_scope(request: Request) -> list[int] | None:
    if not settings.app_route_auth_required:
        return None
    user = current_user(request)
    company_ids = authorized_company_ids_for_user(user)
    if company_ids is None:
        return None
    if not company_ids:
        audit_sink.record(
            AuditLogEntry(
                actor=user.get("username") or "unknown",
                action=AuditAction.authorization_denied,
                target=request.url.path,
                outcome="denied",
                scope={"company_ids": []},
                metadata={"reason": "missing_company_scope"},
            )
        )
        raise HTTPException(status_code=403, detail="No authorized company scope is assigned.")
    return company_ids


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
def login(payload: LoginRequest, request: Request) -> dict:
    if not payload.username or not payload.password:
        raise HTTPException(status_code=400, detail="Username and password are required.")
    user = authenticate_user(payload.username, payload.password, request.client.host if request.client else None)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    if user.get("throttled"):
        raise HTTPException(status_code=429, detail="Too many failed login attempts. Wait and retry.")
    if user.get("disabled"):
        raise HTTPException(status_code=403, detail="User account is disabled.")
    session = create_session_token(user["username"], user["roles"])
    audit_sink.record(AuditLogEntry(actor=user["username"], action=AuditAction.login))
    return {
        "token": session["token"],
        "expires_at": session["expires_at"],
        "user": {"username": user["username"], "roles": user["roles"]},
    }


@app.post("/auth/logout")
def logout() -> dict:
    return {"ok": True}


@app.get("/auth/me")
def auth_me(request: Request) -> dict:
    return {"user": current_user(request)}


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


@app.get("/api/knowledge/noise-report")
def knowledge_noise_report() -> dict:
    return noise_report()


@app.post("/api/sync/reference-data/start")
def start_reference_data_sync() -> dict:
    return sync_reference_data()


@app.get("/api/reference-data/status")
def api_reference_data_status() -> dict:
    return reference_data_status()


@app.post("/api/analytics/classify-tickets")
def api_classify_tickets(payload: SyncRequest | None = None) -> dict:
    return classify_tickets(limit=(payload.limit if payload else None))


@app.get("/api/analytics/ticket-class-report")
def api_ticket_class_report() -> dict:
    return ticket_class_report()


@app.get("/api/analytics/recurring-issues")
def api_recurring_issues(
    limit: int = 8,
    include_excluded: bool = False,
    authorized_company_ids: list[int] | None = Depends(require_company_scope),
) -> dict:
    return recurring_issues_report(limit=limit, include_excluded=include_excluded, authorized_company_ids=authorized_company_ids)


@app.get("/api/operations/status")
def api_operations_status() -> dict:
    return operations_status()


@app.get("/api/operations/settings")
def api_operations_settings() -> dict:
    return {"ok": True, "settings": operations_settings()}


@app.post("/api/operations/settings")
def api_update_operations_settings(payload: OperationsSettingsRequest, _user: dict | None = Depends(require_roles(Role.admin))) -> dict:
    return {"ok": True, "settings": update_operations_settings(payload.settings)}


@app.get("/api/operations/jobs")
def api_operations_jobs() -> dict:
    return operations_jobs()


@app.get("/api/operations/jobs/runs")
def api_operations_job_runs() -> dict:
    return job_runs()


@app.post("/api/operations/jobs/{job_name}/run")
def api_run_operation_job(job_name: str, _user: dict | None = Depends(require_roles(Role.admin))) -> dict:
    return run_job(job_name, triggered_by="manual", force=True)


@app.post("/api/operations/jobs/{job_name}/enable")
def api_enable_operation_job(job_name: str, _user: dict | None = Depends(require_roles(Role.admin))) -> dict:
    return set_job_enabled(job_name, True)


@app.post("/api/operations/jobs/{job_name}/disable")
def api_disable_operation_job(job_name: str, _user: dict | None = Depends(require_roles(Role.admin))) -> dict:
    return set_job_enabled(job_name, False)


@app.post("/api/operations/pause")
def api_pause_operations(_user: dict | None = Depends(require_roles(Role.admin))) -> dict:
    return {"ok": True, "settings": update_operations_settings({"global_pause": True})}


@app.post("/api/operations/resume")
def api_resume_operations(_user: dict | None = Depends(require_roles(Role.admin))) -> dict:
    return {"ok": True, "settings": update_operations_settings({"global_pause": False})}


@app.post("/api/operations/jobs/{run_id}/request-stop")
def api_request_stop(run_id: int, _user: dict | None = Depends(require_roles(Role.admin))) -> dict:
    return request_stop(run_id)


@app.post("/api/assistant/ask")
def assistant_ask(payload: AskRequest, authorized_company_ids: list[int] | None = Depends(require_company_scope)) -> dict:
    audit_sink.record(AuditLogEntry(actor="system", action=AuditAction.assistant_answer, target="assistant.ask"))
    return ask_assistant(
        payload.question,
        mode=payload.mode,
        limit=payload.limit,
        include_noise=payload.include_noise,
        authorized_company_ids=authorized_company_ids,
    )


@app.post("/api/assistant/feedback")
def assistant_feedback(payload: FeedbackRequest) -> dict:
    audit_sink.record(AuditLogEntry(actor="system", action=AuditAction.feedback, target=str(payload.answer_id)))
    return store_feedback(payload.answer_id, payload.rating, payload.notes)


@app.get("/api/admin/curated-memory")
def admin_curated_memory() -> dict:
    return {"items": pending_memory()}
