from datetime import datetime
from xmlrpc.client import Fault

from trading_algos_dashboard.services.data_source_service import (
    DataSourceUnavailableError,
    MarketDataUnavailableError,
    SmarttradeDataSourceService,
)


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

    candles = service.fetch_candles(
        symbol="AAPL",
        start=datetime.fromisoformat("2024-01-01T09:30"),
        end=datetime.fromisoformat("2024-01-01T09:32"),
    )

    assert len(candles) == 2
    assert [item["ts"] for item in candles] == [
        "2024-01-01 09:30:00",
        "2024-01-01 09:32:00",
    ]
    assert all("_id" not in item for item in candles)
    assert seen_minutes == [30, 31, 32]


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
        candles = service.fetch_candles(
            symbol="AAPL",
            start=datetime.fromisoformat("2024-01-01T09:30"),
            end=datetime.fromisoformat("2024-01-01T09:30"),
        )

    assert len(candles) == 1
    assert "candle_fetch_mode_selected; mode=proxy_minute_rpc" in caplog.text


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
        candles = service.fetch_candles(
            symbol="AAPL",
            start=datetime.fromisoformat("2024-01-01T09:30"),
            end=datetime.fromisoformat("2024-01-01T09:30"),
        )

    assert len(candles) == 1
    assert "proxy_fetch_completed" in caplog.text
