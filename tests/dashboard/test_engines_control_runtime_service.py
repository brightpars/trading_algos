from datetime import datetime, timezone

from trading_algos_dashboard.services.engines_control_runtime_service import (
    EnginesControlRuntimeService,
)


class _BacktraceSessionRepositoryStub:
    def __init__(self) -> None:
        self.sessions: dict[str, dict[str, object]] = {}

    def create_session(self, document: dict[str, object]) -> dict[str, object]:
        payload = dict(document)
        self.sessions[str(payload["run_id"])] = payload
        return payload

    def update_session(self, run_id: str, values: dict[str, object]) -> None:
        self.sessions[run_id].update(values)

    def get_run(self, run_id: str) -> dict[str, object] | None:
        payload = self.sessions.get(run_id)
        if payload is None:
            return None
        return dict(payload)

    def list_recent_runs(self, *, limit: int = 20) -> list[dict[str, object]]:
        return list(self.sessions.values())[:limit]


class _DataSourceServiceStub:
    def __init__(self, candles: list[dict[str, object]]) -> None:
        self.candles = [dict(candle) for candle in candles]
        self.calls: list[dict[str, object]] = []

    def fetch_candles(self, *, symbol: str, start: datetime, end: datetime):
        self.calls.append(
            {
                "symbol": symbol,
                "start": start,
                "end": end,
            }
        )
        return type("_FetchResult", (), {"candles": [dict(c) for c in self.candles]})()


def _candles() -> list[dict[str, object]]:
    return [
        {
            "ts": "2025-01-01T10:00:00Z",
            "Open": 100.0,
            "High": 101.0,
            "Low": 99.0,
            "Close": 100.5,
            "Volume": 1000,
        },
        {
            "ts": "2025-01-01T10:01:00Z",
            "Open": 100.5,
            "High": 101.5,
            "Low": 100.0,
            "Close": 101.0,
        },
    ]


def test_run_backtrace_normalizes_defaults_for_valid_request() -> None:
    service = EnginesControlRuntimeService()

    result = service.run_backtrace(
        {
            "algorithm_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
            "symbol": "AAPL",
            "candles": _candles() * 3,
        }
    )

    assert result["status"] == "completed"
    assert result["request_id"] is None
    assert (
        result["algorithm_key"]
        == "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation"
    )
    assert result["symbol"] == "AAPL"
    assert result["error"] is None
    assert result["input_summary"] == {
        "input_mode": "inline_candles",
        "candle_count": 6,
        "buy_enabled": True,
        "sell_enabled": True,
        "has_report_base_path": False,
        "algorithm_param_keys": [],
        "metadata_keys": [],
    }
    assert result["signal_summary"]["total_rows"] == 6
    assert "metric_groups" in result["evaluation_summary"]
    assert result["report"]["report_version"] == "1.0"
    assert result["chart_payload"]
    assert result["execution_steps"]


def test_run_backtrace_fails_for_missing_required_field() -> None:
    service = EnginesControlRuntimeService()

    result = service.run_backtrace(
        {
            "symbol": "AAPL",
            "candles": _candles(),
        }
    )

    assert result["status"] == "failed"
    assert (
        result["error"] == "Backtrace request is missing required field: algorithm_key"
    )
    assert result["algorithm_key"] == ""
    assert result["symbol"] == "AAPL"
    assert result["signal_summary"] == {}
    assert result["evaluation_summary"] == {}
    assert result["report"] == {}
    assert result["chart_payload"] == {}
    assert result["execution_steps"] == []


def test_run_backtrace_fails_for_invalid_candle_payload_shape() -> None:
    service = EnginesControlRuntimeService()

    result = service.run_backtrace(
        {
            "algorithm_key": "demo_algo",
            "symbol": "AAPL",
            "candles": [
                {
                    "ts": "2025-01-01T10:00:00Z",
                    "Open": 100.0,
                    "High": 101.0,
                    "Low": 99.0,
                }
            ],
        }
    )

    assert result["status"] == "failed"
    assert result["error"] == "Candle #0 is missing required field: Close"
    assert result["input_summary"] == {
        "provided_keys": ["algorithm_key", "candles", "symbol"],
        "candle_count": 1,
        "has_data_source": False,
        "start_at": None,
        "end_at": None,
    }


