from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class MongoRepository:
    def __init__(self, db: Any, collection_name: str):
        self.db = db
        self.collection = db[collection_name]

    @staticmethod
    def _without_id(document: Mapping[str, Any] | None) -> dict[str, Any] | None:
        if document is None:
            return None
        result = dict(document)
        result.pop("_id", None)
        return result
