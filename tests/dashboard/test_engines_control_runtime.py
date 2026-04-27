from __future__ import annotations

from trading_algos_dashboard.engines_control_runtime import (
    EnginesControlRuntimeServer,
    run_engine_chain_payload,
)


def _candles() -> list[dict[str, object]]:
    return [
        {
            "ts": "2025-01-01 10:00:00",
            "Open": 10.0,
            "High": 11.0,
            "Low": 9.0,
            "Close": 10.5,
        },
        {
            "ts": "2025-01-01 10:01:00",
            "Open": 10.5,
            "High": 12.0,
            "Low": 10.0,
            "Close": 11.5,
        },
        {
            "ts": "2025-01-01 10:02:00",
            "Open": 11.5,
            "High": 13.0,
            "Low": 11.0,
            "Close": 12.5,
        },
    ]


def test_run_engine_chain_payload_returns_self_contained_dashboard_result(
    tmp_path,
) -> None:
    result = run_engine_chain_payload(
        {
            "symbol": "AAPL",
            "report_base_path": str(tmp_path),
            "candles": _candles(),
            "alertgens": [
                {
                    "symbol": "AAPL",
                    "alg_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
                    "alg_param": {"window": 2},
                    "buy": True,
                    "sell": True,
                }
            ],
            "decmaker": {
                "decmaker_key": "alg1",
                "decmaker_param": {
                    "confidence_threshold_buy": 0.0,
                    "confidence_threshold_sell": 0.0,
                    "max_percent_higher_price_buy": 0.0,
                    "max_percent_lower_price_sell": 0.0,
                },
            },
        }
    )

    assert result["input_kind"] == "engine_chain"
    assert result["alg_name"] == "Engine chain for AAPL"
    assert result["execution_steps"]
    assert result["execution_steps"][0]["step"] == "run_engine_chain"
    assert result["execution_steps"][0]["duration_seconds"] >= 0
    assert result["signal_summary"]["alertgen_count"] == 1
    assert result["signal_summary"]["total_rows"] == 3
    assert result["report"]["algorithm_summary"]["runtime_kind"] == "engine_chain"
    assert result["report"]["diagnostics"]["alertgen_results"]
    assert "latest_decision" in result


def test_engines_control_runtime_server_supports_legacy_method_surface() -> None:
    server = EnginesControlRuntimeServer(
        user_id=1,
        ip="127.0.0.1",
        port=7102,
        sever_name="engines_control",
        log_requests_to_terminal=False,
    )

    assert server.check_connections() == [
        {"central(127.0.0.1:6000)": "down"},
        {"fake_datetime(127.0.0.1:7100)": "down"},
        {"data(127.0.0.1:6010)": "down"},
        {"broker(127.0.0.1:7101)": "down"},
    ]

    run_alertgen_result = server.run_alertgen_and_sensors(
        {
            "execution_id": "exec-1",
            "alertgen_config_list": [
                {
                    "name": "alertgen-a",
                    "enable": True,
                    "engine_config": {"type": "alertgen"},
                    "sensors": [
                        {
                            "name": "sensor-1",
                            "enable": True,
                            "sensor_config": {"symbol": "AAPL"},
                        }
                    ],
                }
            ],
        }
    )
    assert run_alertgen_result == 0
    assert server.get_all_alertgen_info()
    assert server.run_all_engines() == 0
    assert server.pause_all_engines() == 0
    stop_alertgen_reports = server.stop_all_alertgen_instances()
    assert stop_alertgen_reports
    assert server.is_alertgen_stop_complete() is True
    assert server.get_alertgen_stop_reports() == stop_alertgen_reports

    start_decmaker_result = server.start_decision_maker(
        {
            "config": {
                "enable": True,
                "name": "decision-maker-a",
                "engine_config": {
                    "type": "dec1",
                    "confidence_threshold_buy": 0.0,
                    "confidence_threshold_sell": 0.0,
                    "max_percent_higher_price_buy": 0.0,
                    "max_percent_lower_price_sell": 0.0,
                },
            }
        }
    )
    assert start_decmaker_result == 0
    assert server.get_decision_maker_info()["name"] == "decision-maker-a"
    stop_decmaker_report = server.stop_decision_maker_instance()
    assert stop_decmaker_report["name"] == "decision-maker-a"
    assert server.is_decision_maker_stop_complete() is True
    assert server.get_decision_maker_stop_report() == stop_decmaker_report


def test_engines_control_runtime_server_run_engine_chain_populates_reports(
    tmp_path,
) -> None:
    server = EnginesControlRuntimeServer(
        user_id=1,
        ip="127.0.0.1",
        port=7102,
        sever_name="engines_control",
        log_requests_to_terminal=False,
    )

    result = server.run_engine_chain(
        {
            "symbol": "AAPL",
            "report_base_path": str(tmp_path),
            "candles": _candles(),
            "alertgens": [
                {
                    "symbol": "AAPL",
                    "alg_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
                    "alg_param": {"window": 2},
                    "buy": True,
                    "sell": True,
                }
            ],
            "decmaker": {
                "decmaker_key": "alg1",
                "decmaker_param": {
                    "confidence_threshold_buy": 0.0,
                    "confidence_threshold_sell": 0.0,
                    "max_percent_higher_price_buy": 0.0,
                    "max_percent_lower_price_sell": 0.0,
                },
            },
        }
    )

    reports = server.get_all_engines_reports()

    assert (
        result["latest_decision"]
        == reports["decisionmaker_report_dict"]["latest_decision"]
    )
    assert reports["alertgen_report_dict_list"]
    assert server.get_all_alertgen_info()
    assert server.get_decision_maker_info()["type"] == "alg1"
