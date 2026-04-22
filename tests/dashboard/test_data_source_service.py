from datetime import datetime
from xmlrpc.client import DateTime as XmlRpcDateTime
from xmlrpc.client import Fault

from trading_algos_dashboard.services.data_source_service import (
    DataSourceUnavailableError,
    MarketDataFetchResult,
    MarketDataUnavailableError,
    SmarttradeDataSourceService,
)
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

    def try_claim_fill(
        self, *, symbol: str, start: datetime, end: datetime, owner_id: str, lease_until
    ):
        key = (symbol.strip().upper(), start, end)
        entry = self.entries.get(key)
        if entry and entry.get("fill_owner_id") not in {None, owner_id}:
            return False
        if entry is None:
            entry = {
                "symbol": symbol.strip().upper(),
                "start": start,
                "end": end,
            }
            self.entries[key] = entry
        entry["fill_owner_id"] = owner_id
        entry["fill_expires_at"] = lease_until
        return True

    def release_fill_claim(
        self, *, symbol: str, start: datetime, end: datetime, owner_id: str
    ) -> None:
        key = (symbol.strip().upper(), start, end)
        entry = self.entries.get(key)
        if entry is None or entry.get("fill_owner_id") != owner_id:
            return
        entry["fill_owner_id"] = None
        entry["fill_expires_at"] = None


class _MongoLikeRow:
    def __init__(self, payload):
        self._payload = dict(payload)

    def to_mongo(self):
        class _MongoDict:
            def __init__(self, payload):
                self._payload = payload

            def to_dict(self):
                return dict(self._payload)

        return _MongoDict(self._payload)


def test_data_source_service_uses_override_endpoint_for_label():
    service = SmarttradeDataSourceService(
        smarttrade_path="/tmp/smarttrade",
        user_id=1,
        endpoint_resolver=lambda: ("10.1.2.3", 7007),
    )

    assert service._data_server_endpoint_label() == "10.1.2.3:7007"


def test_check_connection_returns_endpoint_from_proxy(monkeypatch):
    class _Proxy:
        def ping_with_timeout(self, timeout_seconds):
            assert timeout_seconds == 2.0
            return "pong"

    service = SmarttradeDataSourceService(
        smarttrade_path="/tmp/smarttrade",
        user_id=1,
        endpoint_resolver=lambda: ("127.0.0.9", 7777),
    )
    monkeypatch.setattr(service, "_data_proxy", lambda: _Proxy())

    payload = service.check_connection()

    assert payload == {
        "status": "ok",
        "endpoint": "127.0.0.9:7777",
        "server_up": True,
    }


def test_check_connection_uses_timeout_aware_ping_once(monkeypatch):
    calls: list[float] = []

    class _Proxy:
        def ping_with_timeout(self, timeout_seconds):
            calls.append(timeout_seconds)
            return "pong"

        def is_server_up(self):
            raise AssertionError(
                "fallback ping should not be used when timeout ping exists"
            )

    service = SmarttradeDataSourceService(
        smarttrade_path="/tmp/smarttrade",
        user_id=1,
        endpoint_resolver=lambda: ("127.0.0.9", 7777),
    )
    monkeypatch.setattr(service, "_data_proxy", lambda: _Proxy())

    payload = service.check_connection()

    assert payload["server_up"] is True
    assert calls == []


def test_is_proxy_server_up_uses_timeout_aware_ping_when_available():
    calls: list[float] = []

    class _Proxy:
        def ping_with_timeout(self, timeout_seconds):
            calls.append(timeout_seconds)
            return "pong"

    service = SmarttradeDataSourceService(
        smarttrade_path="/tmp/smarttrade",
        user_id=1,
    )

    assert service._is_proxy_server_up(_Proxy()) is True
    assert calls == [2.0]


def test_is_proxy_server_up_falls_back_to_is_server_up_when_timeout_ping_missing():
    class _Proxy:
        def is_server_up(self):
            return True

    service = SmarttradeDataSourceService(
        smarttrade_path="/tmp/smarttrade",
        user_id=1,
    )

    assert service._is_proxy_server_up(_Proxy()) is True


