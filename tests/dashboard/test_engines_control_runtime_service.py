from trading_algos_dashboard.services.engines_control_runtime_service import (
    EnginesControlRuntimeService,
)


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
            "algorithm_key": "demo_algo",
            "symbol": "AAPL",
            "candles": _candles(),
        }
    )

    assert result["status"] == "completed"
    assert result["request_id"] is None
    assert result["algorithm_key"] == "demo_algo"
    assert result["symbol"] == "AAPL"
    assert result["error"] is None
    assert result["input_summary"] == {
        "candle_count": 2,
        "buy_enabled": True,
        "sell_enabled": True,
        "has_report_base_path": False,
        "algorithm_param_keys": [],
        "metadata_keys": [],
    }
    assert result["result_payload"] == {
        "execution_mode": "local_stub",
        "buy_enabled": True,
        "sell_enabled": True,
        "candles_processed": 2,
        "signals": [],
        "artifacts": {},
        "summary": {
            "message": "Backtrace execution is not wired yet",
            "algorithm_params": {},
            "metadata": {},
        },
    }


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
    assert result["result_payload"] == {}


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
    }


def test_run_backtrace_returns_stable_result_shape() -> None:
    service = EnginesControlRuntimeService()

    result = service.run_backtrace(
        {
            "algorithm_key": "demo_algo",
            "algorithm_params": {"window": 5},
            "symbol": "AAPL",
            "candles": _candles(),
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
        "result_payload",
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
        "candle_count": 2,
        "buy_enabled": False,
        "sell_enabled": True,
        "has_report_base_path": True,
        "algorithm_param_keys": ["window"],
        "metadata_keys": ["source"],
    }
    assert result["result_payload"] == {
        "execution_mode": "local_stub",
        "buy_enabled": False,
        "sell_enabled": True,
        "candles_processed": 2,
        "signals": [],
        "artifacts": {},
        "summary": {
            "message": "Backtrace execution is not wired yet",
            "algorithm_params": {"window": 5},
            "metadata": {"source": "test"},
        },
    }
