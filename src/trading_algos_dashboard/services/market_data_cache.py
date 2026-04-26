from __future__ import annotations

import logging
import threading
from collections import OrderedDict
from collections.abc import Mapping
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MarketDataCacheKey:
    symbol: str
    start: datetime
    end: datetime


@dataclass(frozen=True)
class CachedMarketData:
    key: MarketDataCacheKey
    candles: tuple[dict[str, Any], ...]
    stored_at: datetime
    candle_count: int
    source_kind: str = "memory_cache"


class InMemoryMarketDataCache:
    def __init__(self, *, enabled: bool = True, max_entries: int = 100) -> None:
        self.enabled = enabled
        self.max_entries = max_entries
        self._entries: OrderedDict[MarketDataCacheKey, CachedMarketData] = OrderedDict()
        self._lock = threading.RLock()

    def configure(self, *, enabled: bool, max_entries: int) -> None:
        self.enabled = enabled
        self.max_entries = max_entries
        self._prune_if_needed()

    def make_key(
        self, *, symbol: str, start: datetime, end: datetime
    ) -> MarketDataCacheKey:
        return MarketDataCacheKey(symbol=symbol.strip().upper(), start=start, end=end)

    def get(
        self, *, symbol: str, start: datetime, end: datetime
    ) -> CachedMarketData | None:
        if not self.enabled:
            return None
        key = self.make_key(symbol=symbol, start=start, end=end)
        with self._lock:
            cached = self._entries.get(key)
            if cached is not None:
                self._entries.move_to_end(key)
        if cached is None:
            logger.info(
                "market_data_cache: miss; symbol=%s start=%s end=%s",
                key.symbol,
                key.start.isoformat(sep=" "),
                key.end.isoformat(sep=" "),
            )
            return None
        logger.info(
            "market_data_cache: hit; symbol=%s start=%s end=%s candle_count=%s",
            key.symbol,
            key.start.isoformat(sep=" "),
            key.end.isoformat(sep=" "),
            cached.candle_count,
        )
        return cached

    def put(
        self,
        *,
        symbol: str,
        start: datetime,
        end: datetime,
        candles: Sequence[Mapping[str, Any]],
    ) -> CachedMarketData:
        key = self.make_key(symbol=symbol, start=start, end=end)
        entry = CachedMarketData(
            key=key,
            candles=tuple(dict(row) for row in candles),
            stored_at=datetime.now(timezone.utc),
            candle_count=len(candles),
            source_kind="memory_cache",
        )
        with self._lock:
            self._entries[key] = entry
            self._entries.move_to_end(key)
            self._prune_if_needed()
        logger.info(
            "market_data_cache: store; symbol=%s start=%s end=%s candle_count=%s",
            key.symbol,
            key.start.isoformat(sep=" "),
            key.end.isoformat(sep=" "),
            entry.candle_count,
        )
        return entry

    def clear(self) -> None:
        with self._lock:
            entry_count = len(self._entries)
            self._entries.clear()
        logger.info("market_data_cache: clear; entry_count=%s", entry_count)

    def stats(self) -> dict[str, int]:
        with self._lock:
            return {"entry_count": len(self._entries)}

    def list_entries(self) -> list[CachedMarketData]:
        with self._lock:
            return list(self._entries.values())

    def delete(self, *, symbol: str, start: datetime, end: datetime) -> bool:
        key = self.make_key(symbol=symbol, start=start, end=end)
        with self._lock:
            deleted = self._entries.pop(key, None) is not None
        if deleted:
            logger.info(
                "market_data_cache: delete; layer=memory symbol=%s start=%s end=%s",
                key.symbol,
                key.start.isoformat(sep=" "),
                key.end.isoformat(sep=" "),
            )
        return deleted

    def _prune_if_needed(self) -> None:
        if self.max_entries < 1:
            self.max_entries = 1
        while len(self._entries) > self.max_entries:
            self._entries.popitem(last=False)