def test_check_connection_raises_when_server_is_unavailable(monkeypatch):
    service = SmarttradeDataSourceService(
        smarttrade_path="/tmp/smarttrade",
        user_id=1,
        endpoint_resolver=lambda: ("127.0.0.9", 7777),
    )
    monkeypatch.setattr(
        service,
        "_data_proxy",
        lambda: (_ for _ in ()).throw(DataSourceUnavailableError("not reachable")),
    )

    try:
        service.check_connection()
    except DataSourceUnavailableError as exc:
        assert str(exc) == "not reachable"
    else:
        raise AssertionError("Expected DataSourceUnavailableError")


def test_fetch_candles_reads_via_proxy_minute_by_minute(monkeypatch):
    service = SmarttradeDataSourceService(
        smarttrade_path="/tmp/smarttrade",
        user_id=1,
    )

    seen_minutes: list[int] = []

    class _Proxy:
        def get_data(self, _symbol, ts):
            seen_minutes.append(ts.minute)
            if ts.minute == 31:
                raise Fault(1, "missing candle")
            return {
                "_id": "mongo-id",
                "ts": ts.isoformat(sep=" "),
                "Open": 10,
                "High": 11,
                "Low": 9,
                "Close": 10.5,
            }

    monkeypatch.setattr(service, "_data_proxy", lambda: _Proxy())

    fetch_result = service.fetch_candles(
        symbol="AAPL",
        start=datetime.fromisoformat("2024-01-01T09:30"),
        end=datetime.fromisoformat("2024-01-01T09:32"),
    )
    candles = fetch_result.candles

    assert len(candles) == 2
    assert fetch_result == MarketDataFetchResult(
        candles=candles,
        cache_hit=False,
        source_kind="dataserver",
        symbol="AAPL",
        start=datetime.fromisoformat("2024-01-01T09:30"),
        end=datetime.fromisoformat("2024-01-01T09:32"),
        candle_count=2,
    )
    assert [item["ts"] for item in candles] == [
        "2024-01-01 09:30:00",
        "2024-01-01 09:32:00",
    ]
    assert all("_id" not in item for item in candles)
    assert seen_minutes == [30, 31, 32]


def test_fetch_candles_prefers_bulk_candles_proxy_method_when_available(monkeypatch):
    service = SmarttradeDataSourceService(
        smarttrade_path="/tmp/smarttrade",
        user_id=1,
    )

    class _Proxy:
        def get_candles(self, _symbol, start, end):
            assert start == datetime.fromisoformat("2024-01-01T09:30")
            assert end == datetime.fromisoformat("2024-01-01T09:32")
            return [
                {
                    "_id": "mongo-id-1",
                    "ts": "2024-01-01 09:30:00",
                    "Open": 10,
                    "High": 11,
                    "Low": 9,
                    "Close": 10.5,
                },
                {
                    "_id": "mongo-id-2",
                    "ts": "2024-01-01 09:32:00",
                    "Open": 12,
                    "High": 13,
                    "Low": 11,
                    "Close": 12.5,
                },
            ]

        def get_data(self, _symbol, _ts):
            raise AssertionError(
                "minute fallback should not be used when get_candles exists"
            )

    monkeypatch.setattr(service, "_data_proxy", lambda: _Proxy())

    fetch_result = service.fetch_candles(
        symbol="AAPL",
        start=datetime.fromisoformat("2024-01-01T09:30"),
        end=datetime.fromisoformat("2024-01-01T09:32"),
    )
    candles = fetch_result.candles

    assert [item["ts"] for item in candles] == [
        "2024-01-01 09:30:00",
        "2024-01-01 09:32:00",
    ]
    assert fetch_result.cache_hit is False
    assert all("_id" not in item for item in candles)