def test_run_backtrace_returns_stable_result_shape() -> None:
    service = EnginesControlRuntimeService()

    result = service.run_backtrace(
        {
            "algorithm_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
            "algorithm_params": {"window": 2},
            "symbol": "AAPL",
            "candles": _candles() * 3,
            "buy": False,
            "sell": True,
            "request_id": "req-123",
            "report_base_path": "/tmp/reports",
            "metadata": {"source": "test"},
        }
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
    assert result["status"] == "completed"
    assert isinstance(result["run_id"], str)
    assert result["run_id"]
    assert result["request_id"] == "req-123"
    assert result["started_at"]
    assert result["finished_at"]
    assert result["input_summary"] == {
        "input_mode": "inline_candles",
        "candle_count": 6,
        "buy_enabled": False,
        "sell_enabled": True,
        "has_report_base_path": True,
        "algorithm_param_keys": ["window"],
        "metadata_keys": ["source"],
    }
    assert result["signal_summary"]["total_rows"] == 6
    assert result["evaluation_summary"] == result["report"]["evaluation_summary"]
    assert result["report"]["charts"]
    assert result["chart_payload"]
    assert result["execution_steps"][0]["step"] == "run_algorithm"


def test_run_backtrace_fails_for_invalid_algorithm_key() -> None:
    service = EnginesControlRuntimeService()

    result = service.run_backtrace(
        {
            "algorithm_key": "does_not_exist",
            "symbol": "AAPL",
            "candles": _candles() * 3,
        }
    )

    assert result["status"] == "failed"
    assert result["algorithm_key"] == "does_not_exist"
    assert result["symbol"] == "AAPL"
    assert result["error"] == "sensor_config alg_key=does_not_exist is unsupported"
    assert result["signal_summary"] == {}
    assert result["evaluation_summary"] == {}
    assert result["report"] == {}
    assert result["chart_payload"] == {}
    assert result["execution_steps"] == []


def test_run_backtrace_handles_short_input_history_consistently() -> None:
    service = EnginesControlRuntimeService()

    result = service.run_backtrace(
        {
            "algorithm_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
            "algorithm_params": {"window": 20},
            "symbol": "AAPL",
            "candles": _candles()[:1],
        }
    )

    assert result["status"] == "completed"
    assert result["signal_summary"]["total_rows"] == 1
    assert result["report"]["evaluation_summary"]["metric_groups"]
    assert result["execution_steps"][0]["metadata"]["candle_count"] == 1
    assert any(
        chart["chart_id"] == "core_indicators" for chart in result["report"]["charts"]
    )


def test_run_backtrace_persists_success_result() -> None:
    repository = _BacktraceSessionRepositoryStub()
    service = EnginesControlRuntimeService(backtrace_session_repository=repository)

    result = service.run_backtrace(
        {
            "algorithm_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
            "symbol": "AAPL",
            "candles": _candles() * 3,
            "request_id": "req-123",
        }
    )

    persisted = repository.get_run(result["run_id"])

    assert persisted is not None
    assert persisted["run_id"] == result["run_id"]
    assert persisted["request_id"] == "req-123"
    assert persisted["status"] == "completed"
    assert persisted["algorithm_key"] == result["algorithm_key"]
    assert persisted["symbol"] == result["symbol"]
    assert persisted["input_summary"] == result["input_summary"]
    assert persisted["result_summary"] == {
        "status": "completed",
        "total_rows": 6,
        "buy_count": result["signal_summary"].get("buy_count"),
        "sell_count": result["signal_summary"].get("sell_count"),
        "execution_step_count": len(result["execution_steps"]),
        "has_report": True,
        "has_chart_payload": True,
    }
    assert persisted["full_result"] == result
    assert persisted["error"] is None
    assert persisted["finished_at"] == result["finished_at"]


def test_run_backtrace_persists_failure_result() -> None:
    repository = _BacktraceSessionRepositoryStub()
    service = EnginesControlRuntimeService(backtrace_session_repository=repository)

    result = service.run_backtrace(
        {
            "symbol": "AAPL",
            "candles": _candles(),
        }
    )

    persisted = repository.get_run(result["run_id"])

    assert result["status"] == "failed"
    assert persisted is not None
    assert persisted["status"] == "failed"
    assert persisted["algorithm_key"] == ""
    assert persisted["symbol"] == "AAPL"
    assert persisted["input_summary"] == result["input_summary"]
    assert persisted["result_summary"] == {}
    assert persisted["full_result"] == result
    assert persisted["error"] == result["error"]
    assert persisted["finished_at"] == result["finished_at"]


def test_run_backtrace_fetches_candles_from_data_source_mode() -> None:
    data_source_service = _DataSourceServiceStub(_candles() * 2)
    service = EnginesControlRuntimeService(data_source_service=data_source_service)

    result = service.run_backtrace(
        {
            "algorithm_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
            "symbol": "AAPL",
            "data_source": {"kind": "market_data_service"},
            "start_at": "2025-01-01T10:00:00Z",
            "end_at": "2025-01-01T10:03:00Z",
        }
    )

    assert result["status"] == "completed"
    assert result["input_summary"] == {
        "input_mode": "data_source",
        "candle_count": 4,
        "buy_enabled": True,
        "sell_enabled": True,
        "has_report_base_path": False,
        "algorithm_param_keys": [],
        "metadata_keys": [],
        "data_source": {"kind": "market_data_service"},
        "start_at": "2025-01-01T10:00:00Z",
        "end_at": "2025-01-01T10:03:00Z",
    }
    assert data_source_service.calls == [
        {
            "symbol": "AAPL",
            "start": datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc),
            "end": datetime(2025, 1, 1, 10, 3, tzinfo=timezone.utc),
        }
    ]


