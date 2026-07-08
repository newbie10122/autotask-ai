from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin

import httpx

from .config import settings
from .db import db_connection


TRANSIENT_STATUS_CODES = {408, 429, 500, 502, 503, 504}


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

    def query_entity(
        self,
        entity: str,
        filters: list[dict[str, Any]] | None = None,
        include_fields: list[str] | None = None,
    ) -> dict[str, Any]:
        query: dict[str, Any] = {
            "MaxRecords": self.page_size,
            "filter": filters or [{"op": "gte", "field": "id", "value": 0}],
        }
        if include_fields:
            query["IncludeFields"] = include_fields
        return self._request("POST", f"/V1.0/{entity}/query", json=query)

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
