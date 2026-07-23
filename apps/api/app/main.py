from typing import Literal

from collections.abc import Callable

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .audit import audit_sink
from .assistant import ask_assistant, pending_memory, store_feedback
from .autotask import AutotaskReadOnlyClient
from .config import settings
from .customer_success import customer_success_detail, customer_success_summary, store_customer_risk_feedback
from .db import database_available, db_connection, init_schema
from .documents import create_documents_from_tickets, noise_report
from .embeddings import run_embedding_batch
from .models import AuditAction, AuditLogEntry, LoginRequest, Role
from .operations import (
    archive_stale_orphaned_run,
    job_runs,
    operations_jobs,
    operations_settings,
    operations_status,
    request_stop,
    run_job,
    set_job_enabled,
    set_global_pause,
    update_operations_settings,
)
from .realtime import recent_realtime_events
from .routing import store_routing_feedback, technician_skill_profiles, ticket_routing_recommendation
from .sync import sync_companies, sync_recent, sync_runs, sync_status as get_sync_status, sync_ticket_notes, sync_tickets
from .ticket_analytics import classify_tickets, recurring_issues_report, reference_data_status, sync_reference_data, ticket_class_report
from .ticket_health import (
    field_certification_report,
    queue_history_source_candidates_report,
    reference_metadata_source_contract_report,
    status_transition_source_candidates_report,
    store_ticket_health_risk_feedback,
    ticket_history_content_certification_report,
    ticket_health_detail_by_number_scoped,
    ticket_health_detail_scoped,
    ticket_health_predictive_evaluation,
    ticket_health_review_queue,
    ticket_health_summary,
)
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


class TicketHealthRiskFeedbackRequest(BaseModel):
    ticket_id: int
    health_score: int | None = Field(default=None, ge=0, le=100)
    risk_bucket: Literal["critical", "high", "watch", "normal"] | None = None
    outcome: Literal["accurate", "too_high", "too_low", "needs_review"]
    notes: str | None = None


class CustomerRiskFeedbackRequest(BaseModel):
    company_id: int
    risk_bucket: Literal["critical", "high", "watch", "normal"] | None = None
    outcome: Literal["confirmed_risk", "dismissed", "needs_review"]
    notes: str | None = None


class RoutingFeedbackRequest(BaseModel):
    ticket_id: int
    recommended_resource_id: int | None = None
    recommended_resource_name: str | None = None
    outcome: Literal["accepted", "rejected", "needs_review"]
    notes: str | None = None


class OperationsSettingsRequest(BaseModel):
    settings: dict[str, object] = Field(default_factory=dict)


class OperationsPauseRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=200)


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


def audit_scope(authorized_company_ids: list[int] | None = None) -> dict:
    if authorized_company_ids is None:
        return {"global": True}
    return {"global": False, "company_ids": authorized_company_ids}


def cache_context_for_request(request: Request, authorized_company_ids: list[int] | None) -> dict | None:
    if not settings.app_route_auth_required:
        return None
    user = current_user(request)
    return {
        "authority_class": "authenticated-read",
        "roles": user.get("roles") or ["Authenticated"],
        "scope": audit_scope(authorized_company_ids),
    }


def audit_actor(user: dict | None = None) -> str:
    if not user:
        return "system"
    return str(user.get("username") or "unknown")


def record_success_audit(
    action: AuditAction,
    target: str,
    user: dict | None = None,
    scope: dict | None = None,
    metadata: dict | None = None,
) -> None:
    safe_metadata = dict(metadata or {})
    if user:
        safe_metadata["roles"] = user.get("roles") or []
    audit_sink.record(
        AuditLogEntry(
            actor=audit_actor(user),
            action=action,
            target=target,
            outcome="success",
            scope=scope or {},
            metadata=safe_metadata,
        )
    )