def test_fetch_candles_normalizes_xmlrpc_datetime_values(monkeypatch):
    service = SmarttradeDataSourceService(
        smarttrade_path="/tmp/smarttrade",
        user_id=1,
    )

    class _Proxy:
        def get_candles(self, _symbol, _start, _end):
            return [
                {
                    "_id": "mongo-id-1",
                    "ts": XmlRpcDateTime("20260402T09:30:00"),
                    "nested": {"opened_at": XmlRpcDateTime("20260402T09:31:00")},
                }
            ]

    monkeypatch.setattr(service, "_data_proxy", lambda: _Proxy())

    fetch_result = service.fetch_candles(
        symbol="AAPL",
        start=datetime.fromisoformat("2026-04-02T09:30"),
        end=datetime.fromisoformat("2026-04-02T09:30"),
    )

    assert fetch_result.candles == [
        {
            "ts": datetime.fromisoformat("2026-04-02T09:30:00+00:00"),
            "nested": {
                "opened_at": datetime.fromisoformat("2026-04-02T09:31:00+00:00")
            },
        }
    ]


def test_fetch_candles_raises_market_data_unavailable_when_all_proxy_rows_missing(
    monkeypatch,
):
    service = SmarttradeDataSourceService(
        smarttrade_path="/tmp/smarttrade",
        user_id=1,
    )

    class _Proxy:
        def get_data(self, _symbol, _ts):
            raise Fault(1, "missing candle")

    monkeypatch.setattr(service, "_data_proxy", lambda: _Proxy())

    try:
        service.fetch_candles(
            symbol="AAPL",
            start=datetime.fromisoformat("2024-01-01T09:30"),
            end=datetime.fromisoformat("2024-01-01T09:31"),
        )
    except MarketDataUnavailableError as exc:
        assert str(exc) == (
            "No candle data is available for the requested symbol and time range. "
            "Please choose a range that contains market data."
        )
    else:
        raise AssertionError("Expected MarketDataUnavailableError")


def test_fetch_candles_logs_selected_proxy_mode(monkeypatch, caplog):
    service = SmarttradeDataSourceService(
        smarttrade_path="/tmp/smarttrade",
        user_id=1,
    )

    class _Proxy:
        def get_data(self, _symbol, ts):
            return {
                "_id": "mongo-id",
                "ts": ts.isoformat(sep=" "),
                "Open": 10,
                "High": 11,
                "Low": 9,
                "Close": 10.5,
            }

    monkeypatch.setattr(service, "_data_proxy", lambda: _Proxy())

    with caplog.at_level("INFO"):
        fetch_result = service.fetch_candles(
            symbol="AAPL",
            start=datetime.fromisoformat("2024-01-01T09:30"),
            end=datetime.fromisoformat("2024-01-01T09:30"),
        )
        candles = fetch_result.candles

    assert len(candles) == 1
    assert (
        "candle_fetch_mode_selected; mode=dataserver_bulk_rpc_with_proxy_fallback"
        in caplog.text
    )


def test_fetch_candles_logs_proxy_completion(monkeypatch, caplog):
    service = SmarttradeDataSourceService(
        smarttrade_path="/tmp/smarttrade",
        user_id=1,
    )

    class _Proxy:
        def get_data(self, _symbol, ts):
            return {
                "_id": "mongo-id",
                "ts": ts.isoformat(sep=" "),
                "Open": 10,
                "High": 11,
                "Low": 9,
                "Close": 10.5,
            }

    monkeypatch.setattr(service, "_data_proxy", lambda: _Proxy())

    with caplog.at_level("INFO"):
        fetch_result = service.fetch_candles(
            symbol="AAPL",
            start=datetime.fromisoformat("2024-01-01T09:30"),
            end=datetime.fromisoformat("2024-01-01T09:30"),
        )
        candles = fetch_result.candles

    assert len(candles) == 1
    assert "proxy_fetch_completed" in caplog.text