class MongoMarketDataCache:
    def __init__(
        self,
        *,
        repository: Any,
        enabled: bool = True,
        max_entries: int = 1000,
        ttl_hours: int = 168,
    ) -> None:
        self.repository = repository
        self.enabled = enabled
        self.max_entries = max_entries
        self.ttl_hours = ttl_hours

    def configure(self, *, enabled: bool, max_entries: int, ttl_hours: int) -> None:
        self.enabled = enabled
        self.max_entries = max_entries
        self.ttl_hours = ttl_hours
        self._prune_expired_entries()
        self._prune_if_needed()

    def get(
        self, *, symbol: str, start: datetime, end: datetime
    ) -> CachedMarketData | None:
        if not self.enabled:
            return None
        self._prune_expired_entries()
        document = self.repository.get_entry(symbol=symbol, start=start, end=end)
        if not isinstance(document, dict):
            return None
        candles = document.get("candles")
        stored_at = document.get("stored_at")
        if not isinstance(candles, list) or not isinstance(stored_at, datetime):
            return None
        key = MarketDataCacheKey(symbol=symbol.strip().upper(), start=start, end=end)
        return CachedMarketData(
            key=key,
            candles=tuple(dict(row) for row in candles if isinstance(row, Mapping)),
            stored_at=stored_at,
            candle_count=int(document.get("candle_count", len(candles))),
            source_kind="shared_cache",
        )

    def put(
        self,
        *,
        symbol: str,
        start: datetime,
        end: datetime,
        candles: Sequence[Mapping[str, Any]],
    ) -> CachedMarketData:
        payload = self.repository.put_entry(
            symbol=symbol,
            start=start,
            end=end,
            candles=[dict(row) for row in candles],
        )
        key = MarketDataCacheKey(symbol=symbol.strip().upper(), start=start, end=end)
        self._prune_expired_entries()
        self._prune_if_needed()
        stored_at = payload.get("stored_at")
        if not isinstance(stored_at, datetime):
            stored_at = datetime.now(timezone.utc)
        return CachedMarketData(
            key=key,
            candles=tuple(dict(row) for row in candles),
            stored_at=stored_at,
            candle_count=len(candles),
            source_kind="shared_cache",
        )

    def stats(self) -> dict[str, int]:
        self._prune_expired_entries()
        return {"entry_count": self.repository._count_documents({})}

    def clear(self) -> int:
        return int(self.repository.clear())

    def list_entries(self) -> list[CachedMarketData]:
        self._prune_expired_entries()
        entries: list[CachedMarketData] = []
        for document in self.repository.list_entries():
            candles = document.get("candles")
            stored_at = document.get("stored_at")
            symbol = document.get("symbol")
            start = document.get("start")
            end = document.get("end")
            if (
                not isinstance(candles, list)
                or not isinstance(stored_at, datetime)
                or not isinstance(symbol, str)
                or not isinstance(start, datetime)
                or not isinstance(end, datetime)
            ):
                continue
            entries.append(
                CachedMarketData(
                    key=MarketDataCacheKey(
                        symbol=symbol.strip().upper(),
                        start=start,
                        end=end,
                    ),
                    candles=tuple(
                        dict(row) for row in candles if isinstance(row, Mapping)
                    ),
                    stored_at=stored_at,
                    candle_count=int(document.get("candle_count", len(candles))),
                    source_kind="shared_cache",
                )
            )
        return entries

    def delete(self, *, symbol: str, start: datetime, end: datetime) -> bool:
        existing = self.repository.get_entry(symbol=symbol, start=start, end=end)
        if not isinstance(existing, dict):
            return False
        cache_key = existing.get("cache_key")
        if not isinstance(cache_key, str):
            return False
        self.repository.delete_entry_by_cache_key(cache_key)
        logger.info(
            "market_data_cache: delete; layer=shared symbol=%s start=%s end=%s",
            symbol.strip().upper(),
            start.isoformat(sep=" "),
            end.isoformat(sep=" "),
        )
        return True

    def try_claim_fill(
        self,
        *,
        symbol: str,
        start: datetime,
        end: datetime,
        owner_id: str,
        lease_until: datetime,
    ) -> bool:
        return bool(
            self.repository.try_claim_fill(
                symbol=symbol,
                start=start,
                end=end,
                owner_id=owner_id,
                lease_until=lease_until,
            )
        )

    def release_fill_claim(
        self,
        *,
        symbol: str,
        start: datetime,
        end: datetime,
        owner_id: str,
    ) -> None:
        self.repository.release_fill_claim(
            symbol=symbol,
            start=start,
            end=end,
            owner_id=owner_id,
        )

    def _prune_expired_entries(self) -> None:
        expires_before = datetime.now(timezone.utc) - timedelta(hours=self.ttl_hours)
        delete_expired_entries = getattr(
            self.repository, "delete_expired_entries", None
        )
        if callable(delete_expired_entries):
            delete_expired_entries(expires_before=expires_before)

    def _prune_if_needed(self) -> None:
        prune_oldest_entries = getattr(self.repository, "prune_oldest_entries", None)
        if callable(prune_oldest_entries):
            prune_oldest_entries(max_entries=max(1, self.max_entries))


