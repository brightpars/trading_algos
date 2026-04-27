from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from trading_algos_dashboard.repositories.mongo_base import MongoRepository

_PREFERENCES_ID = "dashboard_experiment_form_preferences"


class ExperimentFormPreferencesRepository(MongoRepository):
    def __init__(self, db: Any):
        super().__init__(db, "dashboard_experiment_form_preferences")

    def get_preferences(self) -> dict[str, Any] | None:
        document = self.collection.find_one({"preferences_id": _PREFERENCES_ID})
        if document is None:
            return None
        return self._without_id(document)

    def save_preferences(self, preferences: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "preferences_id": _PREFERENCES_ID,
            **preferences,
            "updated_at": datetime.now(timezone.utc),
        }
        self.collection.update_one(
            {"preferences_id": _PREFERENCES_ID},
            {"$set": payload},
            upsert=True,
        )
        return payload
