from __future__ import annotations

from typing import Any
from typing import cast

from trading_algos_dashboard.service_runtime import MongoCounterRepository


def test_mongo_counter_repository_uses_pipeline_update_for_seq_increment() -> None:
    recorded: dict[str, Any] = {}

    class _Collection:
        def update_one(
            self, query: dict[str, Any], update: object, *, upsert: bool
        ) -> None:
            recorded["query"] = query
            recorded["update"] = update
            recorded["upsert"] = upsert

        def find_one(self, query: dict[str, Any]) -> dict[str, Any]:
            recorded.setdefault("find_one_calls", []).append(query)
            return {"_id": query["_id"], "seq": 5}

    repository = cast(
        MongoCounterRepository,
        MongoCounterRepository.__new__(MongoCounterRepository),
    )
    setattr(repository, "_collection", cast(Any, _Collection()))

    value = repository.get_next_counter_value("execution_id", 4)

    assert value == 5
    assert recorded["query"] == {"_id": "execution_id"}
    assert recorded["upsert"] is True
    assert recorded["update"] == [
        {
            "$set": {
                "seq": {
                    "$add": [{"$ifNull": ["$seq", 4]}, 1],
                }
            }
        }
    ]
