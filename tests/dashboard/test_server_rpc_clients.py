from __future__ import annotations

from datetime import datetime
from typing import Any

from trading_algos_dashboard.services.server_rpc_clients import (
    CentralServerClient,
    DataServerClient,
    EnginesControlServerClient,
    FakeDateTimeServerClient,
)


def test_central_server_client_exposes_all_registered_methods(monkeypatch) -> None:
    class _Proxy:
        def ping(self) -> str:
            return "pong"

        def ping_with_timeout(self, timeout_seconds: float) -> str:
            assert timeout_seconds == 2.0
            return "pong"

        def get_next_alertID(self) -> int:
            return 11

        def get_next_assetID(self) -> int:
            return 12

        def get_next_operationID(self) -> int:
            return 13

        def get_next_executionID(self) -> int:
            return 14

    monkeypatch.setattr(
        "trading_algos_dashboard.services.server_rpc_clients.ServerProxy",
        lambda *_args, **_kwargs: _Proxy(),
    )

    client = CentralServerClient(host="127.0.0.1", port=6000)

    assert client.ping() == "pong"
    assert client.ping_with_timeout(2.0) == "pong"
    assert client.get_next_alertID() == 11
    assert client.get_next_assetID() == 12
    assert client.get_next_operationID() == 13
    assert client.get_next_executionID() == 14


def test_data_server_client_exposes_all_registered_methods(monkeypatch) -> None:
    recorded: dict[str, Any] = {}

    class _Proxy:
        def ping_with_timeout(self, timeout_seconds: float) -> str:
            recorded["timeout_seconds"] = timeout_seconds
            return "pong"

        def get_price(self, symbol: str, ts: str) -> float:
            recorded["get_price"] = (symbol, ts)
            return 10.5

        def get_history_price(
            self, symbol: str, ts1: str, ts2: str
        ) -> list[dict[str, Any]]:
            recorded["get_history_price"] = (symbol, ts1, ts2)
            return [{"symbol": symbol, "start": ts1, "end": ts2}]

        def get_data(self, symbol: str, ts: str) -> dict[str, Any]:
            recorded["get_data"] = (symbol, ts)
            return {"symbol": symbol, "ts": ts}

        def get_candles(
            self, symbol: str, start: str, end: str
        ) -> list[dict[str, Any]]:
            recorded["get_candles"] = (symbol, start, end)
            return [{"symbol": symbol, "start": start, "end": end}]

    monkeypatch.setattr(
        "trading_algos_dashboard.services.server_rpc_clients.ServerProxy",
        lambda *_args, **_kwargs: _Proxy(),
    )

    client = DataServerClient(host="127.0.0.1", port=6010, timeout_seconds=2.0)
    ts = datetime.fromisoformat("2024-01-01T09:30:00")

    assert client.ping() == "pong"
    assert recorded["timeout_seconds"] == 2.0
    assert client.get_price("AAPL", ts) == 10.5
    assert client.get_history_price(
        "AAPL",
        ts,
        datetime.fromisoformat("2024-01-01T09:32:00"),
    ) == [
        {
            "symbol": "AAPL",
            "start": "2024-01-01 09:30:00",
            "end": "2024-01-01 09:32:00",
        }
    ]
    assert client.get_data("AAPL", ts) == {
        "symbol": "AAPL",
        "ts": "2024-01-01 09:30:00",
    }
    assert client.get_candles(
        "AAPL", ts, datetime.fromisoformat("2024-01-01T09:32:00")
    ) == [
        {
            "symbol": "AAPL",
            "start": "2024-01-01 09:30:00",
            "end": "2024-01-01 09:32:00",
        }
    ]
    assert recorded["get_price"] == ("AAPL", "2024-01-01 09:30:00")
    assert recorded["get_history_price"] == (
        "AAPL",
        "2024-01-01 09:30:00",
        "2024-01-01 09:32:00",
    )
    assert recorded["get_data"] == ("AAPL", "2024-01-01 09:30:00")
    assert recorded["get_candles"] == (
        "AAPL",
        "2024-01-01 09:30:00",
        "2024-01-01 09:32:00",
    )


def test_fake_datetime_server_client_exposes_all_registered_methods(
    monkeypatch,
) -> None:
    recorded: list[tuple[str, tuple[Any, ...]]] = []

    class _Proxy:
        def ping(self) -> str:
            recorded.append(("ping", ()))
            return "pong"

        def ping_with_timeout(self, timeout_seconds: float) -> str:
            recorded.append(("ping_with_timeout", (timeout_seconds,)))
            return "pong"

        def init(self, date: str, time: str, speed: int) -> int:
            recorded.append(("init", (date, time, speed)))
            return 0

        def start_clock(self) -> int:
            recorded.append(("start_clock", ()))
            return 0

        def stop(self) -> str:
            recorded.append(("stop", ()))
            return "2024-01-01 09:30:00"

        def restart(self) -> int:
            recorded.append(("restart", ()))
            return 0

        def get_ts(self, delta_seconds: int) -> str:
            recorded.append(("get_ts", (delta_seconds,)))
            return "2024-01-01 09:30:05"

        def get_speed_factor(self) -> int:
            recorded.append(("get_speed_factor", ()))
            return 4

    monkeypatch.setattr(
        "trading_algos_dashboard.services.server_rpc_clients.ServerProxy",
        lambda *_args, **_kwargs: _Proxy(),
    )

    client = FakeDateTimeServerClient(host="127.0.0.1", port=7100)

    assert client.ping() == "pong"
    assert client.ping_with_timeout(2.0) == "pong"
    assert client.init("2024-01-01", "09:30:00", 4) == 0
    assert client.start_clock() == 0
    assert client.stop() == "2024-01-01 09:30:00"
    assert client.restart() == 0
    assert client.get_ts(5) == "2024-01-01 09:30:05"
    assert client.get_speed_factor() == 4
    assert recorded == [
        ("ping", ()),
        ("ping_with_timeout", (2.0,)),
        ("init", ("2024-01-01", "09:30:00", 4)),
        ("start_clock", ()),
        ("stop", ()),
        ("restart", ()),
        ("get_ts", (5,)),
        ("get_speed_factor", ()),
    ]