def request_actor(request: Request) -> str:
    if not settings.app_route_auth_required:
        return "system"
    user = current_user(request)
    return str(user.get("username") or "unknown")


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
        "app_route_auth_required": settings.app_route_auth_required,
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
def audit_log(
    actor: str | None = Query(default=None, min_length=1, max_length=128),
    action: AuditAction | None = None,
    outcome: str | None = Query(default=None, min_length=1, max_length=64),
    target: str | None = Query(default=None, min_length=1, max_length=160),
    limit: int = Query(default=100, ge=1, le=500),
    _user: dict | None = Depends(require_roles(Role.admin)),
) -> dict:
    filters = {
        key: value
        for key, value in {
            "actor": actor,
            "action": action.value if action else None,
            "outcome": outcome,
            "target": target,
        }.items()
        if value is not None
    }
    record_success_audit(
        AuditAction.admin_action,
        "audit_log.read",
        _user,
        audit_scope(),
        {"filters": filters, "limit": limit},
    )
    entries = audit_sink.list_recent(
        actor=actor,
        action=action,
        outcome=outcome,
        target=target,
        limit=limit,
    )
    return {"entries": [entry.model_dump(mode="json") for entry in entries], "filters": filters, "limit": limit}


@app.get("/api/autotask/threshold")
def autotask_threshold(_user: dict | None = Depends(require_roles(Role.admin))) -> dict:
    payload = AutotaskReadOnlyClient().threshold_information()
    record_success_audit(AuditAction.admin_action, "autotask.threshold", _user, audit_scope())
    return {"ok": True, "base_url": settings.autotask_base_url, "username": settings.autotask_username, "threshold": payload}


@app.post("/api/autotask/test/companies")
def autotask_test_companies(_user: dict | None = Depends(require_roles(Role.admin))) -> dict:
    payload = AutotaskReadOnlyClient().query_entity("Companies", filters=[{"op": "gte", "field": "id", "value": 0}])
    items = payload.get("items") or payload.get("records") or []
    record_success_audit(AuditAction.admin_action, "autotask.test.companies", _user, audit_scope())
    return {"ok": True, "entity": "Companies", "count": len(items[: settings.autotask_page_size])}


@app.post("/api/autotask/test/tickets")
def autotask_test_tickets(_user: dict | None = Depends(require_roles(Role.admin))) -> dict:
    payload = AutotaskReadOnlyClient().query_entity("Tickets", filters=[{"op": "gte", "field": "id", "value": 0}])
    items = payload.get("items") or payload.get("records") or []
    record_success_audit(AuditAction.admin_action, "autotask.test.tickets", _user, audit_scope())
    return {"ok": True, "entity": "Tickets", "count": len(items[: settings.autotask_page_size])}


@app.post("/api/autotask/test/ticket-notes")
def autotask_test_ticket_notes(_user: dict | None = Depends(require_roles(Role.admin))) -> dict:
    payload = AutotaskReadOnlyClient().query_entity("TicketNotes", filters=[{"op": "gte", "field": "id", "value": 0}])
    items = payload.get("items") or payload.get("records") or []
    record_success_audit(AuditAction.admin_action, "autotask.test.ticket_notes", _user, audit_scope())
    return {"ok": True, "entity": "TicketNotes", "count": len(items[: settings.autotask_page_size])}


@app.post("/api/autotask/probe/status-transition-sources")
def autotask_probe_status_transition_sources(_user: dict | None = Depends(require_roles(Role.admin))) -> dict:
    result = AutotaskReadOnlyClient(delay_seconds=0).probe_status_transition_sources()
    record_success_audit(
        AuditAction.admin_action,
        "autotask.probe.status_transition_sources",
        _user,
        audit_scope(),
        {
            "candidate_entities": result.get("candidate_entities") or [],
            "available_entities": result.get("available_entities") or [],
            "max_records_per_entity": result.get("max_records_per_entity"),
            "autotask_writes_allowed": False,
        },
    )
    return result


@app.post("/api/autotask/probe/reference-metadata-sources")
def autotask_probe_reference_metadata_sources(_user: dict | None = Depends(require_roles(Role.admin))) -> dict:
    result = AutotaskReadOnlyClient(delay_seconds=0).probe_reference_metadata_sources()
    record_success_audit(
        AuditAction.admin_action,
        "autotask.probe.reference_metadata_sources",
        _user,
        audit_scope(),
        {
            "candidate_entities": result.get("candidate_entities") or [],
            "available_entities": result.get("available_entities") or [],
            "max_records_per_entity": result.get("max_records_per_entity"),
            "autotask_writes_allowed": False,
            "automatic_reference_sync_allowed": False,
        },
    )
    return result