class LayeredMarketDataCache:
    def __init__(
        self,
        *,
        memory_cache: InMemoryMarketDataCache,
        shared_cache: MongoMarketDataCache | None = None,
    ) -> None:
        self.memory_cache = memory_cache
        self.shared_cache = shared_cache
        self.enabled = memory_cache.enabled or bool(
            shared_cache and shared_cache.enabled
        )

    def configure(
        self,
        *,
        memory_enabled: bool,
        memory_max_entries: int,
        shared_enabled: bool,
        shared_max_entries: int,
        shared_ttl_hours: int,
    ) -> None:
        self.memory_cache.configure(
            enabled=memory_enabled,
            max_entries=memory_max_entries,
        )
        if self.shared_cache is not None:
            self.shared_cache.configure(
                enabled=shared_enabled,
                max_entries=shared_max_entries,
                ttl_hours=shared_ttl_hours,
            )
        self.enabled = self.memory_cache.enabled or bool(
            self.shared_cache and self.shared_cache.enabled
        )

    def clear_memory(self) -> None:
        self.memory_cache.clear()

    def clear_shared(self) -> int:
        if self.shared_cache is None:
            return 0
        return self.shared_cache.clear()

    def list_memory_entries(self) -> list[CachedMarketData]:
        return self.memory_cache.list_entries()

    def list_shared_entries(self) -> list[CachedMarketData]:
        if self.shared_cache is None:
            return []
        return self.shared_cache.list_entries()

    def delete(self, *, symbol: str, start: datetime, end: datetime) -> dict[str, bool]:
        deleted_memory = self.memory_cache.delete(symbol=symbol, start=start, end=end)
        deleted_shared = False
        if self.shared_cache is not None:
            deleted_shared = self.shared_cache.delete(
                symbol=symbol,
                start=start,
                end=end,
            )
        return {"memory": deleted_memory, "shared": deleted_shared}

    def get(
        self, *, symbol: str, start: datetime, end: datetime
    ) -> CachedMarketData | None:
        cached = self.memory_cache.get(symbol=symbol, start=start, end=end)
        if cached is not None:
            return cached
        if self.shared_cache is None:
            return None
        cached = self.shared_cache.get(symbol=symbol, start=start, end=end)
        if cached is None:
            return None
        self.memory_cache.put(
            symbol=symbol,
            start=start,
            end=end,
            candles=cached.candles,
        )
        return cached

    def put(
        self,
        *,
        symbol: str,
        start: datetime,
        end: datetime,
        candles: Sequence[Mapping[str, Any]],
    ) -> CachedMarketData:
        if self.shared_cache is not None:
            self.shared_cache.put(
                symbol=symbol,
                start=start,
                end=end,
                candles=candles,
            )
        return self.memory_cache.put(
            symbol=symbol,
            start=start,
            end=end,
            candles=candles,
        )

    def stats(self) -> dict[str, int | bool | str]:
        shared_entry_count = 0
        shared_enabled = False
        shared_ttl_hours = 0
        shared_max_entries = 0
        if self.shared_cache is not None:
            shared_enabled = self.shared_cache.enabled
            shared_entry_count = self.shared_cache.stats()["entry_count"]
            shared_ttl_hours = self.shared_cache.ttl_hours
            shared_max_entries = self.shared_cache.max_entries
        memory_stats = self.memory_cache.stats()
        return {
            "memory_entry_count": memory_stats["entry_count"],
            "memory_enabled": self.memory_cache.enabled,
            "memory_max_entries": self.memory_cache.max_entries,
            "shared_entry_count": shared_entry_count,
            "shared_enabled": shared_enabled,
            "shared_max_entries": shared_max_entries,
            "shared_ttl_hours": shared_ttl_hours,
            "shared_backend": "mongo" if self.shared_cache is not None else "none",
        }
