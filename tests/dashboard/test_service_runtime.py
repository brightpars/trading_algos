from __future__ import annotations

from typing import Any, cast

from trading_algos_dashboard.service_runtime import DashboardEnginesControlServer
from trading_algos_dashboard.services.engines_control_runtime_service import (
    EnginesControlRuntimeService,
)


class _RegisteringServerStub:
    def __init__(self) -> None:
        self.functions: list[Any] = []

    def register_function(self, func: Any) -> None:
        self.functions.append(func)


class _RuntimeServiceStub:
    def __init__(self, result: dict[str, Any]) -> None:
        self.result = result
        self.calls: list[Any] = []
        self.batch_result: dict[str, Any] = {
            "status": "completed",
            "item_count": 1,
            "success_count": 1,
            "failure_count": 0,
            "items": [result],
            "started_at": "2025-01-01T10:00:00+00:00",
            "finished_at": "2025-01-01T10:00:01+00:00",
        }
        self.batch_calls: list[Any] = []

    def run_backtrace(self, request: Any) -> dict[str, Any]:
        self.calls.append(request)
        return self.result

    def run_backtrace_batch(self, request: Any) -> dict[str, Any]:
        self.batch_calls.append(request)
        return self.batch_result


def _build_server(
    *, runtime_service: Any = None, reject_calls: list[str] | None = None
) -> DashboardEnginesControlServer:
    server = object.__new__(DashboardEnginesControlServer)
    server.server = _RegisteringServerStub()
    server._runtime_service = runtime_service or EnginesControlRuntimeService()

    def _reject_if_shutting_down() -> None:
        if reject_calls is not None:
            reject_calls.append("called")

    setattr(cast(Any, server), "reject_if_shutting_down", _reject_if_shutting_down)
    return server


def _candles() -> list[dict[str, object]]:
    return [
        {
            "ts": "2025-01-01T10:00:00Z",
            "Open": 100.0,
            "High": 101.0,
            "Low": 99.0,
            "Close": 100.5,
        }
    ]


def test_register_all_functions_registers_run_backtrace() -> None:
    server = _build_server()

    server.register_all_functions()

    registered_names = [func.__name__ for func in server.server.functions]
    assert registered_names == [
        "start_decision_maker",
        "run_alertgen_and_sensors",
        "run_all_engines",
        "stop_all_engines",
        "run_backtrace",
        "run_backtrace_batch",
    ]


def test_run_backtrace_delegates_to_runtime_service_and_returns_dict() -> None:
    reject_calls: list[str] = []
    runtime_service = _RuntimeServiceStub(
        {
            "status": "completed",
            "run_id": "run-1",
            "request_id": "req-1",
            "algorithm_key": "demo_algo",
            "symbol": "AAPL",
            "input_summary": {"candle_count": 1},
            "signal_summary": {"buy_count": 0, "sell_count": 0},
            "evaluation_summary": {},
            "report": {},
            "chart_payload": {},
            "execution_steps": [],
            "error": None,
            "started_at": "2025-01-01T10:00:00+00:00",
            "finished_at": "2025-01-01T10:00:01+00:00",
        }
    )
    server = _build_server(runtime_service=runtime_service, reject_calls=reject_calls)
    request = {"algorithm_key": "demo_algo"}

    result = server.run_backtrace(request)

    assert reject_calls == ["called"]
    assert runtime_service.calls == [request]
    assert result == runtime_service.result
    assert isinstance(result, dict)


def test_run_backtrace_returns_stable_dict_payload_for_invalid_input() -> None:
    reject_calls: list[str] = []
    server = _build_server(reject_calls=reject_calls)

    result = server.run_backtrace({"symbol": "AAPL", "candles": _candles()})

    assert reject_calls == ["called"]
    assert isinstance(result, dict)
    assert result["status"] == "failed"
    assert result["error"] == (
        "Backtrace request is missing required field: algorithm_key"
    )
    assert set(result.keys()) == {
        "status",
        "run_id",
        "request_id",
        "algorithm_key",
        "symbol",
        "input_summary",
        "signal_summary",
        "evaluation_summary",
        "report",
        "chart_payload",
        "execution_steps",
        "error",
        "started_at",
        "finished_at",
    }


def test_run_backtrace_batch_delegates_to_runtime_service_and_returns_dict() -> None:
    reject_calls: list[str] = []
    runtime_service = _RuntimeServiceStub(
        {
            "status": "completed",
            "run_id": "run-1",
            "request_id": "req-1",
            "algorithm_key": "demo_algo",
            "symbol": "AAPL",
            "input_summary": {"candle_count": 1},
            "signal_summary": {"buy_count": 0, "sell_count": 0},
            "evaluation_summary": {},
            "report": {},
            "chart_payload": {},
            "execution_steps": [],
            "error": None,
            "started_at": "2025-01-01T10:00:00+00:00",
            "finished_at": "2025-01-01T10:00:01+00:00",
        }
    )
    server = _build_server(runtime_service=runtime_service, reject_calls=reject_calls)
    request = {
        "items": [
            {"algorithm_key": "demo_algo", "symbol": "AAPL", "candles": _candles()}
        ]
    }

    result = server.run_backtrace_batch(request)

    assert reject_calls == ["called"]
    assert runtime_service.batch_calls == [request]
    assert result == runtime_service.batch_result
    assert isinstance(result, dict)
