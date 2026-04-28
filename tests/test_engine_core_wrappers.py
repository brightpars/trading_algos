from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from trading_algos.alertgen.engine_core import AlertgenAlgorithmCore
from trading_algos.decmaker.engine_core import DecmakerAlgorithmCore
from trading_algos.decmaker.validation import validate_decmaker_engine_payload


def test_decmaker_validation_normalizes_numeric_fields() -> None:
    validated = validate_decmaker_engine_payload(
        {
            "type": "dec1",
            "interval_secs": "60",
            "confidence_threshold_buy": "9.0",
            "confidence_threshold_sell": "8.0",
            "max_percent_higher_price_buy": "7.0",
            "max_percent_lower_price_sell": "6.0",
        }
    )

    assert validated == {
        "type": "dec1",
        "interval_secs": 60,
        "confidence_threshold_buy": 9.0,
        "confidence_threshold_sell": 8.0,
        "max_percent_higher_price_buy": 7.0,
        "max_percent_lower_price_sell": 6.0,
    }


def test_decmaker_validation_rejects_invalid_interval() -> None:
    with pytest.raises(ValueError, match="interval_secs must be > 0"):
        validate_decmaker_engine_payload(
            {
                "type": "dec1",
                "interval_secs": 0,
                "confidence_threshold_buy": 9.0,
                "confidence_threshold_sell": 8.0,
                "max_percent_higher_price_buy": 7.0,
                "max_percent_lower_price_sell": 6.0,
            }
        )


def test_decmaker_algorithm_core_delegates_processing(monkeypatch) -> None:
    algorithm = Mock()
    monkeypatch.setattr(
        "trading_algos.decmaker.engine_core.create_decmaker_algorithm",
        lambda container_obj, engine_config: algorithm,
    )

    core = DecmakerAlgorithmCore(
        container_obj=object(),
        label="dec engine_config",
        engine_config={
            "type": "dec1",
            "interval_secs": "60",
            "confidence_threshold_buy": "9.0",
            "confidence_threshold_sell": "8.0",
            "max_percent_higher_price_buy": "7.0",
            "max_percent_lower_price_sell": "6.0",
        },
    )

    core.process_alerts_list([{"alertID": 1}])

    assert core.confidence_threshold_buy == 9.0
    algorithm.process_alerts_list.assert_called_once_with([{"alertID": 1}])


def test_alertgen_algorithm_core_normalizes_and_delegates(
    monkeypatch, tmp_path
) -> None:
    algorithm = SimpleNamespace(
        latest_data_modifiable={
            "buy_SIGNAL": True,
            "sell_SIGNAL": False,
            "trend_confidence": 0.8,
        },
        process=Mock(),
        interactive_report_payloads=Mock(return_value=[({"chart": 1}, "chart")]),
        alg_specific_report=Mock(return_value=[("figure.png", "figure")]),
    )
    monkeypatch.setattr(
        "trading_algos.alertgen.engine_core.create_alertgen_algorithm",
        lambda sensor_config, report_base_path: (algorithm, sensor_config["alg_param"]),
    )

    core = AlertgenAlgorithmCore(
        name="ag:s1",
        engine_config={"type": "gen1", "interval_secs": 60},
        sensor_config={
            "buy": "true",
            "sell": "false",
            "symbol": "EVGO",
            "alg_key": "OLD_aggregate_boundary_and_channel_NEW_hard_boolean_gating_and_or_majority",
            "alg_param": {"window": 30},
        },
        report_base_path=str(tmp_path),
    )

    core.process({"Close": 10})

    assert core.do_buy is True
    assert core.do_sell is False
    assert core.symbol == "EVGO"
    assert core.buy_signal(core.latest_data_modifiable) is True
    assert core.signal_confidence(core.latest_data_modifiable) == 0.8
    assert core.interactive_report_payloads() == [({"chart": 1}, "chart")]
    assert core.alg_specific_report() == [("figure.png", "figure")]
    algorithm.process.assert_called_once_with({"Close": 10})
