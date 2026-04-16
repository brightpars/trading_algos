from __future__ import annotations

from typing import Any

from trading_algos_dashboard.repositories.mongo_base import MongoRepository


class ResultRepository(MongoRepository):
    def __init__(self, db: Any):
        super().__init__(db, "dashboard_results")

    def insert_result(self, document: dict[str, Any]) -> dict[str, Any]:
        payload = dict(document)
        self.collection.insert_one(payload)
        return self._without_id(payload) or {}

    def list_results_for_experiment(self, experiment_id: str) -> list[dict[str, Any]]:
        return [
            self._without_id(doc) or {}
            for doc in self.collection.find({"experiment_id": experiment_id}).sort(
                "alg_name", 1
            )
        ]

    def get_result(self, experiment_id: str, alg_key: str) -> dict[str, Any] | None:
        return self._without_id(
            self.collection.find_one(
                {"experiment_id": experiment_id, "alg_key": alg_key}
            )
        )