def test_run_backtrace_fails_for_mixed_input_modes() -> None:
    service = EnginesControlRuntimeService(
        data_source_service=_DataSourceServiceStub(_candles())
    )

    result = service.run_backtrace(
        {
            "algorithm_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
            "symbol": "AAPL",
            "candles": _candles(),
            "data_source": {"kind": "market_data_service"},
            "start_at": "2025-01-01T10:00:00Z",
            "end_at": "2025-01-01T10:01:00Z",
        }
    )

    assert result["status"] == "failed"
    assert (
        result["error"]
        == "Backtrace request must use exactly one input mode: inline candles or data_source with start_at/end_at"
    )


def test_run_backtrace_fails_for_missing_input_mode() -> None:
    service = EnginesControlRuntimeService()

    result = service.run_backtrace(
        {
            "algorithm_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
            "symbol": "AAPL",
        }
    )

    assert result["status"] == "failed"
    assert (
        result["error"]
        == "Backtrace request must use exactly one input mode: inline candles or data_source with start_at/end_at"
    )


def test_run_backtrace_fails_when_data_source_mode_missing_time_range() -> None:
    service = EnginesControlRuntimeService(
        data_source_service=_DataSourceServiceStub(_candles())
    )

    result = service.run_backtrace(
        {
            "algorithm_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
            "symbol": "AAPL",
            "data_source": {"kind": "market_data_service"},
            "start_at": "2025-01-01T10:00:00Z",
        }
    )

    assert result["status"] == "failed"
    assert (
        result["error"]
        == "Backtrace request field end_at must be a non-empty ISO datetime string"
    )


def test_run_backtrace_batch_returns_completed_for_multiple_successes() -> None:
    service = EnginesControlRuntimeService()

    result = service.run_backtrace_batch(
        {
            "items": [
                {
                    "algorithm_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
                    "symbol": "AAPL",
                    "candles": _candles() * 2,
                    "request_id": "req-1",
                },
                {
                    "algorithm_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
                    "symbol": "MSFT",
                    "candles": _candles() * 3,
                    "request_id": "req-2",
                },
            ]
        }
    )

    assert result["status"] == "completed"
    assert result["item_count"] == 2
    assert result["success_count"] == 2
    assert result["failure_count"] == 0
    assert len(result["items"]) == 2
    assert [item["request_id"] for item in result["items"]] == ["req-1", "req-2"]
    assert all(item["status"] == "completed" for item in result["items"])
    assert set(result.keys()) == {
        "status",
        "item_count",
        "success_count",
        "failure_count",
        "items",
        "started_at",
        "finished_at",
    }


def test_run_backtrace_batch_isolates_failures_per_item() -> None:
    service = EnginesControlRuntimeService()

    result = service.run_backtrace_batch(
        {
            "items": [
                {
                    "algorithm_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
                    "symbol": "AAPL",
                    "candles": _candles() * 2,
                    "request_id": "req-ok",
                },
                {
                    "algorithm_key": "does_not_exist",
                    "symbol": "MSFT",
                    "candles": _candles() * 2,
                    "request_id": "req-bad",
                },
            ]
        }
    )

    assert result["status"] == "partial_failure"
    assert result["item_count"] == 2
    assert result["success_count"] == 1
    assert result["failure_count"] == 1
    assert result["items"][0]["status"] == "completed"
    assert result["items"][1]["status"] == "failed"
    assert result["items"][1]["algorithm_key"] == "does_not_exist"
    assert (
        result["items"][1]["error"]
        == "sensor_config alg_key=does_not_exist is unsupported"
    )
