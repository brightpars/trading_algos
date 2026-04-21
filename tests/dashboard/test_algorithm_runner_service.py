from trading_algos_dashboard.services.algorithm_runner_service import (
    run_alert_algorithm,
)


def _rows(count=6):
    return [
        {
            "ts": f"2025-01-01 10:00:0{i}",
            "Open": 10 + i,
            "High": 11 + i,
            "Low": 9 + i,
            "Close": 10.5 + i,
        }
        for i in range(count)
    ]


def test_run_alert_algorithm_returns_dashboard_payload(tmp_path):
    result = run_alert_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "close_high_channel_breakout",
            "alg_param": {"window": 2},
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path),
        candles=_rows(),
    )
    assert result["alg_key"] == "close_high_channel_breakout"
    assert "eval_dict" in result
    assert "chart_payload" in result
    assert result["report"]["report_version"] == "1.0"
    assert result["report"]["schema_version"] == "1.0"
    assert result["report"]["charts"]
    assert result["evaluator_outputs"]
    assert result["report"]["diagnostics"]


def test_run_alert_algorithm_handles_short_input_history(tmp_path):
    result = run_alert_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "close_high_channel_breakout",
            "alg_param": {"window": 20},
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path),
        candles=_rows(count=3),
    )

    assert result["signal_summary"]["total_rows"] == 3
    assert result["eval_dict"]["correct_predictions"] >= 0
    assert result["report"]["evaluation_summary"]["metric_groups"]
    assert any(
        chart["chart_id"] == "core_indicators" for chart in result["report"]["charts"]
    )
