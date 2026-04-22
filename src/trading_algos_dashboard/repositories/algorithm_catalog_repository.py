from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import uuid4

from trading_algos_dashboard.repositories.mongo_base import MongoRepository


class AlgorithmCatalogRepository(MongoRepository):
    def __init__(self, db: Any):
        super().__init__(db, "algorithm_catalog_entries")

    def upsert_entry(
        self,
        *,
        source_version: str,
        catalog_type: str,
        catalog_number: int,
        document: Mapping[str, Any],
    ) -> dict[str, Any]:
        existing = self.collection.find_one(
            {
                "source_version": source_version,
                "catalog_type": catalog_type,
                "catalog_number": catalog_number,
            }
        )
        entry_id = str((existing or {}).get("id") or document.get("id") or uuid4().hex)
        payload = dict(document)
        payload["id"] = entry_id
        self.collection.update_one(
            {
                "source_version": source_version,
                "catalog_type": catalog_type,
                "catalog_number": catalog_number,
            },
            {"$set": payload},
            upsert=True,
        )
        stored = self.collection.find_one({"id": entry_id}) or payload
        return self._without_id(stored) or {}

    def mark_missing_entries_inactive(
        self,
        *,
        source_version: str,
        active_keys: set[tuple[str, int]],
        updated_at: str,
    ) -> int:
        deactivated = 0
        for document in self.collection.find({"source_version": source_version}):
            catalog_type = str(document.get("catalog_type", ""))
            number = int(document.get("catalog_number", 0))
            if (catalog_type, number) in active_keys:
                continue
            self.collection.update_one(
                {"id": document.get("id")},
                {"$set": {"is_active": False, "updated_at": updated_at}},
            )
            deactivated += 1
        return deactivated

    def list_active_entries(self) -> list[dict[str, Any]]:
        items = [
            self._without_id(document) or {}
            for document in self.collection.find({"is_active": True}).sort(
                "catalog_number", 1
            )
        ]
        return sorted(
            items,
            key=lambda item: (
                0 if item.get("catalog_type") == "algorithm" else 1,
                int(item.get("catalog_number", 0)),
                str(item.get("name", "")),
            ),
        )

    def list_entries_for_source_version(
        self, source_version: str
    ) -> list[dict[str, Any]]:
        return [
            self._without_id(document) or {}
            for document in self.collection.find({"source_version": source_version})
        ]

    def get_entry_by_id(self, entry_id: str) -> dict[str, Any] | None:
        return self._without_id(self.collection.find_one({"id": entry_id}))

    def get_entry_by_slug(self, slug: str) -> dict[str, Any] | None:
        return self._without_id(
            self.collection.find_one({"slug": slug, "is_active": True})
        )

    def count_entries(self) -> int:
        return self._count_documents({"is_active": True})

    def update_entry_admin_fields(
        self, entry_id: str, values: Mapping[str, Any]
    ) -> dict[str, Any] | None:
        self.collection.update_one({"id": entry_id}, {"$set": dict(values)})
        return self.get_entry_by_id(entry_id)

    def count_entries_with_implementation(self) -> int:
        return sum(
            1
            for document in self.collection.find({"is_active": True})
            if str(document.get("implementation_id", "")).strip()
        )

    def next_catalog_number(self, catalog_type: str) -> int:
        numbers = [
            int(document.get("catalog_number", 0))
            for document in self.collection.find({"catalog_type": catalog_type})
        ]
        return (max(numbers) if numbers else 0) + 1

    def delete_all_entries(self) -> int:
        return self._delete_many({})
