from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from pymongo import ReturnDocument

from trading_algos_dashboard.repositories.mongo_base import MongoRepository

_LEASE_ID = "experiment_dispatch"


class ExperimentSchedulerLeaseRepository(MongoRepository):
    def __init__(self, db: Any):
        super().__init__(db, "dashboard_experiment_scheduler_lease")

    def try_acquire_lease(self, *, owner_id: str, expires_at: datetime) -> bool:
        find_one_and_update = getattr(self.collection, "find_one_and_update", None)
        now = datetime.now(timezone.utc)
        payload = {
            "lease_id": _LEASE_ID,
            "owner_id": owner_id,
            "expires_at": expires_at,
            "updated_at": now,
        }
        if callable(find_one_and_update):
            document = find_one_and_update(
                {
                    "lease_id": _LEASE_ID,
                    "$or": [
                        {"expires_at": {"$lte": now}},
                        {"owner_id": owner_id},
                    ],
                },
                {"$set": payload},
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )
            if isinstance(document, Mapping):
                return document.get("owner_id") == owner_id

        existing = self.collection.find_one({"lease_id": _LEASE_ID})
        if isinstance(existing, Mapping):
            existing_owner_id = existing.get("owner_id")
            existing_expires_at = existing.get("expires_at")
            if (
                isinstance(existing_owner_id, str)
                and existing_owner_id != owner_id
                and isinstance(existing_expires_at, datetime)
                and existing_expires_at > now
            ):
                return False
        self.collection.update_one(
            {"lease_id": _LEASE_ID},
            {"$set": payload},
            upsert=True,
        )
        stored = self.collection.find_one({"lease_id": _LEASE_ID})
        return bool(isinstance(stored, Mapping) and stored.get("owner_id") == owner_id)

    def release_lease(self, *, owner_id: str) -> None:
        document = self.collection.find_one({"lease_id": _LEASE_ID})
        if not isinstance(document, Mapping):
            return
        if document.get("owner_id") != owner_id:
            return
        self.collection.update_one(
            {"lease_id": _LEASE_ID},
            {
                "$set": {
                    "owner_id": None,
                    "expires_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
