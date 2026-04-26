from __future__ import annotations

import hashlib
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from trading_algos_dashboard.repositories.mongo_base import MongoRepository


class MarketDataCacheRepository(MongoRepository):
    @staticmethod
    def _normalize_utc_datetime(value: Any) -> datetime | None:
        if not isinstance(value, datetime):
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def __init__(self, db: Any):
        super().__init__(db, "dashboard_market_data_cache")

    @staticmethod
    def build_cache_key(*, symbol: str, start: datetime, end: datetime) -> str:
        normalized_symbol = symbol.strip().upper()
        normalized_start = MarketDataCacheRepository._normalize_utc_datetime(start)
        normalized_end = MarketDataCacheRepository._normalize_utc_datetime(end)
        if normalized_start is None or normalized_end is None:
            raise ValueError("Cache key datetimes must be valid datetime instances")
        digest = hashlib.sha256(
            (
                f"{normalized_symbol}|{normalized_start.isoformat()}|"
                f"{normalized_end.isoformat()}"
            ).encode()
        ).hexdigest()
        return digest

    def get_entry(
        self, *, symbol: str, start: datetime, end: datetime
    ) -> dict[str, Any] | None:
        cache_key = self.build_cache_key(symbol=symbol, start=start, end=end)
        return self._without_id(self.collection.find_one({"cache_key": cache_key}))

    def list_entries(self) -> list[dict[str, Any]]:
        return [
            self._without_id(document) or {} for document in self.collection.find({})
        ]

    def delete_entry_by_cache_key(self, cache_key: str) -> None:
        self.collection.delete_many({"cache_key": cache_key})

    def clear(self) -> int:
        return self._delete_many({})

    def count_materialized_entries(self) -> int:
        return sum(
            1
            for entry in self.list_entries()
            if isinstance(entry.get("candles"), list)
            and isinstance(entry.get("stored_at"), datetime)
        )

    def put_entry(
        self,
        *,
        symbol: str,
        start: datetime,
        end: datetime,
        candles: list[dict[str, Any]],
        stored_at: datetime | None = None,
    ) -> dict[str, Any]:
        normalized_symbol = symbol.strip().upper()
        normalized_start = self._normalize_utc_datetime(start)
        normalized_end = self._normalize_utc_datetime(end)
        if normalized_start is None or normalized_end is None:
            raise ValueError("Cache entry datetimes must be valid datetime instances")
        effective_stored_at = self._normalize_utc_datetime(stored_at)
        if effective_stored_at is None:
            effective_stored_at = datetime.now(timezone.utc)
        cache_key = self.build_cache_key(
            symbol=normalized_symbol,
            start=normalized_start,
            end=normalized_end,
        )
        payload = {
            "cache_key": cache_key,
            "symbol": normalized_symbol,
            "start": normalized_start,
            "end": normalized_end,
            "candles": [dict(row) for row in candles],
            "candle_count": len(candles),
            "stored_at": effective_stored_at,
        }
        self.collection.update_one(
            {"cache_key": cache_key},
            {"$set": payload},
            upsert=True,
        )
        stored = self.collection.find_one({"cache_key": cache_key})
        if isinstance(stored, Mapping):
            return self._without_id(stored) or {}
        return payload

    def try_claim_fill(
        self,
        *,
        symbol: str,
        start: datetime,
        end: datetime,
        owner_id: str,
        lease_until: datetime,
    ) -> bool:
        cache_key = self.build_cache_key(symbol=symbol, start=start, end=end)
        find_one = getattr(self.collection, "find_one", None)
        update_one = getattr(self.collection, "update_one", None)
        if not callable(find_one) or not callable(update_one):
            return False

        existing = find_one({"cache_key": cache_key})
        now = datetime.now(timezone.utc)
        if isinstance(existing, Mapping):
            current_owner = existing.get("fill_owner_id")
            expires_at = self._normalize_utc_datetime(existing.get("fill_expires_at"))
            has_candles = isinstance(existing.get("candles"), list) and bool(
                existing.get("candles")
            )
            if has_candles:
                return False
            if isinstance(current_owner, str) and isinstance(expires_at, datetime):
                if expires_at > now and current_owner != owner_id:
                    return False

        update_one(
            {"cache_key": cache_key},
            {
                "$set": {
                    "cache_key": cache_key,
                    "symbol": symbol.strip().upper(),
                    "start": self._normalize_utc_datetime(start),
                    "end": self._normalize_utc_datetime(end),
                    "fill_owner_id": owner_id,
                    "fill_expires_at": self._normalize_utc_datetime(lease_until),
                }
            },
            upsert=True,
        )
        claimed = find_one({"cache_key": cache_key})
        return bool(
            isinstance(claimed, Mapping) and claimed.get("fill_owner_id") == owner_id
        )

    def release_fill_claim(
        self,
        *,
        symbol: str,
        start: datetime,
        end: datetime,
        owner_id: str,
    ) -> None:
        cache_key = self.build_cache_key(symbol=symbol, start=start, end=end)
        document = self.collection.find_one({"cache_key": cache_key})
        if not isinstance(document, Mapping):
            return
        if document.get("fill_owner_id") != owner_id:
            return
        has_candles = isinstance(document.get("candles"), list) and bool(
            document.get("candles")
        )
        if not has_candles:
            self.delete_entry_by_cache_key(cache_key)
            return
        self.collection.update_one(
            {"cache_key": cache_key},
            {"$set": {"fill_owner_id": None, "fill_expires_at": None}},
        )

    def delete_expired_entries(self, *, expires_before: datetime) -> int:
        deleted_count = 0
        normalized_expires_before = self._normalize_utc_datetime(expires_before)
        if normalized_expires_before is None:
            return 0
        for entry in self.list_entries():
            stored_at = self._normalize_utc_datetime(entry.get("stored_at"))
            if (
                isinstance(stored_at, datetime)
                and stored_at < normalized_expires_before
            ):
                cache_key = entry.get("cache_key")
                if isinstance(cache_key, str):
                    self.delete_entry_by_cache_key(cache_key)
                    deleted_count += 1
        return deleted_count

    def prune_oldest_entries(self, *, max_entries: int) -> int:
        entries = self.list_entries()
        if len(entries) <= max_entries:
            return 0

        def _stored_at_sort_key(item: dict[str, Any]) -> datetime:
            stored_at = self._normalize_utc_datetime(item.get("stored_at"))
            if isinstance(stored_at, datetime):
                return stored_at
            return datetime.min.replace(tzinfo=timezone.utc)

        sorted_entries = sorted(
            entries,
            key=_stored_at_sort_key,
        )
        delete_count = len(entries) - max_entries
        for entry in sorted_entries[:delete_count]:
            cache_key = entry.get("cache_key")
            if isinstance(cache_key, str):
                self.delete_entry_by_cache_key(cache_key)
        return delete_count