@app.post("/api/autotask/probe/ticket-history-schema")
def autotask_probe_ticket_history_schema(_user: dict | None = Depends(require_roles(Role.admin))) -> dict:
    result = AutotaskReadOnlyClient(delay_seconds=0).probe_ticket_history_schema()
    summary = result.get("summary") or {}
    record_success_audit(
        AuditAction.admin_action,
        "autotask.probe.ticket_history_schema",
        _user,
        audit_scope(),
        {
            "entity": result.get("entity"),
            "field_count": summary.get("field_count"),
            "has_structured_status_transition_fields": summary.get("has_structured_status_transition_fields"),
            "autotask_writes_allowed": False,
            "returns_raw_ticket_history_rows": False,
        },
    )
    return result


@app.post("/autotask/test-connection")
def autotask_test_connection(_user: dict | None = Depends(require_roles(Role.admin))) -> dict:
    payload = AutotaskReadOnlyClient().test_connection()
    record_success_audit(AuditAction.admin_action, "autotask.test_connection", _user, audit_scope())
    return payload


@app.get("/sync/status")
def sync_status() -> dict:
    try:
        status = get_sync_status()
    except Exception as exc:
        status = {"error": str(exc)}
    status.update({"api_calls_tracked": True, "resumable": True})
    return status


@app.post("/api/sync/companies/start")
def start_companies_sync(
    payload: SyncRequest | None = None,
    _user: dict | None = Depends(require_roles(Role.admin)),
) -> dict:
    result = sync_companies(limit=(payload.limit if payload else None), full_sync=bool(payload and payload.full_sync))
    record_success_audit(
        AuditAction.admin_action,
        "sync.companies.start",
        _user,
        audit_scope(),
        {"limit": payload.limit if payload else None, "full_sync": bool(payload and payload.full_sync)},
    )
    return result


@app.post("/api/sync/tickets/start")
def start_tickets_sync(
    payload: SyncRequest | None = None,
    _user: dict | None = Depends(require_roles(Role.admin)),
) -> dict:
    result = sync_tickets(limit=(payload.limit if payload else None), full_sync=bool(payload and payload.full_sync))
    record_success_audit(
        AuditAction.admin_action,
        "sync.tickets.start",
        _user,
        audit_scope(),
        {"limit": payload.limit if payload else None, "full_sync": bool(payload and payload.full_sync)},
    )
    return result


@app.post("/api/sync/ticket-notes/start")
def start_ticket_notes_sync(
    payload: SyncRequest | None = None,
    _user: dict | None = Depends(require_roles(Role.admin)),
) -> dict:
    result = sync_ticket_notes(limit=(payload.limit if payload else None), full_sync=bool(payload and payload.full_sync))
    record_success_audit(
        AuditAction.admin_action,
        "sync.ticket_notes.start",
        _user,
        audit_scope(),
        {"limit": payload.limit if payload else None, "full_sync": bool(payload and payload.full_sync)},
    )
    return result


@app.post("/api/sync/recent/start")
def start_recent_sync(
    payload: SyncRequest | None = None,
    _user: dict | None = Depends(require_roles(Role.admin)),
) -> dict:
    result = sync_recent(limit=(payload.limit if payload else None))
    record_success_audit(AuditAction.admin_action, "sync.recent.start", _user, audit_scope(), {"limit": payload.limit if payload else None})
    return result


@app.get("/api/sync/status")
def api_sync_status() -> dict:
    return sync_status()


@app.get("/api/sync/runs")
def api_sync_runs() -> dict:
    return {"runs": sync_runs()}


@app.post("/api/documents/build")
def build_documents(
    payload: SyncRequest | None = None,
    _user: dict | None = Depends(require_roles(Role.admin)),
) -> dict:
    result = create_documents_from_tickets(limit=(payload.limit if payload else None))
    record_success_audit(AuditAction.admin_action, "documents.build", _user, audit_scope(), {"limit": payload.limit if payload else None})
    return result


