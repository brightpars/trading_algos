from datetime import datetime, timedelta, timezone

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
            "cache_key": f"{symbol.strip().upper()}|{start.isoformat()}|{end.isoformat()}",
            "symbol": symbol.strip().upper(),
            "start": start,
            "end": end,
            "candles": [dict(row) for row in candles],
            "candle_count": len(candles),
            "stored_at": stored_at or datetime.now(timezone.utc),
        }
        self.entries[(symbol.strip().upper(), start, end)] = payload
        return payload

    def _count_documents(self, _query):
        return len(self.entries)

    def list_entries(self):
        return list(self.entries.values())

    def delete_entry_by_cache_key(self, cache_key):
        for key, entry in list(self.entries.items()):
            if entry.get("cache_key") == cache_key:
                del self.entries[key]

    def clear(self):
        deleted_count = len(self.entries)
        self.entries = {}
        return deleted_count

    def delete_expired_entries(self, *, expires_before):
        deleted_count = 0
        for key, entry in list(self.entries.items()):
            stored_at = entry.get("stored_at")
            if isinstance(stored_at, datetime) and stored_at.tzinfo is None:
                stored_at = stored_at.replace(tzinfo=timezone.utc)
            if isinstance(stored_at, datetime) and stored_at < expires_before:
                del self.entries[key]
                deleted_count += 1
        return deleted_count

    def prune_oldest_entries(self, *, max_entries):
        if len(self.entries) <= max_entries:
            return 0

        def _stored_at_sort_key(item):
            stored_at = item[1].get("stored_at")
            if isinstance(stored_at, datetime):
                return stored_at
            return datetime.min.replace(tzinfo=timezone.utc)

        sorted_items = sorted(
            self.entries.items(),
            key=_stored_at_sort_key,
        )
        delete_count = len(self.entries) - max_entries
        for key, _entry in sorted_items[:delete_count]:
            del self.entries[key]
        return delete_count


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


def test_memory_cache_evicts_oldest_entries_when_limit_is_exceeded():
    cache = InMemoryMarketDataCache(max_entries=1)
    start = datetime.fromisoformat("2024-01-01T09:30")
    end = datetime.fromisoformat("2024-01-01T09:31")

    cache.put(symbol="AAPL", start=start, end=end, candles=[{"ts": "x"}])
    cache.put(symbol="MSFT", start=start, end=end, candles=[{"ts": "y"}])

    assert cache.get(symbol="AAPL", start=start, end=end) is None
    assert cache.get(symbol="MSFT", start=start, end=end) is not None


def test_shared_cache_prunes_entries_by_ttl():
    repository = _MarketDataCacheRepository()
    cache = MongoMarketDataCache(repository=repository, ttl_hours=1)
    start = datetime.fromisoformat("2024-01-01T09:30")
    end = datetime.fromisoformat("2024-01-01T09:31")
    repository.put_entry(
        symbol="AAPL",
        start=start,
        end=end,
        candles=[{"ts": "x"}],
        stored_at=datetime.now(timezone.utc) - timedelta(hours=2),
    )

    assert cache.get(symbol="AAPL", start=start, end=end) is None


def test_shared_cache_prunes_oldest_entries_when_limit_is_exceeded():
    repository = _MarketDataCacheRepository()
    cache = MongoMarketDataCache(repository=repository, max_entries=1)
    start = datetime.fromisoformat("2024-01-01T09:30")
    end = datetime.fromisoformat("2024-01-01T09:31")
    repository.put_entry(
        symbol="AAPL",
        start=start,
        end=end,
        candles=[{"ts": "x"}],
        stored_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    cache.put(symbol="MSFT", start=start, end=end, candles=[{"ts": "y"}])

    assert repository.get_entry(symbol="AAPL", start=start, end=end) is None
    assert repository.get_entry(symbol="MSFT", start=start, end=end) is not None
