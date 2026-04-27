from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from trading_algos_dashboard.repositories.mongo_base import MongoRepository

_SETTINGS_ID = "dashboard_service_control"


class ServerControlSettingsRepository(MongoRepository):
    def __init__(self, db: Any):
        super().__init__(db, "dashboard_server_control_settings")

    def get_settings(self) -> dict[str, Any] | None:
        document = self.collection.find_one({"settings_id": _SETTINGS_ID})
        if document is not None:
            return self._without_id(document)
        return None

    def save_settings(self, *, ports: dict[str, int]) -> dict[str, Any]:
        payload = {
            "settings_id": _SETTINGS_ID,
            "ports": dict(ports),
            "updated_at": datetime.now(timezone.utc),
        }
        self.collection.update_one(
            {"settings_id": _SETTINGS_ID},
            {"$set": payload},
            upsert=True,
        )
        return payload