@app.post("/api/embeddings/run")
def run_embeddings(
    payload: SyncRequest | None = None,
    _user: dict | None = Depends(require_roles(Role.admin)),
) -> dict:
    result = run_embedding_batch(limit=(payload.limit if payload else None))
    record_success_audit(AuditAction.admin_action, "embeddings.run", _user, audit_scope(), {"limit": payload.limit if payload else None})
    return result


@app.get("/api/knowledge/noise-report")
def knowledge_noise_report() -> dict:
    return noise_report()


@app.post("/api/sync/reference-data/start")
def start_reference_data_sync(_user: dict | None = Depends(require_roles(Role.admin))) -> dict:
    result = sync_reference_data()
    record_success_audit(AuditAction.admin_action, "sync.reference_data.start", _user, audit_scope())
    return result


@app.get("/api/reference-data/status")
def api_reference_data_status() -> dict:
    return reference_data_status()


@app.post("/api/analytics/classify-tickets")
def api_classify_tickets(
    payload: SyncRequest | None = None,
    _user: dict | None = Depends(require_roles(Role.admin)),
) -> dict:
    result = classify_tickets(limit=(payload.limit if payload else None))
    record_success_audit(AuditAction.admin_action, "analytics.classify_tickets", _user, audit_scope(), {"limit": payload.limit if payload else None})
    return result


@app.get("/api/analytics/ticket-class-report")
def api_ticket_class_report() -> dict:
    return ticket_class_report()


@app.get("/api/analytics/recurring-issues")
def api_recurring_issues(
    request: Request,
    limit: int = 8,
    include_excluded: bool = False,
    authorized_company_ids: list[int] | None = Depends(require_company_scope),
) -> dict:
    result = recurring_issues_report(limit=limit, include_excluded=include_excluded, authorized_company_ids=authorized_company_ids)
    record_success_audit(
        AuditAction.search,
        "analytics.recurring_issues",
        getattr(request.state, "user", None),
        audit_scope(authorized_company_ids),
        {"limit": limit, "include_excluded": include_excluded},
    )
    return result


@app.get("/api/ticket-health/summary")
def api_ticket_health_summary(
    request: Request,
    limit: int = 50,
    queue: str | None = None,
    assigned_resource_id: int | None = None,
    authorized_company_ids: list[int] | None = Depends(require_company_scope),
) -> dict:
    result = ticket_health_summary(
        limit=limit,
        queue=queue,
        assigned_resource_id=assigned_resource_id,
        cache_context=cache_context_for_request(request, authorized_company_ids),
        authorized_company_ids=authorized_company_ids,
    )
    record_success_audit(
        AuditAction.search,
        "ticket_health.summary",
        getattr(request.state, "user", None),
        audit_scope(authorized_company_ids),
        {"limit": limit, "queue": queue, "assigned_resource_id": assigned_resource_id},
    )
    return result


@app.get("/api/ticket-health/tickets/{ticket_id}")
def api_ticket_health_detail(
    ticket_id: int,
    request: Request,
    authorized_company_ids: list[int] | None = Depends(require_company_scope),
) -> dict:
    result = ticket_health_detail_scoped(ticket_id, authorized_company_ids=authorized_company_ids)
    record_success_audit(
        AuditAction.search,
        "ticket_health.detail",
        getattr(request.state, "user", None),
        audit_scope(authorized_company_ids),
        {"ticket_id": ticket_id},
    )
    return result


@app.get("/api/ticket-health/ticket-number/{ticket_number}")
def api_ticket_health_detail_by_number(
    ticket_number: str,
    request: Request,
    authorized_company_ids: list[int] | None = Depends(require_company_scope),
) -> dict:
    result = ticket_health_detail_by_number_scoped(ticket_number, authorized_company_ids=authorized_company_ids)
    record_success_audit(
        AuditAction.search,
        "ticket_health.detail_by_number",
        getattr(request.state, "user", None),
        audit_scope(authorized_company_ids),
        {"ticket_number": ticket_number},
    )
    return result


