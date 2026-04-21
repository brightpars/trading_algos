import json

import pytest

from trading_algos.alertgen import list_alert_algorithm_specs
from trading_algos.alertgen.algorithms.composite.aggregate import (
    AggregateAlertAlgorithm,
    agreegate_algs,
)
from trading_algos.alertgen.algorithms.trend.boundary_breakout import (
    LowAnchoredBoundaryBreakoutAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.channel_breakout import (
    CloseHighChannelBreakoutAlertAlgorithm,
    RollingChannelBreakoutAlertAlgorithm,
)
from trading_algos.alertgen.core.algorithm_registry import (
    get_alert_algorithm_spec_by_key,
)
from trading_algos.alertgen.core.factory import create_alertgen_algorithm
from trading_algos.alertgen.core.validation import normalize_alertgen_sensor_config
from trading_algos.alertgen.shared_utils.models import Candle
from trading_algos.alertgen.shared_utils.reporting import serialize_analysis_report


def _sample_rows(count=5, *, flat=False):
    if flat:
        return [
            {
                "ts": f"2025-01-01 10:00:0{i}",
                "Open": 10,
                "High": 10,
                "Low": 10,
                "Close": 10,
            }
            for i in range(count)
        ]
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


def test_aggregate_alert_algorithm_produces_interactive_payloads(tmp_path):
    aggregate = agreegate_algs(
        "AAPL",
        report_base_path=str(tmp_path),
        buy_algs_obj_list=[
            LowAnchoredBoundaryBreakoutAlertAlgorithm(
                "AAPL", report_base_path=str(tmp_path)
            )
        ],
        sell_algs_obj_list=[
            CloseHighChannelBreakoutAlertAlgorithm(
                "AAPL", report_base_path=str(tmp_path), wlen=2
            )
        ],
    )

    sample_rows = _sample_rows(4)
    aggregate.process_list(sample_rows)

    payloads = aggregate.interactive_report_payloads()

    assert len(payloads) >= 1
    assert all(payload for payload, _description in payloads)


def test_alert_algorithm_catalog_exposes_registered_specs():
    specs = list_alert_algorithm_specs()

    keys = [spec.key for spec in specs]

    assert keys == [
        "boundary_breakout",
        "double_red_confirmation",
        "low_anchored_boundary_breakout",
        "rolling_channel_breakout",
        "close_high_channel_breakout",
        "aggregate_boundary_and_channel",
        "aggregate_channel_dual_window",
    ]
    assert any(spec.tags for spec in specs)
    assert all(spec.version for spec in specs)
    assert all(spec.category for spec in specs)
    assert all(spec.warmup_period >= 1 for spec in specs)


def test_factory_creates_registered_algorithm(tmp_path):
    algorithm, alg_param = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "close_high_channel_breakout",
            "alg_param": {"window": 7},
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path),
    )

    assert algorithm.alg_name == "close_high_channel_breakout_wlen=7"
    assert algorithm.algorithm_metadata()["evaluate_window_len"] == 5
    assert alg_param == {"window": 7}


@pytest.mark.parametrize(
    ("alg_key", "alg_param"),
    [
        ("boundary_breakout", {"period": 5}),
        ("double_red_confirmation", {"period": 5}),
        ("low_anchored_boundary_breakout", {"period": 5}),
        ("rolling_channel_breakout", {"window": 3}),
        ("close_high_channel_breakout", {"window": 3}),
        ("aggregate_boundary_and_channel", {"window": 3}),
        (
            "aggregate_channel_dual_window",
            {"buy_window": 2, "sell_window": 3},
        ),
    ],
)
def test_registered_algorithms_follow_basic_contract(tmp_path, alg_key, alg_param):
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": alg_key,
            "alg_param": alg_param,
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path),
    )

    algorithm.process_list(_sample_rows(5))
    metadata = algorithm.algorithm_metadata()
    decision = algorithm.current_decision()

    assert metadata["alg_name"] == algorithm.alg_name
    assert metadata["symbol"] == "AAPL"
    assert isinstance(algorithm.minimum_history(), int)
    assert decision.trend == algorithm.latest_predicted_trend
    assert isinstance(algorithm.interactive_report_payloads(), list)


@pytest.mark.parametrize(
    "alg_key, alg_param",
    [
        ("boundary_breakout", {"period": 5}),
        ("rolling_channel_breakout", {"window": 2}),
        ("close_high_channel_breakout", {"window": 2}),
    ],
)
def test_algorithms_handle_flat_candles_without_crashing(tmp_path, alg_key, alg_param):
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": alg_key,
            "alg_param": alg_param,
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path),
    )

    algorithm.process_list(_sample_rows(5, flat=True))
    algorithm.evaluate()

    assert isinstance(algorithm.eval_dict, dict)


