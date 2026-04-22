from datetime import datetime

from trading_algos_dashboard.services.market_data_cache import InMemoryMarketDataCache


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
