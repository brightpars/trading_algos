from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class MongoRepository:
    def __init__(self, db: Any, collection_name: str):
        self.db = db
        self.collection = db[collection_name]

    def _count_documents(self, query: Mapping[str, Any] | None = None) -> int:
        effective_query = dict(query or {})
        count_documents = getattr(self.collection, "count_documents", None)
        if callable(count_documents):
            count = count_documents(effective_query)
            if isinstance(count, int):
                return count
            return 0
        return sum(1 for _ in self.collection.find(effective_query))

    def _delete_many(self, query: Mapping[str, Any] | None = None) -> int:
        effective_query = dict(query or {})
        result = self.collection.delete_many(effective_query)
        deleted_count = getattr(result, "deleted_count", 0)
        if isinstance(deleted_count, int):
            return deleted_count
        return 0

    @staticmethod
    def _without_id(document: Mapping[str, Any] | None) -> dict[str, Any] | None:
        if document is None:
            return None
        result = dict(document)
        result.pop("_id", None)
        return result