@app.get("/api/ticket-health/review-queue")
def api_ticket_health_review_queue(
    request: Request,
    limit: int = 25,
    queue: str | None = None,
    assigned_resource_id: int | None = None,
    risk_bucket: str | None = None,
    min_priority: int = 0,
    needs_review_only: bool = False,
    authorized_company_ids: list[int] | None = Depends(require_company_scope),
) -> dict:
    result = ticket_health_review_queue(
        limit=limit,
        queue=queue,
        assigned_resource_id=assigned_resource_id,
        risk_bucket=risk_bucket,
        min_priority=min_priority,
        needs_review_only=needs_review_only,
        authorized_company_ids=authorized_company_ids,
    )
    record_success_audit(
        AuditAction.search,
        "ticket_health.review_queue",
        getattr(request.state, "user", None),
        audit_scope(authorized_company_ids),
        {
            "limit": limit,
            "queue": queue,
            "assigned_resource_id": assigned_resource_id,
            "risk_bucket": risk_bucket,
            "min_priority": min_priority,
            "needs_review_only": needs_review_only,
        },
    )
    return result


@app.get("/api/ticket-health/predictive-evaluation")
def api_ticket_health_predictive_evaluation(
    request: Request,
    limit: int = 500,
    delayed_days_threshold: int = 7,
    authorized_company_ids: list[int] | None = Depends(require_company_scope),
) -> dict:
    result = ticket_health_predictive_evaluation(
        limit=limit,
        delayed_days_threshold=delayed_days_threshold,
        authorized_company_ids=authorized_company_ids,
    )
    record_success_audit(
        AuditAction.search,
        "ticket_health.predictive_evaluation",
        getattr(request.state, "user", None),
        audit_scope(authorized_company_ids),
        {"limit": limit, "delayed_days_threshold": delayed_days_threshold},
    )
    return result


@app.get("/api/ticket-health/field-certification")
def api_ticket_health_field_certification(
    request: Request,
    authorized_company_ids: list[int] | None = Depends(require_company_scope),
) -> dict:
    result = field_certification_report(authorized_company_ids=authorized_company_ids)
    result["authorized_company_scope_applied"] = authorized_company_ids is not None
    record_success_audit(
        AuditAction.search,
        "ticket_health.field_certification",
        getattr(request.state, "user", None),
        audit_scope(authorized_company_ids),
        {"authorized_company_scope_applied": authorized_company_ids is not None},
    )
    return result


@app.get("/api/ticket-health/status-transition-sources")
def api_ticket_health_status_transition_sources(
    request: Request,
    authorized_company_ids: list[int] | None = Depends(require_company_scope),
) -> dict:
    result = status_transition_source_candidates_report(authorized_company_ids=authorized_company_ids)
    record_success_audit(
        AuditAction.search,
        "ticket_health.status_transition_sources",
        getattr(request.state, "user", None),
        audit_scope(authorized_company_ids),
        {"authorized_company_scope_applied": authorized_company_ids is not None},
    )
    return result


@app.get("/api/ticket-health/queue-history-sources")
def api_ticket_health_queue_history_sources(
    request: Request,
    authorized_company_ids: list[int] | None = Depends(require_company_scope),
) -> dict:
    result = queue_history_source_candidates_report(authorized_company_ids=authorized_company_ids)
    record_success_audit(
        AuditAction.search,
        "ticket_health.queue_history_sources",
        getattr(request.state, "user", None),
        audit_scope(authorized_company_ids),
        {"authorized_company_scope_applied": authorized_company_ids is not None},
    )
    return result


@app.get("/api/ticket-health/reference-metadata-source-contract")
def api_ticket_health_reference_metadata_source_contract(
    request: Request,
    authorized_company_ids: list[int] | None = Depends(require_company_scope),
) -> dict:
    result = reference_metadata_source_contract_report(authorized_company_ids=authorized_company_ids)
    record_success_audit(
        AuditAction.search,
        "ticket_health.reference_metadata_source_contract",
        getattr(request.state, "user", None),
        audit_scope(authorized_company_ids),
        {"authorized_company_scope_applied": authorized_company_ids is not None},
    )
    return result


@app.get("/api/ticket-health/ticket-history-content-certification")
def api_ticket_history_content_certification(
    request: Request,
    authorized_company_ids: list[int] | None = Depends(require_company_scope),
) -> dict:
    result = ticket_history_content_certification_report(authorized_company_ids=authorized_company_ids)
    record_success_audit(
        AuditAction.search,
        "ticket_health.ticket_history_content_certification",
        getattr(request.state, "user", None),
        audit_scope(authorized_company_ids),
        {"authorized_company_scope_applied": authorized_company_ids is not None},
    )
    return result


