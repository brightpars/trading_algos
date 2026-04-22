from datetime import datetime

from trading_algos_dashboard.services.market_data_cache import (
    InMemoryMarketDataCache,
    LayeredMarketDataCache,
    MongoMarketDataCache,
)


class _MarketDataCacheRepository:
    def __init__(self) -> None:
        self.entries: dict[tuple[str, datetime, datetime], dict] = {}

    def get_entry(self, *, symbol: str, start: datetime, end: datetime):
        return self.entries.get((symbol.strip().upper(), start, end))

    def put_entry(
        self, *, symbol: str, start: datetime, end: datetime, candles, stored_at=None
    ):
        payload = {
            "symbol": symbol.strip().upper(),
            "start": start,
            "end": end,
            "candles": [dict(row) for row in candles],
            "candle_count": len(candles),
            "stored_at": stored_at or datetime.now(),
        }
        self.entries[(symbol.strip().upper(), start, end)] = payload
        return payload

    def _count_documents(self, _query):
        return len(self.entries)


def test_market_data_cache_uses_exact_match_with_symbol_normalization():
    cache = InMemoryMarketDataCache()
    start = datetime.fromisoformat("2024-01-01T09:30")
    end = datetime.fromisoformat("2024-01-01T09:31")

    cache.put(
        symbol=" aapl ",
        start=start,
        end=end,
        candles=[{"ts": "2024-01-01 09:30:00", "Close": 10.5}],
    )

    cached = cache.get(symbol="AAPL", start=start, end=end)

    assert cached is not None
    assert cached.key.symbol == "AAPL"
    assert cached.candle_count == 1


def test_market_data_cache_clear_removes_all_entries():
    cache = InMemoryMarketDataCache()
    start = datetime.fromisoformat("2024-01-01T09:30")
    end = datetime.fromisoformat("2024-01-01T09:31")

    cache.put(symbol="AAPL", start=start, end=end, candles=[{"ts": "x"}])
    cache.put(symbol="MSFT", start=start, end=end, candles=[{"ts": "y"}])

    assert cache.stats() == {"entry_count": 2}
    cache.clear()
    assert cache.stats() == {"entry_count": 0}


def test_market_data_cache_stores_detached_copy_of_input_rows():
    cache = InMemoryMarketDataCache()
    start = datetime.fromisoformat("2024-01-01T09:30")
    end = datetime.fromisoformat("2024-01-01T09:31")
    candles = [{"ts": "2024-01-01 09:30:00", "Close": 10.5}]

    cache.put(symbol="AAPL", start=start, end=end, candles=candles)
    candles[0]["Close"] = 99.0

    cached = cache.get(symbol="AAPL", start=start, end=end)

    assert cached is not None
    assert cached.candles[0]["Close"] == 10.5


def test_layered_cache_reads_from_shared_cache_and_promotes_to_memory():
    repository = _MarketDataCacheRepository()
    shared_cache = MongoMarketDataCache(repository=repository)
    memory_cache = InMemoryMarketDataCache()
    layered_cache = LayeredMarketDataCache(
        memory_cache=memory_cache,
        shared_cache=shared_cache,
    )
    start = datetime.fromisoformat("2024-01-01T09:30")
    end = datetime.fromisoformat("2024-01-01T09:31")

    shared_cache.put(
        symbol="AAPL",
        start=start,
        end=end,
        candles=[{"ts": "2024-01-01 09:30:00", "Close": 10.5}],
    )

    cached = layered_cache.get(symbol="AAPL", start=start, end=end)

    assert cached is not None
    assert cached.source_kind == "shared_cache"
    assert memory_cache.get(symbol="AAPL", start=start, end=end) is not None


def test_layered_cache_stats_include_memory_and_shared_counts():
    repository = _MarketDataCacheRepository()
    layered_cache = LayeredMarketDataCache(
        memory_cache=InMemoryMarketDataCache(),
        shared_cache=MongoMarketDataCache(repository=repository),
    )
    start = datetime.fromisoformat("2024-01-01T09:30")
    end = datetime.fromisoformat("2024-01-01T09:31")

    layered_cache.put(
        symbol="AAPL",
        start=start,
        end=end,
        candles=[{"ts": "2024-01-01 09:30:00", "Close": 10.5}],
    )

    assert layered_cache.stats()["memory_entry_count"] == 1
    assert layered_cache.stats()["shared_entry_count"] == 1
