from __future__ import annotations

import logging
import threading
from collections.abc import Mapping
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
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
    def __init__(self, *, enabled: bool = True) -> None:
        self.enabled = enabled
        self._entries: dict[MarketDataCacheKey, CachedMarketData] = {}
        self._lock = threading.RLock()

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


class MongoMarketDataCache:
    def __init__(
        self,
        *,
        repository: Any,
        enabled: bool = True,
    ) -> None:
        self.repository = repository
        self.enabled = enabled

    def get(
        self, *, symbol: str, start: datetime, end: datetime
    ) -> CachedMarketData | None:
        if not self.enabled:
            return None
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
        return {"entry_count": self.repository._count_documents({})}

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
        if self.shared_cache is not None:
            shared_enabled = self.shared_cache.enabled
            shared_entry_count = self.shared_cache.stats()["entry_count"]
        memory_stats = self.memory_cache.stats()
        return {
            "memory_entry_count": memory_stats["entry_count"],
            "shared_entry_count": shared_entry_count,
            "shared_enabled": shared_enabled,
            "shared_backend": "mongo" if self.shared_cache is not None else "none",
        }