def test_engines_control_server_client_exposes_all_registered_methods(
    monkeypatch,
) -> None:
    calls: list[tuple[str, tuple[Any, ...]]] = []

    class _Proxy:
        def ping(self) -> str:
            calls.append(("ping", ()))
            return "pong"

        def ping_with_timeout(self, timeout_seconds: float) -> str:
            calls.append(("ping_with_timeout", (timeout_seconds,)))
            return "pong"

        def run_alertgen_and_sensors(self, payload: dict[str, Any]) -> int:
            calls.append(("run_alertgen_and_sensors", (payload,)))
            return 0

        def get_all_alertgen_info(self) -> list[dict[str, Any]]:
            calls.append(("get_all_alertgen_info", ()))
            return [{"name": "alertgen-a"}]

        def stop_all_alertgen_instances(self) -> list[dict[str, Any]]:
            calls.append(("stop_all_alertgen_instances", ()))
            return [{"name": "alertgen-a", "stopped_at": "now"}]

        def start_decision_maker(self, payload: dict[str, Any]) -> int:
            calls.append(("start_decision_maker", (payload,)))
            return 0

        def get_decision_maker_info(self) -> dict[str, Any]:
            calls.append(("get_decision_maker_info", ()))
            return {"name": "decision-maker-a"}

        def stop_decision_maker_instance(self) -> dict[str, Any]:
            calls.append(("stop_decision_maker_instance", ()))
            return {"name": "decision-maker-a", "stopped_at": "now"}

        def is_decision_maker_stop_complete(self) -> bool:
            calls.append(("is_decision_maker_stop_complete", ()))
            return True

        def get_decision_maker_stop_report(self) -> dict[str, Any]:
            calls.append(("get_decision_maker_stop_report", ()))
            return {"name": "decision-maker-a", "stopped_at": "now"}

        def get_all_engines_reports(self) -> dict[str, Any]:
            calls.append(("get_all_engines_reports", ()))
            return {"decisionmaker_report_dict": {}, "alertgen_report_dict_list": []}

        def check_connections(self) -> list[dict[str, str]]:
            calls.append(("check_connections", ()))
            return [{"central(127.0.0.1:6000)": "up"}]

        def run_all_engines(self) -> int:
            calls.append(("run_all_engines", ()))
            return 0

        def pause_all_engines(self) -> int:
            calls.append(("pause_all_engines", ()))
            return 0

        def is_alertgen_stop_complete(self) -> bool:
            calls.append(("is_alertgen_stop_complete", ()))
            return True

        def get_alertgen_stop_reports(self) -> list[dict[str, Any]]:
            calls.append(("get_alertgen_stop_reports", ()))
            return [{"name": "alertgen-a", "stopped_at": "now"}]

        def run_engine_chain(self, payload: dict[str, Any]) -> dict[str, Any]:
            calls.append(("run_engine_chain", (payload,)))
            return {"ok": True, "payload": payload}

        def stop_engine_chain(self) -> int:
            calls.append(("stop_engine_chain", ()))
            return 0

    monkeypatch.setattr(
        "trading_algos_dashboard.services.server_rpc_clients.ServerProxy",
        lambda *_args, **_kwargs: _Proxy(),
    )

    client = EnginesControlServerClient(host="127.0.0.1", port=7102)
    alertgen_payload = {"execution_id": "exec-1"}
    decmaker_payload = {"config": {"enable": True}}
    engine_payload = {"symbol": "AAPL"}

    assert client.ping() == "pong"
    assert client.ping_with_timeout(2.0) == "pong"
    assert client.run_alertgen_and_sensors(alertgen_payload) == 0
    assert client.get_all_alertgen_info() == [{"name": "alertgen-a"}]
    assert client.stop_all_alertgen_instances() == [
        {"name": "alertgen-a", "stopped_at": "now"}
    ]
    assert client.start_decision_maker(decmaker_payload) == 0
    assert client.get_decision_maker_info() == {"name": "decision-maker-a"}
    assert client.stop_decision_maker_instance() == {
        "name": "decision-maker-a",
        "stopped_at": "now",
    }
    assert client.is_decision_maker_stop_complete() is True
    assert client.get_decision_maker_stop_report() == {
        "name": "decision-maker-a",
        "stopped_at": "now",
    }
    assert client.get_all_engines_reports() == {
        "decisionmaker_report_dict": {},
        "alertgen_report_dict_list": [],
    }
    assert client.check_connections() == [{"central(127.0.0.1:6000)": "up"}]
    assert client.run_all_engines() == 0
    assert client.pause_all_engines() == 0
    assert client.is_alertgen_stop_complete() is True
    assert client.get_alertgen_stop_reports() == [
        {"name": "alertgen-a", "stopped_at": "now"}
    ]
    assert client.run_engine_chain(engine_payload) == {
        "ok": True,
        "payload": engine_payload,
    }
    assert client.stop_engine_chain() == 0
