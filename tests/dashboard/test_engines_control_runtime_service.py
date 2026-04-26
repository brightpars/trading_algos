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
