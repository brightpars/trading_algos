import json
from csv import DictReader
from pathlib import Path
from typing import cast

import pytest

from trading_algos.alertgen import list_alert_algorithm_specs
from trading_algos.alertgen.algorithms.composite.rule_based_combination.hard_boolean_gating_and_or_majority import (
    evaluate_boolean_gating_row,
)
from trading_algos.alertgen.algorithms.composite.rule_based_combination.helpers import (
    align_child_outputs,
)
from trading_algos.alertgen.algorithms.composite.rule_based_combination.weighted_linear_score_blend import (
    evaluate_weighted_blend_row,
)
from trading_algos.alertgen.algorithms.composite.aggregate import (
    AggregateAlertAlgorithm,
    agreegate_algs,
)
from trading_algos.alertgen.algorithms.trend.boundary_breakout import (
    LowAnchoredBoundaryBreakoutAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.channel_breakout import (
    CloseHighChannelBreakoutAlertAlgorithm,
)
from trading_algos.alertgen.core.algorithm_registry import (
    get_alert_algorithm_spec_by_key,
)
from trading_algos.alertgen.core.factory import create_alertgen_algorithm
from trading_algos.alertgen.core.validation import normalize_alertgen_sensor_config
from trading_algos.alertgen.shared_utils.models import Candle
from trading_algos.alertgen.shared_utils.reporting import serialize_analysis_report


FIXTURES_ROOT = Path(__file__).resolve().parent / "fixtures" / "trend"
MOMENTUM_FIXTURES_ROOT = Path(__file__).resolve().parent / "fixtures" / "momentum"
COMPOSITE_FIXTURES_ROOT = Path(__file__).resolve().parent / "fixtures" / "composite"


def _load_fixture_rows(name: str) -> list[dict[str, object]]:
    with (FIXTURES_ROOT / name).open(newline="", encoding="utf-8") as handle:
        rows = list(DictReader(handle))
    parsed_rows: list[dict[str, object]] = []
    for row in rows:
        parsed_rows.append(
            {
                "ts": row["ts"],
                "Open": float(row["Open"]),
                "High": float(row["High"]),
                "Low": float(row["Low"]),
                "Close": float(row["Close"]),
                "Volume": float(row["Volume"]),
            }
        )
    return parsed_rows


def _load_momentum_fixture_rows(name: str) -> list[dict[str, object]]:
    with (MOMENTUM_FIXTURES_ROOT / name).open(newline="", encoding="utf-8") as handle:
        rows = list(DictReader(handle))
    parsed_rows: list[dict[str, object]] = []
    for row in rows:
        parsed_rows.append(
            {
                "ts": row["ts"],
                "Open": float(row["Open"]),
                "High": float(row["High"]),
                "Low": float(row["Low"]),
                "Close": float(row["Close"]),
                "Volume": float(row["Volume"]),
            }
        )
    return parsed_rows


def _load_json_fixture_rows(path: Path) -> list[dict[str, object]]:
    return json.loads(path.read_text(encoding="utf-8"))


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
        "simple_moving_average_crossover",
        "exponential_moving_average_crossover",
        "triple_moving_average_crossover",
        "price_vs_moving_average",
        "moving_average_ribbon_trend",
        "boundary_breakout",
        "double_red_confirmation",
        "low_anchored_boundary_breakout",
        "rolling_channel_breakout",
        "close_high_channel_breakout",
        "rate_of_change_momentum",
        "accelerating_momentum",
        "rsi_momentum_continuation",
        "stochastic_momentum",
        "cci_momentum",
        "hard_boolean_gating_and_or_majority",
        "weighted_linear_score_blend",
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
        (
            "simple_moving_average_crossover",
            {
                "short_window": 2,
                "long_window": 4,
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "exponential_moving_average_crossover",
            {
                "short_window": 2,
                "long_window": 4,
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "triple_moving_average_crossover",
            {
                "fast_window": 2,
                "medium_window": 3,
                "slow_window": 4,
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "price_vs_moving_average",
            {
                "window": 3,
                "average_type": "sma",
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "moving_average_ribbon_trend",
            {
                "windows": [2, 3, 4],
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "rate_of_change_momentum",
            {
                "window": 3,
                "bullish_threshold": 1.0,
                "bearish_threshold": -1.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "accelerating_momentum",
            {
                "fast_window": 2,
                "slow_window": 4,
                "acceleration_threshold": 0.5,
                "bearish_threshold": -0.5,
                "confirmation_bars": 1,
            },
        ),
        (
            "rsi_momentum_continuation",
            {
                "window": 3,
                "bullish_threshold": 55.0,
                "bearish_threshold": 45.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "stochastic_momentum",
            {
                "k_window": 3,
                "d_window": 2,
                "bullish_threshold": 55.0,
                "bearish_threshold": 45.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "cci_momentum",
            {
                "window": 3,
                "bullish_threshold": 50.0,
                "bearish_threshold": -50.0,
                "confirmation_bars": 1,
            },
        ),
        ("rolling_channel_breakout", {"window": 3}),
        ("close_high_channel_breakout", {"window": 3}),
        (
            "hard_boolean_gating_and_or_majority",
            {
                "mode": "majority",
                "tie_policy": "neutral",
                "veto_sell_count": 0,
                "rows": _load_json_fixture_rows(
                    COMPOSITE_FIXTURES_ROOT / "boolean_truth_table.json"
                ),
            },
        ),
        (
            "weighted_linear_score_blend",
            {
                "weights": {"trend": 0.6, "momentum": 0.3, "filter": 0.1},
                "buy_threshold": 0.4,
                "sell_threshold": -0.4,
                "rows": _load_json_fixture_rows(
                    COMPOSITE_FIXTURES_ROOT / "weighted_blend.json"
                ),
            },
        ),
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
        (
            "simple_moving_average_crossover",
            {
                "short_window": 2,
                "long_window": 3,
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
        ),
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


def test_boolean_gating_fixture_behaviors_match_truth_table() -> None:
    rows = align_child_outputs(
        _load_json_fixture_rows(COMPOSITE_FIXTURES_ROOT / "boolean_truth_table.json")
    )

    and_directions = [
        evaluate_boolean_gating_row(
            row,
            mode="and",
            tie_policy="neutral",
            veto_sell_count=0,
        ).direction
        for row in rows
    ]
    or_directions = [
        evaluate_boolean_gating_row(
            row,
            mode="or",
            tie_policy="neutral",
            veto_sell_count=0,
        ).direction
        for row in rows
    ]
    majority_directions = [
        evaluate_boolean_gating_row(
            row,
            mode="majority",
            tie_policy="neutral",
            veto_sell_count=0,
        ).direction
        for row in rows
    ]
    veto_direction = evaluate_boolean_gating_row(
        rows[1],
        mode="majority",
        tie_policy="neutral",
        veto_sell_count=1,
    ).direction

    assert and_directions == [0, 0, -1, 1, 0]
    assert or_directions == [1, 0, -1, 1, 0]
    assert majority_directions == [1, 0, -1, 1, 0]
    assert veto_direction == -1


def test_weighted_blend_fixture_behaviors_match_expected_thresholds() -> None:
    rows = align_child_outputs(
        _load_json_fixture_rows(COMPOSITE_FIXTURES_ROOT / "weighted_blend.json")
    )
    weights = {"trend": 0.6, "momentum": 0.3, "filter": 0.1}

    decisions = [
        evaluate_weighted_blend_row(
            row,
            weights=weights,
            buy_threshold=0.4,
            sell_threshold=-0.4,
        )
        for row in rows
    ]

    assert decisions[0].score == pytest.approx(0.66)
    assert decisions[0].direction == 1
    assert decisions[1].score == pytest.approx(-0.45)
    assert decisions[1].direction == -1
    assert decisions[2].direction == 0
    assert decisions[3].score == pytest.approx(0.87)
    assert decisions[3].confidence == pytest.approx(0.91)
    assert decisions[3].direction == 1


def test_composite_boolean_gating_registration_and_contract_metadata(tmp_path) -> None:
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "hard_boolean_gating_and_or_majority",
            "alg_param": {
                "mode": "majority",
                "tie_policy": "neutral",
                "veto_sell_count": 0,
                "expected_child_count": 3,
                "rows": _load_json_fixture_rows(
                    COMPOSITE_FIXTURES_ROOT / "boolean_truth_table.json"
                ),
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    payloads = algorithm.interactive_report_payloads()
    spec = get_alert_algorithm_spec_by_key("hard_boolean_gating_and_or_majority")

    assert spec.catalog_ref == "combination:1"
    assert output.metadata["catalog_ref"] == "combination:1"
    assert output.metadata["reporting_mode"] == "composite_trace"
    assert output.metadata["warmup_period"] == algorithm.minimum_history()
    assert payloads
    assert payloads[0][0]["data"]["summary_metrics"]["point_count"] == len(
        output.points
    )


def test_composite_weighted_blend_registration_and_contract_metadata(tmp_path) -> None:
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "weighted_linear_score_blend",
            "alg_param": {
                "weights": {"trend": 0.6, "momentum": 0.3, "filter": 0.1},
                "buy_threshold": 0.4,
                "sell_threshold": -0.4,
                "expected_child_count": 3,
                "rows": _load_json_fixture_rows(
                    COMPOSITE_FIXTURES_ROOT / "weighted_blend.json"
                ),
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    payloads = algorithm.interactive_report_payloads()
    spec = get_alert_algorithm_spec_by_key("weighted_linear_score_blend")

    assert spec.catalog_ref == "combination:2"
    assert output.metadata["catalog_ref"] == "combination:2"
    assert output.metadata["reporting_mode"] == "composite_trace"
    assert output.metadata["warmup_period"] == algorithm.minimum_history()
    assert payloads
    assert payloads[0][0]["data"]["summary_metrics"]["point_count"] == len(
        output.points
    )


def test_composite_validation_rejects_invalid_parameter_shapes() -> None:
    with pytest.raises(ValueError, match="expected_child_count must be > 0"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "hard_boolean_gating_and_or_majority",
                "alg_param": {
                    "mode": "and",
                    "tie_policy": "neutral",
                    "veto_sell_count": 0,
                    "expected_child_count": 0,
                    "rows": [],
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="weights must not be empty"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "weighted_linear_score_blend",
                "alg_param": {
                    "weights": {},
                    "buy_threshold": 0.4,
                    "sell_threshold": -0.4,
                    "rows": [],
                },
                "buy": True,
                "sell": True,
            }
        )


def test_composite_boolean_gating_short_child_set_stays_neutral_until_ready(
    tmp_path,
) -> None:
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "hard_boolean_gating_and_or_majority",
            "alg_param": {
                "mode": "majority",
                "tie_policy": "neutral",
                "veto_sell_count": 0,
                "expected_child_count": 3,
                "rows": _load_json_fixture_rows(
                    COMPOSITE_FIXTURES_ROOT / "boolean_truth_table.json"
                ),
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()

    assert output.points[-1].signal_label == "neutral"
    assert "warmup_pending_incomplete_child_set" in output.points[-1].reason_codes
    assert output.derived_series["warmup_ready"][-1] is False
    assert output.derived_series["expected_child_count"][-1] == 3
    assert output.derived_series["child_count"][-1] == 2


def test_composite_weighted_blend_short_child_set_stays_neutral_until_ready(
    tmp_path,
) -> None:
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "weighted_linear_score_blend",
            "alg_param": {
                "weights": {"trend": 0.6, "momentum": 0.3, "filter": 0.1},
                "buy_threshold": 0.4,
                "sell_threshold": -0.4,
                "expected_child_count": 3,
                "rows": _load_json_fixture_rows(
                    COMPOSITE_FIXTURES_ROOT / "weighted_blend.json"
                ),
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()

    assert output.points[-1].signal_label == "neutral"
    assert "warmup_pending_incomplete_child_set" in output.points[-1].reason_codes
    assert output.derived_series["warmup_ready"][-1] is False
    assert output.derived_series["expected_child_count"][-1] == 3
    assert output.derived_series["child_count"][-1] == 2


def test_composite_boolean_gating_normalized_output_exposes_dashboard_diagnostics(
    tmp_path,
) -> None:
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "hard_boolean_gating_and_or_majority",
            "alg_param": {
                "mode": "majority",
                "tie_policy": "neutral",
                "veto_sell_count": 0,
                "expected_child_count": 3,
                "rows": _load_json_fixture_rows(
                    COMPOSITE_FIXTURES_ROOT / "boolean_truth_table.json"
                ),
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    payloads = algorithm.interactive_report_payloads()

    assert {
        "child_count",
        "expected_child_count",
        "warmup_ready",
        "decision_reason",
    }.issubset(output.derived_series)
    assert output.summary_metrics["decision_reason_counts"]["majority_buy"] >= 1
    assert payloads[0][0]["data"]["derived_series"]["buy_count"][0] == 2
    assert payloads[0][0]["data"]["derived_series"]["sell_count"][2] == 3


def test_composite_weighted_blend_normalized_output_exposes_dashboard_diagnostics(
    tmp_path,
) -> None:
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "weighted_linear_score_blend",
            "alg_param": {
                "weights": {"trend": 0.6, "momentum": 0.3, "filter": 0.1},
                "buy_threshold": 0.4,
                "sell_threshold": -0.4,
                "expected_child_count": 3,
                "rows": _load_json_fixture_rows(
                    COMPOSITE_FIXTURES_ROOT / "weighted_blend.json"
                ),
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    payloads = algorithm.interactive_report_payloads()

    assert {
        "raw_weighted_score",
        "child_count",
        "expected_child_count",
        "warmup_ready",
    }.issubset(output.derived_series)
    assert output.points[3].score == pytest.approx(0.87)
    assert output.points[3].confidence == pytest.approx(0.91)
    assert payloads[0][0]["data"]["derived_series"]["raw_weighted_score"][
        1
    ] == pytest.approx(-0.45)


def test_composite_wave_1_performance_smoke_on_fixture_repetition(tmp_path) -> None:
    algorithms = [
        (
            "hard_boolean_gating_and_or_majority",
            {
                "mode": "majority",
                "tie_policy": "neutral",
                "veto_sell_count": 0,
                "expected_child_count": 3,
                "rows": _load_json_fixture_rows(
                    COMPOSITE_FIXTURES_ROOT / "boolean_truth_table.json"
                )
                * 300,
            },
        ),
        (
            "weighted_linear_score_blend",
            {
                "weights": {"trend": 0.6, "momentum": 0.3, "filter": 0.1},
                "buy_threshold": 0.4,
                "sell_threshold": -0.4,
                "expected_child_count": 3,
                "rows": _load_json_fixture_rows(
                    COMPOSITE_FIXTURES_ROOT / "weighted_blend.json"
                )
                * 300,
            },
        ),
    ]

    for index, (alg_key, alg_param) in enumerate(algorithms):
        algorithm, _ = create_alertgen_algorithm(
            sensor_config={
                "symbol": "AAPL",
                "alg_key": alg_key,
                "alg_param": alg_param,
                "buy": True,
                "sell": True,
            },
            report_base_path=str(tmp_path / str(index)),
        )
        output = algorithm.normalized_output()

        row_count = len(cast(list[dict[str, object]], alg_param["rows"]))
        assert len(output.points) == row_count
        assert output.metadata["warmup_period"] == algorithm.minimum_history()
        assert output.metadata["reporting_mode"] == "composite_trace"


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


def test_validation_rejects_invalid_rule_based_combination_param_shape() -> None:
    with pytest.raises(ValueError, match="missing required keys: rows"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "hard_boolean_gating_and_or_majority",
                "alg_param": {
                    "mode": "and",
                    "tie_policy": "neutral",
                    "veto_sell_count": 0,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="requires sell_threshold <= buy_threshold"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "weighted_linear_score_blend",
                "alg_param": {
                    "weights": {"a": 1.0},
                    "buy_threshold": -0.2,
                    "sell_threshold": 0.4,
                    "rows": [],
                },
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
    spec = get_alert_algorithm_spec_by_key("simple_moving_average_crossover")
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "simple_moving_average_crossover",
            "alg_param": {
                "short_window": 5,
                "long_window": spec.warmup_period,
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path="/tmp",
    )

    assert spec.warmup_period == algorithm.minimum_history()


def test_algorithm_spec_can_be_resolved_by_key():
    spec = get_alert_algorithm_spec_by_key("simple_moving_average_crossover")

    assert spec.key == "simple_moving_average_crossover"
    assert spec.name == "Simple Moving Average Crossover"


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


@pytest.mark.parametrize(
    ("alg_key", "alg_param"),
    [
        (
            "simple_moving_average_crossover",
            {
                "short_window": 3,
                "long_window": 5,
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "exponential_moving_average_crossover",
            {
                "short_window": 3,
                "long_window": 5,
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "triple_moving_average_crossover",
            {
                "fast_window": 2,
                "medium_window": 3,
                "slow_window": 5,
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "price_vs_moving_average",
            {
                "window": 4,
                "average_type": "sma",
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "moving_average_ribbon_trend",
            {
                "windows": [2, 3, 4, 5],
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
        ),
    ],
)
def test_trend_wave_1_fixture_monotonic_cross_produces_buy_without_late_sell(
    tmp_path, alg_key, alg_param
):
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

    algorithm.process_list(_load_fixture_rows("monotonic_cross.csv"))

    buy_indices = [
        index
        for index, item in enumerate(algorithm.data_list)
        if item.get("buy_SIGNAL")
    ]
    sell_indices = [
        index
        for index, item in enumerate(algorithm.data_list)
        if item.get("sell_SIGNAL")
    ]

    assert buy_indices
    assert sell_indices == [] or max(sell_indices) < min(buy_indices)


def test_trend_wave_1_minimum_spread_reduces_whipsaw_events(tmp_path):
    base_sensor_config = {
        "symbol": "AAPL",
        "alg_key": "simple_moving_average_crossover",
        "buy": True,
        "sell": True,
    }
    loose_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            **base_sensor_config,
            "alg_param": {
                "short_window": 2,
                "long_window": 3,
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
        },
        report_base_path=str(tmp_path / "loose"),
    )
    guarded_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            **base_sensor_config,
            "alg_param": {
                "short_window": 2,
                "long_window": 3,
                "minimum_spread": 0.2,
                "confirmation_bars": 2,
            },
        },
        report_base_path=str(tmp_path / "guarded"),
    )

    rows = _load_fixture_rows("whipsaw_guard.csv")
    loose_algorithm.process_list(rows)
    guarded_algorithm.process_list(rows)

    loose_events = len(loose_algorithm.buy_signals) + len(loose_algorithm.sell_signals)
    guarded_events = len(guarded_algorithm.buy_signals) + len(
        guarded_algorithm.sell_signals
    )

    assert guarded_events <= loose_events


def test_validation_rejects_invalid_trend_wave_1_parameter_shapes():
    with pytest.raises(ValueError, match="short_window < long_window"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "simple_moving_average_crossover",
                "alg_param": {
                    "short_window": 5,
                    "long_window": 5,
                    "minimum_spread": 0.0,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="windows must be sorted ascending"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "moving_average_ribbon_trend",
                "alg_param": {
                    "windows": [5, 3, 4],
                    "minimum_spread": 0.0,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )


@pytest.mark.parametrize(
    ("alg_key", "alg_param", "expected_warmup"),
    [
        (
            "simple_moving_average_crossover",
            {
                "short_window": 3,
                "long_window": 5,
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
            5,
        ),
        (
            "exponential_moving_average_crossover",
            {
                "short_window": 3,
                "long_window": 5,
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
            5,
        ),
        (
            "triple_moving_average_crossover",
            {
                "fast_window": 2,
                "medium_window": 4,
                "slow_window": 6,
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
            6,
        ),
        (
            "price_vs_moving_average",
            {
                "window": 5,
                "average_type": "ema",
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
            5,
        ),
        (
            "moving_average_ribbon_trend",
            {
                "windows": [2, 3, 5, 7],
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
            7,
        ),
    ],
)
def test_trend_wave_1_short_history_stays_neutral_until_warmup(
    tmp_path, alg_key, alg_param, expected_warmup
):
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

    algorithm.process_list(
        _load_fixture_rows("monotonic_cross.csv")[: expected_warmup - 1]
    )
    output = algorithm.normalized_output()

    assert algorithm.minimum_history() == expected_warmup
    assert output.points
    assert all(point.signal_label == "neutral" for point in output.points)
    assert any("warmup_pending" in point.reason_codes for point in output.points)


@pytest.mark.parametrize(
    ("alg_key", "alg_param", "expected_reason_code", "expected_annotation_keys"),
    [
        (
            "simple_moving_average_crossover",
            {
                "short_window": 3,
                "long_window": 5,
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
            "bullish_setup",
            {"short_window", "long_window", "average_type"},
        ),
        (
            "exponential_moving_average_crossover",
            {
                "short_window": 3,
                "long_window": 5,
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
            "bullish_setup",
            {"short_window", "long_window", "average_type"},
        ),
        (
            "triple_moving_average_crossover",
            {
                "fast_window": 2,
                "medium_window": 3,
                "slow_window": 5,
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
            "bullish_setup",
            {"fast_window", "medium_window", "slow_window", "average_type"},
        ),
        (
            "price_vs_moving_average",
            {
                "window": 4,
                "average_type": "sma",
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
            "bullish_setup",
            {"window", "average_type"},
        ),
        (
            "moving_average_ribbon_trend",
            {
                "windows": [2, 3, 4, 5],
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
            "bullish_setup",
            {"windows", "average_type"},
        ),
    ],
)
def test_trend_wave_1_normalized_output_exposes_dashboard_diagnostics(
    tmp_path, alg_key, alg_param, expected_reason_code, expected_annotation_keys
):
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

    algorithm.process_list(_load_fixture_rows("monotonic_cross.csv"))

    output = algorithm.normalized_output()
    payloads = algorithm.interactive_report_payloads()
    last_point = output.points[-1]
    child_output = output.child_outputs[0]

    assert payloads
    assert payloads[0][0]["data"]
    assert expected_reason_code in last_point.reason_codes
    assert {"trend_score", "regime_label", "spread_value", "reason_codes"}.issubset(
        output.derived_series
    )
    assert child_output.signal_label == "buy"
    assert child_output.regime_label == algorithm.latest_predicted_trend
    assert expected_reason_code in child_output.diagnostics["reason_codes"]
    assert expected_annotation_keys.issubset(child_output.diagnostics.keys())
    assert child_output.reason_codes == tuple(child_output.diagnostics.keys())


def test_trend_wave_1_validation_rejects_invalid_additional_parameter_shapes():
    with pytest.raises(ValueError, match="fast_window < medium_window < slow_window"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "triple_moving_average_crossover",
                "alg_param": {
                    "fast_window": 4,
                    "medium_window": 4,
                    "slow_window": 5,
                    "minimum_spread": 0.0,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="average_type must be one of"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "price_vs_moving_average",
                "alg_param": {
                    "window": 4,
                    "average_type": "wma",
                    "minimum_spread": 0.0,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="windows must not contain duplicates"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "moving_average_ribbon_trend",
                "alg_param": {
                    "windows": [2, 3, 3],
                    "minimum_spread": 0.0,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )


def test_trend_wave_1_performance_smoke_on_representative_series(tmp_path):
    rows = _load_fixture_rows("monotonic_cross.csv") * 400
    algorithms = [
        (
            "simple_moving_average_crossover",
            {
                "short_window": 3,
                "long_window": 5,
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "exponential_moving_average_crossover",
            {
                "short_window": 3,
                "long_window": 5,
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "triple_moving_average_crossover",
            {
                "fast_window": 2,
                "medium_window": 3,
                "slow_window": 5,
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "price_vs_moving_average",
            {
                "window": 4,
                "average_type": "sma",
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "moving_average_ribbon_trend",
            {
                "windows": [2, 3, 4, 5],
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
        ),
    ]

    for index, (alg_key, alg_param) in enumerate(algorithms):
        algorithm, _ = create_alertgen_algorithm(
            sensor_config={
                "symbol": "AAPL",
                "alg_key": alg_key,
                "alg_param": alg_param,
                "buy": True,
                "sell": True,
            },
            report_base_path=str(tmp_path / str(index)),
        )
        algorithm.process_list(rows)
        output = algorithm.normalized_output()

        assert len(output.points) == len(rows)
        assert output.metadata["warmup_period"] == algorithm.minimum_history()
        assert "trend_score" in output.derived_series


@pytest.mark.parametrize(
    ("alg_key", "alg_param", "expected_warmup"),
    [
        (
            "rate_of_change_momentum",
            {
                "window": 3,
                "bullish_threshold": 1.0,
                "bearish_threshold": -1.0,
                "confirmation_bars": 1,
            },
            4,
        ),
        (
            "accelerating_momentum",
            {
                "fast_window": 2,
                "slow_window": 4,
                "acceleration_threshold": 0.5,
                "bearish_threshold": -0.5,
                "confirmation_bars": 1,
            },
            5,
        ),
        (
            "rsi_momentum_continuation",
            {
                "window": 3,
                "bullish_threshold": 55.0,
                "bearish_threshold": 45.0,
                "confirmation_bars": 1,
            },
            4,
        ),
        (
            "stochastic_momentum",
            {
                "k_window": 3,
                "d_window": 2,
                "bullish_threshold": 55.0,
                "bearish_threshold": 45.0,
                "confirmation_bars": 1,
            },
            4,
        ),
        (
            "cci_momentum",
            {
                "window": 5,
                "bullish_threshold": 50.0,
                "bearish_threshold": -50.0,
                "confirmation_bars": 1,
            },
            5,
        ),
    ],
)
def test_momentum_wave_1_short_history_stays_neutral_until_warmup(
    tmp_path, alg_key, alg_param, expected_warmup
):
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

    algorithm.process_list(
        _load_momentum_fixture_rows("sustained_up.csv")[: expected_warmup - 1]
    )
    output = algorithm.normalized_output()

    assert algorithm.minimum_history() == expected_warmup
    assert output.points
    assert all(point.signal_label == "neutral" for point in output.points)
    assert any("warmup_pending" in point.reason_codes for point in output.points)


@pytest.mark.parametrize(
    ("alg_key", "alg_param", "expected_reason_code", "expected_annotation_keys"),
    [
        (
            "rate_of_change_momentum",
            {
                "window": 3,
                "bullish_threshold": 1.0,
                "bearish_threshold": -1.0,
                "confirmation_bars": 1,
            },
            "roc_bullish",
            {"window", "bullish_threshold", "bearish_threshold"},
        ),
        (
            "accelerating_momentum",
            {
                "fast_window": 2,
                "slow_window": 4,
                "acceleration_threshold": 0.5,
                "bearish_threshold": -0.5,
                "confirmation_bars": 1,
            },
            "acceleration_bullish",
            {
                "fast_window",
                "slow_window",
                "acceleration_threshold",
                "bearish_threshold",
            },
        ),
        (
            "rsi_momentum_continuation",
            {
                "window": 3,
                "bullish_threshold": 55.0,
                "bearish_threshold": 45.0,
                "confirmation_bars": 1,
            },
            "rsi_bullish",
            {"window", "bullish_threshold", "bearish_threshold"},
        ),
        (
            "stochastic_momentum",
            {
                "k_window": 3,
                "d_window": 2,
                "bullish_threshold": 55.0,
                "bearish_threshold": 45.0,
                "confirmation_bars": 1,
            },
            "stochastic_bullish",
            {"k_window", "d_window", "bullish_threshold", "bearish_threshold"},
        ),
        (
            "cci_momentum",
            {
                "window": 5,
                "bullish_threshold": 50.0,
                "bearish_threshold": -50.0,
                "confirmation_bars": 1,
            },
            "cci_bullish",
            {"window", "bullish_threshold", "bearish_threshold"},
        ),
    ],
)
def test_momentum_wave_1_normalized_output_exposes_dashboard_diagnostics(
    tmp_path, alg_key, alg_param, expected_reason_code, expected_annotation_keys
):
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

    algorithm.process_list(_load_momentum_fixture_rows("sustained_up.csv"))

    output = algorithm.normalized_output()
    payloads = algorithm.interactive_report_payloads()
    last_point = output.points[-1]
    child_output = output.child_outputs[0]

    assert payloads
    assert expected_reason_code in last_point.reason_codes
    assert {"trend_score", "regime_label", "reason_codes", "primary_value"}.issubset(
        output.derived_series
    )
    assert child_output.signal_label == "buy"
    assert child_output.regime_label == algorithm.latest_predicted_trend
    assert expected_reason_code in child_output.diagnostics["reason_codes"]
    assert expected_annotation_keys.issubset(child_output.diagnostics.keys())
    assert child_output.reason_codes == tuple(child_output.diagnostics.keys())


def test_momentum_wave_1_validation_rejects_invalid_parameter_shapes() -> None:
    with pytest.raises(ValueError, match="bearish_threshold <= bullish_threshold"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "rate_of_change_momentum",
                "alg_param": {
                    "window": 3,
                    "bullish_threshold": -1.0,
                    "bearish_threshold": 1.0,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="fast_window < slow_window"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "accelerating_momentum",
                "alg_param": {
                    "fast_window": 4,
                    "slow_window": 4,
                    "acceleration_threshold": 0.5,
                    "bearish_threshold": -0.5,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match=r"within \[0, 100\]"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "rsi_momentum_continuation",
                "alg_param": {
                    "window": 3,
                    "bullish_threshold": 101.0,
                    "bearish_threshold": 45.0,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )


@pytest.mark.parametrize(
    ("alg_key", "alg_param"),
    [
        (
            "rate_of_change_momentum",
            {
                "window": 3,
                "bullish_threshold": 1.0,
                "bearish_threshold": -1.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "accelerating_momentum",
            {
                "fast_window": 2,
                "slow_window": 4,
                "acceleration_threshold": 0.5,
                "bearish_threshold": -0.5,
                "confirmation_bars": 1,
            },
        ),
        (
            "rsi_momentum_continuation",
            {
                "window": 3,
                "bullish_threshold": 55.0,
                "bearish_threshold": 45.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "stochastic_momentum",
            {
                "k_window": 3,
                "d_window": 2,
                "bullish_threshold": 55.0,
                "bearish_threshold": 45.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "cci_momentum",
            {
                "window": 5,
                "bullish_threshold": 50.0,
                "bearish_threshold": -50.0,
                "confirmation_bars": 1,
            },
        ),
    ],
)
def test_momentum_wave_1_fixture_sustained_up_produces_buy_without_bearish_reversal(
    tmp_path, alg_key, alg_param
):
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

    algorithm.process_list(_load_momentum_fixture_rows("sustained_up.csv"))

    buy_indices = [
        index
        for index, item in enumerate(algorithm.data_list)
        if item.get("buy_SIGNAL")
    ]
    sell_indices = [
        index
        for index, item in enumerate(algorithm.data_list)
        if item.get("sell_SIGNAL")
    ]

    assert buy_indices
    assert sell_indices == []


def test_momentum_wave_1_performance_smoke_on_fixture_repetition(tmp_path) -> None:
    rows = _load_momentum_fixture_rows("sustained_up.csv") * 300
    algorithms = [
        (
            "rate_of_change_momentum",
            {
                "window": 3,
                "bullish_threshold": 1.0,
                "bearish_threshold": -1.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "accelerating_momentum",
            {
                "fast_window": 2,
                "slow_window": 4,
                "acceleration_threshold": 0.5,
                "bearish_threshold": -0.5,
                "confirmation_bars": 1,
            },
        ),
        (
            "rsi_momentum_continuation",
            {
                "window": 3,
                "bullish_threshold": 55.0,
                "bearish_threshold": 45.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "stochastic_momentum",
            {
                "k_window": 3,
                "d_window": 2,
                "bullish_threshold": 55.0,
                "bearish_threshold": 45.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "cci_momentum",
            {
                "window": 5,
                "bullish_threshold": 50.0,
                "bearish_threshold": -50.0,
                "confirmation_bars": 1,
            },
        ),
    ]

    for index, (alg_key, alg_param) in enumerate(algorithms):
        algorithm, _ = create_alertgen_algorithm(
            sensor_config={
                "symbol": "AAPL",
                "alg_key": alg_key,
                "alg_param": alg_param,
                "buy": True,
                "sell": True,
            },
            report_base_path=str(tmp_path / str(index)),
        )
        algorithm.process_list(rows)
        output = algorithm.normalized_output()

        assert len(output.points) == len(rows)
        assert output.metadata["warmup_period"] == algorithm.minimum_history()
        assert "trend_score" in output.derived_series