@app.get("/api/customer-success/summary")
def api_customer_success_summary(
    request: Request,
    limit: int = 25,
    recent_days: int = 30,
    authorized_company_ids: list[int] | None = Depends(require_company_scope),
) -> dict:
    result = customer_success_summary(
        limit=limit,
        recent_days=recent_days,
        cache_context=cache_context_for_request(request, authorized_company_ids),
        authorized_company_ids=authorized_company_ids,
    )
    record_success_audit(
        AuditAction.search,
        "customer_success.summary",
        getattr(request.state, "user", None),
        audit_scope(authorized_company_ids),
        {"limit": limit, "recent_days": recent_days},
    )
    return result


@app.get("/api/customer-success/companies/{company_id}")
def api_customer_success_detail(
    company_id: int,
    request: Request,
    recent_days: int = 30,
    authorized_company_ids: list[int] | None = Depends(require_company_scope),
) -> dict:
    result = customer_success_detail(company_id, recent_days=recent_days, authorized_company_ids=authorized_company_ids)
    record_success_audit(
        AuditAction.search,
        "customer_success.detail",
        getattr(request.state, "user", None),
        audit_scope(authorized_company_ids),
        {"company_id": company_id, "recent_days": recent_days},
    )
    return result


@app.get("/api/routing/technician-skill-profiles")
def api_technician_skill_profiles(
    request: Request,
    limit: int = 25,
    authorized_company_ids: list[int] | None = Depends(require_company_scope),
) -> dict:
    result = technician_skill_profiles(limit=limit, authorized_company_ids=authorized_company_ids)
    record_success_audit(
        AuditAction.search,
        "routing.technician_skill_profiles",
        getattr(request.state, "user", None),
        audit_scope(authorized_company_ids),
        {"limit": limit},
    )
    return result


@app.get("/api/routing/tickets/{ticket_id}/recommendation")
def api_ticket_routing_recommendation(
    ticket_id: int,
    request: Request,
    limit: int = 5,
    authorized_company_ids: list[int] | None = Depends(require_company_scope),
) -> dict:
    result = ticket_routing_recommendation(ticket_id, limit=limit, authorized_company_ids=authorized_company_ids)
    record_success_audit(
        AuditAction.search,
        "routing.ticket_recommendation",
        getattr(request.state, "user", None),
        audit_scope(authorized_company_ids),
        {"ticket_id": ticket_id, "limit": limit},
    )
    return result


@app.get("/api/realtime/events")
def api_realtime_events(
    request: Request,
    limit: int = 25,
    authorized_company_ids: list[int] | None = Depends(require_company_scope),
) -> dict:
    result = recent_realtime_events(limit=limit, authorized_company_ids=authorized_company_ids)
    record_success_audit(
        AuditAction.search,
        "realtime.events",
        getattr(request.state, "user", None),
        audit_scope(authorized_company_ids),
        {"limit": limit},
    )
    return result


@app.post("/api/ticket-health/feedback")
def api_ticket_health_risk_feedback(
    payload: TicketHealthRiskFeedbackRequest,
    request: Request,
    _user: dict | None = Depends(require_roles(Role.admin, Role.technician)),
    authorized_company_ids: list[int] | None = Depends(require_company_scope),
) -> dict:
    result = store_ticket_health_risk_feedback(
        payload.ticket_id,
        payload.health_score,
        payload.risk_bucket,
        payload.outcome,
        payload.notes,
        authorized_company_ids=authorized_company_ids,
    )
    record_success_audit(
        AuditAction.feedback,
        "ticket_health.risk_feedback",
        getattr(request.state, "user", None),
        audit_scope(authorized_company_ids),
        {"ticket_id": payload.ticket_id, "outcome": payload.outcome},
    )
    return result


