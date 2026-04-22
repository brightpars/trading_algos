from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import uuid4

from trading_algos_dashboard.repositories.mongo_base import MongoRepository


class AlgorithmCatalogImportRunRepository(MongoRepository):
    def __init__(self, db: Any):
        super().__init__(db, "algorithm_catalog_import_runs")

    def create_run(self, document: Mapping[str, Any]) -> dict[str, Any]:
        payload = dict(document)
        payload["id"] = str(payload.get("id") or uuid4().hex)
        self.collection.insert_one(payload)
        return self._without_id(payload) or {}

    def list_runs(self) -> list[dict[str, Any]]:
        items = [
            self._without_id(document) or {} for document in self.collection.find({})
        ]
        return sorted(items, key=lambda item: item.get("started_at", ""), reverse=True)

    def get_latest_run(self) -> dict[str, Any] | None:
        items = self.list_runs()
        return items[0] if items else None

    def get_run_by_id(self, run_id: str) -> dict[str, Any] | None:
        return self._without_id(self.collection.find_one({"id": run_id}))

    def count_runs(self) -> int:
        return self._count_documents()
