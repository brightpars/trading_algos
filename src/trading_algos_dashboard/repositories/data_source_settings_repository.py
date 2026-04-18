from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from trading_algos_dashboard.repositories.mongo_base import MongoRepository

_SETTINGS_ID = "default"


class DataSourceSettingsRepository(MongoRepository):
    def __init__(self, db: Any):
        super().__init__(db, "dashboard_data_source_settings")

    def get_settings(self) -> dict[str, Any] | None:
        return self._without_id(self.collection.find_one({"settings_id": _SETTINGS_ID}))

    def save_settings(self, *, ip: str, port: int) -> dict[str, Any]:
        payload = {
            "settings_id": _SETTINGS_ID,
            "ip": ip,
            "port": port,
            "updated_at": datetime.now(timezone.utc),
        }
        self.collection.update_one(
            {"settings_id": _SETTINGS_ID},
            {"$set": payload},
            upsert=True,
        )
        return payload