@app.post("/api/customer-success/feedback")
def api_customer_risk_feedback(
    payload: CustomerRiskFeedbackRequest,
    request: Request,
    _user: dict | None = Depends(require_roles(Role.admin, Role.technician)),
    authorized_company_ids: list[int] | None = Depends(require_company_scope),
) -> dict:
    result = store_customer_risk_feedback(
        payload.company_id,
        payload.risk_bucket,
        payload.outcome,
        payload.notes,
        authorized_company_ids=authorized_company_ids,
    )
    record_success_audit(
        AuditAction.feedback,
        "customer_success.risk_feedback",
        getattr(request.state, "user", None),
        audit_scope(authorized_company_ids),
        {"company_id": payload.company_id, "outcome": payload.outcome},
    )
    return result


@app.post("/api/routing/feedback")
def api_routing_feedback(
    payload: RoutingFeedbackRequest,
    request: Request,
    _user: dict | None = Depends(require_roles(Role.admin, Role.technician)),
    authorized_company_ids: list[int] | None = Depends(require_company_scope),
) -> dict:
    result = store_routing_feedback(
        payload.ticket_id,
        payload.recommended_resource_id,
        payload.recommended_resource_name,
        payload.outcome,
        payload.notes,
        authorized_company_ids=authorized_company_ids,
    )
    record_success_audit(
        AuditAction.feedback,
        "routing.feedback",
        getattr(request.state, "user", None),
        audit_scope(authorized_company_ids),
        {"ticket_id": payload.ticket_id, "outcome": payload.outcome},
    )
    return result


@app.get("/api/operations/status")
def api_operations_status(request: Request) -> dict:
    if not settings.app_route_auth_required:
        result = operations_status()
        record_success_audit(
            AuditAction.search,
            "operations.status.read",
            None,
            audit_scope(),
            {"scheduler_state": (result.get("scheduler") or {}).get("state")},
        )
        return result
    user = current_user(request)
    result = operations_status(
        {
            "authority_class": "authenticated-read",
            "roles": user.get("roles") or ["Authenticated"],
            "scope": audit_scope(),
        }
    )
    record_success_audit(
        AuditAction.search,
        "operations.status.read",
        user,
        audit_scope(),
        {"scheduler_state": (result.get("scheduler") or {}).get("state")},
    )
    return result


@app.get("/api/operations/settings")
def api_operations_settings(request: Request) -> dict:
    user = current_user(request) if settings.app_route_auth_required else None
    result = {"ok": True, "settings": operations_settings()}
    record_success_audit(
        AuditAction.search,
        "operations.settings.read",
        user,
        audit_scope(),
        {"setting_count": len(result["settings"])},
    )
    return result


@app.post("/api/operations/settings")
def api_update_operations_settings(payload: OperationsSettingsRequest, _user: dict | None = Depends(require_roles(Role.admin))) -> dict:
    result = {"ok": True, "settings": update_operations_settings(payload.settings)}
    record_success_audit(AuditAction.admin_action, "operations.settings.update", _user, audit_scope(), {"keys": sorted(payload.settings.keys())})
    return result


@app.get("/api/operations/jobs")
def api_operations_jobs(request: Request) -> dict:
    user = current_user(request) if settings.app_route_auth_required else None
    result = operations_jobs()
    record_success_audit(
        AuditAction.search,
        "operations.jobs.read",
        user,
        audit_scope(),
        {"job_count": len(result.get("jobs") or [])},
    )
    return result


@app.get("/api/operations/jobs/runs")
def api_operations_job_runs(request: Request) -> dict:
    user = current_user(request) if settings.app_route_auth_required else None
    result = job_runs()
    record_success_audit(
        AuditAction.search,
        "operations.job_runs.read",
        user,
        audit_scope(),
        {"run_count": len(result.get("runs") or []), "limit": result.get("limit")},
    )
    return result


@app.post("/api/operations/jobs/{job_name}/run")
def api_run_operation_job(job_name: str, _user: dict | None = Depends(require_roles(Role.admin))) -> dict:
    result = run_job(job_name, triggered_by="manual", force=True)
    record_success_audit(AuditAction.admin_action, "operations.job.run", _user, audit_scope(), {"job_name": job_name})
    return result


@app.post("/api/operations/jobs/{job_name}/enable")
def api_enable_operation_job(job_name: str, _user: dict | None = Depends(require_roles(Role.admin))) -> dict:
    result = set_job_enabled(job_name, True)
    record_success_audit(AuditAction.admin_action, "operations.job.enable", _user, audit_scope(), {"job_name": job_name})
    return result


