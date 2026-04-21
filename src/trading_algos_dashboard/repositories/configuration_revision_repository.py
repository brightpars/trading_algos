from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from trading_algos_dashboard.repositories.mongo_base import MongoRepository


class ConfigurationRevisionRepository(MongoRepository):
    def __init__(self, db: Any):
        super().__init__(db, "dashboard_configuration_revisions")

    def create_revision(self, document: Mapping[str, Any]) -> dict[str, Any]:
        payload = dict(document)
        self.collection.insert_one(payload)
        return self._without_id(payload) or {}

    def list_revisions(self, draft_id: str) -> list[dict[str, Any]]:
        return [
            self._without_id(doc) or {}
            for doc in self.collection.find({"draft_id": draft_id}).sort(
                "revision_no", -1
            )
        ]

    def delete_revisions(self, draft_id: str) -> int:
        result = self.collection.delete_many({"draft_id": draft_id})
        return int(getattr(result, "deleted_count", 0))
