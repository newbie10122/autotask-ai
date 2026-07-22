from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin

import httpx

from .config import settings
from .db import db_connection


TRANSIENT_STATUS_CODES = {408, 429, 500, 502, 503, 504}
STATUS_TRANSITION_CANDIDATE_ENTITIES: tuple[str, ...] = (
    "TicketStatusHistory",
    "TicketStatusHistories",
    "TicketHistory",
    "TicketChangeHistory",
)
REFERENCE_METADATA_CANDIDATE_ENTITIES: tuple[str, ...] = (
    "TicketPriorities",
    "Priorities",
    "TicketCategories",
    "TicketIssueTypes",
    "TicketSubIssueTypes",
    "Queues",
    "TicketQueues",
    "TicketStatuses",
)
STATUS_TRANSITION_PROBE_FILTERS: dict[str, list[dict[str, Any]]] = {}


@dataclass(frozen=True)
class AutotaskHeaders:
    username: str
    secret: str
    api_integration_code: str

    def as_http_headers(self) -> dict[str, str]:
        return {
            "Username": self.username,
            "Secret": self.secret,
            "APIIntegrationcode": self.api_integration_code,
            "Content-Type": "application/json",
        }


class AutotaskReadOnlyClient:
    def __init__(self, sync_run_id: int | None = None, delay_seconds: float = 0.25) -> None:
        self.base_url = settings.autotask_base_url.rstrip("/")
        self.page_size = min(max(settings.autotask_page_size, 1), 500)
        self.sync_run_id = sync_run_id
        self.delay_seconds = delay_seconds
        self.headers = AutotaskHeaders(
            username=settings.autotask_username,
            secret=settings.autotask_secret,
            api_integration_code=settings.autotask_api_integration_code,
        )
        self._consecutive_errors = 0

    def _check_config(self) -> None:
        missing = [
            name
            for name, value in {
                "AUTOTASK_BASE_URL": self.base_url,
                "AUTOTASK_USERNAME": self.headers.username,
                "AUTOTASK_SECRET": self.headers.secret,
                "AUTOTASK_API_INTEGRATION_CODE": self.headers.api_integration_code,
            }.items()
            if not value
        ]
        if missing:
            raise RuntimeError(f"Missing Autotask configuration: {', '.join(missing)}")

    def _url(self, endpoint_or_url: str) -> str:
        if endpoint_or_url.startswith("http://") or endpoint_or_url.startswith("https://"):
            return endpoint_or_url
        return urljoin(f"{self.base_url}/", endpoint_or_url.lstrip("/"))

    def _log_call(
        self,
        endpoint: str,
        method: str,
        status_code: int | None,
        duration_ms: int,
        success: bool,
        error_message: str | None = None,
        record_count: int = 0,
    ) -> None:
        try:
            with db_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO autotask_api_calls
                    (sync_run_id, endpoint, method, status_code, duration_ms, success, error_message, record_count)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        self.sync_run_id,
                        endpoint,
                        method,
                        status_code,
                        duration_ms,
                        success,
                        error_message[:500] if error_message else None,
                        record_count,
                    ),
                )
        except Exception:
            pass

    def _request(self, method: str, endpoint_or_url: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        self._check_config()
        endpoint = endpoint_or_url.replace(self.base_url, "")
        last_error: Exception | None = None
        for attempt in range(1, 4):
            started = time.monotonic()
            status_code: int | None = None
            try:
                if self.delay_seconds:
                    time.sleep(self.delay_seconds)
                with httpx.Client(timeout=45) as client:
                    response = client.request(
                        method,
                        self._url(endpoint_or_url),
                        headers=self.headers.as_http_headers(),
                        json=json,
                    )
                status_code = response.status_code
                duration_ms = int((time.monotonic() - started) * 1000)
                if response.status_code in TRANSIENT_STATUS_CODES and attempt < 3:
                    self._log_call(endpoint, method, status_code, duration_ms, False, "transient status")
                    time.sleep(attempt)
                    continue
                response.raise_for_status()
                payload = response.json() if response.content else {}
                records = payload.get("items") or payload.get("records") or payload.get("value") or []
                self._consecutive_errors = 0
                self._log_call(endpoint, method, status_code, duration_ms, True, record_count=len(records))
                return payload
            except Exception as exc:
                duration_ms = int((time.monotonic() - started) * 1000)
                last_error = exc
                self._consecutive_errors += 1
                self._log_call(endpoint, method, status_code, duration_ms, False, str(exc))
                if self._consecutive_errors >= 5:
                    raise RuntimeError("Autotask sync stopped after repeated request errors.") from exc
                if attempt < 3:
                    time.sleep(attempt)
                    continue
                raise
        raise RuntimeError("Autotask request failed.") from last_error

    def threshold_information(self) -> dict[str, Any]:
        return self._request("GET", "/V1.0/ThresholdInformation")

    def test_connection(self) -> dict[str, Any]:
        payload = self.threshold_information()
        return {
            "ok": True,
            "base_url": self.base_url,
            "username": self.headers.username,
            "threshold": payload,
        }

    def ticket_entity_fields(self) -> list[dict[str, Any]]:
        payload = self._request("GET", "/V1.0/Tickets/entityInformation/fields")
        fields = payload.get("fields") or []
        return [field for field in fields if isinstance(field, dict)]

    def query_entity(
        self,
        entity: str,
        filters: list[dict[str, Any]] | None = None,
        include_fields: list[str] | None = None,
        max_records: int | None = None,
    ) -> dict[str, Any]:
        record_limit = min(max(max_records or self.page_size, 1), 500)
        query: dict[str, Any] = {
            "MaxRecords": record_limit,
            "filter": filters or [{"op": "gte", "field": "id", "value": 0}],
        }
        if include_fields:
            query["IncludeFields"] = include_fields
        return self._request("POST", f"/V1.0/{entity}/query", json=query)

    def _ticket_history_probe_filters(self) -> list[dict[str, Any]]:
        try:
            with db_connection() as conn:
                row = conn.execute(
                    """
                    SELECT autotask_id
                    FROM autotask_tickets
                    WHERE autotask_id IS NOT NULL
                    ORDER BY updated_at_autotask DESC NULLS LAST, id DESC
                    LIMIT 1
                    """
                ).fetchone()
            if row and row.get("autotask_id") is not None:
                return [{"op": "eq", "field": "ticketID", "value": int(row["autotask_id"])}]
        except Exception:
            pass
        return [{"op": "gte", "field": "ticketID", "value": 0}]

    def _status_transition_probe_filters(self, entity: str) -> list[dict[str, Any]]:
        if entity == "TicketHistory":
            return self._ticket_history_probe_filters()
        return STATUS_TRANSITION_PROBE_FILTERS.get(entity) or [{"op": "gte", "field": "id", "value": 0}]

    def probe_status_transition_sources(
        self,
        entities: tuple[str, ...] = STATUS_TRANSITION_CANDIDATE_ENTITIES,
    ) -> dict[str, Any]:
        results: list[dict[str, Any]] = []
        for entity in entities:
            self._consecutive_errors = 0
            filters = self._status_transition_probe_filters(entity)
            try:
                payload = self.query_entity(
                    entity,
                    filters=filters,
                    max_records=1,
                )
                items = payload.get("items") or payload.get("records") or payload.get("value") or []
                results.append(
                    {
                        "entity": entity,
                        "availability": "available",
                        "sample_count": len(items[:1]),
                        "probe_filter": filters,
                        "has_next_page": bool(
                            payload.get("pageDetails", {}).get("nextPageUrl") or payload.get("nextPageUrl")
                        ),
                        "error": None,
                    }
                )
            except Exception as exc:
                self._consecutive_errors = 0
                results.append(
                    {
                        "entity": entity,
                        "availability": "unavailable",
                        "sample_count": 0,
                        "probe_filter": filters,
                        "has_next_page": False,
                        "error": f"{exc.__class__.__name__}: {str(exc)[:240]}",
                    }
                )
        return {
            "ok": True,
            "probe": "status_transition_source_candidates",
            "live_autotask_probe_ran": True,
            "autotask_writes_allowed": False,
            "max_records_per_entity": 1,
            "candidate_entities": list(entities),
            "results": results,
            "available_entities": [item["entity"] for item in results if item["availability"] == "available"],
            "policy": {
                "read_only": True,
                "manual_admin_only": True,
                "automatic_sync_path_changes_allowed": False,
                "automatic_model_or_workflow_changes_allowed": False,
            },
        }

    def probe_reference_metadata_sources(
        self,
        entities: tuple[str, ...] = REFERENCE_METADATA_CANDIDATE_ENTITIES,
    ) -> dict[str, Any]:
        results: list[dict[str, Any]] = []
        for entity in entities:
            self._consecutive_errors = 0
            filters = [{"op": "gte", "field": "id", "value": 0}]
            try:
                payload = self.query_entity(entity, filters=filters, max_records=1)
                items = payload.get("items") or payload.get("records") or payload.get("value") or []
                results.append(
                    {
                        "entity": entity,
                        "availability": "available",
                        "sample_count": len(items[:1]),
                        "probe_filter": filters,
                        "has_next_page": bool(
                            payload.get("pageDetails", {}).get("nextPageUrl") or payload.get("nextPageUrl")
                        ),
                        "error": None,
                    }
                )
            except Exception as exc:
                self._consecutive_errors = 0
                results.append(
                    {
                        "entity": entity,
                        "availability": "unavailable",
                        "sample_count": 0,
                        "probe_filter": filters,
                        "has_next_page": False,
                        "error": f"{exc.__class__.__name__}: {str(exc)[:240]}",
                    }
                )
        return {
            "ok": True,
            "probe": "reference_metadata_source_candidates",
            "live_autotask_probe_ran": True,
            "autotask_writes_allowed": False,
            "max_records_per_entity": 1,
            "candidate_entities": list(entities),
            "results": results,
            "available_entities": [item["entity"] for item in results if item["availability"] == "available"],
            "policy": {
                "read_only": True,
                "manual_admin_only": True,
                "automatic_reference_sync_allowed": False,
                "automatic_model_or_workflow_changes_allowed": False,
            },
        }

    def follow_next_page(self, next_page_url: str) -> dict[str, Any]:
        method = "POST" if "/query/next" in next_page_url else "GET"
        return self._request(method, next_page_url)

    def iter_entity_pages(
        self,
        entity: str,
        filters: list[dict[str, Any]] | None = None,
        limit: int | None = None,
    ):
        pulled = 0
        payload = self.query_entity(entity, filters=filters)
        while True:
            items = payload.get("items") or payload.get("records") or payload.get("value") or []
            if limit is not None:
                items = items[: max(0, limit - pulled)]
            pulled += len(items)
            yield items, payload
            if limit is not None and pulled >= limit:
                break
            next_page_url = payload.get("pageDetails", {}).get("nextPageUrl") or payload.get("nextPageUrl")
            if not next_page_url:
                break
            payload = self.follow_next_page(next_page_url)

    def query_tickets_page(self, resume_token: str | None = None) -> dict:
        filters = [{"op": "gt", "field": "id", "value": int(resume_token or 0)}]
        payload = self.query_entity("Tickets", filters=filters)
        records = payload.get("items") or payload.get("records") or []
        next_resume_token = str(max([item.get("id", 0) for item in records] or [resume_token or 0]))
        return {"records": records, "next_resume_token": next_resume_token, "page_size": self.page_size}

    def create_ticket(self, *_args, **_kwargs):
        raise NotImplementedError("Autotask write calls are disabled in the MVP.")

    def update_ticket(self, *_args, **_kwargs):
        raise NotImplementedError("Autotask write calls are disabled in the MVP.")

    def delete_ticket(self, *_args, **_kwargs):
        raise NotImplementedError("Autotask write calls are disabled in the MVP.")
