from trading_algos_dashboard.services.data_source_service import (
    DataSourceUnavailableError,
    SmarttradeDataSourceService,
)


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
