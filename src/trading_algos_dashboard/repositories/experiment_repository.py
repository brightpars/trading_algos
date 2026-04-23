from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any

from pymongo import ReturnDocument

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

    def get_running_experiment(self) -> dict[str, Any] | None:
        running = self.list_running_experiments()
        if not running:
            return None
        return running[0]

    def list_running_experiments(self) -> list[dict[str, Any]]:
        running = self._list_documents({"status": "running"})
        return sorted(running, key=self._running_sort_key)

    def count_running_experiments(self) -> int:
        return self._count_documents({"status": "running"})

    def list_queued_experiments(self) -> list[dict[str, Any]]:
        queued = self._list_documents({"status": "queued"})
        return sorted(queued, key=self._queued_sort_key)

    def get_next_queued_experiment(self) -> dict[str, Any] | None:
        queued = self.list_queued_experiments()
        if not queued:
            return None
        return queued[0]

    def claim_next_queued_experiment(
        self, *, started_at: datetime
    ) -> dict[str, Any] | None:
        find_one_and_update = getattr(self.collection, "find_one_and_update", None)
        update_values = {
            "status": "running",
            "started_at": started_at,
            "updated_at": started_at,
            "finished_at": None,
            "duration_seconds": None,
            "cancelled_at": None,
            "error_message": None,
        }
        if callable(find_one_and_update):
            document = find_one_and_update(
                {"status": "queued"},
                {"$set": update_values},
                sort=[
                    ("queue_enqueued_at", 1),
                    ("created_at", 1),
                    ("experiment_id", 1),
                ],
                return_document=ReturnDocument.AFTER,
            )
            if not isinstance(document, Mapping):
                return None
            return self._without_id(document)

        queued = self.list_queued_experiments()
        if not queued:
            return None
        experiment = queued[0]
        experiment_id = str(experiment.get("experiment_id", ""))
        if not experiment_id:
            return None
        self.update_experiment(experiment_id, update_values)
        return self.get_experiment(experiment_id)

    def count_queued_before(self, experiment_id: str) -> int:
        for index, experiment in enumerate(self.list_queued_experiments()):
            if experiment.get("experiment_id") == experiment_id:
                return index
        return 0

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
        experiments = self._list_documents(filters)
        return sorted(experiments, key=self._created_at_sort_key, reverse=True)

    def list_completed_experiments_for_scope(
        self,
        *,
        symbol: str,
        start: datetime,
        end: datetime,
        status: str = "completed",
    ) -> list[dict[str, Any]]:
        experiments = self.list_experiments({"symbol": symbol, "status": status})
        normalized_start = self._normalize_datetime(start)
        normalized_end = self._normalize_datetime(end)
        matching: list[dict[str, Any]] = []
        for experiment in experiments:
            time_range = experiment.get("time_range")
            if not isinstance(time_range, Mapping):
                continue
            experiment_start = self._normalize_datetime(time_range.get("start"))
            experiment_end = self._normalize_datetime(time_range.get("end"))
            if (
                experiment_start == normalized_start
                and experiment_end == normalized_end
            ):
                matching.append(experiment)
        return matching

    def list_completed_experiment_cohorts(self) -> list[dict[str, Any]]:
        experiments = self.list_experiments({"status": "completed"})
        cohorts_by_key: dict[tuple[str, datetime, datetime], dict[str, Any]] = {}
        for experiment in experiments:
            symbol = str(experiment.get("symbol", "")).strip().upper()
            if not symbol:
                continue
            time_range = experiment.get("time_range")
            if not isinstance(time_range, Mapping):
                continue
            start = self._normalize_datetime(time_range.get("start"))
            end = self._normalize_datetime(time_range.get("end"))
            if start is None or end is None:
                continue
            cohort_key = (symbol, start, end)
            cohort = cohorts_by_key.setdefault(
                cohort_key,
                {
                    "symbol": symbol,
                    "start": start,
                    "end": end,
                    "completed_run_count": 0,
                    "latest_finished_at": None,
                    "candle_counts": set(),
                    "dataset_endpoints": set(),
                    "experiment_ids": [],
                },
            )
            cohort["completed_run_count"] += 1
            cohort["experiment_ids"].append(str(experiment.get("experiment_id", "")))
            finished_at = self._normalize_datetime(experiment.get("finished_at"))
            latest_finished_at = cohort.get("latest_finished_at")
            if isinstance(finished_at, datetime) and (
                latest_finished_at is None or finished_at > latest_finished_at
            ):
                cohort["latest_finished_at"] = finished_at
            candle_count = experiment.get("candle_count")
            if isinstance(candle_count, int):
                cohort["candle_counts"].add(candle_count)
            dataset_source = experiment.get("dataset_source")
            if isinstance(dataset_source, Mapping):
                endpoint = str(dataset_source.get("endpoint", "")).strip()
                if endpoint:
                    cohort["dataset_endpoints"].add(endpoint)

        normalized_cohorts: list[dict[str, Any]] = []
        for cohort in cohorts_by_key.values():
            normalized_cohorts.append(
                {
                    "symbol": cohort["symbol"],
                    "start": cohort["start"],
                    "end": cohort["end"],
                    "completed_run_count": cohort["completed_run_count"],
                    "latest_finished_at": cohort["latest_finished_at"],
                    "candle_counts": sorted(cohort["candle_counts"]),
                    "dataset_endpoints": sorted(cohort["dataset_endpoints"]),
                    "experiment_ids": sorted(cohort["experiment_ids"]),
                }
            )
        return sorted(
            normalized_cohorts,
            key=lambda item: (
                item["latest_finished_at"] or datetime.min.replace(tzinfo=timezone.utc),
                str(item["symbol"]),
                str(item["start"]),
                str(item["end"]),
            ),
            reverse=True,
        )

    def count_experiments(self) -> int:
        return self._count_documents()

    def delete_experiment(self, experiment_id: str) -> bool:
        result = self.collection.delete_one({"experiment_id": experiment_id})
        return bool(getattr(result, "deleted_count", 0))

    def delete_all_experiments(self) -> int:
        return self._delete_many()

    @staticmethod
    def _created_at_sort_key(document: Mapping[str, Any]) -> tuple[datetime, str]:
        created_at = ExperimentRepository._normalize_datetime(
            document.get("created_at")
        )
        fallback = datetime.min.replace(tzinfo=timezone.utc)
        return created_at or fallback, str(document.get("experiment_id", ""))

    @staticmethod
    def _queued_sort_key(document: Mapping[str, Any]) -> tuple[datetime, datetime, str]:
        enqueued_at = ExperimentRepository._normalize_datetime(
            document.get("queue_enqueued_at")
        )
        created_at = ExperimentRepository._normalize_datetime(
            document.get("created_at")
        )
        fallback = datetime.min.replace(tzinfo=timezone.utc)
        return (
            enqueued_at or created_at or fallback,
            created_at or fallback,
            str(document.get("experiment_id", "")),
        )

    @staticmethod
    def _running_sort_key(document: Mapping[str, Any]) -> tuple[datetime, str]:
        started_at = ExperimentRepository._normalize_datetime(
            document.get("started_at")
        )
        created_at = ExperimentRepository._normalize_datetime(
            document.get("created_at")
        )
        fallback = datetime.min.replace(tzinfo=timezone.utc)
        return started_at or created_at or fallback, str(
            document.get("experiment_id", "")
        )

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

    @staticmethod
    def _iter_documents(cursor: object) -> list[Mapping[str, Any]]:
        if isinstance(cursor, list):
            return [doc for doc in cursor if isinstance(doc, Mapping)]
        if isinstance(cursor, Iterable):
            return [doc for doc in cursor if isinstance(doc, Mapping)]
        docs = getattr(cursor, "docs", None)
        if isinstance(docs, list):
            return [doc for doc in docs if isinstance(doc, Mapping)]
        return []

    def _list_documents(
        self, filters: Mapping[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        query = dict(filters or {})
        documents = [
            self._without_id(doc) or {}
            for doc in self._iter_documents(self.collection.find(query))
        ]
        if query:
            documents = [
                doc
                for doc in documents
                if all(doc.get(key) == value for key, value in query.items())
            ]
        return documents