def test_aggregate_algorithm_supports_composition_metadata_and_alias(tmp_path):
    aggregate = AggregateAlertAlgorithm(
        "AAPL",
        report_base_path=str(tmp_path),
        buy_algs_obj_list=[
            LowAnchoredBoundaryBreakoutAlertAlgorithm(
                "AAPL", report_base_path=str(tmp_path)
            )
        ],
        sell_algs_obj_list=[
            CloseHighChannelBreakoutAlertAlgorithm(
                "AAPL", report_base_path=str(tmp_path), wlen=2
            )
        ],
    )

    metadata = aggregate.composition_metadata()

    assert metadata["buy_method"] == agreegate_algs.Method.And
    assert metadata["sell_algorithms"]


def test_validation_rejects_missing_algorithm_key():
    with pytest.raises(ValueError, match="missing required keys: alg_key"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_param": {"window": 1},
                "buy": True,
                "sell": True,
            }
        )


def test_validation_rejects_unsupported_algorithm_key():
    with pytest.raises(ValueError, match="unsupported"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "not_real",
                "alg_param": {"window": 1},
                "buy": True,
                "sell": True,
            }
        )


def test_validation_rejects_invalid_dual_window_param_shape():
    with pytest.raises(ValueError, match="missing required keys: sell_window"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "aggregate_channel_dual_window",
                "alg_param": {"buy_window": 1},
                "buy": True,
                "sell": True,
            }
        )


def test_reporting_serialization_writes_expected_payload(tmp_path):
    report_file = serialize_analysis_report(
        path=str(tmp_path),
        filename="sample",
        data_list=_sample_rows(2),
        eval_dict={"B~": 1},
    )

    payload = json.loads((tmp_path / "sample.dict").read_text())

    assert report_file.endswith("sample.dict")
    assert payload["eval_dict"] == {"B~": 1}


def test_aggregate_method_or_promotes_buy_signal(tmp_path):
    aggregate = AggregateAlertAlgorithm(
        "AAPL",
        report_base_path=str(tmp_path),
        buy_algs_obj_list=[
            LowAnchoredBoundaryBreakoutAlertAlgorithm(
                "AAPL", report_base_path=str(tmp_path)
            )
        ],
        sell_algs_obj_list=[],
        buy_method=AggregateAlertAlgorithm.Method.Or,
    )

    aggregate.latest_predicted_trend_list_buy = [("UP", 7.0)]
    aggregate.latest_predicted_trend_list_sell = []
    aggregate.aggregate_trends_and_set_confidence()

    assert aggregate.latest_predicted_trend == "UP"
    assert aggregate.latest_predicted_trend_confidence == 7.0


def test_candle_model_round_trip():
    raw = {
        "ts": "2025-01-01 10:00:00",
        "Open": 10,
        "High": 12,
        "Low": 9,
        "Close": 11,
        "Volume": 100,
    }

    candle = Candle.from_mapping(raw)

    assert candle.close == 11.0
    assert candle.extra == {"Volume": 100}
    assert candle.to_mapping() == raw


def test_algorithm_exposes_typed_current_decision(tmp_path):
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "close_high_channel_breakout",
            "alg_param": {"window": 2},
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path),
    )

    algorithm.process(
        {
            "ts": "2025-01-01 10:00:00",
            "Open": 10,
            "High": 11,
            "Low": 9,
            "Close": 10.5,
        }
    )

    decision = algorithm.current_decision()

    assert decision.trend == algorithm.latest_predicted_trend
    assert decision.confidence == algorithm.latest_predicted_trend_confidence


def test_algorithm_evaluate_populates_metrics_via_evaluation_module(tmp_path):
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "close_high_channel_breakout",
            "alg_param": {"window": 2},
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path),
    )

    rows = _sample_rows(5)
    algorithm.process_list(rows)

    algorithm.evaluate()

    assert {"B~", "B+", "S~", "S+", "!!"}.issubset(algorithm.eval_dict)


def test_algorithm_spec_warmup_metadata_matches_runtime_behavior():
    spec = get_alert_algorithm_spec_by_key("rolling_channel_breakout")
    algorithm = RollingChannelBreakoutAlertAlgorithm(
        "AAPL", report_base_path="/tmp", wlen=spec.warmup_period
    )

    assert spec.warmup_period == algorithm.minimum_history()


def test_algorithm_spec_can_be_resolved_by_key():
    spec = get_alert_algorithm_spec_by_key("rolling_channel_breakout")

    assert spec.key == "rolling_channel_breakout"
    assert spec.name == "Rolling Channel Breakout"


def test_validation_accepts_alg_key_without_alg_code():
    normalized = normalize_alertgen_sensor_config(
        {
            "symbol": "AAPL",
            "alg_key": "close_high_channel_breakout",
            "alg_param": {"window": 2},
            "buy": True,
            "sell": True,
        }
    )

    assert normalized["alg_key"] == "close_high_channel_breakout"
    assert normalized["alg_param"] == {"window": 2}


def test_default_alertgen_sensor_config_prefers_alg_key_only():
    from trading_algos.alertgen.core.registry import get_default_alertgen_sensor_config

    sensor = get_default_alertgen_sensor_config()
    sensor_config = sensor["sensor_config"]

    assert sensor_config["alg_key"] == "aggregate_boundary_and_channel"
    assert "alg_code" not in sensor_config
    assert sensor_config["symbol"] == "SYMBOL"
