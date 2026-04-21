from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from trading_algos_dashboard.repositories.publication_record_repository import (
    PublicationRecordRepository,
)


class SmartTradePublishError(RuntimeError):
    pass


class ConfigurationPublishService:
    def __init__(
        self,
        *,
        publication_record_repository: PublicationRecordRepository,
        base_url: str,
        token: str,
        timeout_secs: int,
    ):
        self.publication_record_repository = publication_record_repository
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout_secs = timeout_secs

    def _request(
        self, *, method: str, path: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        data = None
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
        request = Request(
            url=f"{self.base_url}{path}",
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=self.timeout_secs) as response:
                response_payload = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8") if exc.fp else str(exc)
            raise SmartTradePublishError(detail) from exc
        except URLError as exc:
            raise SmartTradePublishError(str(exc.reason)) from exc
        if response_payload == "":
            return {}
        parsed = json.loads(response_payload)
        if not isinstance(parsed, dict):
            raise SmartTradePublishError(
                "SmartTrade API returned a non-object response"
            )
        return parsed

    def validate_remote(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request(
            method="POST",
            path="/api/algorithm-configurations/validate",
            payload=payload,
        )

    def publish(self, *, draft_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        result = self._request(
            method="POST",
            path="/api/algorithm-configurations",
            payload=payload,
        )
        self.publication_record_repository.create_record(
            {
                "draft_id": draft_id,
                "created_at": datetime.now(timezone.utc),
                "result": result,
                "remote_config_id": result.get("config_id"),
                "remote_status": result.get("status", "published"),
            }
        )
        return result

    def list_records_for_draft(self, draft_id: str) -> list[dict[str, Any]]:
        return self.publication_record_repository.list_records_for_draft(draft_id)
