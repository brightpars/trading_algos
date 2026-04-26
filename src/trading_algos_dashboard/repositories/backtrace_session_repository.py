from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from trading_algos_dashboard.repositories.mongo_base import MongoRepository


class BacktraceSessionRepository(MongoRepository):
    def __init__(self, db: Any):
        super().__init__(db, "dashboard_backtrace_sessions")

    def create_session(self, document: Mapping[str, Any]) -> dict[str, Any]:
        payload = dict(document)
        self.collection.insert_one(payload)
        return self._without_id(payload) or {}

    def update_session(self, run_id: str, values: Mapping[str, Any]) -> None:
        self.collection.update_one(
            {"run_id": run_id},
            {"$set": dict(values)},
        )

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        return self._without_id(self.collection.find_one({"run_id": run_id}))

    def list_recent_runs(self, *, limit: int = 20) -> list[dict[str, Any]]:
        documents = self._list_documents()
        documents.sort(key=self._recent_sort_key, reverse=True)
        return documents[: max(limit, 0)]

    @staticmethod
    def _recent_sort_key(document: Mapping[str, Any]) -> tuple[datetime, str]:
        created_at = BacktraceSessionRepository._normalize_datetime(
            document.get("created_at")
        )
        fallback = datetime.min.replace(tzinfo=timezone.utc)
        return created_at or fallback, str(document.get("run_id", ""))

    @staticmethod
    def _normalize_datetime(value: object) -> datetime | None:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        return None

    def _list_documents(self) -> list[dict[str, Any]]:
        return [
            self._without_id(doc) or {}
            for doc in self.collection.find({})
            if isinstance(doc, Mapping)
        ]