def test_fetch_candles_logs_bulk_proxy_completion(monkeypatch, caplog):
    service = SmarttradeDataSourceService(
        smarttrade_path="/tmp/smarttrade",
        user_id=1,
    )

    class _Proxy:
        def get_candles(self, _symbol, _start, _end):
            return [{"ts": "2024-01-01 09:30:00", "Close": 10.5}]

    monkeypatch.setattr(service, "_data_proxy", lambda: _Proxy())

    with caplog.at_level("INFO"):
        fetch_result = service.fetch_candles(
            symbol="AAPL",
            start=datetime.fromisoformat("2024-01-01T09:30"),
            end=datetime.fromisoformat("2024-01-01T09:30"),
        )
        candles = fetch_result.candles

    assert len(candles) == 1
    assert "proxy_bulk_candle_fetch_completed" in caplog.text


def test_fetch_candles_uses_cache_for_identical_request(monkeypatch):
    service = SmarttradeDataSourceService(
        smarttrade_path="/tmp/smarttrade",
        user_id=1,
    )
    calls: list[str] = []

    class _Proxy:
        def get_candles(self, symbol, _start, _end):
            calls.append(symbol)
            return [{"ts": "2024-01-01 09:30:00", "Close": 10.5}]

    monkeypatch.setattr(service, "_data_proxy", lambda: _Proxy())

    first = service.fetch_candles(
        symbol="aapl",
        start=datetime.fromisoformat("2024-01-01T09:30"),
        end=datetime.fromisoformat("2024-01-01T09:30"),
    )
    second = service.fetch_candles(
        symbol=" AAPL ",
        start=datetime.fromisoformat("2024-01-01T09:30"),
        end=datetime.fromisoformat("2024-01-01T09:30"),
    )

    assert calls == ["AAPL"]
    assert first.cache_hit is False
    assert second.cache_hit is True
    assert second.source_kind == "memory_cache"
    assert second.candles == first.candles


def test_fetch_candles_returns_fresh_copies_for_cache_hits(monkeypatch):
    service = SmarttradeDataSourceService(
        smarttrade_path="/tmp/smarttrade",
        user_id=1,
    )

    class _Proxy:
        def get_candles(self, _symbol, _start, _end):
            return [{"ts": "2024-01-01 09:30:00", "Close": 10.5}]

    monkeypatch.setattr(service, "_data_proxy", lambda: _Proxy())

    first = service.fetch_candles(
        symbol="AAPL",
        start=datetime.fromisoformat("2024-01-01T09:30"),
        end=datetime.fromisoformat("2024-01-01T09:30"),
    )
    first.candles[0]["Close"] = 99.0

    second = service.fetch_candles(
        symbol="AAPL",
        start=datetime.fromisoformat("2024-01-01T09:30"),
        end=datetime.fromisoformat("2024-01-01T09:30"),
    )

    assert second.cache_hit is True
    assert second.candles[0]["Close"] == 10.5


def test_fetch_candles_logs_cache_events(monkeypatch, caplog):
    service = SmarttradeDataSourceService(
        smarttrade_path="/tmp/smarttrade",
        user_id=1,
    )

    class _Proxy:
        def get_candles(self, _symbol, _start, _end):
            return [{"ts": "2024-01-01 09:30:00", "Close": 10.5}]

    monkeypatch.setattr(service, "_data_proxy", lambda: _Proxy())

    with caplog.at_level("INFO"):
        service.fetch_candles(
            symbol="AAPL",
            start=datetime.fromisoformat("2024-01-01T09:30"),
            end=datetime.fromisoformat("2024-01-01T09:30"),
        )
        service.fetch_candles(
            symbol="AAPL",
            start=datetime.fromisoformat("2024-01-01T09:30"),
            end=datetime.fromisoformat("2024-01-01T09:30"),
        )

    assert "market_data_cache: miss; symbol=AAPL" in caplog.text
    assert "market_data_cache: store; symbol=AAPL" in caplog.text
    assert "market_data_cache: hit; symbol=AAPL" in caplog.text


