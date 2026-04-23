from __future__ import annotations

from datetime import datetime, timezone
from collections.abc import Mapping
from typing import Any

from trading_algos_dashboard.repositories.mongo_base import MongoRepository

_SETTINGS_ID = "market_data_cache"


class MarketDataCacheSettingsRepository(MongoRepository):
    def __init__(self, db: Any):
        super().__init__(db, "dashboard_market_data_cache_settings")

    def get_settings(self) -> dict[str, Any] | None:
        find_one = getattr(self.collection, "find_one", None)
        if callable(find_one):
            document = find_one({"settings_id": _SETTINGS_ID})
            if isinstance(document, Mapping):
                return self._without_id(document)
            return None
        for document in self.collection.find({"settings_id": _SETTINGS_ID}):
            if isinstance(document, Mapping):
                return self._without_id(document)
        return None

    def save_settings(
        self,
        *,
        memory_enabled: bool,
        memory_max_entries: int,
        shared_enabled: bool,
        shared_max_entries: int,
        shared_ttl_hours: int,
    ) -> dict[str, Any]:
        payload = {
            "settings_id": _SETTINGS_ID,
            "memory_enabled": memory_enabled,
            "memory_max_entries": memory_max_entries,
            "shared_enabled": shared_enabled,
            "shared_max_entries": shared_max_entries,
            "shared_ttl_hours": shared_ttl_hours,
            "updated_at": datetime.now(timezone.utc),
        }
        self.collection.update_one(
            {"settings_id": _SETTINGS_ID},
            {"$set": payload},
            upsert=True,
        )
        return payload
