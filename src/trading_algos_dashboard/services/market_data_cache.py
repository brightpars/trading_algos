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
