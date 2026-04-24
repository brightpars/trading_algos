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
MEAN_REVERSION_FIXTURES_ROOT = (
    Path(__file__).resolve().parent / "fixtures" / "mean_reversion"
)
VOLATILITY_FIXTURES_ROOT = Path(__file__).resolve().parent / "fixtures" / "volatility"
PATTERN_FIXTURES_ROOT = Path(__file__).resolve().parent / "fixtures" / "patterns"
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


def _load_mean_reversion_fixture_rows(name: str) -> list[dict[str, object]]:
    with (MEAN_REVERSION_FIXTURES_ROOT / name).open(
        newline="", encoding="utf-8"
    ) as handle:
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


def _load_volatility_fixture_rows(name: str) -> list[dict[str, object]]:
    with (VOLATILITY_FIXTURES_ROOT / name).open(newline="", encoding="utf-8") as handle:
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


def _load_pattern_fixture_rows(name: str) -> list[dict[str, object]]:
    with (PATTERN_FIXTURES_ROOT / name).open(newline="", encoding="utf-8") as handle:
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
        "ichimoku_trend_strategy",
        "macd_trend_strategy",
        "linear_regression_trend",
        "time_series_momentum",
        "simple_moving_average_crossover",
        "exponential_moving_average_crossover",
        "triple_moving_average_crossover",
        "price_vs_moving_average",
        "moving_average_ribbon_trend",
        "breakout_donchian_channel",
        "channel_breakout_with_confirmation",
        "adx_trend_filter",
        "parabolic_sar_trend_following",
        "supertrend",
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
        "kst_know_sure_thing",
        "volume_confirmed_momentum",
        "support_resistance_bounce",
        "breakout_retest",
        "pivot_point_strategy",
        "opening_range_breakout",
        "inside_bar_breakout",
        "z_score_mean_reversion",
        "bollinger_bands_reversion",
        "rsi_reversion",
        "stochastic_reversion",
        "cci_reversion",
        "williams_percent_r_reversion",
        "range_reversion",
        "long_horizon_reversal",
        "volatility_adjusted_reversion",
        "volatility_breakout",
        "atr_channel_breakout",
        "volatility_mean_reversion",
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
            "ichimoku_trend_strategy",
            {
                "conversion_window": 2,
                "base_window": 3,
                "span_b_window": 4,
                "displacement": 2,
                "minimum_cloud_gap": 0.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "macd_trend_strategy",
            {
                "fast_window": 2,
                "slow_window": 4,
                "signal_window": 2,
                "histogram_threshold": 0.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "linear_regression_trend",
            {
                "window": 3,
                "slope_threshold": 0.0,
                "min_r_squared": 0.2,
                "confirmation_bars": 1,
            },
        ),
        (
            "time_series_momentum",
            {
                "window": 3,
                "return_threshold": 0.0,
                "confirmation_bars": 1,
            },
        ),
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
            "breakout_donchian_channel",
            {
                "window": 3,
                "minimum_breakout": 0.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "channel_breakout_with_confirmation",
            {
                "window": 3,
                "breakout_threshold": 0.0,
                "confirmation_bars": 2,
            },
        ),
        (
            "adx_trend_filter",
            {
                "window": 3,
                "adx_threshold": 10.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "parabolic_sar_trend_following",
            {
                "step": 0.02,
                "max_step": 0.2,
                "confirmation_bars": 1,
            },
        ),
        (
            "supertrend",
            {
                "window": 3,
                "multiplier": 2.0,
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
        (
            "kst_know_sure_thing",
            {
                "roc_windows": [3, 4, 5, 6],
                "smoothing_windows": [3, 3, 3, 3],
                "signal_window": 4,
                "entry_mode": "signal_cross",
                "confirmation_bars": 1,
            },
        ),
        (
            "volume_confirmed_momentum",
            {
                "momentum_window": 3,
                "volume_window": 5,
                "relative_volume_threshold": 1.0,
                "signal_threshold": 1.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "z_score_mean_reversion",
            {
                "window": 5,
                "entry_zscore": 1.0,
                "exit_zscore": 0.5,
                "confirmation_bars": 1,
            },
        ),
        (
            "bollinger_bands_reversion",
            {
                "window": 5,
                "std_multiplier": 1.0,
                "exit_band_fraction": 0.25,
                "confirmation_bars": 1,
            },
        ),
        (
            "rsi_reversion",
            {
                "window": 3,
                "oversold_threshold": 35.0,
                "overbought_threshold": 65.0,
                "exit_threshold": 50.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "stochastic_reversion",
            {
                "k_window": 3,
                "d_window": 2,
                "oversold_threshold": 25.0,
                "overbought_threshold": 75.0,
                "exit_threshold": 50.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "cci_reversion",
            {
                "window": 5,
                "oversold_threshold": -50.0,
                "overbought_threshold": 50.0,
                "exit_threshold": 0.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "williams_percent_r_reversion",
            {
                "window": 5,
                "oversold_threshold": -80.0,
                "overbought_threshold": -20.0,
                "exit_threshold": -50.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "range_reversion",
            {
                "window": 5,
                "entry_band_fraction": 0.2,
                "exit_band_fraction": 0.5,
                "confirmation_bars": 1,
            },
        ),
        (
            "long_horizon_reversal",
            {
                "window": 5,
                "entry_return_threshold": 5.0,
                "exit_return_threshold": 2.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "volatility_adjusted_reversion",
            {
                "window": 5,
                "atr_window": 3,
                "entry_atr_multiple": 1.0,
                "exit_atr_multiple": 0.5,
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
        (
            "breakout_donchian_channel",
            {
                "window": 2,
                "minimum_breakout": 0.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "channel_breakout_with_confirmation",
            {
                "window": 2,
                "breakout_threshold": 0.0,
                "confirmation_bars": 2,
            },
        ),
        (
            "adx_trend_filter",
            {
                "window": 2,
                "adx_threshold": 5.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "parabolic_sar_trend_following",
            {"step": 0.02, "max_step": 0.2, "confirmation_bars": 1},
        ),
        (
            "supertrend",
            {"window": 2, "multiplier": 2.0, "confirmation_bars": 1},
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
    ("alg_key", "alg_param"),
    [
        (
            "breakout_donchian_channel",
            {"window": 5, "minimum_breakout": 0.0, "confirmation_bars": 1},
        ),
        (
            "channel_breakout_with_confirmation",
            {"window": 5, "breakout_threshold": 0.0, "confirmation_bars": 2},
        ),
        (
            "adx_trend_filter",
            {"window": 5, "adx_threshold": 10.0, "confirmation_bars": 1},
        ),
        (
            "parabolic_sar_trend_following",
            {"step": 0.02, "max_step": 0.2, "confirmation_bars": 1},
        ),
        (
            "supertrend",
            {"window": 5, "multiplier": 2.0, "confirmation_bars": 1},
        ),
    ],
)
def test_trend_wave_2_fixture_monotonic_cross_produces_buy_without_late_sell(
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


def test_trend_wave_2_whipsaw_controls_reduce_or_limit_events(tmp_path) -> None:
    rows = _load_fixture_rows("whipsaw_guard.csv")
    loose_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "channel_breakout_with_confirmation",
            "alg_param": {
                "window": 3,
                "breakout_threshold": 0.0,
                "confirmation_bars": 1,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path / "loose"),
    )
    guarded_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "channel_breakout_with_confirmation",
            "alg_param": {
                "window": 3,
                "breakout_threshold": 0.2,
                "confirmation_bars": 2,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path / "guarded"),
    )

    loose_algorithm.process_list(rows)
    guarded_algorithm.process_list(rows)

    loose_events = len(loose_algorithm.buy_signals) + len(loose_algorithm.sell_signals)
    guarded_events = len(guarded_algorithm.buy_signals) + len(
        guarded_algorithm.sell_signals
    )

    assert guarded_events <= loose_events
    guarded_output = guarded_algorithm.normalized_output()

    assert "confirmation_state_label" in guarded_output.derived_series
    assert all(
        state in {"idle", "pending", "confirmed"}
        for state in guarded_output.derived_series["confirmation_state_label"]
    )
    assert any(
        "confirmation_pending" in point.reason_codes
        or "channel_waiting_confirmation" in point.reason_codes
        for point in guarded_output.points
    )


@pytest.mark.parametrize(
    ("alg_key", "alg_param", "expected_warmup"),
    [
        (
            "breakout_donchian_channel",
            {"window": 5, "minimum_breakout": 0.0, "confirmation_bars": 1},
            5,
        ),
        (
            "channel_breakout_with_confirmation",
            {"window": 5, "breakout_threshold": 0.0, "confirmation_bars": 2},
            5,
        ),
        (
            "adx_trend_filter",
            {"window": 5, "adx_threshold": 10.0, "confirmation_bars": 1},
            9,
        ),
        (
            "parabolic_sar_trend_following",
            {"step": 0.02, "max_step": 0.2, "confirmation_bars": 1},
            2,
        ),
        (
            "supertrend",
            {"window": 5, "multiplier": 2.0, "confirmation_bars": 1},
            5,
        ),
    ],
)
def test_trend_wave_2_short_history_stays_neutral_until_warmup(
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
            "breakout_donchian_channel",
            {"window": 5, "minimum_breakout": 0.0, "confirmation_bars": 1},
            "donchian_breakout_up",
            {"window", "minimum_breakout", "channel_type"},
        ),
        (
            "channel_breakout_with_confirmation",
            {"window": 5, "breakout_threshold": 0.0, "confirmation_bars": 2},
            "confirmed_channel_breakout_up",
            {"window", "breakout_threshold", "channel_type"},
        ),
        (
            "adx_trend_filter",
            {"window": 5, "adx_threshold": 10.0, "confirmation_bars": 1},
            "adx_bullish_filter_pass",
            {"window", "adx_threshold", "indicator"},
        ),
        (
            "parabolic_sar_trend_following",
            {"step": 0.02, "max_step": 0.2, "confirmation_bars": 1},
            "parabolic_sar_bullish",
            {"step", "max_step", "indicator"},
        ),
        (
            "supertrend",
            {"window": 5, "multiplier": 2.0, "confirmation_bars": 1},
            "supertrend_bullish",
            {"window", "multiplier", "indicator"},
        ),
    ],
)
def test_trend_wave_2_normalized_output_exposes_dashboard_diagnostics(
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
    assert expected_reason_code in last_point.reason_codes
    assert {
        "trend_score",
        "regime_label",
        "reason_codes",
        "primary_value",
        "signal_value",
        "confirmation_state_label",
        "warmup_ready",
    }.issubset(output.derived_series)
    assert output.metadata["family"] == "trend"
    assert output.metadata["reporting_mode"] == "bar_series"
    assert output.metadata["catalog_ref"] == child_output.diagnostics["catalog_ref"]
    assert child_output.signal_label == "buy"
    assert expected_reason_code in child_output.diagnostics["reason_codes"]
    assert expected_annotation_keys.issubset(child_output.diagnostics.keys())
    assert child_output.diagnostics["warmup_ready"] is True
    assert child_output.diagnostics["confirmation_state_label"] == "confirmed"


@pytest.mark.parametrize(
    ("alg_key", "expected_catalog_ref", "expected_warmup"),
    [
        ("breakout_donchian_channel", "algorithm:6", 20),
        ("channel_breakout_with_confirmation", "algorithm:7", 20),
        ("adx_trend_filter", "algorithm:8", 27),
        ("parabolic_sar_trend_following", "algorithm:9", 2),
        ("supertrend", "algorithm:10", 10),
    ],
)
def test_trend_wave_2_registration_metadata_matches_catalog(
    alg_key, expected_catalog_ref, expected_warmup
) -> None:
    spec = get_alert_algorithm_spec_by_key(alg_key)

    assert spec.catalog_ref == expected_catalog_ref
    assert spec.family == "trend"
    assert spec.category == "trend"
    assert spec.warmup_period == expected_warmup


def test_validation_rejects_invalid_trend_wave_2_parameter_shapes() -> None:
    with pytest.raises(ValueError, match="max_step >= step"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "parabolic_sar_trend_following",
                "alg_param": {
                    "step": 0.2,
                    "max_step": 0.1,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="multiplier must be > 0"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "supertrend",
                "alg_param": {
                    "window": 5,
                    "multiplier": 0.0,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )


def test_trend_wave_2_performance_smoke_on_representative_series(tmp_path) -> None:
    rows = _load_fixture_rows("monotonic_cross.csv") * 400
    algorithms = [
        (
            "breakout_donchian_channel",
            {"window": 5, "minimum_breakout": 0.0, "confirmation_bars": 1},
        ),
        (
            "channel_breakout_with_confirmation",
            {"window": 5, "breakout_threshold": 0.0, "confirmation_bars": 2},
        ),
        (
            "adx_trend_filter",
            {"window": 5, "adx_threshold": 10.0, "confirmation_bars": 1},
        ),
        (
            "parabolic_sar_trend_following",
            {"step": 0.02, "max_step": 0.2, "confirmation_bars": 1},
        ),
        (
            "supertrend",
            {"window": 5, "multiplier": 2.0, "confirmation_bars": 1},
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
        assert output.metadata["reporting_mode"] == "bar_series"


@pytest.mark.parametrize(
    ("alg_key", "alg_param"),
    [
        (
            "ichimoku_trend_strategy",
            {
                "conversion_window": 3,
                "base_window": 5,
                "span_b_window": 7,
                "displacement": 2,
                "minimum_cloud_gap": 0.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "macd_trend_strategy",
            {
                "fast_window": 3,
                "slow_window": 5,
                "signal_window": 2,
                "histogram_threshold": 0.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "linear_regression_trend",
            {
                "window": 5,
                "slope_threshold": 0.0,
                "min_r_squared": 0.2,
                "confirmation_bars": 1,
            },
        ),
        (
            "time_series_momentum",
            {
                "window": 4,
                "return_threshold": 0.0,
                "confirmation_bars": 1,
            },
        ),
    ],
)
def test_trend_wave_3_fixture_monotonic_cross_produces_buy_without_late_sell(
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


def test_trend_wave_3_whipsaw_controls_reduce_or_limit_events(tmp_path) -> None:
    rows = _load_fixture_rows("whipsaw_guard.csv")
    loose_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "macd_trend_strategy",
            "alg_param": {
                "fast_window": 2,
                "slow_window": 3,
                "signal_window": 2,
                "histogram_threshold": 0.0,
                "confirmation_bars": 1,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path / "loose"),
    )
    guarded_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "macd_trend_strategy",
            "alg_param": {
                "fast_window": 2,
                "slow_window": 3,
                "signal_window": 2,
                "histogram_threshold": 0.1,
                "confirmation_bars": 2,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path / "guarded"),
    )

    loose_algorithm.process_list(rows)
    guarded_algorithm.process_list(rows)

    loose_events = len(loose_algorithm.buy_signals) + len(loose_algorithm.sell_signals)
    guarded_events = len(guarded_algorithm.buy_signals) + len(
        guarded_algorithm.sell_signals
    )

    assert guarded_events <= loose_events

    guarded_output = guarded_algorithm.normalized_output()
    assert "macd_histogram" in guarded_output.derived_series
    assert "confirmation_state_label" in guarded_output.derived_series
    assert any(
        "confirmation_pending" in point.reason_codes
        or "macd_inside_threshold" in point.reason_codes
        for point in guarded_output.points
    )


@pytest.mark.parametrize(
    ("alg_key", "alg_param", "expected_warmup"),
    [
        (
            "ichimoku_trend_strategy",
            {
                "conversion_window": 3,
                "base_window": 5,
                "span_b_window": 7,
                "displacement": 2,
                "minimum_cloud_gap": 0.0,
                "confirmation_bars": 1,
            },
            7,
        ),
        (
            "macd_trend_strategy",
            {
                "fast_window": 3,
                "slow_window": 5,
                "signal_window": 2,
                "histogram_threshold": 0.0,
                "confirmation_bars": 1,
            },
            5,
        ),
        (
            "linear_regression_trend",
            {
                "window": 5,
                "slope_threshold": 0.0,
                "min_r_squared": 0.2,
                "confirmation_bars": 1,
            },
            5,
        ),
        (
            "time_series_momentum",
            {
                "window": 4,
                "return_threshold": 0.0,
                "confirmation_bars": 1,
            },
            5,
        ),
    ],
)
def test_trend_wave_3_short_history_stays_neutral_until_warmup(
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
            "ichimoku_trend_strategy",
            {
                "conversion_window": 3,
                "base_window": 5,
                "span_b_window": 7,
                "displacement": 2,
                "minimum_cloud_gap": 0.0,
                "confirmation_bars": 1,
            },
            "ichimoku_bullish_cloud_breakout",
            {"conversion_window", "base_window", "span_b_window", "indicator"},
        ),
        (
            "macd_trend_strategy",
            {
                "fast_window": 3,
                "slow_window": 5,
                "signal_window": 2,
                "histogram_threshold": 0.0,
                "confirmation_bars": 1,
            },
            "macd_bullish_crossover",
            {"fast_window", "slow_window", "signal_window", "indicator"},
        ),
        (
            "linear_regression_trend",
            {
                "window": 5,
                "slope_threshold": 0.0,
                "min_r_squared": 0.2,
                "confirmation_bars": 1,
            },
            "linear_regression_bullish",
            {"window", "slope_threshold", "min_r_squared", "indicator"},
        ),
        (
            "time_series_momentum",
            {
                "window": 4,
                "return_threshold": 0.0,
                "confirmation_bars": 1,
            },
            "time_series_momentum_bullish",
            {"window", "return_threshold", "indicator"},
        ),
    ],
)
def test_trend_wave_3_normalized_output_exposes_dashboard_diagnostics(
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
    assert expected_reason_code in last_point.reason_codes
    assert {
        "trend_score",
        "regime_label",
        "reason_codes",
        "primary_value",
        "signal_value",
        "confirmation_state_label",
        "warmup_ready",
    }.issubset(output.derived_series)
    assert output.metadata["family"] == "trend"
    assert output.metadata["reporting_mode"] == "bar_series"
    assert output.metadata["catalog_ref"] == child_output.diagnostics["catalog_ref"]
    assert child_output.signal_label == "buy"
    assert expected_reason_code in child_output.diagnostics["reason_codes"]
    assert expected_annotation_keys.issubset(child_output.diagnostics.keys())
    if alg_key == "ichimoku_trend_strategy":
        assert {
            "ichimoku_conversion",
            "ichimoku_base",
            "ichimoku_span_a",
            "ichimoku_span_b",
            "ichimoku_lagging",
            "cloud_top",
            "cloud_bottom",
            "cloud_gap",
            "price_cloud_gap",
            "conversion_spread",
            "lagging_confirmation",
        }.issubset(child_output.diagnostics.keys())
    elif alg_key == "macd_trend_strategy":
        assert {"macd_line", "macd_signal", "macd_histogram"}.issubset(
            child_output.diagnostics.keys()
        )
    elif alg_key == "linear_regression_trend":
        assert {
            "regression_slope",
            "regression_intercept",
            "regression_r_squared",
        }.issubset(child_output.diagnostics.keys())
    elif alg_key == "time_series_momentum":
        assert {"tsmom_return"}.issubset(child_output.diagnostics.keys())


def test_trend_wave_3_validation_rejects_invalid_parameter_shapes() -> None:
    with pytest.raises(
        ValueError, match="conversion_window < base_window < span_b_window"
    ):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "ichimoku_trend_strategy",
                "alg_param": {
                    "conversion_window": 5,
                    "base_window": 5,
                    "span_b_window": 7,
                    "displacement": 2,
                    "minimum_cloud_gap": 0.0,
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
                "alg_key": "macd_trend_strategy",
                "alg_param": {
                    "fast_window": 5,
                    "slow_window": 4,
                    "signal_window": 2,
                    "histogram_threshold": 0.0,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="min_r_squared must be <= 1"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "linear_regression_trend",
                "alg_param": {
                    "window": 5,
                    "slope_threshold": 0.0,
                    "min_r_squared": 1.1,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="return_threshold must be >= 0"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "time_series_momentum",
                "alg_param": {
                    "window": 5,
                    "return_threshold": -0.1,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )


@pytest.mark.parametrize(
    ("alg_key", "expected_catalog_ref", "expected_warmup"),
    [
        ("ichimoku_trend_strategy", "algorithm:11", 52),
        ("macd_trend_strategy", "algorithm:12", 26),
        ("linear_regression_trend", "algorithm:13", 20),
        ("time_series_momentum", "algorithm:14", 21),
    ],
)
def test_trend_wave_3_registration_metadata_matches_catalog(
    alg_key, expected_catalog_ref, expected_warmup
) -> None:
    spec = get_alert_algorithm_spec_by_key(alg_key)

    assert spec.catalog_ref == expected_catalog_ref
    assert spec.family == "trend"
    assert spec.category == "trend"
    assert spec.warmup_period == expected_warmup


def test_trend_wave_3_performance_smoke_on_representative_series(tmp_path) -> None:
    rows = _load_fixture_rows("monotonic_cross.csv") * 400
    algorithms = [
        (
            "ichimoku_trend_strategy",
            {
                "conversion_window": 3,
                "base_window": 5,
                "span_b_window": 7,
                "displacement": 2,
                "minimum_cloud_gap": 0.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "macd_trend_strategy",
            {
                "fast_window": 3,
                "slow_window": 5,
                "signal_window": 2,
                "histogram_threshold": 0.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "linear_regression_trend",
            {
                "window": 5,
                "slope_threshold": 0.0,
                "min_r_squared": 0.2,
                "confirmation_bars": 1,
            },
        ),
        (
            "time_series_momentum",
            {
                "window": 4,
                "return_threshold": 0.0,
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
        assert output.metadata["reporting_mode"] == "bar_series"


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

    with pytest.raises(ValueError, match=r"within \[0, 100\]"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "stochastic_momentum",
                "alg_param": {
                    "k_window": 3,
                    "d_window": 2,
                    "bullish_threshold": 55.0,
                    "bearish_threshold": 101.0,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="bearish_threshold <= acceleration_threshold"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "accelerating_momentum",
                "alg_param": {
                    "fast_window": 2,
                    "slow_window": 4,
                    "acceleration_threshold": -0.5,
                    "bearish_threshold": 0.5,
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


def test_momentum_wave_1_registration_metadata_matches_manifest_contract() -> None:
    expected = {
        "rate_of_change_momentum": ("algorithm:15", "momentum", "rate", 6),
        "accelerating_momentum": ("algorithm:20", "momentum", "accelerating", 8),
        "rsi_momentum_continuation": ("algorithm:21", "momentum", "rsi", 7),
        "stochastic_momentum": ("algorithm:22", "momentum", "stochastic", 7),
        "cci_momentum": ("algorithm:23", "momentum", "cci", 5),
    }

    for alg_key, (catalog_ref, family, subcategory, warmup_period) in expected.items():
        spec = get_alert_algorithm_spec_by_key(alg_key)

        assert spec.catalog_ref == catalog_ref
        assert spec.family == family
        assert spec.subcategory == subcategory
        assert spec.warmup_period == warmup_period
        assert spec.output_modes == ("signal", "score", "confidence")


@pytest.mark.parametrize(
    ("alg_key", "alg_param", "expected_warmup"),
    [
        (
            "kst_know_sure_thing",
            {
                "roc_windows": [3, 4, 5, 6],
                "smoothing_windows": [3, 3, 3, 3],
                "signal_window": 4,
                "entry_mode": "signal_cross",
                "confirmation_bars": 1,
            },
            13,
        ),
        (
            "volume_confirmed_momentum",
            {
                "momentum_window": 3,
                "volume_window": 5,
                "relative_volume_threshold": 1.0,
                "signal_threshold": 1.0,
                "confirmation_bars": 1,
            },
            5,
        ),
    ],
)
def test_momentum_wave_2_short_history_stays_neutral_until_warmup(
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
            "kst_know_sure_thing",
            {
                "roc_windows": [3, 4, 5, 6],
                "smoothing_windows": [3, 3, 3, 3],
                "signal_window": 4,
                "entry_mode": "signal_cross",
                "confirmation_bars": 1,
            },
            "kst_inside_threshold",
            {
                "roc_windows",
                "smoothing_windows",
                "signal_window",
                "entry_mode",
                "indicator",
            },
        ),
        (
            "volume_confirmed_momentum",
            {
                "momentum_window": 3,
                "volume_window": 5,
                "relative_volume_threshold": 1.0,
                "signal_threshold": 1.0,
                "confirmation_bars": 1,
            },
            "volume_confirmed_bullish",
            {
                "momentum_window",
                "volume_window",
                "relative_volume_threshold",
                "signal_threshold",
                "indicator",
            },
        ),
    ],
)
def test_momentum_wave_2_normalized_output_exposes_dashboard_diagnostics(
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
    last_point = output.points[-1]
    child_output = output.child_outputs[0]

    assert expected_reason_code in last_point.reason_codes
    assert {
        "trend_score",
        "regime_label",
        "reason_codes",
        "primary_value",
        "signal_value",
        "confirmation_state_label",
        "warmup_ready",
    }.issubset(output.derived_series)
    if alg_key == "kst_know_sure_thing":
        assert child_output.signal_label == "neutral"
        assert child_output.diagnostics["primary_value"] > 0.0
        assert child_output.diagnostics["signal_value"] > 0.0
    else:
        assert child_output.signal_label == "buy"
    assert expected_reason_code in child_output.diagnostics["reason_codes"]
    assert expected_annotation_keys.issubset(child_output.diagnostics.keys())
    assert child_output.diagnostics["family"] == "momentum"
    assert child_output.diagnostics["reporting_mode"] == "bar_series"
    assert child_output.diagnostics["warmup_ready"] is True


def test_momentum_wave_2_kst_signal_cross_fixture_exposes_component_diagnostics(
    tmp_path,
) -> None:
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "kst_know_sure_thing",
            "alg_param": {
                "roc_windows": [3, 4, 5, 6],
                "smoothing_windows": [3, 3, 3, 3],
                "signal_window": 4,
                "entry_mode": "signal_cross",
                "confirmation_bars": 1,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path),
    )

    algorithm.process_list(_load_momentum_fixture_rows("sustained_up.csv"))
    output = algorithm.normalized_output()
    payloads = algorithm.interactive_report_payloads()
    child_output = output.child_outputs[0]

    assert output.metadata["catalog_ref"] == "algorithm:24"
    assert output.metadata["family"] == "momentum"
    assert output.metadata["reporting_mode"] == "bar_series"
    assert payloads
    assert payloads[0][0]["data"]
    assert payloads[0][0]["layout"]["title"]["text"].startswith("specific_")
    assert {"kst_value", "kst_signal", "kst_spread"}.issubset(output.derived_series)
    assert child_output.signal_label == "neutral"
    assert child_output.diagnostics["primary_value"] == pytest.approx(
        output.derived_series["kst_value"][-1]
    )
    assert child_output.diagnostics["signal_value"] == pytest.approx(
        output.derived_series["kst_signal"][-1]
    )
    assert output.derived_series["kst_spread"][-1] < 0.0
    assert child_output.diagnostics["aligned_count"] == 4
    assert "kst_inside_threshold" in child_output.diagnostics["reason_codes"]


def test_momentum_wave_2_kst_zero_cross_entry_mode_promotes_bullish_regime(
    tmp_path,
) -> None:
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "kst_know_sure_thing",
            "alg_param": {
                "roc_windows": [3, 4, 5, 6],
                "smoothing_windows": [3, 3, 3, 3],
                "signal_window": 4,
                "entry_mode": "zero_cross",
                "confirmation_bars": 1,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path),
    )

    algorithm.process_list(_load_momentum_fixture_rows("sustained_up.csv"))
    output = algorithm.normalized_output()
    child_output = output.child_outputs[0]

    assert output.points[-1].signal_label == "buy"
    assert child_output.diagnostics["entry_mode"] == "zero_cross"
    assert child_output.diagnostics["primary_value"] > 0.0
    assert child_output.diagnostics["regime_label"] == algorithm.latest_predicted_trend


@pytest.mark.parametrize(
    ("alg_key", "alg_param"),
    [
        (
            "volume_confirmed_momentum",
            {
                "momentum_window": 3,
                "volume_window": 5,
                "relative_volume_threshold": 1.0,
                "signal_threshold": 1.0,
                "confirmation_bars": 1,
            },
        ),
    ],
)
def test_momentum_wave_2_fixture_sustained_up_produces_buy_without_bearish_reversal(
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


def test_momentum_wave_2_validation_rejects_invalid_parameter_shapes() -> None:
    with pytest.raises(ValueError, match="equal length"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "kst_know_sure_thing",
                "alg_param": {
                    "roc_windows": [3, 4, 5],
                    "smoothing_windows": [3, 3],
                    "signal_window": 4,
                    "entry_mode": "signal_cross",
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="entry_mode must be one of"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "kst_know_sure_thing",
                "alg_param": {
                    "roc_windows": [3, 4, 5, 6],
                    "smoothing_windows": [3, 3, 3, 3],
                    "signal_window": 4,
                    "entry_mode": "cross_and_zero",
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="relative_volume_threshold must be > 0"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "volume_confirmed_momentum",
                "alg_param": {
                    "momentum_window": 3,
                    "volume_window": 5,
                    "relative_volume_threshold": 0.0,
                    "signal_threshold": 1.0,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="signal_threshold must be >= 0"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "volume_confirmed_momentum",
                "alg_param": {
                    "momentum_window": 3,
                    "volume_window": 5,
                    "relative_volume_threshold": 1.0,
                    "signal_threshold": -0.1,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )


def test_momentum_wave_2_registration_metadata_matches_manifest_contract() -> None:
    expected = {
        "kst_know_sure_thing": ("algorithm:24", "momentum", "kst", 13),
        "volume_confirmed_momentum": ("algorithm:25", "momentum", "volume", 5),
    }

    for alg_key, (catalog_ref, family, subcategory, warmup_period) in expected.items():
        spec = get_alert_algorithm_spec_by_key(alg_key)

        assert spec.catalog_ref == catalog_ref
        assert spec.family == family
        assert spec.subcategory == subcategory
        assert spec.warmup_period == warmup_period
        assert spec.output_modes == ("signal", "score", "confidence")


def test_momentum_wave_2_performance_smoke_on_fixture_repetition(tmp_path) -> None:
    rows = _load_momentum_fixture_rows("sustained_up.csv") * 300
    algorithms = [
        (
            "kst_know_sure_thing",
            {
                "roc_windows": [3, 4, 5, 6],
                "smoothing_windows": [3, 3, 3, 3],
                "signal_window": 4,
                "entry_mode": "signal_cross",
                "confirmation_bars": 1,
            },
        ),
        (
            "volume_confirmed_momentum",
            {
                "momentum_window": 3,
                "volume_window": 5,
                "relative_volume_threshold": 1.0,
                "signal_threshold": 1.0,
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
            "support_resistance_bounce",
            {
                "level_window": 5,
                "touch_tolerance": 0.3,
                "rejection_min_close_delta": 0.2,
                "confirmation_bars": 1,
            },
            6,
        ),
        (
            "breakout_retest",
            {
                "breakout_window": 5,
                "breakout_buffer": 0.2,
                "retest_tolerance": 0.3,
                "confirmation_bars": 1,
            },
            7,
        ),
        (
            "pivot_point_strategy",
            {
                "pivot_lookback": 3,
                "level_tolerance": 0.4,
                "confirmation_bars": 1,
            },
            4,
        ),
        (
            "opening_range_breakout",
            {
                "opening_range_minutes": 15,
                "breakout_buffer": 0.2,
                "confirmation_bars": 1,
            },
            2,
        ),
        (
            "inside_bar_breakout",
            {
                "breakout_buffer": 0.1,
                "confirmation_bars": 1,
            },
            3,
        ),
    ],
)
def test_pattern_wave_1_short_history_stays_neutral_until_warmup(
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

    fixture_name = (
        "opening_range_breakout.csv"
        if alg_key == "opening_range_breakout"
        else "support_rejection.csv"
    )
    algorithm.process_list(
        _load_pattern_fixture_rows(fixture_name)[: expected_warmup - 1]
    )
    output = algorithm.normalized_output()

    assert algorithm.minimum_history() == expected_warmup
    assert output.points
    assert all(point.signal_label == "neutral" for point in output.points)
    expected_pending_code = (
        "opening_range_pending"
        if alg_key == "opening_range_breakout"
        else "warmup_pending"
    )
    assert any(expected_pending_code in point.reason_codes for point in output.points)


@pytest.mark.parametrize(
    ("alg_key", "alg_param", "fixture_name", "expected_reason_code", "expected_keys"),
    [
        (
            "support_resistance_bounce",
            {
                "level_window": 5,
                "touch_tolerance": 0.3,
                "rejection_min_close_delta": 0.2,
                "confirmation_bars": 1,
            },
            "support_rejection.csv",
            "support_rejection_bullish",
            {
                "level_window",
                "touch_tolerance",
                "rejection_min_close_delta",
                "support_level",
            },
        ),
        (
            "breakout_retest",
            {
                "breakout_window": 5,
                "breakout_buffer": 0.2,
                "retest_tolerance": 0.3,
                "confirmation_bars": 1,
            },
            "support_rejection.csv",
            "awaiting_breakout",
            {
                "breakout_window",
                "breakout_buffer",
                "retest_tolerance",
                "breakout_level",
            },
        ),
        (
            "pivot_point_strategy",
            {
                "pivot_lookback": 3,
                "level_tolerance": 0.4,
                "confirmation_bars": 1,
            },
            "support_rejection.csv",
            "pivot_not_supportive",
            {"pivot_lookback", "level_tolerance", "pivot_level", "pivot_level_name"},
        ),
        (
            "opening_range_breakout",
            {
                "opening_range_minutes": 15,
                "breakout_buffer": 0.2,
                "confirmation_bars": 1,
            },
            "opening_range_breakout.csv",
            "opening_range_breakout_bullish",
            {
                "opening_range_minutes",
                "breakout_buffer",
                "opening_range_high",
                "opening_range_complete",
            },
        ),
        (
            "inside_bar_breakout",
            {
                "breakout_buffer": 0.1,
                "confirmation_bars": 1,
            },
            "support_rejection.csv",
            "inside_bar_not_detected",
            {"breakout_buffer", "mother_high", "mother_low", "inside_bar_detected"},
        ),
    ],
)
def test_pattern_wave_1_normalized_output_exposes_dashboard_diagnostics(
    tmp_path, alg_key, alg_param, fixture_name, expected_reason_code, expected_keys
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

    algorithm.process_list(_load_pattern_fixture_rows(fixture_name))
    output = algorithm.normalized_output()
    payloads = algorithm.interactive_report_payloads()
    child_output = output.child_outputs[0]

    assert payloads
    assert any(expected_reason_code in point.reason_codes for point in output.points)
    assert {
        "trend_score",
        "regime_label",
        "reason_codes",
        "primary_value",
        "signal_value",
        "threshold_value",
        "confirmation_state_label",
        "warmup_ready",
    }.issubset(output.derived_series)
    assert child_output.diagnostics["family"] == "pattern_price_action"
    assert child_output.diagnostics["reporting_mode"] == "bar_series"
    assert expected_keys.issubset(child_output.diagnostics.keys())
    assert child_output.signal_label in {"buy", "neutral"}
    assert child_output.reason_codes == tuple(child_output.diagnostics["reason_codes"])


def test_pattern_wave_1_fixture_behavior_matches_manifest_expectations(
    tmp_path,
) -> None:
    support_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "support_resistance_bounce",
            "alg_param": {
                "level_window": 5,
                "touch_tolerance": 0.3,
                "rejection_min_close_delta": 0.2,
                "confirmation_bars": 1,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path / "support"),
    )
    support_algorithm.process_list(_load_pattern_fixture_rows("support_rejection.csv"))
    support_output = support_algorithm.normalized_output()

    touch_indices = [
        index
        for index, value in enumerate(support_output.derived_series["support_touched"])
        if value
    ]
    buy_indices = [
        index
        for index, point in enumerate(support_output.points)
        if point.signal_label == "buy"
    ]
    assert touch_indices
    assert buy_indices
    assert min(touch_indices) <= min(buy_indices)

    orb_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "opening_range_breakout",
            "alg_param": {
                "opening_range_minutes": 15,
                "breakout_buffer": 0.2,
                "confirmation_bars": 1,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path / "orb"),
    )
    orb_algorithm.process_list(_load_pattern_fixture_rows("opening_range_breakout.csv"))
    orb_output = orb_algorithm.normalized_output()
    orb_buy_indices = [
        index
        for index, point in enumerate(orb_output.points)
        if point.signal_label == "buy"
    ]
    complete_indices = [
        index
        for index, value in enumerate(
            orb_output.derived_series["opening_range_complete"]
        )
        if value
    ]
    assert complete_indices
    assert orb_buy_indices
    assert min(orb_buy_indices) >= min(complete_indices)


def test_pattern_wave_1_validation_rejects_invalid_parameter_shapes() -> None:
    with pytest.raises(ValueError, match="level_window must be > 0"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "support_resistance_bounce",
                "alg_param": {
                    "level_window": 0,
                    "touch_tolerance": 0.3,
                    "rejection_min_close_delta": 0.2,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="breakout_buffer must be >= 0"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "breakout_retest",
                "alg_param": {
                    "breakout_window": 5,
                    "breakout_buffer": -0.1,
                    "retest_tolerance": 0.3,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="opening_range_minutes must be > 0"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "opening_range_breakout",
                "alg_param": {
                    "opening_range_minutes": 0,
                    "breakout_buffer": 0.2,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )


def test_pattern_wave_1_registration_metadata_matches_manifest_contract() -> None:
    expected = {
        "support_resistance_bounce": (
            "algorithm:70",
            "pattern_price_action",
            "support_resistance",
            6,
        ),
        "breakout_retest": ("algorithm:71", "pattern_price_action", "breakout", 7),
        "pivot_point_strategy": ("algorithm:72", "pattern_price_action", "pivot", 4),
        "opening_range_breakout": (
            "algorithm:73",
            "pattern_price_action",
            "opening",
            2,
        ),
        "inside_bar_breakout": ("algorithm:74", "pattern_price_action", "inside", 3),
    }

    for alg_key, (catalog_ref, family, subcategory, warmup_period) in expected.items():
        spec = get_alert_algorithm_spec_by_key(alg_key)

        assert spec.catalog_ref == catalog_ref
        assert spec.family == family
        assert spec.subcategory == subcategory
        assert spec.warmup_period == warmup_period
        assert spec.output_modes == ("signal", "score", "confidence")


def test_pattern_wave_1_performance_smoke_on_fixture_repetition(tmp_path) -> None:
    support_rows = _load_pattern_fixture_rows("support_rejection.csv") * 300
    opening_rows = _load_pattern_fixture_rows("opening_range_breakout.csv") * 300
    algorithms = [
        (
            "support_resistance_bounce",
            {
                "level_window": 5,
                "touch_tolerance": 0.3,
                "rejection_min_close_delta": 0.2,
                "confirmation_bars": 1,
            },
            support_rows,
        ),
        (
            "breakout_retest",
            {
                "breakout_window": 5,
                "breakout_buffer": 0.2,
                "retest_tolerance": 0.3,
                "confirmation_bars": 1,
            },
            support_rows,
        ),
        (
            "pivot_point_strategy",
            {
                "pivot_lookback": 3,
                "level_tolerance": 0.4,
                "confirmation_bars": 1,
            },
            support_rows,
        ),
        (
            "opening_range_breakout",
            {
                "opening_range_minutes": 15,
                "breakout_buffer": 0.2,
                "confirmation_bars": 1,
            },
            opening_rows,
        ),
        (
            "inside_bar_breakout",
            {
                "breakout_buffer": 0.1,
                "confirmation_bars": 1,
            },
            support_rows,
        ),
    ]

    for index, (alg_key, alg_param, rows) in enumerate(algorithms):
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
        assert output.metadata["reporting_mode"] == "bar_series"


def test_momentum_wave_2_volume_confirmation_missing_stays_neutral_with_explanatory_reason(
    tmp_path,
) -> None:
    rows = _load_momentum_fixture_rows("sustained_up.csv")
    low_volume_rows = [
        {**row, "Volume": 100.0 if index >= 5 else row["Volume"]}
        for index, row in enumerate(rows)
    ]
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "volume_confirmed_momentum",
            "alg_param": {
                "momentum_window": 3,
                "volume_window": 5,
                "relative_volume_threshold": 1.5,
                "signal_threshold": 1.0,
                "confirmation_bars": 1,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path),
    )

    algorithm.process_list(low_volume_rows)
    output = algorithm.normalized_output()
    child_output = output.child_outputs[0]

    assert output.points[-1].signal_label == "neutral"
    assert "volume_confirmation_missing" in output.points[-1].reason_codes
    assert child_output.diagnostics["primary_value"] > 1.0
    assert child_output.diagnostics["signal_value"] < 1.5
    assert child_output.diagnostics["threshold_value"] == pytest.approx(1.5)
    assert child_output.diagnostics["aligned_count"] == 1


def test_momentum_wave_1_acceleration_exposes_fast_and_acceleration_diagnostics(
    tmp_path,
) -> None:
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "accelerating_momentum",
            "alg_param": {
                "fast_window": 2,
                "slow_window": 4,
                "acceleration_threshold": 0.5,
                "bearish_threshold": -0.5,
                "confirmation_bars": 1,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path),
    )

    algorithm.process_list(_load_momentum_fixture_rows("sustained_up.csv"))
    output = algorithm.normalized_output()
    child_output = output.child_outputs[0]

    assert output.points[-1].signal_label == "buy"
    assert output.derived_series["primary_value"][-1] == pytest.approx(
        output.derived_series["fast_roc"][-1]
    )
    assert output.derived_series["signal_value"][-1] == pytest.approx(
        output.derived_series["acceleration_value"][-1]
    )
    assert output.derived_series["primary_value"][-1] > 0.5
    assert output.derived_series["slow_roc"][-1] > 0.0
    assert child_output.diagnostics["primary_value"] == pytest.approx(
        output.derived_series["fast_roc"][-1]
    )
    assert child_output.diagnostics["signal_value"] == pytest.approx(
        output.derived_series["acceleration_value"][-1]
    )


@pytest.mark.parametrize(
    ("alg_key", "catalog_ref"),
    [
        ("rate_of_change_momentum", "algorithm:15"),
        ("accelerating_momentum", "algorithm:20"),
        ("rsi_momentum_continuation", "algorithm:21"),
        ("stochastic_momentum", "algorithm:22"),
        ("cci_momentum", "algorithm:23"),
    ],
)
def test_momentum_wave_1_normalized_output_metadata_exposes_dashboard_contract_fields(
    tmp_path, alg_key, catalog_ref
) -> None:
    default_params = {
        "rate_of_change_momentum": {
            "window": 3,
            "bullish_threshold": 1.0,
            "bearish_threshold": -1.0,
            "confirmation_bars": 1,
        },
        "accelerating_momentum": {
            "fast_window": 2,
            "slow_window": 4,
            "acceleration_threshold": 0.5,
            "bearish_threshold": -0.5,
            "confirmation_bars": 1,
        },
        "rsi_momentum_continuation": {
            "window": 3,
            "bullish_threshold": 55.0,
            "bearish_threshold": 45.0,
            "confirmation_bars": 1,
        },
        "stochastic_momentum": {
            "k_window": 3,
            "d_window": 2,
            "bullish_threshold": 55.0,
            "bearish_threshold": 45.0,
            "confirmation_bars": 1,
        },
        "cci_momentum": {
            "window": 5,
            "bullish_threshold": 50.0,
            "bearish_threshold": -50.0,
            "confirmation_bars": 1,
        },
    }
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": alg_key,
            "alg_param": default_params[alg_key],
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path),
    )

    algorithm.process_list(_load_momentum_fixture_rows("sustained_up.csv"))
    output = algorithm.normalized_output()
    child_output = output.child_outputs[0]

    assert output.metadata["family"] == "momentum"
    assert output.metadata["reporting_mode"] == "bar_series"
    assert output.metadata["catalog_ref"] == catalog_ref
    assert child_output.diagnostics["family"] == "momentum"
    assert child_output.diagnostics["reporting_mode"] == "bar_series"
    assert child_output.diagnostics["catalog_ref"] == catalog_ref


@pytest.mark.parametrize(
    ("alg_key", "alg_param", "expected_warmup"),
    [
        (
            "z_score_mean_reversion",
            {
                "window": 5,
                "entry_zscore": 1.0,
                "exit_zscore": 0.5,
                "confirmation_bars": 1,
            },
            5,
        ),
        (
            "bollinger_bands_reversion",
            {
                "window": 5,
                "std_multiplier": 1.0,
                "exit_band_fraction": 0.25,
                "confirmation_bars": 1,
            },
            5,
        ),
        (
            "rsi_reversion",
            {
                "window": 3,
                "oversold_threshold": 35.0,
                "overbought_threshold": 65.0,
                "exit_threshold": 50.0,
                "confirmation_bars": 1,
            },
            4,
        ),
        (
            "stochastic_reversion",
            {
                "k_window": 3,
                "d_window": 2,
                "oversold_threshold": 25.0,
                "overbought_threshold": 75.0,
                "exit_threshold": 50.0,
                "confirmation_bars": 1,
            },
            4,
        ),
        (
            "cci_reversion",
            {
                "window": 5,
                "oversold_threshold": -50.0,
                "overbought_threshold": 50.0,
                "exit_threshold": 0.0,
                "confirmation_bars": 1,
            },
            5,
        ),
    ],
)
def test_mean_reversion_wave_1_short_history_stays_neutral_until_warmup(
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
        _load_mean_reversion_fixture_rows("one_overshoot.csv")[: expected_warmup - 1]
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
            "z_score_mean_reversion",
            {
                "window": 5,
                "entry_zscore": 1.0,
                "exit_zscore": 0.5,
                "confirmation_bars": 1,
            },
            "zscore_oversold",
            {"window", "entry_zscore", "exit_zscore"},
        ),
        (
            "bollinger_bands_reversion",
            {
                "window": 5,
                "std_multiplier": 1.0,
                "exit_band_fraction": 0.25,
                "confirmation_bars": 1,
            },
            "bollinger_below_lower_band",
            {"window", "std_multiplier", "exit_band_fraction"},
        ),
        (
            "rsi_reversion",
            {
                "window": 3,
                "oversold_threshold": 35.0,
                "overbought_threshold": 65.0,
                "exit_threshold": 50.0,
                "confirmation_bars": 1,
            },
            "rsi_oversold",
            {"window", "oversold_threshold", "overbought_threshold", "exit_threshold"},
        ),
        (
            "stochastic_reversion",
            {
                "k_window": 3,
                "d_window": 2,
                "oversold_threshold": 25.0,
                "overbought_threshold": 75.0,
                "exit_threshold": 50.0,
                "confirmation_bars": 1,
            },
            "stochastic_oversold",
            {
                "k_window",
                "d_window",
                "oversold_threshold",
                "overbought_threshold",
                "exit_threshold",
            },
        ),
        (
            "cci_reversion",
            {
                "window": 5,
                "oversold_threshold": -50.0,
                "overbought_threshold": 50.0,
                "exit_threshold": 0.0,
                "confirmation_bars": 1,
            },
            "cci_oversold",
            {"window", "oversold_threshold", "overbought_threshold", "exit_threshold"},
        ),
    ],
)
def test_mean_reversion_wave_1_normalized_output_exposes_dashboard_diagnostics(
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

    algorithm.process_list(_load_mean_reversion_fixture_rows("one_overshoot.csv"))

    output = algorithm.normalized_output()
    payloads = algorithm.interactive_report_payloads()
    last_point = output.points[-1]
    child_output = output.child_outputs[0]

    assert payloads
    assert expected_reason_code in {
        code for point in output.points for code in point.reason_codes
    }
    assert {
        "trend_score",
        "regime_label",
        "reason_codes",
        "primary_value",
        "signal_value",
        "threshold_value",
        "exit_value",
        "bullish_confirmation_count",
        "bearish_confirmation_count",
        "bullish_confirmed",
        "bearish_confirmed",
    }.issubset(output.derived_series)
    assert last_point.signal_label in {"buy", "neutral", "sell"}
    assert child_output.regime_label == algorithm.latest_predicted_trend
    assert child_output.diagnostics["reason_codes"]
    assert child_output.diagnostics["warmup_ready"] is True
    assert child_output.diagnostics["warmup_period"] == algorithm.minimum_history()
    assert expected_annotation_keys.issubset(child_output.diagnostics.keys())
    assert child_output.reason_codes == tuple(child_output.diagnostics.keys())


def test_mean_reversion_wave_1_validation_rejects_invalid_parameter_shapes() -> None:
    with pytest.raises(ValueError, match="exit_zscore <= entry_zscore"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "z_score_mean_reversion",
                "alg_param": {
                    "window": 5,
                    "entry_zscore": 1.0,
                    "exit_zscore": 1.5,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="exit_band_fraction must be <= 1"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "bollinger_bands_reversion",
                "alg_param": {
                    "window": 5,
                    "std_multiplier": 1.0,
                    "exit_band_fraction": 1.5,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="oversold_threshold < overbought_threshold"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "rsi_reversion",
                "alg_param": {
                    "window": 3,
                    "oversold_threshold": 70.0,
                    "overbought_threshold": 65.0,
                    "exit_threshold": 50.0,
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
                "alg_key": "stochastic_reversion",
                "alg_param": {
                    "k_window": 3,
                    "d_window": 2,
                    "oversold_threshold": -1.0,
                    "overbought_threshold": 75.0,
                    "exit_threshold": 50.0,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(
        ValueError, match="oversold_threshold <= exit_threshold <= overbought_threshold"
    ):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "cci_reversion",
                "alg_param": {
                    "window": 5,
                    "oversold_threshold": -50.0,
                    "overbought_threshold": 50.0,
                    "exit_threshold": 100.0,
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
            "z_score_mean_reversion",
            {
                "window": 5,
                "entry_zscore": 1.0,
                "exit_zscore": 0.5,
                "confirmation_bars": 1,
            },
        ),
        (
            "bollinger_bands_reversion",
            {
                "window": 5,
                "std_multiplier": 1.0,
                "exit_band_fraction": 0.25,
                "confirmation_bars": 1,
            },
        ),
        (
            "rsi_reversion",
            {
                "window": 3,
                "oversold_threshold": 35.0,
                "overbought_threshold": 65.0,
                "exit_threshold": 50.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "stochastic_reversion",
            {
                "k_window": 3,
                "d_window": 2,
                "oversold_threshold": 25.0,
                "overbought_threshold": 75.0,
                "exit_threshold": 50.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "cci_reversion",
            {
                "window": 5,
                "oversold_threshold": -50.0,
                "overbought_threshold": 50.0,
                "exit_threshold": 0.0,
                "confirmation_bars": 1,
            },
        ),
    ],
)
def test_mean_reversion_wave_1_fixture_one_overshoot_produces_buy_signal(
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

    algorithm.process_list(_load_mean_reversion_fixture_rows("one_overshoot.csv"))

    buy_indices = [
        index
        for index, item in enumerate(algorithm.data_list)
        if item.get("buy_SIGNAL")
    ]

    first_buy_index = buy_indices[0]
    post_entry_rows = algorithm.data_list[first_buy_index + 1 :]

    assert buy_indices
    assert any(not bool(item.get("bullish_setup")) for item in post_entry_rows)


@pytest.mark.parametrize(
    ("alg_key", "alg_param"),
    [
        (
            "z_score_mean_reversion",
            {
                "window": 5,
                "entry_zscore": 1.0,
                "exit_zscore": 0.5,
                "confirmation_bars": 1,
            },
        ),
        (
            "bollinger_bands_reversion",
            {
                "window": 5,
                "std_multiplier": 1.0,
                "exit_band_fraction": 0.25,
                "confirmation_bars": 1,
            },
        ),
        (
            "rsi_reversion",
            {
                "window": 3,
                "oversold_threshold": 35.0,
                "overbought_threshold": 65.0,
                "exit_threshold": 50.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "stochastic_reversion",
            {
                "k_window": 3,
                "d_window": 2,
                "oversold_threshold": 25.0,
                "overbought_threshold": 75.0,
                "exit_threshold": 50.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "cci_reversion",
            {
                "window": 5,
                "oversold_threshold": -50.0,
                "overbought_threshold": 50.0,
                "exit_threshold": 0.0,
                "confirmation_bars": 1,
            },
        ),
    ],
)
def test_mean_reversion_wave_1_scores_and_child_output_match_dashboard_contract(
    tmp_path, alg_key, alg_param
) -> None:
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

    algorithm.process_list(_load_mean_reversion_fixture_rows("one_overshoot.csv"))
    output = algorithm.normalized_output()
    child_output = output.child_outputs[0]

    assert output.points[-1].score == pytest.approx(
        output.derived_series["trend_score"][-1]
    )
    assert child_output.score == pytest.approx(output.derived_series["trend_score"][-1])
    assert child_output.diagnostics["trend_score"] == pytest.approx(
        output.derived_series["trend_score"][-1]
    )
    assert (
        child_output.diagnostics["primary_value"]
        == output.derived_series["primary_value"][-1]
    )
    assert (
        child_output.diagnostics["threshold_value"]
        == output.derived_series["threshold_value"][-1]
    )
    assert (
        child_output.diagnostics["exit_value"]
        == output.derived_series["exit_value"][-1]
    )


def test_mean_reversion_wave_1_performance_smoke_on_fixture_repetition(
    tmp_path,
) -> None:
    rows = _load_mean_reversion_fixture_rows("one_overshoot.csv") * 300
    algorithms = [
        (
            "z_score_mean_reversion",
            {
                "window": 5,
                "entry_zscore": 1.0,
                "exit_zscore": 0.5,
                "confirmation_bars": 1,
            },
        ),
        (
            "bollinger_bands_reversion",
            {
                "window": 5,
                "std_multiplier": 1.0,
                "exit_band_fraction": 0.25,
                "confirmation_bars": 1,
            },
        ),
        (
            "rsi_reversion",
            {
                "window": 3,
                "oversold_threshold": 35.0,
                "overbought_threshold": 65.0,
                "exit_threshold": 50.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "stochastic_reversion",
            {
                "k_window": 3,
                "d_window": 2,
                "oversold_threshold": 25.0,
                "overbought_threshold": 75.0,
                "exit_threshold": 50.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "cci_reversion",
            {
                "window": 5,
                "oversold_threshold": -50.0,
                "overbought_threshold": 50.0,
                "exit_threshold": 0.0,
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


def test_mean_reversion_wave_1_registration_metadata_matches_manifest_contract() -> (
    None
):
    expected = {
        "z_score_mean_reversion": ("algorithm:26", "mean_reversion", "z", 20),
        "bollinger_bands_reversion": (
            "algorithm:27",
            "mean_reversion",
            "bollinger",
            20,
        ),
        "rsi_reversion": ("algorithm:28", "mean_reversion", "rsi", 15),
        "stochastic_reversion": ("algorithm:29", "mean_reversion", "stochastic", 16),
        "cci_reversion": ("algorithm:30", "mean_reversion", "cci", 20),
    }

    for alg_key, (catalog_ref, family, subcategory, warmup_period) in expected.items():
        spec = get_alert_algorithm_spec_by_key(alg_key)

        assert spec.catalog_ref == catalog_ref
        assert spec.family == family
        assert spec.subcategory == subcategory
        assert spec.warmup_period == warmup_period
        assert spec.output_modes == ("signal", "score", "confidence")


@pytest.mark.parametrize(
    ("alg_key", "catalog_ref"),
    [
        ("z_score_mean_reversion", "algorithm:26"),
        ("bollinger_bands_reversion", "algorithm:27"),
        ("rsi_reversion", "algorithm:28"),
        ("stochastic_reversion", "algorithm:29"),
        ("cci_reversion", "algorithm:30"),
    ],
)
def test_mean_reversion_wave_1_normalized_output_metadata_exposes_dashboard_contract_fields(
    tmp_path, alg_key, catalog_ref
) -> None:
    default_params = {
        "z_score_mean_reversion": {
            "window": 5,
            "entry_zscore": 1.0,
            "exit_zscore": 0.5,
            "confirmation_bars": 1,
        },
        "bollinger_bands_reversion": {
            "window": 5,
            "std_multiplier": 1.0,
            "exit_band_fraction": 0.25,
            "confirmation_bars": 1,
        },
        "rsi_reversion": {
            "window": 3,
            "oversold_threshold": 35.0,
            "overbought_threshold": 65.0,
            "exit_threshold": 50.0,
            "confirmation_bars": 1,
        },
        "stochastic_reversion": {
            "k_window": 3,
            "d_window": 2,
            "oversold_threshold": 25.0,
            "overbought_threshold": 75.0,
            "exit_threshold": 50.0,
            "confirmation_bars": 1,
        },
        "cci_reversion": {
            "window": 5,
            "oversold_threshold": -50.0,
            "overbought_threshold": 50.0,
            "exit_threshold": 0.0,
            "confirmation_bars": 1,
        },
    }
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": alg_key,
            "alg_param": default_params[alg_key],
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path),
    )

    algorithm.process_list(_load_mean_reversion_fixture_rows("one_overshoot.csv"))
    output = algorithm.normalized_output()
    child_output = output.child_outputs[0]

    assert output.metadata["family"] == "mean_reversion"
    assert output.metadata["reporting_mode"] == "bar_series"
    assert output.metadata["catalog_ref"] == catalog_ref
    assert child_output.diagnostics["family"] == "mean_reversion"
    assert child_output.diagnostics["reporting_mode"] == "bar_series"


@pytest.mark.parametrize(
    ("alg_key", "alg_param", "fixture_name"),
    [
        (
            "williams_percent_r_reversion",
            {
                "window": 5,
                "oversold_threshold": -80.0,
                "overbought_threshold": -20.0,
                "exit_threshold": -50.0,
                "confirmation_bars": 1,
            },
            "one_overshoot.csv",
        ),
        (
            "range_reversion",
            {
                "window": 5,
                "entry_band_fraction": 0.2,
                "exit_band_fraction": 0.5,
                "confirmation_bars": 1,
            },
            "range_oscillation.csv",
        ),
        (
            "long_horizon_reversal",
            {
                "window": 5,
                "entry_return_threshold": 3.0,
                "exit_return_threshold": 1.0,
                "confirmation_bars": 1,
            },
            "one_overshoot.csv",
        ),
        (
            "volatility_adjusted_reversion",
            {
                "window": 5,
                "atr_window": 3,
                "entry_atr_multiple": 0.4,
                "exit_atr_multiple": 0.2,
                "confirmation_bars": 1,
            },
            "range_oscillation.csv",
        ),
    ],
)
def test_mean_reversion_wave_2_fixture_behavior_emits_reversion_signals(
    tmp_path, alg_key, alg_param, fixture_name
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

    algorithm.process_list(_load_mean_reversion_fixture_rows(fixture_name))

    event_count = len(algorithm.buy_signals) + len(algorithm.sell_signals)

    assert event_count >= 1
    assert any(
        point.signal_label in {"buy", "sell"}
        for point in algorithm.normalized_output().points
    )
    if fixture_name == "one_overshoot.csv":
        buy_indices = [
            index
            for index, item in enumerate(algorithm.data_list)
            if item.get("buy_SIGNAL")
        ]
        assert buy_indices
        assert any(
            not bool(item.get("bullish_setup"))
            for item in algorithm.data_list[buy_indices[0] + 1 :]
        )
    if alg_key == "range_reversion":
        assert event_count >= 2


@pytest.mark.parametrize(
    ("alg_key", "alg_param", "expected_warmup"),
    [
        (
            "williams_percent_r_reversion",
            {
                "window": 5,
                "oversold_threshold": -80.0,
                "overbought_threshold": -20.0,
                "exit_threshold": -50.0,
                "confirmation_bars": 1,
            },
            5,
        ),
        (
            "range_reversion",
            {
                "window": 5,
                "entry_band_fraction": 0.2,
                "exit_band_fraction": 0.5,
                "confirmation_bars": 1,
            },
            5,
        ),
        (
            "long_horizon_reversal",
            {
                "window": 5,
                "entry_return_threshold": 3.0,
                "exit_return_threshold": 1.0,
                "confirmation_bars": 1,
            },
            6,
        ),
        (
            "volatility_adjusted_reversion",
            {
                "window": 5,
                "atr_window": 3,
                "entry_atr_multiple": 0.4,
                "exit_atr_multiple": 0.2,
                "confirmation_bars": 1,
            },
            5,
        ),
    ],
)
def test_mean_reversion_wave_2_short_history_stays_neutral_until_warmup(
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
        _load_mean_reversion_fixture_rows("one_overshoot.csv")[: expected_warmup - 1]
    )
    output = algorithm.normalized_output()

    assert algorithm.minimum_history() == expected_warmup
    assert output.points
    assert all(point.signal_label == "neutral" for point in output.points)
    assert any("warmup_pending" in point.reason_codes for point in output.points)


@pytest.mark.parametrize(
    (
        "alg_key",
        "alg_param",
        "fixture_name",
        "expected_reason_code",
        "expected_annotation_keys",
    ),
    [
        (
            "williams_percent_r_reversion",
            {
                "window": 5,
                "oversold_threshold": -80.0,
                "overbought_threshold": -20.0,
                "exit_threshold": -50.0,
                "confirmation_bars": 1,
            },
            "one_overshoot.csv",
            "williams_percent_r_overbought",
            {"window", "oversold_threshold", "overbought_threshold", "indicator"},
        ),
        (
            "range_reversion",
            {
                "window": 5,
                "entry_band_fraction": 0.2,
                "exit_band_fraction": 0.5,
                "confirmation_bars": 1,
            },
            "range_oscillation.csv",
            "range_resistance_reversion",
            {"window", "entry_band_fraction", "exit_band_fraction", "indicator"},
        ),
        (
            "long_horizon_reversal",
            {
                "window": 5,
                "entry_return_threshold": 3.0,
                "exit_return_threshold": 1.0,
                "confirmation_bars": 1,
            },
            "one_overshoot.csv",
            "long_horizon_neutral",
            {"window", "entry_return_threshold", "exit_return_threshold", "indicator"},
        ),
        (
            "volatility_adjusted_reversion",
            {
                "window": 5,
                "atr_window": 3,
                "entry_atr_multiple": 0.4,
                "exit_atr_multiple": 0.2,
                "confirmation_bars": 1,
            },
            "range_oscillation.csv",
            "volatility_adjusted_neutral",
            {"window", "atr_window", "entry_atr_multiple", "indicator"},
        ),
    ],
)
def test_mean_reversion_wave_2_normalized_output_exposes_dashboard_diagnostics(
    tmp_path,
    alg_key,
    alg_param,
    fixture_name,
    expected_reason_code,
    expected_annotation_keys,
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

    algorithm.process_list(_load_mean_reversion_fixture_rows(fixture_name))

    output = algorithm.normalized_output()
    payloads = algorithm.interactive_report_payloads()
    last_point = output.points[-1]
    child_output = output.child_outputs[0]

    assert payloads
    assert any(expected_reason_code in point.reason_codes for point in output.points)
    assert {
        "trend_score",
        "regime_label",
        "reason_codes",
        "primary_value",
        "signal_value",
        "threshold_value",
        "exit_value",
        "confirmation_state_label",
        "warmup_ready",
    }.issubset(output.derived_series)
    assert output.metadata["family"] == "mean_reversion"
    assert output.metadata["reporting_mode"] == "bar_series"
    assert output.metadata["catalog_ref"] == child_output.diagnostics["catalog_ref"]
    assert expected_annotation_keys.issubset(child_output.diagnostics.keys())
    assert child_output.diagnostics["warmup_ready"] is True
    assert child_output.diagnostics["confirmation_state_label"] in {
        "idle",
        "pending",
        "confirmed",
    }
    assert last_point.signal_label in {"buy", "sell", "neutral"}
    assert child_output.reason_codes == tuple(child_output.diagnostics["reason_codes"])
    if alg_key == "williams_percent_r_reversion":
        assert "williams_percent_r" in output.derived_series
        assert child_output.diagnostics["williams_percent_r"] == pytest.approx(
            output.derived_series["williams_percent_r"][-1]
        )
    elif alg_key == "range_reversion":
        assert {
            "range_upper",
            "range_lower",
            "range_midpoint",
            "range_position",
        }.issubset(output.derived_series)
        assert child_output.diagnostics["range_position"] == pytest.approx(
            output.derived_series["range_position"][-1]
        )
    elif alg_key == "long_horizon_reversal":
        assert "long_horizon_return" in output.derived_series
        assert child_output.diagnostics["long_horizon_return"] == pytest.approx(
            output.derived_series["long_horizon_return"][-1]
        )
    elif alg_key == "volatility_adjusted_reversion":
        assert {"rolling_mean", "atr_value", "atr_distance"}.issubset(
            output.derived_series
        )
        assert child_output.diagnostics["atr_distance"] == pytest.approx(
            output.derived_series["atr_distance"][-1]
        )


def test_mean_reversion_wave_2_validation_rejects_invalid_parameter_shapes() -> None:
    with pytest.raises(
        ValueError, match=r"oversold_threshold must be within \[-100, 0\]"
    ):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "williams_percent_r_reversion",
                "alg_param": {
                    "window": 5,
                    "oversold_threshold": 10.0,
                    "overbought_threshold": -20.0,
                    "exit_threshold": -50.0,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="entry_band_fraction <= exit_band_fraction"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "range_reversion",
                "alg_param": {
                    "window": 5,
                    "entry_band_fraction": 0.3,
                    "exit_band_fraction": 0.2,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="entry_band_fraction must be < 0.5"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "range_reversion",
                "alg_param": {
                    "window": 5,
                    "entry_band_fraction": 0.5,
                    "exit_band_fraction": 0.5,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(
        ValueError, match="exit_return_threshold <= entry_return_threshold"
    ):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "long_horizon_reversal",
                "alg_param": {
                    "window": 10,
                    "entry_return_threshold": 5.0,
                    "exit_return_threshold": 6.0,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="entry_return_threshold must be > 0"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "long_horizon_reversal",
                "alg_param": {
                    "window": 10,
                    "entry_return_threshold": 0.0,
                    "exit_return_threshold": 0.0,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="exit_atr_multiple <= entry_atr_multiple"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "volatility_adjusted_reversion",
                "alg_param": {
                    "window": 5,
                    "atr_window": 3,
                    "entry_atr_multiple": 1.0,
                    "exit_atr_multiple": 1.5,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="entry_atr_multiple must be > 0"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "volatility_adjusted_reversion",
                "alg_param": {
                    "window": 5,
                    "atr_window": 3,
                    "entry_atr_multiple": 0.0,
                    "exit_atr_multiple": 0.0,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )


def test_mean_reversion_wave_2_performance_smoke_on_fixture_repetition(
    tmp_path,
) -> None:
    repeated_rows = _load_mean_reversion_fixture_rows("range_oscillation.csv") * 300
    algorithms = [
        (
            "williams_percent_r_reversion",
            {
                "window": 5,
                "oversold_threshold": -80.0,
                "overbought_threshold": -20.0,
                "exit_threshold": -50.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "range_reversion",
            {
                "window": 5,
                "entry_band_fraction": 0.2,
                "exit_band_fraction": 0.5,
                "confirmation_bars": 1,
            },
        ),
        (
            "long_horizon_reversal",
            {
                "window": 5,
                "entry_return_threshold": 3.0,
                "exit_return_threshold": 1.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "volatility_adjusted_reversion",
            {
                "window": 5,
                "atr_window": 3,
                "entry_atr_multiple": 0.4,
                "exit_atr_multiple": 0.2,
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
        algorithm.process_list(repeated_rows)
        output = algorithm.normalized_output()

        assert len(output.points) == len(repeated_rows)
        assert output.metadata["warmup_period"] == algorithm.minimum_history()
        assert output.metadata["reporting_mode"] == "bar_series"


def test_mean_reversion_wave_2_registration_metadata_matches_manifest_contract() -> (
    None
):
    expected = {
        "williams_percent_r_reversion": (
            "algorithm:31",
            "mean_reversion",
            "williams",
            14,
        ),
        "range_reversion": ("algorithm:34", "mean_reversion", "range", 20),
        "long_horizon_reversal": ("algorithm:36", "mean_reversion", "long", 64),
        "volatility_adjusted_reversion": (
            "algorithm:37",
            "mean_reversion",
            "volatility",
            20,
        ),
    }

    for alg_key, (catalog_ref, family, subcategory, warmup) in expected.items():
        spec = get_alert_algorithm_spec_by_key(alg_key)
        assert spec.catalog_ref == catalog_ref
        assert spec.family == family
        assert spec.subcategory == subcategory
        assert spec.warmup_period == warmup
        assert spec.output_modes == ("signal", "score", "confidence")


@pytest.mark.parametrize(
    ("alg_key", "catalog_ref", "alg_param", "fixture_name"),
    [
        (
            "williams_percent_r_reversion",
            "algorithm:31",
            {
                "window": 5,
                "oversold_threshold": -80.0,
                "overbought_threshold": -20.0,
                "exit_threshold": -50.0,
                "confirmation_bars": 1,
            },
            "one_overshoot.csv",
        ),
        (
            "range_reversion",
            "algorithm:34",
            {
                "window": 5,
                "entry_band_fraction": 0.2,
                "exit_band_fraction": 0.5,
                "confirmation_bars": 1,
            },
            "range_oscillation.csv",
        ),
        (
            "long_horizon_reversal",
            "algorithm:36",
            {
                "window": 5,
                "entry_return_threshold": 3.0,
                "exit_return_threshold": 1.0,
                "confirmation_bars": 1,
            },
            "one_overshoot.csv",
        ),
        (
            "volatility_adjusted_reversion",
            "algorithm:37",
            {
                "window": 5,
                "atr_window": 3,
                "entry_atr_multiple": 0.4,
                "exit_atr_multiple": 0.2,
                "confirmation_bars": 1,
            },
            "range_oscillation.csv",
        ),
    ],
)
def test_mean_reversion_wave_2_normalized_output_metadata_exposes_dashboard_contract_fields(
    tmp_path, alg_key, catalog_ref, alg_param, fixture_name
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

    algorithm.process_list(_load_mean_reversion_fixture_rows(fixture_name))
    output = algorithm.normalized_output()
    child_output = output.child_outputs[0]

    assert output.metadata["family"] == "mean_reversion"
    assert output.metadata["reporting_mode"] == "bar_series"
    assert output.metadata["catalog_ref"] == catalog_ref
    assert child_output.diagnostics["family"] == "mean_reversion"
    assert child_output.diagnostics["reporting_mode"] == "bar_series"
    assert child_output.diagnostics["catalog_ref"] == catalog_ref
    assert child_output.diagnostics["catalog_ref"] == catalog_ref
    assert child_output.reason_codes == tuple(child_output.diagnostics["reason_codes"])


@pytest.mark.parametrize(
    ("alg_key", "alg_param", "expected_warmup"),
    [
        (
            "volatility_breakout",
            {
                "atr_window": 5,
                "compression_window": 5,
                "compression_threshold": 2.0,
                "breakout_lookback": 5,
                "breakout_buffer": 0.1,
                "confirmation_bars": 1,
            },
            6,
        ),
        (
            "atr_channel_breakout",
            {
                "channel_window": 5,
                "atr_window": 5,
                "atr_multiplier": 1.0,
                "confirmation_bars": 1,
            },
            5,
        ),
        (
            "volatility_mean_reversion",
            {
                "volatility_window": 5,
                "baseline_window": 8,
                "high_threshold": 1.2,
                "low_threshold": 0.8,
                "confirmation_bars": 1,
            },
            13,
        ),
    ],
)
def test_volatility_wave_1_short_history_stays_neutral_until_warmup(
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
        _load_volatility_fixture_rows("compression_release.csv")[: expected_warmup - 1]
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
            "volatility_breakout",
            {
                "atr_window": 5,
                "compression_window": 5,
                "compression_threshold": 2.0,
                "breakout_lookback": 5,
                "breakout_buffer": 0.1,
                "confirmation_bars": 1,
            },
            "volatility_breakout_up",
            {
                "atr_window",
                "compression_window",
                "compression_threshold",
                "breakout_lookback",
                "indicator",
            },
        ),
        (
            "atr_channel_breakout",
            {
                "channel_window": 5,
                "atr_window": 5,
                "atr_multiplier": 1.0,
                "confirmation_bars": 1,
            },
            "atr_channel_breakout_up",
            {"channel_window", "atr_window", "atr_multiplier", "indicator"},
        ),
        (
            "volatility_mean_reversion",
            {
                "volatility_window": 5,
                "baseline_window": 8,
                "high_threshold": 1.2,
                "low_threshold": 0.8,
                "confirmation_bars": 1,
            },
            "volatility_ratio_high",
            {
                "volatility_window",
                "baseline_window",
                "high_threshold",
                "low_threshold",
                "indicator",
            },
        ),
    ],
)
def test_volatility_wave_1_normalized_output_exposes_dashboard_diagnostics(
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

    algorithm.process_list(_load_volatility_fixture_rows("compression_release.csv"))

    output = algorithm.normalized_output()
    payloads = algorithm.interactive_report_payloads()
    child_output = output.child_outputs[0]

    assert payloads
    assert any(expected_reason_code in point.reason_codes for point in output.points)
    assert {
        "trend_score",
        "regime_label",
        "reason_codes",
        "primary_value",
        "signal_value",
        "threshold_value",
        "confirmation_state_label",
        "warmup_ready",
    }.issubset(output.derived_series)
    assert output.metadata["family"] == "volatility_options"
    assert output.metadata["reporting_mode"] == "bar_series"
    assert expected_annotation_keys.issubset(child_output.diagnostics.keys())
    assert child_output.diagnostics["family"] == "volatility_options"
    assert child_output.diagnostics["reporting_mode"] == "bar_series"
    assert child_output.diagnostics["warmup_ready"] is True
    assert child_output.diagnostics["catalog_ref"] == output.metadata["catalog_ref"]
    assert child_output.reason_codes == tuple(child_output.diagnostics["reason_codes"])
    assert child_output.diagnostics["confirmation_state_label"] in {
        "idle",
        "pending",
        "confirmed",
    }
    assert (
        child_output.diagnostics["decision_reason"]
        in child_output.diagnostics["reason_codes"]
    )
    if alg_key == "volatility_breakout":
        assert any(output.derived_series["compression_flag"][:-1])
        assert any(point.signal_label == "buy" for point in output.points)
        assert {"compression_ratio", "compression_flag", "breakout_level"}.issubset(
            output.derived_series
        )
    elif alg_key == "atr_channel_breakout":
        assert {"channel_mid", "upper_band", "lower_band"}.issubset(
            output.derived_series
        )
        assert any(point.signal_label == "buy" for point in output.points)
    else:
        assert "volatility_ratio" in output.derived_series
        assert child_output.diagnostics["primary_value"] == pytest.approx(
            output.derived_series["volatility_ratio"][-1]
        )
        assert child_output.signal_label == "sell"


def test_volatility_wave_1_validation_rejects_invalid_parameter_shapes() -> None:
    with pytest.raises(ValueError, match="compression_threshold must be > 0"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "volatility_breakout",
                "alg_param": {
                    "atr_window": 5,
                    "compression_window": 5,
                    "compression_threshold": 0.0,
                    "breakout_lookback": 5,
                    "breakout_buffer": 0.1,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="atr_multiplier must be > 0"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "atr_channel_breakout",
                "alg_param": {
                    "channel_window": 5,
                    "atr_window": 5,
                    "atr_multiplier": 0.0,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="high_threshold must be > 1"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "volatility_mean_reversion",
                "alg_param": {
                    "volatility_window": 5,
                    "baseline_window": 8,
                    "high_threshold": 1.0,
                    "low_threshold": 0.8,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match=r"low_threshold must be within \(0, 1\)"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "volatility_mean_reversion",
                "alg_param": {
                    "volatility_window": 5,
                    "baseline_window": 8,
                    "high_threshold": 1.2,
                    "low_threshold": 1.1,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )


def test_volatility_wave_1_fixture_behavior_matches_manifest_expectations(
    tmp_path,
) -> None:
    breakout_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "volatility_breakout",
            "alg_param": {
                "atr_window": 5,
                "compression_window": 5,
                "compression_threshold": 2.0,
                "breakout_lookback": 5,
                "breakout_buffer": 0.1,
                "confirmation_bars": 1,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path / "breakout"),
    )
    breakout_algorithm.process_list(
        _load_volatility_fixture_rows("compression_release.csv")
    )
    breakout_output = breakout_algorithm.normalized_output()

    compression_indices = [
        index
        for index, flag in enumerate(breakout_output.derived_series["compression_flag"])
        if flag
    ]
    breakout_indices = [
        index
        for index, point in enumerate(breakout_output.points)
        if point.signal_label == "buy"
    ]

    assert compression_indices
    assert breakout_indices
    assert min(compression_indices) < min(breakout_indices)

    atr_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "atr_channel_breakout",
            "alg_param": {
                "channel_window": 5,
                "atr_window": 5,
                "atr_multiplier": 1.0,
                "confirmation_bars": 1,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path / "atr_channel"),
    )
    atr_algorithm.process_list(_load_volatility_fixture_rows("compression_release.csv"))
    atr_output = atr_algorithm.normalized_output()
    atr_buy_indices = [
        index
        for index, point in enumerate(atr_output.points)
        if point.signal_label == "buy"
    ]

    assert atr_buy_indices
    assert min(atr_buy_indices) >= min(breakout_indices)
    assert atr_output.derived_series["upper_band"][atr_buy_indices[0]] is not None

    mean_reversion_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "volatility_mean_reversion",
            "alg_param": {
                "volatility_window": 5,
                "baseline_window": 8,
                "high_threshold": 1.2,
                "low_threshold": 0.8,
                "confirmation_bars": 1,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path / "mean_reversion"),
    )
    mean_reversion_algorithm.process_list(
        _load_volatility_fixture_rows("compression_release.csv")
    )
    mean_reversion_output = mean_reversion_algorithm.normalized_output()
    sell_indices = [
        index
        for index, point in enumerate(mean_reversion_output.points)
        if point.signal_label == "sell"
    ]
    elevated_ratio_indices = [
        index
        for index, ratio in enumerate(
            mean_reversion_output.derived_series["volatility_ratio"]
        )
        if isinstance(ratio, (int, float)) and ratio >= 1.2
    ]

    assert sell_indices
    assert elevated_ratio_indices
    assert min(elevated_ratio_indices) <= min(sell_indices)
    assert all(index > max(compression_indices) for index in sell_indices)


def test_volatility_wave_1_performance_smoke_on_fixture_repetition(tmp_path) -> None:
    rows = _load_volatility_fixture_rows("compression_release.csv") * 300
    algorithms = [
        (
            "volatility_breakout",
            {
                "atr_window": 5,
                "compression_window": 5,
                "compression_threshold": 2.0,
                "breakout_lookback": 5,
                "breakout_buffer": 0.1,
                "confirmation_bars": 1,
            },
        ),
        (
            "atr_channel_breakout",
            {
                "channel_window": 5,
                "atr_window": 5,
                "atr_multiplier": 1.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "volatility_mean_reversion",
            {
                "volatility_window": 5,
                "baseline_window": 8,
                "high_threshold": 1.2,
                "low_threshold": 0.8,
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
        assert output.metadata["reporting_mode"] == "bar_series"


def test_volatility_wave_1_registration_metadata_matches_manifest_contract() -> None:
    expected = {
        "volatility_breakout": ("algorithm:52", "volatility_options", "volatility", 6),
        "atr_channel_breakout": ("algorithm:53", "volatility_options", "atr", 5),
        "volatility_mean_reversion": (
            "algorithm:54",
            "volatility_options",
            "volatility",
            13,
        ),
    }

    for alg_key, (catalog_ref, family, subcategory, warmup_period) in expected.items():
        spec = get_alert_algorithm_spec_by_key(alg_key)

        assert spec.catalog_ref == catalog_ref
        assert spec.family == family
        assert spec.subcategory == subcategory
        assert spec.warmup_period == warmup_period
        assert spec.output_modes == ("signal", "score", "confidence")


@pytest.mark.parametrize(
    ("alg_key", "catalog_ref", "alg_param"),
    [
        (
            "volatility_breakout",
            "algorithm:52",
            {
                "atr_window": 5,
                "compression_window": 5,
                "compression_threshold": 2.0,
                "breakout_lookback": 5,
                "breakout_buffer": 0.1,
                "confirmation_bars": 1,
            },
        ),
        (
            "atr_channel_breakout",
            "algorithm:53",
            {
                "channel_window": 5,
                "atr_window": 5,
                "atr_multiplier": 1.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "volatility_mean_reversion",
            "algorithm:54",
            {
                "volatility_window": 5,
                "baseline_window": 8,
                "high_threshold": 1.2,
                "low_threshold": 0.8,
                "confirmation_bars": 1,
            },
        ),
    ],
)
def test_volatility_wave_1_normalized_output_metadata_exposes_dashboard_contract_fields(
    tmp_path, alg_key, catalog_ref, alg_param
) -> None:
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

    algorithm.process_list(_load_volatility_fixture_rows("compression_release.csv"))
    output = algorithm.normalized_output()
    child_output = output.child_outputs[0]

    assert output.metadata["family"] == "volatility_options"
    assert output.metadata["reporting_mode"] == "bar_series"
    assert output.metadata["catalog_ref"] == catalog_ref
    assert child_output.diagnostics["family"] == "volatility_options"
    assert child_output.diagnostics["reporting_mode"] == "bar_series"
    assert child_output.diagnostics["catalog_ref"] == catalog_ref