def test_fetch_candles_returns_shared_cache_hit_without_proxy_call(monkeypatch):
    layered_cache = LayeredMarketDataCache(
        memory_cache=InMemoryMarketDataCache(),
        shared_cache=MongoMarketDataCache(repository=_MarketDataCacheRepository()),
    )
    service = SmarttradeDataSourceService(
        smarttrade_path="/tmp/smarttrade",
        user_id=1,
        market_data_cache=layered_cache,
    )
    start = datetime.fromisoformat("2024-01-01T09:30")
    end = datetime.fromisoformat("2024-01-01T09:30")
    layered_cache.shared_cache.put(  # type: ignore[union-attr]
        symbol="AAPL",
        start=start,
        end=end,
        candles=[{"ts": "2024-01-01 09:30:00", "Close": 10.5}],
    )
    monkeypatch.setattr(
        service,
        "_fetch_candles_via_proxy",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("proxy must not run")),
    )

    result = service.fetch_candles(symbol="AAPL", start=start, end=end)

    assert result.cache_hit is True
    assert result.source_kind == "shared_cache"


def test_market_data_server_details_include_shared_cache_metadata():
    layered_cache = LayeredMarketDataCache(
        memory_cache=InMemoryMarketDataCache(),
        shared_cache=MongoMarketDataCache(repository=_MarketDataCacheRepository()),
    )
    service = SmarttradeDataSourceService(
        smarttrade_path="/tmp/smarttrade",
        user_id=1,
        endpoint_resolver=lambda: ("127.0.0.2", 6010),
        market_data_cache=layered_cache,
    )

    details = service.get_market_data_server_details()

    assert details["cache"]["shared_enabled"] is True
    assert details["cache"]["shared_backend"] == "mongo"


def test_fetch_candles_waits_for_inflight_shared_fill_before_proxy(monkeypatch):
    repository = _MarketDataCacheRepository()
    layered_cache = LayeredMarketDataCache(
        memory_cache=InMemoryMarketDataCache(),
        shared_cache=MongoMarketDataCache(repository=repository),
    )

    def _sleep_fn(_seconds: float) -> None:
        repository.put_entry(
            symbol="AAPL",
            start=datetime.fromisoformat("2024-01-01T09:30"),
            end=datetime.fromisoformat("2024-01-01T09:30"),
            candles=[{"ts": "2024-01-01 09:30:00", "Close": 10.5}],
        )

    service = SmarttradeDataSourceService(
        smarttrade_path="/tmp/smarttrade",
        user_id=1,
        market_data_cache=layered_cache,
        sleep_fn=_sleep_fn,
    )
    monkeypatch.setattr(
        repository,
        "try_claim_fill",
        lambda **_kwargs: False,
    )
    monkeypatch.setattr(
        service,
        "_fetch_candles_via_proxy",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("proxy must not run")),
    )

    result = service.fetch_candles(
        symbol="AAPL",
        start=datetime.fromisoformat("2024-01-01T09:30"),
        end=datetime.fromisoformat("2024-01-01T09:30"),
    )

    assert result.cache_hit is True
    assert result.source_kind == "shared_cache"


def test_fetch_candles_releases_fill_claim_after_proxy_fetch(monkeypatch):
    repository = _MarketDataCacheRepository()
    layered_cache = LayeredMarketDataCache(
        memory_cache=InMemoryMarketDataCache(),
        shared_cache=MongoMarketDataCache(repository=repository),
    )
    service = SmarttradeDataSourceService(
        smarttrade_path="/tmp/smarttrade",
        user_id=1,
        market_data_cache=layered_cache,
    )
    start = datetime.fromisoformat("2024-01-01T09:30")
    end = datetime.fromisoformat("2024-01-01T09:30")
    monkeypatch.setattr(
        service,
        "_fetch_candles_via_proxy",
        lambda **_kwargs: [{"ts": "2024-01-01 09:30:00", "Close": 10.5}],
    )

    result = service.fetch_candles(symbol="AAPL", start=start, end=end)

    assert result.cache_hit is False
    assert repository.get_entry(symbol="AAPL", start=start, end=end) is not None
    entry = repository.entries[("AAPL", start, end)]
    assert entry.get("fill_owner_id") is None
