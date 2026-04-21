from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from trading_algos_dashboard.repositories.mongo_base import MongoRepository


class ConfigurationDraftRepository(MongoRepository):
    def __init__(self, db: Any):
        super().__init__(db, "dashboard_configuration_drafts")

    def create_draft(self, document: Mapping[str, Any]) -> dict[str, Any]:
        payload = dict(document)
        self.collection.insert_one(payload)
        return self._without_id(payload) or {}

    def update_draft(self, draft_id: str, updates: Mapping[str, Any]) -> None:
        self.collection.update_one({"draft_id": draft_id}, {"$set": dict(updates)})

    def get_draft(self, draft_id: str) -> dict[str, Any] | None:
        return self._without_id(self.collection.find_one({"draft_id": draft_id}))

    def list_drafts(self) -> list[dict[str, Any]]:
        return [
            self._without_id(doc) or {}
            for doc in self.collection.find({}).sort("updated_at", -1)
        ]

    def delete_draft(self, draft_id: str) -> bool:
        result = self.collection.delete_one({"draft_id": draft_id})
        return bool(getattr(result, "deleted_count", 0))
