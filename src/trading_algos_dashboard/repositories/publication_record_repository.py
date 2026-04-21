from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from trading_algos_dashboard.repositories.mongo_base import MongoRepository


class PublicationRecordRepository(MongoRepository):
    def __init__(self, db: Any):
        super().__init__(db, "dashboard_publication_records")

    def create_record(self, document: Mapping[str, Any]) -> dict[str, Any]:
        payload = dict(document)
        self.collection.insert_one(payload)
        return self._without_id(payload) or {}

    def list_records_for_draft(self, draft_id: str) -> list[dict[str, Any]]:
        return [
            self._without_id(doc) or {}
            for doc in self.collection.find({"draft_id": draft_id}).sort(
                "created_at", -1
            )
        ]