@app.post("/api/operations/jobs/{job_name}/disable")
def api_disable_operation_job(job_name: str, _user: dict | None = Depends(require_roles(Role.admin))) -> dict:
    result = set_job_enabled(job_name, False)
    record_success_audit(AuditAction.admin_action, "operations.job.disable", _user, audit_scope(), {"job_name": job_name})
    return result


@app.post("/api/operations/pause")
def api_pause_operations(
    payload: OperationsPauseRequest | None = None,
    _user: dict | None = Depends(require_roles(Role.admin)),
) -> dict:
    reason = payload.reason if payload else None
    result = set_global_pause(True, actor=audit_actor(_user), reason=reason)
    record_success_audit(
        AuditAction.admin_action,
        "operations.pause",
        _user,
        audit_scope(),
        {
            "paused": True,
            "reason": (result.get("pause_provenance") or {}).get("reason"),
            "local_metadata_only": True,
            "runs_jobs": False,
            "autotask_writes_allowed": False,
        },
    )
    return result


@app.post("/api/operations/resume")
def api_resume_operations(
    payload: OperationsPauseRequest | None = None,
    _user: dict | None = Depends(require_roles(Role.admin)),
) -> dict:
    reason = payload.reason if payload else None
    result = set_global_pause(False, actor=audit_actor(_user), reason=reason)
    record_success_audit(
        AuditAction.admin_action,
        "operations.resume",
        _user,
        audit_scope(),
        {
            "paused": False,
            "reason": (result.get("pause_provenance") or {}).get("reason"),
            "local_metadata_only": True,
            "runs_jobs": False,
            "autotask_writes_allowed": False,
        },
    )
    return result


@app.post("/api/operations/jobs/{run_id}/request-stop")
def api_request_stop(run_id: int, _user: dict | None = Depends(require_roles(Role.admin))) -> dict:
    result = request_stop(run_id)
    record_success_audit(AuditAction.admin_action, "operations.job.request_stop", _user, audit_scope(), {"run_id": run_id})
    return result


@app.post("/api/operations/jobs/{run_id}/archive-stale")
def api_archive_stale_operation_job(run_id: int, _user: dict | None = Depends(require_roles(Role.admin))) -> dict:
    result = archive_stale_orphaned_run(run_id)
    record_success_audit(
        AuditAction.admin_action,
        "operations.job.archive_stale",
        _user,
        audit_scope(),
        {"run_id": run_id, "archived": bool(result.get("archived"))},
    )
    return result


@app.post("/api/assistant/ask")
def assistant_ask(
    payload: AskRequest,
    request: Request,
    authorized_company_ids: list[int] | None = Depends(require_company_scope),
) -> dict:
    actor = request_actor(request)
    result = ask_assistant(
        payload.question,
        mode=payload.mode,
        limit=payload.limit,
        include_noise=payload.include_noise,
        authorized_company_ids=authorized_company_ids,
        actor_username=actor,
    )
    record_success_audit(
        AuditAction.assistant_answer,
        "assistant.ask",
        getattr(request.state, "user", None),
        audit_scope(authorized_company_ids),
    )
    return result


@app.post("/api/assistant/feedback")
def assistant_feedback(
    payload: FeedbackRequest,
    request: Request,
    authorized_company_ids: list[int] | None = Depends(require_company_scope),
) -> dict:
    actor = request_actor(request)
    result = store_feedback(
        payload.answer_id,
        payload.rating,
        payload.notes,
        actor_username=actor,
        authorized_company_ids=authorized_company_ids,
    )
    record_success_audit(
        AuditAction.feedback,
        str(payload.answer_id),
        getattr(request.state, "user", None),
        audit_scope(authorized_company_ids),
        {"rating": payload.rating},
    )
    return result


@app.get("/api/admin/curated-memory")
def admin_curated_memory(_user: dict | None = Depends(require_roles(Role.admin))) -> dict:
    items = pending_memory()
    record_success_audit(AuditAction.admin_action, "curated_memory.pending.read", _user, audit_scope(), {"item_count": len(items)})
    return {"items": items}
