from __future__ import annotations

from typing import Any
from typing import cast

from pymongo import ReturnDocument

from trading_algos_dashboard.service_runtime import MongoCounterRepository


def test_mongo_counter_repository_uses_pipeline_update_for_seq_increment() -> None:
    recorded: dict[str, Any] = {}

    class _CounterCollection:
        def find_one_and_update(
            self,
            query: dict[str, Any],
            update: object,
            *,
            upsert: bool,
            return_document: Any,
        ) -> dict[str, Any]:
            recorded["query"] = query
            recorded["update"] = update
            recorded["upsert"] = upsert
            recorded["return_document"] = return_document
            return {"_id": query["_id"], "seq": 5}

    repository = cast(
        MongoCounterRepository,
        MongoCounterRepository.__new__(MongoCounterRepository),
    )
    setattr(repository, "_counter_collection", cast(Any, _CounterCollection()))

    value = repository.get_next_counter_value("execution_id", 4)

    assert value == 5
    assert recorded["query"] == {"_id": "execution_id"}
    assert recorded["upsert"] is True
    assert recorded["return_document"] == ReturnDocument.AFTER
    assert recorded["update"] == [
        {
            "$set": {
                "seq": {
                    "$add": [{"$ifNull": ["$seq", 4]}, 1],
                }
            }
        }
    ]


def test_mongo_counter_repository_seed_reads_latest_domain_value() -> None:
    class _Collection:
        def __init__(self, latest: dict[str, Any] | None) -> None:
            self.latest = latest
            self.calls: list[dict[str, Any]] = []

        def find_one(
            self, *, sort: list[tuple[str, int]], projection: dict[str, bool]
        ) -> dict[str, Any] | None:
            self.calls.append({"sort": sort, "projection": projection})
            return self.latest

    executions_collection = _Collection({"executionID": 17})
    repository = cast(
        MongoCounterRepository,
        MongoCounterRepository.__new__(MongoCounterRepository),
    )
    setattr(
        repository,
        "_counter_specs",
        {"execution_id": ("executions", "executionID")},
    )
    setattr(repository, "_db", {"executions": executions_collection})

    value = repository.get_counter_seed_value("execution_id")

    assert value == 17
    assert executions_collection.calls == [
        {
            "sort": [("executionID", -1)],
            "projection": {"executionID": True},
        }
    ]
