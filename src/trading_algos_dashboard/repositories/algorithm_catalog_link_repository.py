from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any
from uuid import uuid4

from trading_algos_dashboard.repositories.mongo_base import MongoRepository


class AlgorithmCatalogLinkRepository(MongoRepository):
    def __init__(self, db: Any):
        super().__init__(db, "algorithm_catalog_links")

    def upsert_link(
        self, *, catalog_entry_id: str, alg_impl_id: str, document: Mapping[str, Any]
    ) -> dict[str, Any]:
        existing = self.collection.find_one(
            {"catalog_entry_id": catalog_entry_id, "alg_impl_id": alg_impl_id}
        )
        payload = dict(document)
        payload["id"] = str(
            (existing or {}).get("id") or payload.get("id") or uuid4().hex
        )
        payload["catalog_entry_id"] = catalog_entry_id
        payload["alg_impl_id"] = alg_impl_id
        self.collection.update_one(
            {"catalog_entry_id": catalog_entry_id, "alg_impl_id": alg_impl_id},
            {"$set": payload},
            upsert=True,
        )
        stored = (
            self.collection.find_one(
                {"catalog_entry_id": catalog_entry_id, "alg_impl_id": alg_impl_id}
            )
            or payload
        )
        return self._without_id(stored) or {}

    def replace_all_links(
        self, documents: Sequence[Mapping[str, Any]]
    ) -> list[dict[str, Any]]:
        self._delete_many({})
        stored: list[dict[str, Any]] = []
        for document in documents:
            catalog_entry_id = str(document.get("catalog_entry_id", ""))
            alg_impl_id = str(document.get("alg_impl_id", ""))
            if not catalog_entry_id or not alg_impl_id:
                continue
            stored.append(
                self.upsert_link(
                    catalog_entry_id=catalog_entry_id,
                    alg_impl_id=alg_impl_id,
                    document=document,
                )
            )
        return stored

    def list_links(self) -> list[dict[str, Any]]:
        return [
            self._without_id(document) or {} for document in self.collection.find({})
        ]

    def list_links_for_entry(self, catalog_entry_id: str) -> list[dict[str, Any]]:
        return [
            self._without_id(document) or {}
            for document in self.collection.find({"catalog_entry_id": catalog_entry_id})
        ]

    def get_primary_link(self, catalog_entry_id: str) -> dict[str, Any] | None:
        candidates = [
            self._without_id(document) or {}
            for document in self.collection.find({"catalog_entry_id": catalog_entry_id})
        ]
        if not candidates:
            return None
        candidates.sort(
            key=lambda item: (
                0 if item.get("match_type") == "runtime_declared" else 1,
                -float(item.get("match_confidence", 0.0)),
            )
        )
        return candidates[0]

    def count_links(self) -> int:
        return self._count_documents()

    def delete_all_links(self) -> int:
        return self._delete_many({})
