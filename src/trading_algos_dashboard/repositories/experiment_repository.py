from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from trading_algos_dashboard.repositories.mongo_base import MongoRepository


class ExperimentRepository(MongoRepository):
    def __init__(self, db: Any):
        super().__init__(db, "dashboard_experiments")

    def create_experiment(self, document: Mapping[str, Any]) -> dict[str, Any]:
        payload = dict(document)
        self.collection.insert_one(payload)
        return self._without_id(payload) or {}

    def update_experiment_status(self, experiment_id: str, status: str) -> None:
        self.collection.update_one(
            {"experiment_id": experiment_id},
            {"$set": {"status": status}},
        )

    def update_experiment(self, experiment_id: str, values: Mapping[str, Any]) -> None:
        self.collection.update_one(
            {"experiment_id": experiment_id},
            {"$set": dict(values)},
        )

    def update_selected_algorithms(
        self, experiment_id: str, selected_algorithms: list[dict[str, Any]]
    ) -> None:
        self.collection.update_one(
            {"experiment_id": experiment_id},
            {"$set": {"selected_algorithms": selected_algorithms}},
        )

    def clear_selected_algorithms(self, experiment_id: str) -> None:
        self.collection.update_one(
            {"experiment_id": experiment_id},
            {"$set": {"selected_algorithms": []}},
        )

    def get_experiment(self, experiment_id: str) -> dict[str, Any] | None:
        return self._without_id(
            self.collection.find_one({"experiment_id": experiment_id})
        )

    def update_input_snapshot(
        self, experiment_id: str, *, input_kind: str, input_snapshot: dict[str, Any]
    ) -> None:
        self.collection.update_one(
            {"experiment_id": experiment_id},
            {"$set": {"input_kind": input_kind, "input_snapshot": input_snapshot}},
        )

    def list_experiments(
        self, filters: Mapping[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        query = dict(filters or {})
        return [
            self._without_id(doc) or {}
            for doc in self.collection.find(query).sort("created_at", -1)
        ]

    def count_experiments(self) -> int:
        return self._count_documents()

    def delete_all_experiments(self) -> int:
        return self._delete_many()
