import json
from csv import DictReader
from pathlib import Path
from typing import Any, cast

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
FACTOR_FIXTURES_ROOT = Path(__file__).resolve().parent / "fixtures" / "factors"


def _build_cross_asset_fixture_rows() -> list[dict[str, object]]:
    return [
        {
            "ts": "2025-01-02",
            "symbol": "AAA",
            "Close": 100.0,
            "carry": 0.05,
            "yield_diff": 0.04,
            "risk_score": 0.90,
            "credit_impulse": 0.70,
            "confirmation": 0.85,
            "leader_return": 0.03,
            "yield_2y": 0.020,
            "yield_10y": 0.040,
            "front_roll": 0.030,
            "back_roll": 0.010,
            "near_contract": 101.0,
            "far_contract": 98.0,
        },
        {
            "ts": "2025-01-02",
            "symbol": "BBB",
            "Close": 100.0,
            "carry": 0.02,
            "yield_diff": 0.01,
            "risk_score": 0.20,
            "credit_impulse": 0.10,
            "confirmation": 0.30,
            "leader_return": 0.01,
            "yield_2y": 0.025,
            "yield_10y": 0.030,
            "front_roll": 0.010,
            "back_roll": 0.015,
            "near_contract": 99.0,
            "far_contract": 100.0,
        },
        {
            "ts": "2025-02-03",
            "symbol": "AAA",
            "Close": 101.0,
            "carry": 0.06,
            "yield_diff": 0.05,
            "risk_score": 0.15,
            "credit_impulse": 0.20,
            "confirmation": 0.40,
            "leader_return": 0.00,
            "yield_2y": 0.021,
            "yield_10y": 0.045,
            "front_roll": 0.028,
            "back_roll": 0.011,
            "near_contract": 102.0,
            "far_contract": 99.0,
        },
        {
            "ts": "2025-02-03",
            "symbol": "BBB",
            "Close": 99.0,
            "carry": 0.01,
            "yield_diff": 0.02,
            "risk_score": 0.95,
            "credit_impulse": 0.80,
            "confirmation": 0.88,
            "leader_return": 0.04,
            "yield_2y": 0.030,
            "yield_10y": 0.032,
            "front_roll": 0.008,
            "back_roll": 0.018,
            "near_contract": 97.0,
            "far_contract": 101.0,
        },
    ]


def _build_event_fixture_rows() -> list[dict[str, object]]:
    return [
        {
            "symbol": "AAA",
            "event_timestamp": "2025-02-03 16:05:00",
            "surprise": 0.15,
        },
        {
            "symbol": "BBB",
            "event_timestamp": "2025-02-03 16:10:00",
            "surprise": -0.05,
        },
    ]


def _build_factor_fixture_rows() -> list[dict[str, object]]:
    return [
        {
            "ts": "2025-01-02",
            "symbol": "AAA",
            "Close": 100.0,
            "volatility_20d": 0.10,
            "realized_volatility": 0.11,
            "beta_252d": 0.80,
            "market_beta": 0.82,
            "dividend_yield": 0.040,
            "forward_dividend_yield": 0.041,
            "earnings_growth": 0.18,
            "sales_growth": 0.15,
            "liquidity_score": 0.90,
            "turnover_ratio": 0.70,
            "price_to_book": 1.2,
            "price_to_earnings": 10.0,
            "return_on_equity": 0.24,
            "gross_margin": 0.48,
            "market_cap_billions": 40.0,
            "return_on_assets": 0.12,
            "gross_profitability": 0.33,
            "cash_earnings_ratio": 0.92,
            "earnings_stability": 0.88,
            "debt_to_equity": 0.30,
            "net_debt_to_ebitda": 0.90,
        },
        {
            "ts": "2025-01-02",
            "symbol": "BBB",
            "Close": 100.0,
            "volatility_20d": 0.22,
            "realized_volatility": 0.20,
            "beta_252d": 1.25,
            "market_beta": 1.20,
            "dividend_yield": 0.020,
            "forward_dividend_yield": 0.021,
            "earnings_growth": 0.08,
            "sales_growth": 0.07,
            "liquidity_score": 0.65,
            "turnover_ratio": 0.55,
            "price_to_book": 2.6,
            "price_to_earnings": 18.0,
            "return_on_equity": 0.12,
            "gross_margin": 0.32,
            "market_cap_billions": 15.0,
            "return_on_assets": 0.07,
            "gross_profitability": 0.19,
            "cash_earnings_ratio": 0.74,
            "earnings_stability": 0.71,
            "debt_to_equity": 0.75,
            "net_debt_to_ebitda": 1.80,
        },
        {
            "ts": "2025-01-02",
            "symbol": "CCC",
            "Close": 100.0,
            "volatility_20d": 0.14,
            "realized_volatility": 0.13,
            "beta_252d": 0.95,
            "market_beta": 0.97,
            "dividend_yield": 0.055,
            "forward_dividend_yield": 0.054,
            "earnings_growth": 0.14,
            "sales_growth": 0.13,
            "liquidity_score": 0.85,
            "turnover_ratio": 0.72,
            "price_to_book": 1.5,
            "price_to_earnings": 12.0,
            "return_on_equity": 0.18,
            "gross_margin": 0.44,
            "market_cap_billions": 8.0,
            "return_on_assets": 0.10,
            "gross_profitability": 0.28,
            "cash_earnings_ratio": 0.86,
            "earnings_stability": 0.82,
            "debt_to_equity": 0.45,
            "net_debt_to_ebitda": 1.20,
        },
        {
            "ts": "2025-01-02",
            "symbol": "DDD",
            "Close": 100.0,
            "volatility_20d": 0.30,
            "realized_volatility": 0.29,
            "beta_252d": 1.50,
            "market_beta": 1.45,
            "dividend_yield": 0.015,
            "forward_dividend_yield": 0.016,
            "earnings_growth": 0.04,
            "sales_growth": 0.05,
            "liquidity_score": 0.45,
            "turnover_ratio": 0.40,
            "price_to_book": 3.5,
            "price_to_earnings": 24.0,
            "return_on_equity": 0.06,
            "gross_margin": 0.21,
            "market_cap_billions": 2.0,
            "return_on_assets": 0.03,
            "gross_profitability": 0.11,
            "cash_earnings_ratio": 0.61,
            "earnings_stability": 0.58,
            "debt_to_equity": 1.10,
            "net_debt_to_ebitda": 2.60,
        },
    ]


def _build_factor_fixture_rows_with_multiple_rebalances() -> list[dict[str, object]]:
    january_rows = _build_factor_fixture_rows()
    february_rows = [
        {
            "ts": "2025-02-03",
            "symbol": "AAA",
            "Close": 102.0,
            "volatility_20d": 0.18,
            "realized_volatility": 0.17,
            "beta_252d": 1.10,
            "market_beta": 1.08,
            "dividend_yield": 0.022,
            "forward_dividend_yield": 0.023,
            "earnings_growth": 0.10,
            "sales_growth": 0.09,
            "liquidity_score": 0.68,
            "turnover_ratio": 0.60,
            "price_to_book": 2.4,
            "price_to_earnings": 19.0,
            "return_on_equity": 0.15,
            "gross_margin": 0.36,
            "market_cap_billions": 35.0,
            "return_on_assets": 0.08,
            "gross_profitability": 0.22,
            "cash_earnings_ratio": 0.76,
            "earnings_stability": 0.74,
            "debt_to_equity": 0.60,
            "net_debt_to_ebitda": 1.50,
        },
        {
            "ts": "2025-02-03",
            "symbol": "BBB",
            "Close": 101.0,
            "volatility_20d": 0.12,
            "realized_volatility": 0.11,
            "beta_252d": 0.86,
            "market_beta": 0.88,
            "dividend_yield": 0.035,
            "forward_dividend_yield": 0.036,
            "earnings_growth": 0.20,
            "sales_growth": 0.18,
            "liquidity_score": 0.88,
            "turnover_ratio": 0.79,
            "price_to_book": 1.1,
            "price_to_earnings": 9.0,
            "return_on_equity": 0.26,
            "gross_margin": 0.50,
            "market_cap_billions": 12.0,
            "return_on_assets": 0.13,
            "gross_profitability": 0.35,
            "cash_earnings_ratio": 0.94,
            "earnings_stability": 0.90,
            "debt_to_equity": 0.28,
            "net_debt_to_ebitda": 0.85,
        },
        {
            "ts": "2025-02-03",
            "symbol": "CCC",
            "Close": 103.0,
            "volatility_20d": 0.15,
            "realized_volatility": 0.16,
            "beta_252d": 0.98,
            "market_beta": 1.00,
            "dividend_yield": 0.060,
            "forward_dividend_yield": 0.059,
            "earnings_growth": 0.16,
            "sales_growth": 0.15,
            "liquidity_score": 0.82,
            "turnover_ratio": 0.74,
            "price_to_book": 1.6,
            "price_to_earnings": 13.0,
            "return_on_equity": 0.19,
            "gross_margin": 0.46,
            "market_cap_billions": 9.0,
            "return_on_assets": 0.11,
            "gross_profitability": 0.30,
            "cash_earnings_ratio": 0.88,
            "earnings_stability": 0.84,
            "debt_to_equity": 0.40,
            "net_debt_to_ebitda": 1.10,
        },
        {
            "ts": "2025-02-03",
            "symbol": "DDD",
            "Close": 98.0,
            "volatility_20d": 0.26,
            "realized_volatility": 0.25,
            "beta_252d": 1.42,
            "market_beta": 1.40,
            "dividend_yield": 0.018,
            "forward_dividend_yield": 0.019,
            "earnings_growth": 0.06,
            "sales_growth": 0.06,
            "liquidity_score": 0.50,
            "turnover_ratio": 0.43,
            "price_to_book": 3.2,
            "price_to_earnings": 22.0,
            "return_on_equity": 0.08,
            "gross_margin": 0.24,
            "market_cap_billions": 3.0,
            "return_on_assets": 0.04,
            "gross_profitability": 0.14,
            "cash_earnings_ratio": 0.65,
            "earnings_stability": 0.62,
            "debt_to_equity": 0.95,
            "net_debt_to_ebitda": 2.20,
        },
    ]
    return [*january_rows, *february_rows]


def _load_factor_fixture_rows(name: str) -> list[dict[str, object]]:
    with (FACTOR_FIXTURES_ROOT / name).open(newline="", encoding="utf-8") as handle:
        rows = list(DictReader(handle))
    parsed_rows: list[dict[str, object]] = []
    for row in rows:
        parsed_rows.append(
            {
                "ts": row["ts"],
                "symbol": row["symbol"],
                "Close": float(row["Close"]),
                "volatility_20d": float(row["volatility_20d"]),
                "realized_volatility": float(row["realized_volatility"]),
                "beta_252d": float(row["beta_252d"]),
                "market_beta": float(row["market_beta"]),
                "dividend_yield": float(row["dividend_yield"]),
                "forward_dividend_yield": float(row["forward_dividend_yield"]),
                "earnings_growth": float(row["earnings_growth"]),
                "sales_growth": float(row["sales_growth"]),
                "liquidity_score": float(row["liquidity_score"]),
                "turnover_ratio": float(row["turnover_ratio"]),
                "price_to_book": float(row["price_to_book"]),
                "price_to_earnings": float(row["price_to_earnings"]),
                "return_on_equity": float(row["return_on_equity"]),
                "gross_margin": float(row["gross_margin"]),
                "market_cap_billions": float(row["market_cap_billions"]),
                "return_on_assets": float(row["return_on_assets"]),
                "gross_profitability": float(row["gross_profitability"]),
                "cash_earnings_ratio": float(row["cash_earnings_ratio"]),
                "earnings_stability": float(row["earnings_stability"]),
                "debt_to_equity": float(row["debt_to_equity"]),
                "net_debt_to_ebitda": float(row["net_debt_to_ebitda"]),
            }
        )
    return parsed_rows


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


def _load_cross_sectional_momentum_fixture_rows(name: str) -> list[dict[str, object]]:
    with (MOMENTUM_FIXTURES_ROOT / name).open(newline="", encoding="utf-8") as handle:
        rows = list(DictReader(handle))
    parsed_rows: list[dict[str, object]] = []
    for row in rows:
        parsed_rows.append(
            {
                "ts": row["ts"],
                "symbol": row["symbol"],
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


def _build_intraday_mean_reversion_rows() -> list[dict[str, object]]:
    return [
        {
            "ts": "2025-01-01 09:30:00",
            "Open": 100.0,
            "High": 101.0,
            "Low": 99.5,
            "Close": 100.5,
            "Volume": 1200.0,
        },
        {
            "ts": "2025-01-01 09:35:00",
            "Open": 100.5,
            "High": 101.0,
            "Low": 99.8,
            "Close": 100.2,
            "Volume": 1100.0,
        },
        {
            "ts": "2025-01-02 09:30:00",
            "Open": 96.0,
            "High": 96.5,
            "Low": 95.0,
            "Close": 95.5,
            "Volume": 1500.0,
        },
        {
            "ts": "2025-01-02 09:35:00",
            "Open": 95.4,
            "High": 95.8,
            "Low": 94.0,
            "Close": 94.4,
            "Volume": 1800.0,
        },
        {
            "ts": "2025-01-02 09:40:00",
            "Open": 94.5,
            "High": 94.8,
            "Low": 92.8,
            "Close": 93.2,
            "Volume": 1700.0,
        },
    ]


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
                "Volume": 1000,
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
            "Volume": 1000 + (i * 100),
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
        "cross_sectional_momentum",
        "accelerating_momentum",
        "rsi_momentum_continuation",
        "stochastic_momentum",
        "cci_momentum",
        "kst_know_sure_thing",
        "relative_strength_momentum",
        "dual_momentum",
        "volume_confirmed_momentum",
        "residual_momentum",
        "low_volatility_strategy",
        "residual_volatility_strategy",
        "low_beta_betting_against_beta",
        "defensive_equity_strategy",
        "dividend_yield_strategy",
        "growth_factor_strategy",
        "liquidity_factor_strategy",
        "minimum_variance_strategy",
        "size_small_cap_strategy",
        "mid_cap_tilt_strategy",
        "profitability_factor_strategy",
        "earnings_quality_strategy",
        "low_leverage_balance_sheet_strength",
        "investment_quality_strategy",
        "earnings_stability_low_earnings_variability",
        "value_strategy",
        "quality_strategy",
        "multi_factor_composite",
        "support_resistance_bounce",
        "breakout_retest",
        "pivot_point_strategy",
        "opening_range_breakout",
        "inside_bar_breakout",
        "gap_and_go",
        "trendline_break_strategy",
        "volatility_squeeze_breakout",
        "intraday_vwap_reversion",
        "opening_gap_fade",
        "z_score_mean_reversion",
        "bollinger_bands_reversion",
        "rsi_reversion",
        "stochastic_reversion",
        "cci_reversion",
        "williams_percent_r_reversion",
        "range_reversion",
        "ornstein_uhlenbeck_reversion",
        "long_horizon_reversal",
        "volatility_adjusted_reversion",
        "volatility_breakout",
        "atr_channel_breakout",
        "volatility_mean_reversion",
        "carry_trade_fx_rates",
        "yield_curve_steepener_flattener",
        "curve_roll_down_strategy",
        "commodity_term_structure_roll_yield",
        "risk_on_risk_off_regime",
        "intermarket_confirmation",
        "seasonality_calendar_effects",
        "earnings_drift_post_event_momentum",
        "hard_boolean_gating_and_or_majority",
        "weighted_linear_score_blend",
        "aggregate_boundary_and_channel",
        "aggregate_channel_dual_window",
    ]
    assert any(spec.tags for spec in specs)
    assert all(spec.version for spec in specs)
    assert all(spec.category for spec in specs)
    assert all(spec.warmup_period >= 1 for spec in specs)


@pytest.mark.parametrize(
    (
        "alg_key",
        "alg_param",
        "expected_catalog_ref",
        "expected_family",
        "expected_top_symbol",
    ),
    [
        (
            "carry_trade_fx_rates",
            {
                "rows": _build_cross_asset_fixture_rows(),
                "field_names": ["carry", "yield_diff"],
                "rebalance_frequency": "monthly",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
            "algorithm:78",
            "cross_asset_macro_carry",
            "AAA",
        ),
        (
            "risk_on_risk_off_regime",
            {
                "rows": _build_cross_asset_fixture_rows(),
                "field_names": ["risk_score", "credit_impulse"],
                "rebalance_frequency": "monthly",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 1,
            },
            "algorithm:82",
            "cross_asset_macro_carry",
            "BBB",
        ),
        (
            "intermarket_confirmation",
            {
                "rows": _build_cross_asset_fixture_rows(),
                "field_names": ["confirmation", "leader_return"],
                "rebalance_frequency": "monthly",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
            "algorithm:83",
            "cross_asset_macro_carry",
            "BBB",
        ),
        (
            "seasonality_calendar_effects",
            {
                "rows": _build_cross_asset_fixture_rows(),
                "rebalance_frequency": "monthly",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 1,
                "calendar_pattern": "month_end",
            },
            "algorithm:84",
            "cross_asset_macro_carry",
            "AAA",
        ),
        (
            "earnings_drift_post_event_momentum",
            {
                "rows": _build_cross_asset_fixture_rows(),
                "event_rows": _build_event_fixture_rows(),
                "field_names": ["surprise"],
                "rebalance_frequency": "all",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 1,
                "post_event_window_days": 3,
                "surprise_field": "surprise",
            },
            "algorithm:85",
            "cross_asset_macro_carry",
            None,
        ),
    ],
)
def test_cross_asset_wave_1_registration_and_fixture_behavior(
    tmp_path,
    alg_key,
    alg_param,
    expected_catalog_ref,
    expected_family,
    expected_top_symbol,
) -> None:
    spec = get_alert_algorithm_spec_by_key(alg_key)
    assert spec.catalog_ref == expected_catalog_ref
    assert spec.family == expected_family

    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "UNIVERSE",
            "alg_key": alg_key,
            "alg_param": alg_param,
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    payload, payload_name = algorithm.interactive_report_payloads()[0]

    assert output.metadata["catalog_ref"] == expected_catalog_ref
    assert output.metadata["family"] == expected_family
    assert output.metadata["reporting_mode"] == "rebalance_report"
    assert output.metadata["warmup_period"] == algorithm.minimum_history()
    assert output.derived_series["top_symbol"][-1] == expected_top_symbol
    assert "reason_codes" in output.derived_series
    assert "regime_label" in output.derived_series
    assert output.child_outputs[0].diagnostics["catalog_ref"] == expected_catalog_ref
    assert output.child_outputs[0].diagnostics["reporting_mode"] == "rebalance_report"
    assert output.child_outputs[0].reason_codes == tuple(
        output.child_outputs[0].diagnostics["reason_codes"]
    )
    assert payload_name.startswith(f"rebalance_report_{alg_key}_")
    assert payload["data"]["metadata"]["catalog_ref"] == expected_catalog_ref
    assert payload["portfolio"]["metadata"]["catalog_ref"] == expected_catalog_ref
    assert output.child_outputs[0].diagnostics["family"] == expected_family


@pytest.mark.parametrize(
    ("alg_key", "alg_param"),
    [
        (
            "carry_trade_fx_rates",
            {
                "rows": _build_cross_asset_fixture_rows()[:1],
                "field_names": ["carry", "yield_diff"],
                "rebalance_frequency": "all",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
        ),
        (
            "risk_on_risk_off_regime",
            {
                "rows": _build_cross_asset_fixture_rows()[:1],
                "field_names": ["risk_score", "credit_impulse"],
                "rebalance_frequency": "all",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
        ),
        (
            "intermarket_confirmation",
            {
                "rows": _build_cross_asset_fixture_rows()[:1],
                "field_names": ["confirmation", "leader_return"],
                "rebalance_frequency": "all",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
        ),
        (
            "seasonality_calendar_effects",
            {
                "rows": _build_cross_asset_fixture_rows()[:1],
                "rebalance_frequency": "all",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
                "calendar_pattern": "month_end",
            },
        ),
        (
            "earnings_drift_post_event_momentum",
            {
                "rows": _build_cross_asset_fixture_rows()[:1],
                "event_rows": _build_event_fixture_rows(),
                "field_names": ["surprise"],
                "rebalance_frequency": "all",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
                "post_event_window_days": 3,
                "surprise_field": "surprise",
            },
        ),
    ],
)
def test_cross_asset_wave_1_short_history_stays_neutral_until_minimum_universe_size(
    tmp_path, alg_key, alg_param
) -> None:
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "UNIVERSE",
            "alg_key": alg_key,
            "alg_param": alg_param,
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()

    assert output.points
    assert all(point.signal_label == "neutral" for point in output.points)
    assert all("warmup_pending" in point.reason_codes for point in output.points)
    assert all(flag is False for flag in output.derived_series["warmup_ready"])
    assert output.child_outputs[0].diagnostics["decision_reason"] == "warmup_pending"
    assert output.child_outputs[0].diagnostics["warmup_ready"] is False


@pytest.mark.parametrize(
    ("alg_key", "alg_param", "expected_message"),
    [
        (
            "carry_trade_fx_rates",
            {
                "rows": _build_cross_asset_fixture_rows(),
                "field_names": ["carry"],
                "rebalance_frequency": "monthly",
                "top_n": 1,
                "bottom_n": 1,
                "long_only": True,
                "minimum_universe_size": 1,
            },
            "bottom_n must be 0 when long_only is true",
        ),
        (
            "yield_curve_steepener_flattener",
            {
                "rows": _build_cross_asset_fixture_rows(),
                "field_names": ["curve_2y10y"],
                "front_leg_field": "",
                "back_leg_field": "yield_10y",
                "rebalance_frequency": "monthly",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 1,
            },
            "front_leg_field is required",
        ),
        (
            "seasonality_calendar_effects",
            {
                "rows": _build_cross_asset_fixture_rows(),
                "rebalance_frequency": "monthly",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 1,
                "calendar_pattern": "invalid",
            },
            "calendar_pattern must be one of",
        ),
        (
            "earnings_drift_post_event_momentum",
            {
                "rows": _build_cross_asset_fixture_rows(),
                "event_rows": [{"symbol": "AAA"}],
                "field_names": ["surprise"],
                "rebalance_frequency": "all",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 1,
                "post_event_window_days": 3,
            },
            r"event_rows\[0\] event_timestamp is required",
        ),
    ],
)
def test_cross_asset_wave_1_validation_rejects_invalid_parameter_shapes(
    alg_key, alg_param, expected_message
) -> None:
    with pytest.raises(ValueError, match=expected_message):
        normalize_alertgen_sensor_config(
            {
                "symbol": "UNIVERSE",
                "alg_key": alg_key,
                "alg_param": alg_param,
                "buy": True,
                "sell": False,
            }
        )


@pytest.mark.parametrize(
    ("alg_key", "alg_param"),
    [
        (
            "yield_curve_steepener_flattener",
            {
                "rows": _build_cross_asset_fixture_rows(),
                "field_names": ["curve_2y10y"],
                "front_leg_field": "yield_2y",
                "back_leg_field": "yield_10y",
                "rebalance_frequency": "monthly",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 1,
            },
        ),
        (
            "curve_roll_down_strategy",
            {
                "rows": _build_cross_asset_fixture_rows(),
                "field_names": ["roll_down"],
                "front_leg_field": "front_roll",
                "back_leg_field": "back_roll",
                "rebalance_frequency": "monthly",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 1,
            },
        ),
        (
            "commodity_term_structure_roll_yield",
            {
                "rows": _build_cross_asset_fixture_rows(),
                "field_names": ["roll_yield"],
                "front_leg_field": "near_contract",
                "back_leg_field": "far_contract",
                "rebalance_frequency": "monthly",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 1,
            },
        ),
    ],
)
def test_cross_asset_wave_1_multi_leg_outputs_expose_leg_diagnostics(
    tmp_path, alg_key, alg_param
) -> None:
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "UNIVERSE",
            "alg_key": alg_key,
            "alg_param": alg_param,
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    portfolio_output = algorithm.portfolio_output()

    assert output.derived_series["legs"][-1]
    assert len(portfolio_output.rebalances[-1].legs) == 2
    assert portfolio_output.metadata["reporting_mode"] == "rebalance_report"
    assert output.child_outputs[0].diagnostics["selected_symbol"] in {"AAA", "BBB"}
    assert output.derived_series["hedge_ratio"][-1] == pytest.approx(1.0)
    assert output.child_outputs[0].diagnostics["hedge_ratio"] == pytest.approx(1.0)
    assert output.child_outputs[0].diagnostics["decision_reason"] == "selection_ready"


def test_cross_asset_wave_1_fixture_behavior_matches_manifest_expectations(
    tmp_path,
) -> None:
    carry_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "UNIVERSE",
            "alg_key": "carry_trade_fx_rates",
            "alg_param": {
                "rows": _build_cross_asset_fixture_rows(),
                "field_names": ["carry", "yield_diff"],
                "rebalance_frequency": "monthly",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path / "carry"),
    )
    carry_output = carry_algorithm.normalized_output()

    assert carry_output.derived_series["top_symbol"] == ["AAA", "AAA"]
    assert all(
        symbol == ["AAA"] for symbol in carry_output.derived_series["selected_symbols"]
    )
    assert carry_output.child_outputs[0].diagnostics["selected_count"] == 1
    assert carry_output.child_outputs[0].diagnostics["gross_exposure"] == pytest.approx(
        1.0
    )

    regime_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "UNIVERSE",
            "alg_key": "risk_on_risk_off_regime",
            "alg_param": {
                "rows": _build_cross_asset_fixture_rows(),
                "field_names": ["risk_score", "credit_impulse"],
                "rebalance_frequency": "monthly",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 1,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path / "regime"),
    )
    regime_output = regime_algorithm.normalized_output()

    assert regime_output.derived_series["top_symbol"] == ["AAA", "BBB"]
    assert regime_output.derived_series["regime_label"] == ["selected", "selected"]
    assert regime_output.child_outputs[0].diagnostics["top_ranked_symbol"] == "BBB"

    seasonality_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "UNIVERSE",
            "alg_key": "seasonality_calendar_effects",
            "alg_param": {
                "rows": _build_cross_asset_fixture_rows(),
                "rebalance_frequency": "monthly",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 1,
                "calendar_pattern": "month_end",
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path / "seasonality"),
    )
    seasonality_output = seasonality_algorithm.normalized_output()

    assert seasonality_output.derived_series["top_score"] == [0.0, 0.0]
    assert (
        seasonality_output.child_outputs[0].diagnostics["score_label"]
        == "calendar_score"
    )

    earnings_rows = [
        *_build_cross_asset_fixture_rows(),
        {
            "ts": "2025-02-04",
            "symbol": "AAA",
            "Close": 102.0,
            "carry": 0.06,
            "yield_diff": 0.05,
            "risk_score": 0.20,
            "credit_impulse": 0.25,
            "confirmation": 0.45,
            "leader_return": 0.01,
            "yield_2y": 0.022,
            "yield_10y": 0.046,
            "front_roll": 0.027,
            "back_roll": 0.012,
            "near_contract": 103.0,
            "far_contract": 100.0,
        },
        {
            "ts": "2025-02-04",
            "symbol": "BBB",
            "Close": 98.0,
            "carry": 0.01,
            "yield_diff": 0.02,
            "risk_score": 0.90,
            "credit_impulse": 0.70,
            "confirmation": 0.80,
            "leader_return": 0.03,
            "yield_2y": 0.031,
            "yield_10y": 0.033,
            "front_roll": 0.007,
            "back_roll": 0.019,
            "near_contract": 96.0,
            "far_contract": 102.0,
        },
    ]
    earnings_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "UNIVERSE",
            "alg_key": "earnings_drift_post_event_momentum",
            "alg_param": {
                "rows": earnings_rows,
                "event_rows": _build_event_fixture_rows(),
                "field_names": ["surprise"],
                "rebalance_frequency": "all",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 1,
                "post_event_window_days": 3,
                "surprise_field": "surprise",
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path / "earnings"),
    )
    earnings_output = earnings_algorithm.normalized_output()

    assert earnings_output.points[0].signal_label == "neutral"
    assert "warmup_pending" in earnings_output.points[0].reason_codes
    assert earnings_output.points[-1].signal_label == "buy"
    assert earnings_output.child_outputs[0].diagnostics["event_window_active"] is True
    assert earnings_output.child_outputs[0].diagnostics["latest_event_timestamp"] == (
        "2025-02-03 16:05:00"
    )
    assert earnings_output.child_outputs[0].diagnostics[
        "latest_event_surprise"
    ] == pytest.approx(0.15)


def test_cross_asset_wave_1_registration_metadata_matches_manifest_contract() -> None:
    expected = {
        "carry_trade_fx_rates": ("algorithm:78", "cross_asset_macro_carry", "carry", 1),
        "yield_curve_steepener_flattener": (
            "algorithm:79",
            "cross_asset_macro_carry",
            "yield",
            1,
        ),
        "curve_roll_down_strategy": (
            "algorithm:80",
            "cross_asset_macro_carry",
            "curve",
            1,
        ),
        "commodity_term_structure_roll_yield": (
            "algorithm:81",
            "cross_asset_macro_carry",
            "commodity",
            1,
        ),
        "risk_on_risk_off_regime": (
            "algorithm:82",
            "cross_asset_macro_carry",
            "risk",
            1,
        ),
        "intermarket_confirmation": (
            "algorithm:83",
            "cross_asset_macro_carry",
            "intermarket",
            1,
        ),
        "seasonality_calendar_effects": (
            "algorithm:84",
            "cross_asset_macro_carry",
            "seasonality",
            1,
        ),
        "earnings_drift_post_event_momentum": (
            "algorithm:85",
            "cross_asset_macro_carry",
            "earnings",
            1,
        ),
    }

    for alg_key, (catalog_ref, family, subcategory, warmup_period) in expected.items():
        spec = get_alert_algorithm_spec_by_key(alg_key)

        assert spec.catalog_ref == catalog_ref
        assert spec.family == family
        assert spec.subcategory == subcategory
        assert spec.warmup_period == warmup_period
        assert spec.category == "cross_asset_macro_carry"
        assert spec.asset_scope == "portfolio"


@pytest.mark.parametrize(
    ("alg_key", "catalog_ref", "alg_param"),
    [
        (
            "carry_trade_fx_rates",
            "algorithm:78",
            {
                "rows": _build_cross_asset_fixture_rows(),
                "field_names": ["carry", "yield_diff"],
                "rebalance_frequency": "monthly",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
        ),
        (
            "risk_on_risk_off_regime",
            "algorithm:82",
            {
                "rows": _build_cross_asset_fixture_rows(),
                "field_names": ["risk_score", "credit_impulse"],
                "rebalance_frequency": "monthly",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 1,
            },
        ),
        (
            "earnings_drift_post_event_momentum",
            "algorithm:85",
            {
                "rows": _build_cross_asset_fixture_rows(),
                "event_rows": _build_event_fixture_rows(),
                "field_names": ["surprise"],
                "rebalance_frequency": "all",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 1,
                "post_event_window_days": 3,
                "surprise_field": "surprise",
            },
        ),
    ],
)
def test_cross_asset_wave_1_normalized_output_metadata_exposes_dashboard_contract_fields(
    tmp_path, alg_key, catalog_ref, alg_param
) -> None:
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "UNIVERSE",
            "alg_key": alg_key,
            "alg_param": alg_param,
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    child_output = output.child_outputs[0]

    assert output.metadata["family"] == "cross_asset_macro_carry"
    assert output.metadata["reporting_mode"] == "rebalance_report"
    assert output.metadata["catalog_ref"] == catalog_ref
    assert child_output.diagnostics["family"] == "cross_asset_macro_carry"
    assert child_output.diagnostics["reporting_mode"] == "rebalance_report"
    assert child_output.diagnostics["catalog_ref"] == catalog_ref
    assert child_output.reason_codes == tuple(child_output.diagnostics["reason_codes"])
    assert (
        child_output.diagnostics["decision_reason"]
        in child_output.diagnostics["reason_codes"]
    )


def test_cross_asset_wave_1_performance_smoke_on_fixture_repetition(tmp_path) -> None:
    rows = _build_cross_asset_fixture_rows() * 40
    algorithms: list[tuple[str, dict[str, Any]]] = [
        (
            "carry_trade_fx_rates",
            {
                "rows": rows,
                "field_names": ["carry", "yield_diff"],
                "rebalance_frequency": "monthly",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
        ),
        (
            "risk_on_risk_off_regime",
            {
                "rows": rows,
                "field_names": ["risk_score", "credit_impulse"],
                "rebalance_frequency": "monthly",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 1,
            },
        ),
        (
            "earnings_drift_post_event_momentum",
            {
                "rows": rows,
                "event_rows": _build_event_fixture_rows(),
                "field_names": ["surprise"],
                "rebalance_frequency": "all",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 1,
                "post_event_window_days": 3,
                "surprise_field": "surprise",
            },
        ),
    ]

    for index, (alg_key, alg_param) in enumerate(algorithms):
        algorithm, _ = create_alertgen_algorithm(
            sensor_config={
                "symbol": "UNIVERSE",
                "alg_key": alg_key,
                "alg_param": alg_param,
                "buy": True,
                "sell": False,
            },
            report_base_path=str(tmp_path / str(index)),
        )
        output = algorithm.normalized_output()

        assert output.metadata["warmup_period"] == algorithm.minimum_history()
        assert output.metadata["reporting_mode"] == "rebalance_report"
        assert len(output.points) >= 1


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
            "gap_and_go",
            {
                "gap_threshold": 0.15,
                "continuation_threshold": 0.05,
                "volume_window": 3,
                "relative_volume_threshold": 1.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "trendline_break_strategy",
            {
                "trendline_window": 5,
                "break_buffer": 0.1,
                "slope_tolerance": 0.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "volatility_squeeze_breakout",
            {
                "squeeze_window": 5,
                "bollinger_multiplier": 2.0,
                "keltner_multiplier": 1.5,
                "breakout_buffer": 0.05,
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
            "intraday_vwap_reversion",
            {
                "entry_deviation_percent": 1.0,
                "exit_deviation_percent": 0.5,
                "min_session_bars": 2,
                "confirmation_bars": 1,
            },
        ),
        (
            "opening_gap_fade",
            {
                "min_gap_percent": 1.0,
                "exit_gap_fill_percent": 0.25,
                "min_session_bars": 2,
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
            "ornstein_uhlenbeck_reversion",
            {
                "window": 4,
                "entry_sigma": 0.5,
                "exit_sigma": 0.25,
                "min_mean_reversion_speed": 0.01,
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
        (
            "low_volatility_strategy",
            {
                "rows": _build_factor_fixture_rows(),
                "field_names": ["volatility_20d", "realized_volatility"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
        ),
        (
            "low_beta_betting_against_beta",
            {
                "rows": _build_factor_fixture_rows(),
                "field_names": ["beta_252d", "market_beta"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
        ),
        (
            "dividend_yield_strategy",
            {
                "rows": _build_factor_fixture_rows(),
                "field_names": ["dividend_yield", "forward_dividend_yield"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
        ),
        (
            "growth_factor_strategy",
            {
                "rows": _build_factor_fixture_rows(),
                "field_names": ["earnings_growth", "sales_growth"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
        ),
        (
            "liquidity_factor_strategy",
            {
                "rows": _build_factor_fixture_rows(),
                "field_names": ["liquidity_score", "turnover_ratio"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
        ),
        (
            "minimum_variance_strategy",
            {
                "rows": _build_factor_fixture_rows(),
                "field_names": ["volatility_20d", "realized_volatility"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
                "weighting_mode": "inverse_metric",
            },
        ),
        (
            "size_small_cap_strategy",
            {
                "rows": _build_factor_fixture_rows(),
                "field_names": ["market_cap_billions"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
        ),
        (
            "mid_cap_tilt_strategy",
            {
                "rows": _build_factor_fixture_rows(),
                "field_names": ["market_cap_billions"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
                "target_value": 10.0,
            },
        ),
        (
            "profitability_factor_strategy",
            {
                "rows": _build_factor_fixture_rows(),
                "field_names": ["return_on_assets", "gross_profitability"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
        ),
        (
            "earnings_quality_strategy",
            {
                "rows": _build_factor_fixture_rows(),
                "field_names": ["cash_earnings_ratio", "earnings_stability"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
        ),
        (
            "low_leverage_balance_sheet_strength",
            {
                "rows": _build_factor_fixture_rows(),
                "field_names": ["debt_to_equity", "net_debt_to_ebitda"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
        ),
        (
            "value_strategy",
            {
                "rows": _build_factor_fixture_rows(),
                "field_names": ["price_to_book", "price_to_earnings"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
        ),
        (
            "quality_strategy",
            {
                "rows": _build_factor_fixture_rows(),
                "field_names": ["return_on_equity", "gross_margin"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
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
    algorithms: list[tuple[str, dict[str, Any]]] = [
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
    assert child_output.reason_codes == tuple(child_output.diagnostics["reason_codes"])


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
    assert child_output.reason_codes == tuple(child_output.diagnostics["reason_codes"])


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
        (
            "gap_and_go",
            {
                "gap_threshold": 0.15,
                "continuation_threshold": 0.05,
                "volume_window": 3,
                "relative_volume_threshold": 1.0,
                "confirmation_bars": 1,
            },
            5,
        ),
        (
            "trendline_break_strategy",
            {
                "trendline_window": 5,
                "break_buffer": 0.1,
                "slope_tolerance": 0.0,
                "confirmation_bars": 1,
            },
            5,
        ),
        (
            "volatility_squeeze_breakout",
            {
                "squeeze_window": 5,
                "bollinger_multiplier": 2.0,
                "keltner_multiplier": 1.5,
                "breakout_buffer": 0.05,
                "confirmation_bars": 1,
            },
            6,
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
    assert all(point.score == 0.0 for point in output.points)
    expected_pending_code = (
        "opening_range_pending"
        if alg_key == "opening_range_breakout"
        else "warmup_pending"
    )
    assert any(expected_pending_code in point.reason_codes for point in output.points)
    assert output.metadata["warmup_period"] == expected_warmup
    assert output.derived_series["warmup_ready"][-1] is False


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
        (
            "gap_and_go",
            {
                "gap_threshold": 0.15,
                "continuation_threshold": 0.05,
                "volume_window": 3,
                "relative_volume_threshold": 1.0,
                "confirmation_bars": 1,
            },
            "support_rejection.csv",
            "awaiting_gap",
            {
                "gap_threshold",
                "continuation_threshold",
                "volume_window",
                "relative_volume_threshold",
                "gap_size",
                "relative_volume",
            },
        ),
        (
            "trendline_break_strategy",
            {
                "trendline_window": 5,
                "break_buffer": 0.1,
                "slope_tolerance": 0.0,
                "confirmation_bars": 1,
            },
            "support_rejection.csv",
            "trendline_break_bullish",
            {"trendline_window", "break_buffer", "trendline_level", "trendline_slope"},
        ),
        (
            "volatility_squeeze_breakout",
            {
                "squeeze_window": 5,
                "bollinger_multiplier": 2.0,
                "keltner_multiplier": 1.5,
                "breakout_buffer": 0.05,
                "confirmation_bars": 1,
            },
            "support_rejection.csv",
            "squeeze_active",
            {"squeeze_window", "bollinger_upper", "keltner_upper", "squeeze_on"},
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
        "exit_value",
        "bullish_confirmation_count",
        "bearish_confirmation_count",
        "bullish_confirmed",
        "bearish_confirmed",
        "confirmation_state_label",
        "warmup_ready",
    }.issubset(output.derived_series)
    assert output.metadata["family"] == "pattern_price_action"
    assert output.metadata["reporting_mode"] == "bar_series"
    assert output.metadata["catalog_ref"] == child_output.diagnostics["catalog_ref"]
    assert child_output.diagnostics["family"] == "pattern_price_action"
    assert child_output.diagnostics["reporting_mode"] == "bar_series"
    assert child_output.diagnostics["warmup_ready"] is True
    assert child_output.diagnostics["warmup_period"] == algorithm.minimum_history()
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
    assert any(point.signal_label == "buy" for point in support_output.points)
    assert any(support_output.derived_series["support_touched"])
    assert any(support_output.derived_series["rejection_confirmed"])

    breakout_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "breakout_retest",
            "alg_param": {
                "breakout_window": 5,
                "breakout_buffer": 0.2,
                "retest_tolerance": 0.3,
                "confirmation_bars": 1,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path / "breakout"),
    )
    breakout_algorithm.process_list(_load_pattern_fixture_rows("support_rejection.csv"))
    breakout_output = breakout_algorithm.normalized_output()
    assert all(point.signal_label == "neutral" for point in breakout_output.points)
    assert breakout_output.points[-1].reason_codes[0] == "awaiting_breakout"

    pivot_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "pivot_point_strategy",
            "alg_param": {
                "pivot_lookback": 3,
                "level_tolerance": 0.4,
                "confirmation_bars": 1,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path / "pivot"),
    )
    pivot_algorithm.process_list(_load_pattern_fixture_rows("support_rejection.csv"))
    pivot_output = pivot_algorithm.normalized_output()
    assert pivot_output.points[-1].signal_label == "neutral"
    assert pivot_output.derived_series["pivot_level_name"][-1] is not None

    inside_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "inside_bar_breakout",
            "alg_param": {
                "breakout_buffer": 0.1,
                "confirmation_bars": 1,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path / "inside"),
    )
    inside_algorithm.process_list(_load_pattern_fixture_rows("support_rejection.csv"))
    inside_output = inside_algorithm.normalized_output()
    assert inside_output.points[-1].signal_label == "neutral"
    assert inside_output.derived_series["inside_bar_detected"][-1] is False

    gap_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "gap_and_go",
            "alg_param": {
                "gap_threshold": 0.15,
                "continuation_threshold": 0.05,
                "volume_window": 3,
                "relative_volume_threshold": 1.0,
                "confirmation_bars": 1,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path / "gap"),
    )
    gap_algorithm.process_list(_load_pattern_fixture_rows("support_rejection.csv"))
    gap_output = gap_algorithm.normalized_output()
    assert gap_output.points[-1].signal_label == "neutral"
    assert gap_output.points[-1].reason_codes[0] == "awaiting_gap"

    trendline_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "trendline_break_strategy",
            "alg_param": {
                "trendline_window": 5,
                "break_buffer": 0.1,
                "slope_tolerance": 0.0,
                "confirmation_bars": 1,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path / "trendline"),
    )
    trendline_algorithm.process_list(
        _load_pattern_fixture_rows("support_rejection.csv")
    )
    trendline_output = trendline_algorithm.normalized_output()
    assert trendline_output.points[-1].signal_label == "neutral"
    assert trendline_output.derived_series["trendline_break_detected"][-1] is False

    squeeze_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "volatility_squeeze_breakout",
            "alg_param": {
                "squeeze_window": 5,
                "bollinger_multiplier": 2.0,
                "keltner_multiplier": 1.5,
                "breakout_buffer": 0.05,
                "confirmation_bars": 1,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path / "squeeze"),
    )
    squeeze_algorithm.process_list(_load_pattern_fixture_rows("support_rejection.csv"))
    squeeze_output = squeeze_algorithm.normalized_output()
    assert squeeze_output.points[-1].signal_label == "neutral"
    assert "squeeze_active" in squeeze_output.points[-1].reason_codes

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
    assert orb_output.points[-1].signal_label == "buy"
    assert orb_output.derived_series["session_label"][-1] == "2025-01-02"
    assert orb_output.derived_series["session_minute"][-1] == 20


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

    with pytest.raises(ValueError, match="level_tolerance must be >= 0"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "pivot_point_strategy",
                "alg_param": {
                    "pivot_lookback": 3,
                    "level_tolerance": -0.1,
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
                "alg_key": "inside_bar_breakout",
                "alg_param": {
                    "breakout_buffer": -0.1,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="volume_window must be > 0"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "gap_and_go",
                "alg_param": {
                    "gap_threshold": 0.15,
                    "continuation_threshold": 0.05,
                    "volume_window": 0,
                    "relative_volume_threshold": 1.0,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="trendline_window must be > 0"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "trendline_break_strategy",
                "alg_param": {
                    "trendline_window": 0,
                    "break_buffer": 0.1,
                    "slope_tolerance": 0.0,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="bollinger_multiplier must be > 0"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "volatility_squeeze_breakout",
                "alg_param": {
                    "squeeze_window": 5,
                    "bollinger_multiplier": 0.0,
                    "keltner_multiplier": 1.5,
                    "breakout_buffer": 0.05,
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
        "gap_and_go": ("algorithm:75", "pattern_price_action", "gap", 5),
        "trendline_break_strategy": (
            "algorithm:76",
            "pattern_price_action",
            "trendline",
            5,
        ),
        "volatility_squeeze_breakout": (
            "algorithm:77",
            "pattern_price_action",
            "volatility",
            6,
        ),
    }

    for alg_key, (catalog_ref, family, subcategory, warmup_period) in expected.items():
        spec = get_alert_algorithm_spec_by_key(alg_key)

        assert spec.catalog_ref == catalog_ref
        assert spec.family == family
        assert spec.subcategory == subcategory
        assert spec.warmup_period == warmup_period
        assert spec.output_modes == ("signal", "score", "confidence")
        assert spec.category == "pattern_price_action"


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
        (
            "gap_and_go",
            {
                "gap_threshold": 0.15,
                "continuation_threshold": 0.05,
                "volume_window": 3,
                "relative_volume_threshold": 1.0,
                "confirmation_bars": 1,
            },
            support_rows,
        ),
        (
            "trendline_break_strategy",
            {
                "trendline_window": 5,
                "break_buffer": 0.1,
                "slope_tolerance": 0.0,
                "confirmation_bars": 1,
            },
            support_rows,
        ),
        (
            "volatility_squeeze_breakout",
            {
                "squeeze_window": 5,
                "bollinger_multiplier": 2.0,
                "keltner_multiplier": 1.5,
                "breakout_buffer": 0.05,
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


@pytest.mark.parametrize(
    ("alg_key", "alg_param", "expected_catalog_ref", "expected_subcategory"),
    [
        (
            "cross_sectional_momentum",
            {
                "rows": _load_cross_sectional_momentum_fixture_rows(
                    "cross_sectional_ranking.csv"
                ),
                "lookback_window": 1,
                "top_n": 2,
                "bottom_n": 0,
                "rebalance_frequency": "monthly",
                "long_only": True,
            },
            "algorithm:16",
            "cross",
        ),
        (
            "relative_strength_momentum",
            {
                "rows": _load_cross_sectional_momentum_fixture_rows(
                    "cross_sectional_ranking.csv"
                ),
                "lookback_window": 1,
                "top_n": 2,
                "bottom_n": 0,
                "rebalance_frequency": "monthly",
                "long_only": True,
            },
            "algorithm:17",
            "relative",
        ),
        (
            "dual_momentum",
            {
                "rows": _load_cross_sectional_momentum_fixture_rows(
                    "cross_sectional_ranking.csv"
                ),
                "lookback_window": 1,
                "top_n": 1,
                "bottom_n": 0,
                "rebalance_frequency": "monthly",
                "long_only": True,
                "absolute_momentum_threshold": 0.0,
                "defensive_symbol": "BIL",
            },
            "algorithm:18",
            "dual",
        ),
        (
            "residual_momentum",
            {
                "rows": _load_cross_sectional_momentum_fixture_rows(
                    "cross_sectional_ranking.csv"
                ),
                "lookback_window": 1,
                "top_n": 2,
                "bottom_n": 0,
                "rebalance_frequency": "monthly",
                "long_only": True,
                "score_adjustments": {"BBB": 5.0, "AAA": -1.0},
            },
            "algorithm:19",
            "residual",
        ),
    ],
)
def test_momentum_wave_3_registration_metadata_matches_manifest_contract(
    alg_key, alg_param, expected_catalog_ref, expected_subcategory
) -> None:
    del alg_param
    spec = get_alert_algorithm_spec_by_key(alg_key)

    assert spec.catalog_ref == expected_catalog_ref
    assert spec.family == "momentum"
    assert spec.subcategory == expected_subcategory
    assert spec.warmup_period == 4
    assert spec.output_modes == ("ranking", "selection", "diagnostics")


@pytest.mark.parametrize(
    ("alg_key", "alg_param", "expected_top_symbol"),
    [
        (
            "cross_sectional_momentum",
            {
                "rows": _load_cross_sectional_momentum_fixture_rows(
                    "cross_sectional_ranking.csv"
                ),
                "lookback_window": 1,
                "top_n": 2,
                "bottom_n": 0,
                "rebalance_frequency": "monthly",
                "long_only": True,
            },
            "AAA",
        ),
        (
            "relative_strength_momentum",
            {
                "rows": _load_cross_sectional_momentum_fixture_rows(
                    "cross_sectional_ranking.csv"
                ),
                "lookback_window": 1,
                "top_n": 2,
                "bottom_n": 0,
                "rebalance_frequency": "monthly",
                "long_only": True,
            },
            "AAA",
        ),
        (
            "dual_momentum",
            {
                "rows": _load_cross_sectional_momentum_fixture_rows(
                    "cross_sectional_ranking.csv"
                ),
                "lookback_window": 1,
                "top_n": 1,
                "bottom_n": 0,
                "rebalance_frequency": "monthly",
                "long_only": True,
                "absolute_momentum_threshold": 0.0,
                "defensive_symbol": "BIL",
            },
            "AAA",
        ),
        (
            "residual_momentum",
            {
                "rows": _load_cross_sectional_momentum_fixture_rows(
                    "cross_sectional_ranking.csv"
                ),
                "lookback_window": 1,
                "top_n": 2,
                "bottom_n": 0,
                "rebalance_frequency": "monthly",
                "long_only": True,
                "score_adjustments": {"BBB": 5.0, "AAA": -1.0},
            },
            "BBB",
        ),
    ],
)
def test_momentum_wave_3_fixture_behavior_matches_manifest_expectations(
    tmp_path, alg_key, alg_param, expected_top_symbol
) -> None:
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "UNIVERSE",
            "alg_key": alg_key,
            "alg_param": alg_param,
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    portfolio_output = algorithm.portfolio_output()

    assert output.points
    assert output.points[-1].signal_label == "buy"
    assert output.derived_series["top_symbol"][-1] == expected_top_symbol
    assert output.derived_series["selected_count"][-1] >= 1
    assert output.metadata["family"] == "momentum"
    assert output.metadata["reporting_mode"] == "rebalance_report"
    assert portfolio_output.metadata["catalog_ref"] == output.metadata["catalog_ref"]
    assert portfolio_output.rebalances[-1].ranking[0].symbol == expected_top_symbol
    assert expected_top_symbol in portfolio_output.rebalances[-1].selected_symbols


def test_momentum_wave_3_dual_momentum_defensive_fallback_is_used_when_threshold_fails(
    tmp_path,
) -> None:
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "UNIVERSE",
            "alg_key": "dual_momentum",
            "alg_param": {
                "rows": _load_cross_sectional_momentum_fixture_rows(
                    "cross_sectional_ranking.csv"
                ),
                "lookback_window": 1,
                "top_n": 1,
                "bottom_n": 0,
                "rebalance_frequency": "monthly",
                "long_only": True,
                "absolute_momentum_threshold": 100.0,
                "defensive_symbol": "BIL",
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    child_output = output.child_outputs[0]

    assert output.derived_series["selected_symbols"][-1] == ["BIL"]
    assert child_output.diagnostics["selected_symbols"] == ["BIL"]
    assert child_output.diagnostics["weights"] == {"BIL": 1.0}


def test_momentum_wave_3_validation_rejects_invalid_parameter_shapes() -> None:
    with pytest.raises(ValueError, match="bottom_n must be 0 when long_only is true"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "UNIVERSE",
                "alg_key": "cross_sectional_momentum",
                "alg_param": {
                    "rows": _load_cross_sectional_momentum_fixture_rows(
                        "cross_sectional_ranking.csv"
                    ),
                    "lookback_window": 1,
                    "top_n": 2,
                    "bottom_n": 1,
                    "rebalance_frequency": "monthly",
                    "long_only": True,
                },
                "buy": True,
                "sell": False,
            }
        )

    with pytest.raises(ValueError, match=r"rows\[0\] symbol is required"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "UNIVERSE",
                "alg_key": "relative_strength_momentum",
                "alg_param": {
                    "rows": [{"ts": "2025-01-01", "Close": 100.0}],
                    "lookback_window": 1,
                    "top_n": 1,
                    "rebalance_frequency": "monthly",
                    "long_only": True,
                },
                "buy": True,
                "sell": False,
            }
        )

    with pytest.raises(ValueError, match="defensive_symbol is required"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "UNIVERSE",
                "alg_key": "dual_momentum",
                "alg_param": {
                    "rows": _load_cross_sectional_momentum_fixture_rows(
                        "cross_sectional_ranking.csv"
                    ),
                    "lookback_window": 1,
                    "top_n": 1,
                    "rebalance_frequency": "monthly",
                    "long_only": True,
                    "absolute_momentum_threshold": 100.0,
                    "defensive_symbol": "   ",
                },
                "buy": True,
                "sell": False,
            }
        )


def test_momentum_wave_3_short_history_stays_neutral_until_warmup(tmp_path) -> None:
    rows = _load_cross_sectional_momentum_fixture_rows("cross_sectional_ranking.csv")[
        :4
    ]
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "UNIVERSE",
            "alg_key": "cross_sectional_momentum",
            "alg_param": {
                "rows": rows,
                "lookback_window": 1,
                "top_n": 2,
                "bottom_n": 0,
                "rebalance_frequency": "monthly",
                "long_only": True,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    portfolio_output = algorithm.portfolio_output()
    child_output = output.child_outputs[0]

    assert algorithm.minimum_history() == 2
    assert output.points
    assert all(point.signal_label == "neutral" for point in output.points)
    assert all(point.reason_codes == ("warmup_pending",) for point in output.points)
    assert output.derived_series["warmup_ready"][-1] is False
    assert portfolio_output.rebalances[-1].selected_symbols == ()
    assert child_output.reason_codes == ("warmup_pending",)
    assert child_output.diagnostics["warmup_pending_symbols"] == (
        "AAA",
        "BBB",
        "CCC",
        "DDD",
    )


def test_momentum_wave_3_diagnostics_expose_defensive_reason_and_ranked_payload(
    tmp_path,
) -> None:
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "UNIVERSE",
            "alg_key": "dual_momentum",
            "alg_param": {
                "rows": _load_cross_sectional_momentum_fixture_rows(
                    "cross_sectional_ranking.csv"
                ),
                "lookback_window": 1,
                "top_n": 1,
                "bottom_n": 0,
                "rebalance_frequency": "monthly",
                "long_only": True,
                "absolute_momentum_threshold": 100.0,
                "defensive_symbol": "BIL",
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    portfolio_output = algorithm.portfolio_output()
    child_output = output.child_outputs[0]
    latest_rebalance = portfolio_output.rebalances[-1]

    assert output.points[-1].reason_codes == ("defensive_fallback",)
    assert child_output.reason_codes == ("defensive_fallback",)
    assert child_output.diagnostics["selection_reason"] == "defensive_fallback"
    assert child_output.diagnostics["defensive_symbol_used"] is True
    assert latest_rebalance.ranking[-1].symbol == "BIL"
    assert latest_rebalance.ranking[-1].side == "defensive"
    assert latest_rebalance.ranking[-1].selected is True
    assert latest_rebalance.ranking[-1].weight == pytest.approx(1.0)


@pytest.mark.parametrize(
    ("alg_key", "catalog_ref", "alg_param"),
    [
        (
            "cross_sectional_momentum",
            "algorithm:16",
            {
                "rows": _load_cross_sectional_momentum_fixture_rows(
                    "cross_sectional_ranking.csv"
                ),
                "lookback_window": 1,
                "top_n": 2,
                "bottom_n": 0,
                "rebalance_frequency": "monthly",
                "long_only": True,
            },
        ),
        (
            "relative_strength_momentum",
            "algorithm:17",
            {
                "rows": _load_cross_sectional_momentum_fixture_rows(
                    "cross_sectional_ranking.csv"
                ),
                "lookback_window": 1,
                "top_n": 2,
                "bottom_n": 0,
                "rebalance_frequency": "monthly",
                "long_only": True,
            },
        ),
        (
            "dual_momentum",
            "algorithm:18",
            {
                "rows": _load_cross_sectional_momentum_fixture_rows(
                    "cross_sectional_ranking.csv"
                ),
                "lookback_window": 1,
                "top_n": 1,
                "bottom_n": 0,
                "rebalance_frequency": "monthly",
                "long_only": True,
                "absolute_momentum_threshold": 0.0,
                "defensive_symbol": "BIL",
            },
        ),
        (
            "residual_momentum",
            "algorithm:19",
            {
                "rows": _load_cross_sectional_momentum_fixture_rows(
                    "cross_sectional_ranking.csv"
                ),
                "lookback_window": 1,
                "top_n": 2,
                "bottom_n": 0,
                "rebalance_frequency": "monthly",
                "long_only": True,
                "score_adjustments": {"BBB": 5.0, "AAA": -1.0},
            },
        ),
    ],
)
def test_momentum_wave_3_normalized_output_metadata_exposes_dashboard_contract_fields(
    tmp_path, alg_key, catalog_ref, alg_param
) -> None:
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "UNIVERSE",
            "alg_key": alg_key,
            "alg_param": alg_param,
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    child_output = output.child_outputs[0]

    assert output.metadata["family"] == "momentum"
    assert output.metadata["reporting_mode"] == "rebalance_report"
    assert output.metadata["catalog_ref"] == catalog_ref
    assert child_output.diagnostics["family"] == "momentum"
    assert child_output.diagnostics["reporting_mode"] == "rebalance_report"
    assert child_output.diagnostics["catalog_ref"] == catalog_ref
    assert {
        "selected_symbols",
        "weights",
        "eligible_universe_size",
        "selection_reason",
        "warmup_ready",
    }.issubset(child_output.diagnostics.keys())
    assert child_output.reason_codes == tuple(child_output.diagnostics["reason_codes"])


def test_momentum_wave_3_performance_smoke_on_fixture_repetition(tmp_path) -> None:
    rows = (
        _load_cross_sectional_momentum_fixture_rows("cross_sectional_ranking.csv") * 50
    )
    algorithms = [
        (
            "cross_sectional_momentum",
            {
                "rows": rows,
                "lookback_window": 1,
                "top_n": 2,
                "bottom_n": 0,
                "rebalance_frequency": "monthly",
                "long_only": True,
            },
        ),
        (
            "relative_strength_momentum",
            {
                "rows": rows,
                "lookback_window": 1,
                "top_n": 2,
                "bottom_n": 0,
                "rebalance_frequency": "monthly",
                "long_only": True,
            },
        ),
        (
            "dual_momentum",
            {
                "rows": rows,
                "lookback_window": 1,
                "top_n": 1,
                "bottom_n": 0,
                "rebalance_frequency": "monthly",
                "long_only": True,
                "absolute_momentum_threshold": 0.0,
                "defensive_symbol": "BIL",
            },
        ),
        (
            "residual_momentum",
            {
                "rows": rows,
                "lookback_window": 1,
                "top_n": 2,
                "bottom_n": 0,
                "rebalance_frequency": "monthly",
                "long_only": True,
                "score_adjustments": {"BBB": 5.0, "AAA": -1.0},
            },
        ),
    ]

    for index, (alg_key, alg_param) in enumerate(algorithms):
        algorithm, _ = create_alertgen_algorithm(
            sensor_config={
                "symbol": "UNIVERSE",
                "alg_key": alg_key,
                "alg_param": alg_param,
                "buy": True,
                "sell": False,
            },
            report_base_path=str(tmp_path / str(index)),
        )
        output = algorithm.normalized_output()

        assert output.metadata["warmup_period"] == algorithm.minimum_history()
        assert output.metadata["reporting_mode"] == "rebalance_report"
        assert len(output.points) >= 1


@pytest.mark.parametrize(
    ("alg_key", "field_names", "expected_catalog_ref", "expected_top_symbol"),
    [
        (
            "low_volatility_strategy",
            ["volatility_20d", "realized_volatility"],
            "algorithm:100",
            "AAA",
        ),
        (
            "low_beta_betting_against_beta",
            ["beta_252d", "market_beta"],
            "algorithm:103",
            "AAA",
        ),
        (
            "dividend_yield_strategy",
            ["dividend_yield", "forward_dividend_yield"],
            "algorithm:107",
            "CCC",
        ),
        (
            "growth_factor_strategy",
            ["earnings_growth", "sales_growth"],
            "algorithm:108",
            "AAA",
        ),
        (
            "liquidity_factor_strategy",
            ["liquidity_score", "turnover_ratio"],
            "algorithm:109",
            "AAA",
        ),
    ],
)
def test_factor_wave_1_registration_and_fixture_behavior(
    tmp_path, alg_key, field_names, expected_catalog_ref, expected_top_symbol
) -> None:
    spec = get_alert_algorithm_spec_by_key(alg_key)
    assert spec.catalog_ref == expected_catalog_ref
    assert spec.family == "factor_risk_premia"
    assert spec.output_modes == ("ranking", "selection", "weights", "diagnostics")

    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "UNIVERSE",
            "alg_key": alg_key,
            "alg_param": {
                "rows": _build_factor_fixture_rows(),
                "field_names": field_names,
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    portfolio_output = algorithm.portfolio_output()
    child_output = output.child_outputs[0]

    assert output.points[-1].signal_label == "buy"
    assert output.derived_series["top_symbol"][-1] == expected_top_symbol
    assert output.metadata["reporting_mode"] == "rebalance_report"
    assert output.metadata["family"] == "factor_risk_premia"
    assert output.metadata["catalog_ref"] == expected_catalog_ref
    assert portfolio_output.metadata["catalog_ref"] == expected_catalog_ref
    assert portfolio_output.rebalances[-1].ranking[0].symbol == expected_top_symbol
    assert (
        portfolio_output.rebalances[-1].diagnostics["top_ranked_symbol"]
        == expected_top_symbol
    )
    assert child_output.diagnostics["catalog_ref"] == expected_catalog_ref
    assert child_output.diagnostics["family"] == "factor_risk_premia"
    assert child_output.diagnostics["reporting_mode"] == "rebalance_report"
    assert child_output.diagnostics["selected_symbols"]
    assert child_output.reason_codes == tuple(child_output.diagnostics["reason_codes"])
    assert {
        "selection_strength",
        "gross_exposure",
        "net_exposure",
        "long_count",
        "short_count",
    }.issubset(output.derived_series)
    assert output.derived_series["selection_strength"][-1] == pytest.approx(
        child_output.diagnostics["selection_strength"]
    )
    assert output.derived_series["gross_exposure"][-1] == pytest.approx(1.0)
    assert output.derived_series["net_exposure"][-1] == pytest.approx(1.0)
    assert output.derived_series["long_count"][-1] == 2
    assert output.derived_series["short_count"][-1] == 0
    assert 0.0 <= output.points[-1].score <= 1.0
    assert output.points[-1].confidence == output.points[-1].score


def test_factor_wave_1_short_history_stays_neutral_until_minimum_universe_ready(
    tmp_path,
) -> None:
    rows = _build_factor_fixture_rows()[:1]
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "UNIVERSE",
            "alg_key": "low_volatility_strategy",
            "alg_param": {
                "rows": rows,
                "field_names": ["volatility_20d", "realized_volatility"],
                "rebalance_frequency": "monthly",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    portfolio_output = algorithm.portfolio_output()

    assert all(point.signal_label == "neutral" for point in output.points)
    assert output.points[-1].reason_codes == ("warmup_pending",)
    assert output.derived_series["warmup_ready"][-1] is False
    assert output.derived_series["selection_strength"][-1] == pytest.approx(0.0)
    assert portfolio_output.rebalances[-1].selected_symbols == ()
    assert (
        portfolio_output.rebalances[-1].diagnostics["selection_reason"]
        == "warmup_pending"
    )
    assert portfolio_output.rebalances[-1].diagnostics["missing_metric_symbols"] == ()


def test_factor_wave_1_validation_rejects_invalid_parameter_shapes() -> None:
    with pytest.raises(ValueError, match="field_names must contain at least 1 items"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "UNIVERSE",
                "alg_key": "growth_factor_strategy",
                "alg_param": {
                    "rows": _build_factor_fixture_rows(),
                    "field_names": [],
                    "rebalance_frequency": "monthly",
                    "top_n": 2,
                    "long_only": True,
                    "minimum_universe_size": 2,
                },
                "buy": True,
                "sell": False,
            }
        )

    with pytest.raises(ValueError, match="minimum_universe_size must be > 0"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "UNIVERSE",
                "alg_key": "low_beta_betting_against_beta",
                "alg_param": {
                    "rows": _build_factor_fixture_rows(),
                    "field_names": ["beta_252d"],
                    "rebalance_frequency": "monthly",
                    "top_n": 2,
                    "bottom_n": 0,
                    "long_only": True,
                    "minimum_universe_size": 0,
                },
                "buy": True,
                "sell": False,
            }
        )

    with pytest.raises(
        ValueError, match="rebalance_frequency must be one of: all, monthly, weekly"
    ):
        normalize_alertgen_sensor_config(
            {
                "symbol": "UNIVERSE",
                "alg_key": "dividend_yield_strategy",
                "alg_param": {
                    "rows": _build_factor_fixture_rows(),
                    "field_names": ["dividend_yield"],
                    "rebalance_frequency": "quarterly",
                    "top_n": 2,
                    "bottom_n": 0,
                    "long_only": True,
                    "minimum_universe_size": 2,
                },
                "buy": True,
                "sell": False,
            }
        )

    with pytest.raises(ValueError, match="bottom_n must be 0 when long_only is true"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "UNIVERSE",
                "alg_key": "liquidity_factor_strategy",
                "alg_param": {
                    "rows": _build_factor_fixture_rows(),
                    "field_names": ["liquidity_score"],
                    "rebalance_frequency": "monthly",
                    "top_n": 2,
                    "bottom_n": 1,
                    "long_only": True,
                    "minimum_universe_size": 2,
                },
                "buy": True,
                "sell": False,
            }
        )


def test_factor_wave_1_fixture_behavior_matches_manifest_expectations(tmp_path) -> None:
    rows = _load_factor_fixture_rows("monthly_rebalance.csv")
    algorithms = [
        (
            "low_volatility_strategy",
            ["volatility_20d", "realized_volatility"],
            "AAA",
            "BBB",
        ),
        ("low_beta_betting_against_beta", ["beta_252d", "market_beta"], "AAA", "BBB"),
        (
            "dividend_yield_strategy",
            ["dividend_yield", "forward_dividend_yield"],
            "CCC",
            "CCC",
        ),
        ("growth_factor_strategy", ["earnings_growth", "sales_growth"], "AAA", "BBB"),
        (
            "liquidity_factor_strategy",
            ["liquidity_score", "turnover_ratio"],
            "AAA",
            "BBB",
        ),
    ]

    for index, (
        alg_key,
        field_names,
        expected_first_top,
        expected_second_top,
    ) in enumerate(algorithms):
        algorithm, _ = create_alertgen_algorithm(
            sensor_config={
                "symbol": "UNIVERSE",
                "alg_key": alg_key,
                "alg_param": {
                    "rows": rows,
                    "field_names": field_names,
                    "rebalance_frequency": "monthly",
                    "top_n": 2,
                    "bottom_n": 0,
                    "long_only": True,
                    "minimum_universe_size": 2,
                },
                "buy": True,
                "sell": False,
            },
            report_base_path=str(tmp_path / f"fixture_{index}"),
        )

        output = algorithm.normalized_output()
        portfolio_output = algorithm.portfolio_output()
        payloads = algorithm.interactive_report_payloads()

        assert [point.timestamp for point in output.points] == [
            "2025-01-02",
            "2025-02-03",
        ]
        assert [rebalance.timestamp for rebalance in portfolio_output.rebalances] == [
            "2025-01-02",
            "2025-02-03",
        ]
        assert [point.signal_label for point in output.points] == ["buy", "buy"]
        assert output.derived_series["top_symbol"] == [
            expected_first_top,
            expected_second_top,
        ]
        assert output.derived_series["warmup_ready"] == [True, True]
        assert all(
            reason == "selection_ready"
            for reason in output.derived_series["selection_reason"]
        )
        assert all(
            count == 4 for count in output.derived_series["eligible_universe_size"]
        )
        assert all(
            count == 4 for count in output.derived_series["scored_universe_size"]
        )
        assert all(
            value == pytest.approx(1.0)
            for value in output.derived_series["gross_exposure"]
        )
        assert all(
            value == pytest.approx(1.0)
            for value in output.derived_series["net_exposure"]
        )
        assert all(value == 2 for value in output.derived_series["long_count"])
        assert all(value == 0 for value in output.derived_series["short_count"])
        assert all(
            0.0 <= value <= 1.0 for value in output.derived_series["selection_strength"]
        )
        assert (
            payloads[0][0]["portfolio"]["rebalances"][-1]["diagnostics"][
                "top_ranked_symbol"
            ]
            == expected_second_top
        )
        assert (
            payloads[0][0]["data"]["metadata"]["reporting_mode"] == "rebalance_report"
        )
        assert (
            payloads[0][0]["portfolio"]["metadata"]["reporting_mode"]
            == "rebalance_report"
        )
        assert payloads[0][0]["data"]["derived_series"]["top_symbol"] == [
            expected_first_top,
            expected_second_top,
        ]


def test_factor_wave_1_fixture_behavior_exposes_dashboard_diagnostics_and_weight_contract(
    tmp_path,
) -> None:
    rows = _load_factor_fixture_rows("monthly_rebalance.csv")
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "UNIVERSE",
            "alg_key": "low_volatility_strategy",
            "alg_param": {
                "rows": rows,
                "field_names": ["volatility_20d", "realized_volatility"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    portfolio_output = algorithm.portfolio_output()
    child_output = output.child_outputs[0]
    latest_rebalance = portfolio_output.rebalances[-1]

    assert output.summary_metrics == {"rebalance_count": 2, "selection_count": 2}
    assert output.derived_series["selected_symbols"][-1] == ["BBB", "CCC"]
    assert output.derived_series["selected_count"][-1] == 2
    assert output.derived_series["weights"][-1] == {
        "BBB": pytest.approx(0.5),
        "CCC": pytest.approx(0.5),
    }
    assert latest_rebalance.weights == {
        "BBB": pytest.approx(0.5),
        "CCC": pytest.approx(0.5),
    }
    assert latest_rebalance.diagnostics["factor_name"] == "low_volatility"
    assert latest_rebalance.diagnostics["field_names"] == (
        "volatility_20d",
        "realized_volatility",
    )
    assert latest_rebalance.diagnostics["top_ranked_symbol"] == "BBB"
    assert latest_rebalance.diagnostics["top_ranked_score"] == pytest.approx(-0.115)
    assert latest_rebalance.diagnostics["raw_scores"]["BBB"] == pytest.approx(0.115)
    assert latest_rebalance.diagnostics["normalized_scores"]["BBB"] == pytest.approx(
        -0.115
    )
    assert child_output.diagnostics["weights"] == {
        "BBB": pytest.approx(0.5),
        "CCC": pytest.approx(0.5),
    }
    assert child_output.diagnostics["selected_symbols"] == ["BBB", "CCC"]
    assert child_output.diagnostics["selection_reason"] == "selection_ready"
    assert child_output.diagnostics["warmup_ready"] is True


def test_factor_wave_1_weekly_rebalance_uses_calendar_weeks(tmp_path) -> None:
    rows = [
        {
            "ts": "2025-01-31",
            "symbol": "AAA",
            "Close": 100.0,
            "volatility_20d": 0.10,
            "realized_volatility": 0.10,
        },
        {
            "ts": "2025-01-31",
            "symbol": "BBB",
            "Close": 100.0,
            "volatility_20d": 0.20,
            "realized_volatility": 0.20,
        },
        {
            "ts": "2025-02-03",
            "symbol": "AAA",
            "Close": 101.0,
            "volatility_20d": 0.12,
            "realized_volatility": 0.12,
        },
        {
            "ts": "2025-02-03",
            "symbol": "BBB",
            "Close": 99.0,
            "volatility_20d": 0.18,
            "realized_volatility": 0.18,
        },
    ]
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "UNIVERSE",
            "alg_key": "low_volatility_strategy",
            "alg_param": {
                "rows": rows,
                "field_names": ["volatility_20d", "realized_volatility"],
                "rebalance_frequency": "weekly",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()

    assert [point.timestamp for point in output.points] == ["2025-01-31", "2025-02-03"]
    assert output.derived_series["top_symbol"] == ["AAA", "AAA"]


def test_factor_wave_1_performance_smoke_on_fixture_repetition(tmp_path) -> None:
    rows = _build_factor_fixture_rows() * 50
    algorithms = [
        ("low_volatility_strategy", ["volatility_20d", "realized_volatility"]),
        ("low_beta_betting_against_beta", ["beta_252d", "market_beta"]),
        ("dividend_yield_strategy", ["dividend_yield", "forward_dividend_yield"]),
        ("growth_factor_strategy", ["earnings_growth", "sales_growth"]),
        ("liquidity_factor_strategy", ["liquidity_score", "turnover_ratio"]),
    ]

    for index, (alg_key, field_names) in enumerate(algorithms):
        algorithm, _ = create_alertgen_algorithm(
            sensor_config={
                "symbol": "UNIVERSE",
                "alg_key": alg_key,
                "alg_param": {
                    "rows": rows,
                    "field_names": field_names,
                    "rebalance_frequency": "monthly",
                    "top_n": 2,
                    "bottom_n": 0,
                    "long_only": True,
                    "minimum_universe_size": 2,
                },
                "buy": True,
                "sell": False,
            },
            report_base_path=str(tmp_path / str(index)),
        )
        output = algorithm.normalized_output()

        assert output.metadata["warmup_period"] == algorithm.minimum_history()
        assert output.metadata["reporting_mode"] == "rebalance_report"
        assert len(output.points) >= 1


@pytest.mark.parametrize(
    (
        "alg_key",
        "field_names",
        "expected_catalog_ref",
        "expected_family",
        "expected_first_top",
        "expected_second_top",
    ),
    [
        (
            "value_strategy",
            ["price_to_book", "price_to_earnings"],
            "algorithm:86",
            "fundamental_ml_composite",
            "AAA",
            "BBB",
        ),
        (
            "quality_strategy",
            ["return_on_equity", "gross_margin"],
            "algorithm:87",
            "fundamental_ml_composite",
            "AAA",
            "BBB",
        ),
        (
            "minimum_variance_strategy",
            ["volatility_20d", "realized_volatility"],
            "algorithm:101",
            "factor_risk_premia",
            "AAA",
            "BBB",
        ),
        (
            "size_small_cap_strategy",
            ["market_cap_billions"],
            "algorithm:105",
            "factor_risk_premia",
            "DDD",
            "DDD",
        ),
        (
            "mid_cap_tilt_strategy",
            ["market_cap_billions"],
            "algorithm:106",
            "factor_risk_premia",
            "CCC",
            "CCC",
        ),
        (
            "profitability_factor_strategy",
            ["return_on_assets", "gross_profitability"],
            "algorithm:110",
            "factor_risk_premia",
            "AAA",
            "BBB",
        ),
        (
            "earnings_quality_strategy",
            ["cash_earnings_ratio", "earnings_stability"],
            "algorithm:111",
            "factor_risk_premia",
            "AAA",
            "BBB",
        ),
        (
            "low_leverage_balance_sheet_strength",
            ["debt_to_equity", "net_debt_to_ebitda"],
            "algorithm:113",
            "factor_risk_premia",
            "AAA",
            "BBB",
        ),
    ],
)
def test_factor_wave_2_registration_and_fixture_behavior(
    tmp_path,
    alg_key,
    field_names,
    expected_catalog_ref,
    expected_family,
    expected_first_top,
    expected_second_top,
) -> None:
    spec = get_alert_algorithm_spec_by_key(alg_key)
    assert spec.catalog_ref == expected_catalog_ref
    assert spec.family == expected_family
    assert spec.output_modes == ("ranking", "selection", "weights", "diagnostics")

    rows = _load_factor_fixture_rows("monthly_rebalance.csv")
    alg_param = {
        "rows": rows,
        "field_names": field_names,
        "rebalance_frequency": "monthly",
        "top_n": 2,
        "bottom_n": 0,
        "long_only": True,
        "minimum_universe_size": 2,
    }
    if alg_key == "minimum_variance_strategy":
        alg_param["weighting_mode"] = "inverse_metric"
    if alg_key == "mid_cap_tilt_strategy":
        alg_param["target_value"] = 10.0

    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "UNIVERSE",
            "alg_key": alg_key,
            "alg_param": alg_param,
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    portfolio_output = algorithm.portfolio_output()
    child_output = output.child_outputs[0]

    assert [point.signal_label for point in output.points] == ["buy", "buy"]
    assert output.derived_series["top_symbol"] == [
        expected_first_top,
        expected_second_top,
    ]
    assert output.metadata["catalog_ref"] == expected_catalog_ref
    assert output.metadata["family"] == expected_family
    assert portfolio_output.metadata["catalog_ref"] == expected_catalog_ref
    assert portfolio_output.metadata["family"] == expected_family
    assert child_output.diagnostics["catalog_ref"] == expected_catalog_ref
    assert child_output.diagnostics["family"] == expected_family
    assert child_output.diagnostics["selected_symbols"]
    assert child_output.reason_codes == tuple(child_output.diagnostics["reason_codes"])
    assert portfolio_output.rebalances[0].ranking[0].symbol == expected_first_top
    assert portfolio_output.rebalances[-1].ranking[0].symbol == expected_second_top

    if alg_key == "minimum_variance_strategy":
        weights = portfolio_output.rebalances[-1].weights
        assert weights["BBB"] > weights["CCC"]
        assert child_output.diagnostics["weighting_mode"] == "inverse_metric"
    if alg_key == "mid_cap_tilt_strategy":
        assert child_output.diagnostics["target_value"] == pytest.approx(10.0)
        assert portfolio_output.rebalances[-1].diagnostics[
            "top_ranked_score"
        ] == pytest.approx(-1.0)


def test_factor_wave_2_validation_rejects_invalid_parameter_shapes() -> None:
    with pytest.raises(ValueError, match="weighting_mode must be one of"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "UNIVERSE",
                "alg_key": "minimum_variance_strategy",
                "alg_param": {
                    "rows": _build_factor_fixture_rows(),
                    "field_names": ["volatility_20d"],
                    "rebalance_frequency": "monthly",
                    "top_n": 2,
                    "bottom_n": 0,
                    "long_only": True,
                    "minimum_universe_size": 2,
                    "weighting_mode": "risk_parity",
                },
                "buy": True,
                "sell": False,
            }
        )

    with pytest.raises(ValueError, match="target_value must be a number"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "UNIVERSE",
                "alg_key": "mid_cap_tilt_strategy",
                "alg_param": {
                    "rows": _build_factor_fixture_rows(),
                    "field_names": ["market_cap_billions"],
                    "rebalance_frequency": "monthly",
                    "top_n": 2,
                    "bottom_n": 0,
                    "long_only": True,
                    "minimum_universe_size": 2,
                    "target_value": "mid",
                },
                "buy": True,
                "sell": False,
            }
        )


def test_factor_wave_2_fixture_behavior_exposes_normalized_diagnostics_and_composition_contract(
    tmp_path,
) -> None:
    rows = _load_factor_fixture_rows("monthly_rebalance.csv")
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "UNIVERSE",
            "alg_key": "quality_strategy",
            "alg_param": {
                "rows": rows,
                "field_names": ["return_on_equity", "gross_margin"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    portfolio_output = algorithm.portfolio_output()
    child_output = output.child_outputs[0]

    assert output.summary_metrics == {"rebalance_count": 2, "selection_count": 2}
    assert output.derived_series["selected_symbols"][-1] == ["BBB", "CCC"]
    assert output.derived_series["weights"][-1] == {
        "BBB": pytest.approx(0.5),
        "CCC": pytest.approx(0.5),
    }
    assert portfolio_output.rebalances[-1].diagnostics["factor_name"] == "quality"
    assert portfolio_output.rebalances[-1].diagnostics["top_ranked_symbol"] == "BBB"
    assert child_output.diagnostics["family"] == "fundamental_ml_composite"
    assert child_output.diagnostics["selection_reason"] == "selection_ready"
    assert child_output.diagnostics["warmup_ready"] is True
    assert output.derived_series["raw_scores"][-1]["BBB"] == pytest.approx(0.38)
    assert output.derived_series["normalized_scores"][-1]["BBB"] == pytest.approx(0.38)
    assert output.derived_series["missing_metric_symbols"][-1] == []


def test_factor_wave_2_fixture_behavior_matches_manifest_expectations(tmp_path) -> None:
    rows = _load_factor_fixture_rows("monthly_rebalance.csv")
    expected_top_symbols = {
        "value_strategy": ["AAA", "BBB"],
        "quality_strategy": ["AAA", "BBB"],
        "minimum_variance_strategy": ["AAA", "BBB"],
        "size_small_cap_strategy": ["DDD", "DDD"],
        "mid_cap_tilt_strategy": ["CCC", "CCC"],
        "profitability_factor_strategy": ["AAA", "BBB"],
        "earnings_quality_strategy": ["AAA", "BBB"],
        "low_leverage_balance_sheet_strength": ["AAA", "BBB"],
    }

    for alg_key, expected in expected_top_symbols.items():
        field_names = {
            "value_strategy": ["price_to_book", "price_to_earnings"],
            "quality_strategy": ["return_on_equity", "gross_margin"],
            "minimum_variance_strategy": ["volatility_20d", "realized_volatility"],
            "size_small_cap_strategy": ["market_cap_billions"],
            "mid_cap_tilt_strategy": ["market_cap_billions"],
            "profitability_factor_strategy": [
                "return_on_assets",
                "gross_profitability",
            ],
            "earnings_quality_strategy": ["cash_earnings_ratio", "earnings_stability"],
            "low_leverage_balance_sheet_strength": [
                "debt_to_equity",
                "net_debt_to_ebitda",
            ],
        }[alg_key]
        extra_params: dict[str, Any] = {}
        if alg_key == "minimum_variance_strategy":
            extra_params["weighting_mode"] = "inverse_metric"
        if alg_key == "mid_cap_tilt_strategy":
            extra_params["target_value"] = 10.0

        algorithm, _ = create_alertgen_algorithm(
            sensor_config={
                "symbol": "UNIVERSE",
                "alg_key": alg_key,
                "alg_param": {
                    "rows": rows,
                    "field_names": field_names,
                    "rebalance_frequency": "monthly",
                    "top_n": 2,
                    "bottom_n": 0,
                    "long_only": True,
                    "minimum_universe_size": 2,
                    **extra_params,
                },
                "buy": True,
                "sell": False,
            },
            report_base_path=str(tmp_path / alg_key),
        )

        output = algorithm.normalized_output()
        assert output.derived_series["top_symbol"] == expected

    low_vol_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "UNIVERSE",
            "alg_key": "minimum_variance_strategy",
            "alg_param": {
                "rows": rows,
                "field_names": ["volatility_20d", "realized_volatility"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
                "weighting_mode": "inverse_metric",
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path / "minimum-variance-explicit"),
    )
    min_var_output = low_vol_algorithm.normalized_output()
    assert min_var_output.derived_series["top_symbol"] == ["AAA", "BBB"]


def test_factor_wave_2_short_history_reports_warmup_reason_and_missing_symbols(
    tmp_path,
) -> None:
    rows = [
        {
            "ts": "2025-01-02",
            "symbol": "AAA",
            "Close": 100.0,
            "return_on_equity": 0.24,
            "gross_margin": 0.48,
        },
        {
            "ts": "2025-01-02",
            "symbol": "BBB",
            "Close": 100.0,
        },
    ]
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "UNIVERSE",
            "alg_key": "quality_strategy",
            "alg_param": {
                "rows": rows,
                "field_names": ["return_on_equity", "gross_margin"],
                "rebalance_frequency": "monthly",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    child_output = output.child_outputs[0]

    assert output.points[-1].signal_label == "neutral"
    assert output.points[-1].reason_codes == ("warmup_pending",)
    assert output.derived_series["warmup_ready"][-1] is False
    assert output.derived_series["scored_universe_size"][-1] == 1
    assert output.derived_series["missing_metric_symbols"][-1] == ["BBB"]
    assert child_output.diagnostics["selection_reason"] == "warmup_pending"
    assert child_output.diagnostics["missing_metric_symbols"] == ("BBB",)


def test_factor_wave_2_performance_smoke_on_fixture_repetition(tmp_path) -> None:
    rows = _build_factor_fixture_rows() * 50
    algorithms: list[tuple[str, list[str], dict[str, Any]]] = [
        (
            "value_strategy",
            ["price_to_book", "price_to_earnings"],
            {},
        ),
        (
            "quality_strategy",
            ["return_on_equity", "gross_margin"],
            {},
        ),
        (
            "minimum_variance_strategy",
            ["volatility_20d", "realized_volatility"],
            {"weighting_mode": "inverse_metric"},
        ),
        (
            "size_small_cap_strategy",
            ["market_cap_billions"],
            {},
        ),
        (
            "mid_cap_tilt_strategy",
            ["market_cap_billions"],
            {"target_value": 10.0},
        ),
        (
            "profitability_factor_strategy",
            ["return_on_assets", "gross_profitability"],
            {},
        ),
        (
            "earnings_quality_strategy",
            ["cash_earnings_ratio", "earnings_stability"],
            {},
        ),
        (
            "low_leverage_balance_sheet_strength",
            ["debt_to_equity", "net_debt_to_ebitda"],
            {},
        ),
    ]

    for index, (alg_key, field_names, extra_params) in enumerate(algorithms):
        algorithm, _ = create_alertgen_algorithm(
            sensor_config={
                "symbol": "UNIVERSE",
                "alg_key": alg_key,
                "alg_param": {
                    "rows": rows,
                    "field_names": field_names,
                    "rebalance_frequency": "monthly",
                    "top_n": 2,
                    "bottom_n": 0,
                    "long_only": True,
                    "minimum_universe_size": 2,
                    **extra_params,
                },
                "buy": True,
                "sell": False,
            },
            report_base_path=str(tmp_path / str(index)),
        )
        output = algorithm.normalized_output()

        assert output.metadata["warmup_period"] == algorithm.minimum_history()
        assert output.metadata["reporting_mode"] == "rebalance_report"
        assert len(output.points) >= 1


@pytest.mark.parametrize(
    (
        "alg_key",
        "field_names",
        "expected_catalog_ref",
        "expected_family",
        "expected_first_top",
        "expected_second_top",
        "extra_params",
    ),
    [
        (
            "multi_factor_composite",
            [
                "price_to_book",
                "price_to_earnings",
                "return_on_equity",
                "gross_margin",
                "volatility_20d",
                "realized_volatility",
            ],
            "algorithm:88",
            "fundamental_ml_composite",
            "AAA",
            "BBB",
            {
                "field_weights": [0.20, 0.15, 0.20, 0.15, 0.15, 0.15],
                "lower_is_better_fields": [
                    "price_to_book",
                    "price_to_earnings",
                    "volatility_20d",
                    "realized_volatility",
                ],
            },
        ),
        (
            "residual_volatility_strategy",
            ["beta_252d", "volatility_20d", "realized_volatility"],
            "algorithm:102",
            "factor_risk_premia",
            "AAA",
            "BBB",
            {
                "field_weights": [0.25, 0.35, 0.40],
                "lower_is_better_fields": [
                    "beta_252d",
                    "volatility_20d",
                    "realized_volatility",
                ],
            },
        ),
        (
            "defensive_equity_strategy",
            [
                "volatility_20d",
                "beta_252d",
                "cash_earnings_ratio",
                "earnings_stability",
            ],
            "algorithm:104",
            "factor_risk_premia",
            "AAA",
            "BBB",
            {
                "field_weights": [0.30, 0.20, 0.25, 0.25],
                "lower_is_better_fields": ["volatility_20d", "beta_252d"],
            },
        ),
        (
            "investment_quality_strategy",
            [
                "debt_to_equity",
                "net_debt_to_ebitda",
                "return_on_assets",
                "gross_profitability",
            ],
            "algorithm:112",
            "factor_risk_premia",
            "AAA",
            "BBB",
            {
                "field_weights": [0.25, 0.20, 0.25, 0.30],
                "lower_is_better_fields": ["debt_to_equity", "net_debt_to_ebitda"],
            },
        ),
        (
            "earnings_stability_low_earnings_variability",
            ["earnings_stability", "cash_earnings_ratio"],
            "algorithm:114",
            "factor_risk_premia",
            "AAA",
            "BBB",
            {"field_weights": [0.65, 0.35]},
        ),
    ],
)
def test_factor_wave_3_registration_and_fixture_behavior(
    tmp_path,
    alg_key,
    field_names,
    expected_catalog_ref,
    expected_family,
    expected_first_top,
    expected_second_top,
    extra_params,
) -> None:
    spec = get_alert_algorithm_spec_by_key(alg_key)
    assert spec.catalog_ref == expected_catalog_ref
    assert spec.family == expected_family
    assert spec.output_modes == ("ranking", "selection", "weights", "diagnostics")

    rows = _load_factor_fixture_rows("monthly_rebalance.csv")
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "UNIVERSE",
            "alg_key": alg_key,
            "alg_param": {
                "rows": rows,
                "field_names": field_names,
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
                **extra_params,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    portfolio_output = algorithm.portfolio_output()
    child_output = output.child_outputs[0]

    assert [point.signal_label for point in output.points] == ["buy", "buy"]
    assert output.derived_series["top_symbol"] == [
        expected_first_top,
        expected_second_top,
    ]
    assert output.metadata["catalog_ref"] == expected_catalog_ref
    assert output.metadata["family"] == expected_family
    assert portfolio_output.metadata["catalog_ref"] == expected_catalog_ref
    assert portfolio_output.metadata["family"] == expected_family
    assert child_output.diagnostics["catalog_ref"] == expected_catalog_ref
    assert child_output.diagnostics["family"] == expected_family
    assert child_output.diagnostics["selected_symbols"]
    assert child_output.reason_codes == tuple(child_output.diagnostics["reason_codes"])
    assert portfolio_output.rebalances[0].ranking[0].symbol == expected_first_top
    assert portfolio_output.rebalances[-1].ranking[0].symbol == expected_second_top
    assert "component_scores" in output.derived_series
    assert "oriented_component_scores" in output.derived_series
    assert output.derived_series["component_scores"][-1][expected_second_top]
    assert output.derived_series["oriented_component_scores"][-1][expected_second_top]
    if "field_weights" in extra_params:
        assert child_output.diagnostics["field_weights"] == tuple(
            extra_params["field_weights"]
        )
    if "lower_is_better_fields" in extra_params:
        assert child_output.diagnostics["lower_is_better_fields"] == tuple(
            sorted(extra_params["lower_is_better_fields"])
        )


def test_factor_wave_3_validation_rejects_invalid_parameter_shapes() -> None:
    with pytest.raises(ValueError, match="field_weights must match field_names length"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "UNIVERSE",
                "alg_key": "multi_factor_composite",
                "alg_param": {
                    "rows": _build_factor_fixture_rows(),
                    "field_names": ["price_to_book", "price_to_earnings"],
                    "field_weights": [1.0],
                    "rebalance_frequency": "monthly",
                    "top_n": 2,
                    "bottom_n": 0,
                    "long_only": True,
                    "minimum_universe_size": 2,
                },
                "buy": True,
                "sell": False,
            }
        )

    with pytest.raises(
        ValueError, match="lower_is_better_fields must be a subset of field_names"
    ):
        normalize_alertgen_sensor_config(
            {
                "symbol": "UNIVERSE",
                "alg_key": "residual_volatility_strategy",
                "alg_param": {
                    "rows": _build_factor_fixture_rows(),
                    "field_names": ["beta_252d", "volatility_20d"],
                    "field_weights": [0.5, 0.5],
                    "lower_is_better_fields": ["beta_252d", "missing_field"],
                    "rebalance_frequency": "monthly",
                    "top_n": 2,
                    "bottom_n": 0,
                    "long_only": True,
                    "minimum_universe_size": 2,
                },
                "buy": True,
                "sell": False,
            }
        )

    with pytest.raises(ValueError, match=r"field_weights\[0\] must be > 0"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "UNIVERSE",
                "alg_key": "defensive_equity_strategy",
                "alg_param": {
                    "rows": _build_factor_fixture_rows(),
                    "field_names": ["volatility_20d", "beta_252d"],
                    "field_weights": [0.0, 1.0],
                    "lower_is_better_fields": ["volatility_20d", "beta_252d"],
                    "rebalance_frequency": "monthly",
                    "top_n": 2,
                    "bottom_n": 0,
                    "long_only": True,
                    "minimum_universe_size": 2,
                },
                "buy": True,
                "sell": False,
            }
        )


def test_factor_wave_3_fixture_behavior_matches_manifest_expectations(tmp_path) -> None:
    rows = _load_factor_fixture_rows("monthly_rebalance.csv")
    expected_top_symbols = {
        "multi_factor_composite": ["AAA", "BBB"],
        "residual_volatility_strategy": ["AAA", "BBB"],
        "defensive_equity_strategy": ["AAA", "BBB"],
        "investment_quality_strategy": ["AAA", "BBB"],
        "earnings_stability_low_earnings_variability": ["AAA", "BBB"],
    }
    params_by_alg = {
        "multi_factor_composite": {
            "field_names": [
                "price_to_book",
                "price_to_earnings",
                "return_on_equity",
                "gross_margin",
                "volatility_20d",
                "realized_volatility",
            ],
            "field_weights": [0.20, 0.15, 0.20, 0.15, 0.15, 0.15],
            "lower_is_better_fields": [
                "price_to_book",
                "price_to_earnings",
                "volatility_20d",
                "realized_volatility",
            ],
        },
        "residual_volatility_strategy": {
            "field_names": ["beta_252d", "volatility_20d", "realized_volatility"],
            "field_weights": [0.25, 0.35, 0.40],
            "lower_is_better_fields": [
                "beta_252d",
                "volatility_20d",
                "realized_volatility",
            ],
        },
        "defensive_equity_strategy": {
            "field_names": [
                "volatility_20d",
                "beta_252d",
                "cash_earnings_ratio",
                "earnings_stability",
            ],
            "field_weights": [0.30, 0.20, 0.25, 0.25],
            "lower_is_better_fields": ["volatility_20d", "beta_252d"],
        },
        "investment_quality_strategy": {
            "field_names": [
                "debt_to_equity",
                "net_debt_to_ebitda",
                "return_on_assets",
                "gross_profitability",
            ],
            "field_weights": [0.25, 0.20, 0.25, 0.30],
            "lower_is_better_fields": ["debt_to_equity", "net_debt_to_ebitda"],
        },
        "earnings_stability_low_earnings_variability": {
            "field_names": ["earnings_stability", "cash_earnings_ratio"],
            "field_weights": [0.65, 0.35],
        },
    }

    for alg_key, expected in expected_top_symbols.items():
        algorithm, _ = create_alertgen_algorithm(
            sensor_config={
                "symbol": "UNIVERSE",
                "alg_key": alg_key,
                "alg_param": {
                    "rows": rows,
                    "rebalance_frequency": "monthly",
                    "top_n": 2,
                    "bottom_n": 0,
                    "long_only": True,
                    "minimum_universe_size": 2,
                    **params_by_alg[alg_key],
                },
                "buy": True,
                "sell": False,
            },
            report_base_path=str(tmp_path / alg_key),
        )

        output = algorithm.normalized_output()
        assert output.derived_series["top_symbol"] == expected


def test_factor_wave_3_diagnostics_expose_weighted_components_and_contract(
    tmp_path,
) -> None:
    rows = _load_factor_fixture_rows("monthly_rebalance.csv")
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "UNIVERSE",
            "alg_key": "multi_factor_composite",
            "alg_param": {
                "rows": rows,
                "field_names": [
                    "price_to_book",
                    "price_to_earnings",
                    "return_on_equity",
                    "gross_margin",
                    "volatility_20d",
                    "realized_volatility",
                ],
                "field_weights": [0.20, 0.15, 0.20, 0.15, 0.15, 0.15],
                "lower_is_better_fields": [
                    "price_to_book",
                    "price_to_earnings",
                    "volatility_20d",
                    "realized_volatility",
                ],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    portfolio_output = algorithm.portfolio_output()
    child_output = output.child_outputs[0]
    latest_rebalance = portfolio_output.rebalances[-1]

    assert output.summary_metrics == {"rebalance_count": 2, "selection_count": 2}
    assert output.derived_series["selected_symbols"][-1] == ["BBB", "CCC"]
    assert output.derived_series["weights"][-1] == {
        "BBB": pytest.approx(0.5),
        "CCC": pytest.approx(0.5),
    }
    assert latest_rebalance.diagnostics["field_weights"] == (
        0.20,
        0.15,
        0.20,
        0.15,
        0.15,
        0.15,
    )
    assert latest_rebalance.diagnostics["component_scores"]["BBB"][
        "return_on_equity"
    ] == pytest.approx(0.26)
    assert latest_rebalance.diagnostics["oriented_component_scores"]["BBB"][
        "price_to_book"
    ] == pytest.approx(-1.1)
    assert child_output.diagnostics["component_scores"]["BBB"][
        "gross_margin"
    ] == pytest.approx(0.50)
    assert child_output.diagnostics["lower_is_better_fields"] == (
        "price_to_book",
        "price_to_earnings",
        "realized_volatility",
        "volatility_20d",
    )


@pytest.mark.parametrize(
    (
        "alg_key",
        "field_names",
        "extra_params",
        "expected_catalog_ref",
        "expected_family",
    ),
    [
        (
            "multi_factor_composite",
            [
                "price_to_book",
                "price_to_earnings",
                "return_on_equity",
                "gross_margin",
                "volatility_20d",
                "realized_volatility",
            ],
            {
                "field_weights": [0.20, 0.15, 0.20, 0.15, 0.15, 0.15],
                "lower_is_better_fields": [
                    "price_to_book",
                    "price_to_earnings",
                    "volatility_20d",
                    "realized_volatility",
                ],
            },
            "algorithm:88",
            "fundamental_ml_composite",
        ),
        (
            "residual_volatility_strategy",
            ["beta_252d", "volatility_20d", "realized_volatility"],
            {
                "field_weights": [0.25, 0.35, 0.40],
                "lower_is_better_fields": [
                    "beta_252d",
                    "volatility_20d",
                    "realized_volatility",
                ],
            },
            "algorithm:102",
            "factor_risk_premia",
        ),
        (
            "defensive_equity_strategy",
            [
                "volatility_20d",
                "beta_252d",
                "cash_earnings_ratio",
                "earnings_stability",
            ],
            {
                "field_weights": [0.30, 0.20, 0.25, 0.25],
                "lower_is_better_fields": ["volatility_20d", "beta_252d"],
            },
            "algorithm:104",
            "factor_risk_premia",
        ),
        (
            "investment_quality_strategy",
            [
                "debt_to_equity",
                "net_debt_to_ebitda",
                "return_on_assets",
                "gross_profitability",
            ],
            {
                "field_weights": [0.25, 0.20, 0.25, 0.30],
                "lower_is_better_fields": ["debt_to_equity", "net_debt_to_ebitda"],
            },
            "algorithm:112",
            "factor_risk_premia",
        ),
        (
            "earnings_stability_low_earnings_variability",
            ["earnings_stability", "cash_earnings_ratio"],
            {"field_weights": [0.65, 0.35]},
            "algorithm:114",
            "factor_risk_premia",
        ),
    ],
)
def test_factor_wave_3_short_history_stays_neutral_until_minimum_universe_size_met(
    tmp_path,
    alg_key,
    field_names,
    extra_params,
    expected_catalog_ref,
    expected_family,
) -> None:
    rows = [
        {
            "ts": "2025-01-02",
            "symbol": "AAA",
            "Close": 100.0,
            "price_to_book": 1.2,
            "price_to_earnings": 10.0,
            "return_on_equity": 0.24,
            "gross_margin": 0.48,
            "volatility_20d": 0.10,
            "realized_volatility": 0.11,
            "beta_252d": 0.80,
            "cash_earnings_ratio": 0.92,
            "earnings_stability": 0.88,
            "debt_to_equity": 0.30,
            "net_debt_to_ebitda": 0.90,
            "return_on_assets": 0.12,
            "gross_profitability": 0.33,
        },
        {
            "ts": "2025-01-02",
            "symbol": "BBB",
            "Close": 100.0,
        },
    ]
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "UNIVERSE",
            "alg_key": alg_key,
            "alg_param": {
                "rows": rows,
                "field_names": field_names,
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
                **extra_params,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path / alg_key),
    )

    output = algorithm.normalized_output()
    portfolio_output = algorithm.portfolio_output()
    child_output = output.child_outputs[0]
    payload, payload_name = algorithm.interactive_report_payloads()[0]

    assert output.points[-1].signal_label == "neutral"
    assert output.points[-1].reason_codes == ("warmup_pending",)
    assert output.derived_series["warmup_ready"][-1] is False
    assert output.derived_series["scored_universe_size"][-1] == 1
    assert output.derived_series["eligible_universe_size"][-1] == 2
    assert output.derived_series["selected_symbols"][-1] == []
    assert output.derived_series["weights"][-1] == {}
    assert output.derived_series["selection_strength"][-1] == pytest.approx(0.0)
    assert output.derived_series["missing_metric_symbols"][-1] == ["BBB"]
    assert portfolio_output.rebalances[-1].selected_symbols == ()
    assert portfolio_output.rebalances[-1].weights == {}
    assert (
        portfolio_output.rebalances[-1].diagnostics["selection_reason"]
        == "warmup_pending"
    )
    assert portfolio_output.rebalances[-1].diagnostics["warmup_pending_symbols"] == (
        "BBB",
    )
    assert child_output.signal_label == "neutral"
    assert child_output.reason_codes == ("warmup_pending",)
    assert child_output.diagnostics["selection_reason"] == "warmup_pending"
    assert child_output.diagnostics["missing_metric_symbols"] == ("BBB",)
    assert child_output.diagnostics["catalog_ref"] == expected_catalog_ref
    assert child_output.diagnostics["family"] == expected_family
    assert output.metadata["catalog_ref"] == expected_catalog_ref
    assert output.metadata["family"] == expected_family
    assert payload_name.startswith(f"rebalance_report_{alg_key}_")
    assert payload["data"]["metadata"]["catalog_ref"] == expected_catalog_ref
    assert payload["portfolio"]["metadata"]["family"] == expected_family
    assert payload["portfolio"]["rebalances"][-1]["diagnostics"][
        "selection_reason"
    ] == ("warmup_pending")


@pytest.mark.parametrize(
    ("alg_key", "extra_params", "expected_catalog_ref", "expected_family"),
    [
        (
            "multi_factor_composite",
            {
                "field_names": [
                    "price_to_book",
                    "price_to_earnings",
                    "return_on_equity",
                    "gross_margin",
                    "volatility_20d",
                    "realized_volatility",
                ],
                "field_weights": [0.20, 0.15, 0.20, 0.15, 0.15, 0.15],
                "lower_is_better_fields": [
                    "price_to_book",
                    "price_to_earnings",
                    "volatility_20d",
                    "realized_volatility",
                ],
            },
            "algorithm:88",
            "fundamental_ml_composite",
        ),
        (
            "residual_volatility_strategy",
            {
                "field_names": ["beta_252d", "volatility_20d", "realized_volatility"],
                "field_weights": [0.25, 0.35, 0.40],
                "lower_is_better_fields": [
                    "beta_252d",
                    "volatility_20d",
                    "realized_volatility",
                ],
            },
            "algorithm:102",
            "factor_risk_premia",
        ),
        (
            "defensive_equity_strategy",
            {
                "field_names": [
                    "volatility_20d",
                    "beta_252d",
                    "cash_earnings_ratio",
                    "earnings_stability",
                ],
                "field_weights": [0.30, 0.20, 0.25, 0.25],
                "lower_is_better_fields": ["volatility_20d", "beta_252d"],
            },
            "algorithm:104",
            "factor_risk_premia",
        ),
        (
            "investment_quality_strategy",
            {
                "field_names": [
                    "debt_to_equity",
                    "net_debt_to_ebitda",
                    "return_on_assets",
                    "gross_profitability",
                ],
                "field_weights": [0.25, 0.20, 0.25, 0.30],
                "lower_is_better_fields": ["debt_to_equity", "net_debt_to_ebitda"],
            },
            "algorithm:112",
            "factor_risk_premia",
        ),
        (
            "earnings_stability_low_earnings_variability",
            {
                "field_names": ["earnings_stability", "cash_earnings_ratio"],
                "field_weights": [0.65, 0.35],
            },
            "algorithm:114",
            "factor_risk_premia",
        ),
    ],
)
def test_factor_wave_3_report_payload_exposes_dashboard_explanation_fields(
    tmp_path, alg_key, extra_params, expected_catalog_ref, expected_family
) -> None:
    rows = _load_factor_fixture_rows("monthly_rebalance.csv")
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "UNIVERSE",
            "alg_key": alg_key,
            "alg_param": {
                "rows": rows,
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
                **extra_params,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path / f"payload-{alg_key}"),
    )

    output = algorithm.normalized_output()
    portfolio_output = algorithm.portfolio_output()
    child_output = output.child_outputs[0]
    payload, payload_name = algorithm.interactive_report_payloads()[0]

    assert payload_name.startswith(f"rebalance_report_{alg_key}_")
    assert {
        "selected_symbols",
        "weights",
        "ranking",
        "selection_strength",
        "eligible_universe_size",
        "scored_universe_size",
        "gross_exposure",
        "net_exposure",
        "long_count",
        "short_count",
    }.issubset(output.derived_series)
    assert output.derived_series["gross_exposure"][-1] == pytest.approx(1.0)
    assert output.derived_series["net_exposure"][-1] == pytest.approx(1.0)
    assert 0.0 <= output.derived_series["selection_strength"][-1] <= 1.0
    assert child_output.diagnostics["selection_strength"] == pytest.approx(
        output.derived_series["selection_strength"][-1]
    )
    assert (
        child_output.diagnostics["selected_symbols"]
        == output.derived_series["selected_symbols"][-1]
    )
    assert child_output.diagnostics["weights"] == output.derived_series["weights"][-1]
    assert child_output.diagnostics["reporting_mode"] == "rebalance_report"
    assert child_output.diagnostics["catalog_ref"] == expected_catalog_ref
    assert child_output.diagnostics["family"] == expected_family
    assert (
        portfolio_output.rebalances[-1].diagnostics["top_ranked_symbol"]
        == output.derived_series["top_symbol"][-1]
    )
    assert payload["data"]["metadata"]["catalog_ref"] == expected_catalog_ref
    assert payload["data"]["metadata"]["family"] == expected_family
    assert payload["portfolio"]["metadata"]["reporting_mode"] == "rebalance_report"
    assert (
        payload["portfolio"]["rebalances"][-1]["diagnostics"]["top_ranked_symbol"]
        == output.derived_series["top_symbol"][-1]
    )
    assert payload["portfolio"]["rebalances"][-1]["diagnostics"][
        "selection_strength"
    ] == pytest.approx(output.derived_series["selection_strength"][-1])


def test_factor_wave_3_performance_smoke_on_fixture_repetition(tmp_path) -> None:
    rows = _build_factor_fixture_rows() * 50
    algorithms: list[tuple[str, dict[str, Any]]] = [
        (
            "multi_factor_composite",
            {
                "field_names": [
                    "price_to_book",
                    "price_to_earnings",
                    "return_on_equity",
                    "gross_margin",
                    "volatility_20d",
                    "realized_volatility",
                ],
                "field_weights": [0.20, 0.15, 0.20, 0.15, 0.15, 0.15],
                "lower_is_better_fields": [
                    "price_to_book",
                    "price_to_earnings",
                    "volatility_20d",
                    "realized_volatility",
                ],
            },
        ),
        (
            "residual_volatility_strategy",
            {
                "field_names": [
                    "beta_252d",
                    "volatility_20d",
                    "realized_volatility",
                ],
                "field_weights": [0.25, 0.35, 0.40],
                "lower_is_better_fields": [
                    "beta_252d",
                    "volatility_20d",
                    "realized_volatility",
                ],
            },
        ),
        (
            "defensive_equity_strategy",
            {
                "field_names": [
                    "volatility_20d",
                    "beta_252d",
                    "cash_earnings_ratio",
                    "earnings_stability",
                ],
                "field_weights": [0.30, 0.20, 0.25, 0.25],
                "lower_is_better_fields": ["volatility_20d", "beta_252d"],
            },
        ),
        (
            "investment_quality_strategy",
            {
                "field_names": [
                    "debt_to_equity",
                    "net_debt_to_ebitda",
                    "return_on_assets",
                    "gross_profitability",
                ],
                "field_weights": [0.25, 0.20, 0.25, 0.30],
                "lower_is_better_fields": ["debt_to_equity", "net_debt_to_ebitda"],
            },
        ),
        (
            "earnings_stability_low_earnings_variability",
            {
                "field_names": ["earnings_stability", "cash_earnings_ratio"],
                "field_weights": [0.65, 0.35],
            },
        ),
    ]

    for index, (alg_key, extra_params) in enumerate(algorithms):
        algorithm, _ = create_alertgen_algorithm(
            sensor_config={
                "symbol": "UNIVERSE",
                "alg_key": alg_key,
                "alg_param": {
                    "rows": rows,
                    "rebalance_frequency": "monthly",
                    "top_n": 2,
                    "bottom_n": 0,
                    "long_only": True,
                    "minimum_universe_size": 2,
                    **extra_params,
                },
                "buy": True,
                "sell": False,
            },
            report_base_path=str(tmp_path / str(index)),
        )
        output = algorithm.normalized_output()

        assert output.metadata["warmup_period"] == algorithm.minimum_history()
        assert output.metadata["reporting_mode"] == "rebalance_report"
        assert len(output.points) >= 1


@pytest.mark.parametrize(
    ("alg_key", "alg_param", "expected_warmup"),
    [
        (
            "gap_and_go",
            {
                "gap_threshold": 0.15,
                "continuation_threshold": 0.05,
                "volume_window": 3,
                "relative_volume_threshold": 1.0,
                "confirmation_bars": 1,
            },
            5,
        ),
        (
            "trendline_break_strategy",
            {
                "trendline_window": 5,
                "break_buffer": 0.1,
                "slope_tolerance": 0.0,
                "confirmation_bars": 1,
            },
            5,
        ),
        (
            "volatility_squeeze_breakout",
            {
                "squeeze_window": 5,
                "bollinger_multiplier": 2.0,
                "keltner_multiplier": 1.5,
                "breakout_buffer": 0.05,
                "confirmation_bars": 1,
            },
            6,
        ),
    ],
)
def test_pattern_wave_2_short_history_stays_neutral_until_warmup(
    tmp_path, alg_key, alg_param, expected_warmup
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

    algorithm.process_list(
        _load_pattern_fixture_rows("support_rejection.csv")[: expected_warmup - 1]
    )
    output = algorithm.normalized_output()

    assert algorithm.minimum_history() == expected_warmup
    assert output.points
    assert all(point.signal_label == "neutral" for point in output.points)
    assert any("warmup_pending" in point.reason_codes for point in output.points)
    assert output.metadata["warmup_period"] == expected_warmup


@pytest.mark.parametrize(
    (
        "alg_key",
        "alg_param",
        "expected_reason_code",
        "expected_annotation_keys",
    ),
    [
        (
            "gap_and_go",
            {
                "gap_threshold": 0.15,
                "continuation_threshold": 0.05,
                "volume_window": 3,
                "relative_volume_threshold": 1.0,
                "confirmation_bars": 1,
            },
            "awaiting_gap",
            {
                "gap_threshold",
                "continuation_threshold",
                "volume_window",
                "relative_volume_threshold",
                "gap_size",
                "continuation_amount",
                "relative_volume",
                "gap_detected",
                "continuation_confirmed",
            },
        ),
        (
            "trendline_break_strategy",
            {
                "trendline_window": 5,
                "break_buffer": 0.1,
                "slope_tolerance": 0.0,
                "confirmation_bars": 1,
            },
            "trendline_break_bullish",
            {
                "trendline_window",
                "break_buffer",
                "slope_tolerance",
                "trendline_level",
                "trendline_slope",
                "trendline_intercept",
                "break_distance",
                "trendline_break_detected",
            },
        ),
        (
            "volatility_squeeze_breakout",
            {
                "squeeze_window": 5,
                "bollinger_multiplier": 2.0,
                "keltner_multiplier": 1.5,
                "breakout_buffer": 0.05,
                "confirmation_bars": 1,
            },
            "squeeze_active",
            {
                "squeeze_window",
                "bollinger_multiplier",
                "keltner_multiplier",
                "breakout_buffer",
                "bollinger_upper",
                "bollinger_lower",
                "keltner_upper",
                "keltner_lower",
                "squeeze_on",
                "breakout_distance",
            },
        ),
    ],
)
def test_pattern_wave_2_normalized_output_exposes_dashboard_diagnostics(
    tmp_path, alg_key, alg_param, expected_reason_code, expected_annotation_keys
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

    algorithm.process_list(_load_pattern_fixture_rows("support_rejection.csv"))
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
        "exit_value",
        "confirmation_state_label",
        "warmup_ready",
    }.issubset(output.derived_series)
    assert output.metadata["family"] == "pattern_price_action"
    assert output.metadata["reporting_mode"] == "bar_series"
    assert output.metadata["catalog_ref"] == child_output.diagnostics["catalog_ref"]
    assert expected_annotation_keys.issubset(child_output.diagnostics.keys())
    assert child_output.reason_codes == tuple(child_output.diagnostics["reason_codes"])
    assert child_output.score == pytest.approx(output.derived_series["trend_score"][-1])
    assert child_output.diagnostics["trend_score"] == pytest.approx(
        output.derived_series["trend_score"][-1]
    )
    assert (
        child_output.diagnostics["threshold_value"]
        == output.derived_series["threshold_value"][-1]
    )


def test_pattern_wave_2_fixture_behavior_matches_manifest_expectations(
    tmp_path,
) -> None:
    gap_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "gap_and_go",
            "alg_param": {
                "gap_threshold": 0.15,
                "continuation_threshold": 0.05,
                "volume_window": 3,
                "relative_volume_threshold": 1.0,
                "confirmation_bars": 1,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path / "gap"),
    )
    gap_algorithm.process_list(_load_pattern_fixture_rows("support_rejection.csv"))
    gap_output = gap_algorithm.normalized_output()

    assert all(point.signal_label == "neutral" for point in gap_output.points)
    assert gap_output.points[-1].reason_codes[0] == "awaiting_gap"
    assert gap_output.derived_series["gap_detected"][-1] is False
    assert gap_output.derived_series["relative_volume"][-1] > 1.0
    assert gap_output.child_outputs[0].diagnostics["continuation_confirmed"] is False

    trendline_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "trendline_break_strategy",
            "alg_param": {
                "trendline_window": 5,
                "break_buffer": 0.1,
                "slope_tolerance": 0.0,
                "confirmation_bars": 1,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path / "trendline"),
    )
    trendline_algorithm.process_list(
        _load_pattern_fixture_rows("support_rejection.csv")
    )
    trendline_output = trendline_algorithm.normalized_output()

    assert any(point.signal_label == "buy" for point in trendline_output.points)
    assert any(
        value is True
        for value in trendline_output.derived_series["trendline_break_detected"]
    )
    assert trendline_output.points[-1].signal_label == "neutral"
    assert trendline_output.derived_series["trendline_slope"][-1] > 0.0
    assert (
        trendline_output.child_outputs[0].diagnostics["trendline_break_detected"]
        is False
    )

    squeeze_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "volatility_squeeze_breakout",
            "alg_param": {
                "squeeze_window": 5,
                "bollinger_multiplier": 2.0,
                "keltner_multiplier": 1.5,
                "breakout_buffer": 0.05,
                "confirmation_bars": 1,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path / "squeeze"),
    )
    squeeze_algorithm.process_list(_load_pattern_fixture_rows("support_rejection.csv"))
    squeeze_output = squeeze_algorithm.normalized_output()

    assert squeeze_output.points[-1].signal_label == "neutral"
    assert "squeeze_active" in squeeze_output.points[-1].reason_codes
    assert squeeze_output.derived_series["squeeze_on"][-1] is True
    assert (
        squeeze_output.child_outputs[0].diagnostics["bollinger_upper"]
        <= squeeze_output.child_outputs[0].diagnostics["keltner_upper"]
    )


def test_pattern_wave_2_validation_rejects_invalid_parameter_shapes() -> None:
    with pytest.raises(ValueError, match="relative_volume_threshold must be >= 0"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "gap_and_go",
                "alg_param": {
                    "gap_threshold": 0.15,
                    "continuation_threshold": 0.05,
                    "volume_window": 3,
                    "relative_volume_threshold": -0.1,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="break_buffer must be >= 0"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "trendline_break_strategy",
                "alg_param": {
                    "trendline_window": 5,
                    "break_buffer": -0.1,
                    "slope_tolerance": 0.0,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="keltner_multiplier must be > 0"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "volatility_squeeze_breakout",
                "alg_param": {
                    "squeeze_window": 5,
                    "bollinger_multiplier": 2.0,
                    "keltner_multiplier": 0.0,
                    "breakout_buffer": 0.05,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )


def test_pattern_wave_2_registration_metadata_matches_manifest_contract() -> None:
    expected = {
        "gap_and_go": ("algorithm:75", "pattern_price_action", "gap", 5),
        "trendline_break_strategy": (
            "algorithm:76",
            "pattern_price_action",
            "trendline",
            5,
        ),
        "volatility_squeeze_breakout": (
            "algorithm:77",
            "pattern_price_action",
            "volatility",
            6,
        ),
    }

    for alg_key, (catalog_ref, family, subcategory, warmup_period) in expected.items():
        spec = get_alert_algorithm_spec_by_key(alg_key)

        assert spec.catalog_ref == catalog_ref
        assert spec.family == family
        assert spec.subcategory == subcategory
        assert spec.warmup_period == warmup_period
        assert spec.output_modes == ("signal", "score", "confidence")
        assert spec.category == "pattern_price_action"


def test_pattern_wave_2_performance_smoke_on_fixture_repetition(tmp_path) -> None:
    rows = _load_pattern_fixture_rows("support_rejection.csv") * 300
    algorithms = [
        (
            "gap_and_go",
            {
                "gap_threshold": 0.15,
                "continuation_threshold": 0.05,
                "volume_window": 3,
                "relative_volume_threshold": 1.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "trendline_break_strategy",
            {
                "trendline_window": 5,
                "break_buffer": 0.1,
                "slope_tolerance": 0.0,
                "confirmation_bars": 1,
            },
        ),
        (
            "volatility_squeeze_breakout",
            {
                "squeeze_window": 5,
                "bollinger_multiplier": 2.0,
                "keltner_multiplier": 1.5,
                "breakout_buffer": 0.05,
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
            report_base_path=str(tmp_path / f"pattern-wave-2-{index}"),
        )
        algorithm.process_list(rows)
        output = algorithm.normalized_output()

        assert len(output.points) == len(rows)
        assert output.metadata["warmup_period"] == algorithm.minimum_history()
        assert output.metadata["reporting_mode"] == "bar_series"
        assert "trend_score" in output.derived_series


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
    assert child_output.reason_codes == tuple(child_output.diagnostics["reason_codes"])


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


@pytest.mark.parametrize(
    ("alg_key", "alg_param", "expected_warmup"),
    [
        (
            "intraday_vwap_reversion",
            {
                "entry_deviation_percent": 1.0,
                "exit_deviation_percent": 0.5,
                "min_session_bars": 2,
                "confirmation_bars": 1,
            },
            2,
        ),
        (
            "opening_gap_fade",
            {
                "min_gap_percent": 1.0,
                "exit_gap_fill_percent": 0.25,
                "min_session_bars": 2,
                "confirmation_bars": 1,
            },
            3,
        ),
        (
            "ornstein_uhlenbeck_reversion",
            {
                "window": 4,
                "entry_sigma": 0.5,
                "exit_sigma": 0.25,
                "min_mean_reversion_speed": 0.01,
                "confirmation_bars": 1,
            },
            4,
        ),
    ],
)
def test_mean_reversion_wave_3_short_history_stays_neutral_until_warmup(
    tmp_path, alg_key, alg_param, expected_warmup
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

    rows = (
        _build_intraday_mean_reversion_rows()
        if alg_key in {"intraday_vwap_reversion", "opening_gap_fade"}
        else _load_mean_reversion_fixture_rows("one_overshoot.csv")
    )
    algorithm.process_list(rows[: expected_warmup - 1])
    output = algorithm.normalized_output()

    assert algorithm.minimum_history() == expected_warmup
    assert output.points
    assert all(point.signal_label == "neutral" for point in output.points)
    assert any("warmup_pending" in point.reason_codes for point in output.points)


@pytest.mark.parametrize(
    ("alg_key", "alg_param", "expected_reason_code", "expected_annotation_keys"),
    [
        (
            "intraday_vwap_reversion",
            {
                "entry_deviation_percent": 1.0,
                "exit_deviation_percent": 0.5,
                "min_session_bars": 2,
                "confirmation_bars": 1,
            },
            "vwap_below_session_mean",
            {"entry_deviation_percent", "min_session_bars", "session_vwap"},
        ),
        (
            "opening_gap_fade",
            {
                "min_gap_percent": 1.0,
                "exit_gap_fill_percent": 0.25,
                "min_session_bars": 2,
                "confirmation_bars": 1,
            },
            "gap_down_fade",
            {"min_gap_percent", "prior_session_close", "opening_gap_percent"},
        ),
        (
            "ornstein_uhlenbeck_reversion",
            {
                "window": 4,
                "entry_sigma": 0.5,
                "exit_sigma": 0.25,
                "min_mean_reversion_speed": 0.01,
                "confirmation_bars": 1,
            },
            "ou_oversold",
            {"window", "ou_equilibrium", "ou_residual_zscore"},
        ),
    ],
)
def test_mean_reversion_wave_3_normalized_output_exposes_dashboard_diagnostics(
    tmp_path, alg_key, alg_param, expected_reason_code, expected_annotation_keys
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

    rows = (
        _build_intraday_mean_reversion_rows()
        if alg_key in {"intraday_vwap_reversion", "opening_gap_fade"}
        else _load_mean_reversion_fixture_rows("one_overshoot.csv")
    )
    algorithm.process_list(rows)
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
        "exit_value",
        "confirmation_state_label",
        "warmup_ready",
    }.issubset(output.derived_series)
    assert output.metadata["family"] == "mean_reversion"
    assert output.metadata["reporting_mode"] == "bar_series"
    assert output.metadata["catalog_ref"] == child_output.diagnostics["catalog_ref"]
    assert child_output.signal_label in {"buy", "neutral"}
    assert expected_annotation_keys.issubset(child_output.diagnostics.keys())
    assert child_output.diagnostics["warmup_ready"] is True
    if alg_key == "intraday_vwap_reversion":
        assert output.derived_series["session_bars_ready"][-1] is True
        assert child_output.diagnostics["session_bars_ready"] is True
        assert (
            child_output.diagnostics["session_bar_index"]
            >= alg_param["min_session_bars"]
        )
    elif alg_key == "opening_gap_fade":
        assert output.derived_series["session_bars_ready"][-1] is True
        assert output.derived_series["gap_fill_ready"][-1] is True
        assert child_output.diagnostics["session_bars_ready"] is True
        assert child_output.diagnostics["gap_fill_ready"] is True
        assert child_output.diagnostics["gap_fill_progress"] == pytest.approx(
            -0.6666666666666655
        )
    elif alg_key == "ornstein_uhlenbeck_reversion":
        assert output.derived_series["ou_speed_ready"][-1] is True
        assert child_output.diagnostics["ou_speed_ready"] is True
        assert child_output.diagnostics["ou_mean_reversion_speed"] >= 0.0


def test_mean_reversion_wave_3_validation_rejects_invalid_parameter_shapes() -> None:
    with pytest.raises(
        ValueError, match="exit_deviation_percent <= entry_deviation_percent"
    ):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "intraday_vwap_reversion",
                "alg_param": {
                    "entry_deviation_percent": 1.0,
                    "exit_deviation_percent": 1.1,
                    "min_session_bars": 2,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="exit_gap_fill_percent must be <= 1"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "opening_gap_fade",
                "alg_param": {
                    "min_gap_percent": 1.0,
                    "exit_gap_fill_percent": 1.5,
                    "min_session_bars": 2,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="exit_sigma <= entry_sigma"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "ornstein_uhlenbeck_reversion",
                "alg_param": {
                    "window": 4,
                    "entry_sigma": 0.5,
                    "exit_sigma": 0.75,
                    "min_mean_reversion_speed": 0.01,
                    "confirmation_bars": 1,
                },
                "buy": True,
                "sell": True,
            }
        )


def test_mean_reversion_wave_3_fixture_behavior_emits_reversion_signals(
    tmp_path,
) -> None:
    algorithms = [
        (
            "intraday_vwap_reversion",
            {
                "entry_deviation_percent": 1.0,
                "exit_deviation_percent": 0.5,
                "min_session_bars": 2,
                "confirmation_bars": 1,
            },
        ),
        (
            "opening_gap_fade",
            {
                "min_gap_percent": 1.0,
                "exit_gap_fill_percent": 0.25,
                "min_session_bars": 2,
                "confirmation_bars": 1,
            },
        ),
        (
            "ornstein_uhlenbeck_reversion",
            {
                "window": 4,
                "entry_sigma": 0.5,
                "exit_sigma": 0.25,
                "min_mean_reversion_speed": 0.01,
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
        rows = (
            _build_intraday_mean_reversion_rows()
            if alg_key in {"intraday_vwap_reversion", "opening_gap_fade"}
            else _load_mean_reversion_fixture_rows("one_overshoot.csv")
        )
        algorithm.process_list(rows)
        output = algorithm.normalized_output()

        assert any(point.signal_label == "buy" for point in output.points)
        assert output.metadata["family"] == "mean_reversion"


def test_mean_reversion_wave_3_intraday_outputs_report_session_specific_warmup_flags(
    tmp_path,
) -> None:
    algorithms = [
        (
            "intraday_vwap_reversion",
            {
                "entry_deviation_percent": 1.0,
                "exit_deviation_percent": 0.5,
                "min_session_bars": 2,
                "confirmation_bars": 1,
            },
        ),
        (
            "opening_gap_fade",
            {
                "min_gap_percent": 1.0,
                "exit_gap_fill_percent": 0.25,
                "min_session_bars": 2,
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
        algorithm.process_list(_build_intraday_mean_reversion_rows())
        output = algorithm.normalized_output()
        child_output = output.child_outputs[0]

        assert output.points[0].signal_label == "neutral"
        assert output.derived_series["warmup_ready"][0] is False
        assert output.derived_series["warmup_ready"][-1] is True
        assert child_output.diagnostics["warmup_ready"] is True
        assert child_output.diagnostics["reporting_mode"] == "bar_series"


def test_mean_reversion_wave_3_opening_gap_fade_reports_gap_fill_progress_against_open(
    tmp_path,
) -> None:
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "opening_gap_fade",
            "alg_param": {
                "min_gap_percent": 1.0,
                "exit_gap_fill_percent": 0.25,
                "min_session_bars": 2,
                "confirmation_bars": 1,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path),
    )

    algorithm.process_list(_build_intraday_mean_reversion_rows())
    output = algorithm.normalized_output()

    assert output.derived_series["gap_fill_progress"][-1] == pytest.approx(
        -0.6666666666666655
    )
    assert output.child_outputs[0].diagnostics["gap_fill_progress"] == pytest.approx(
        -0.6666666666666655
    )


def test_mean_reversion_wave_3_registration_metadata_matches_manifest_contract() -> (
    None
):
    expected = {
        "intraday_vwap_reversion": ("algorithm:32", "mean_reversion", "intraday", 3),
        "opening_gap_fade": ("algorithm:33", "mean_reversion", "opening", 3),
        "ornstein_uhlenbeck_reversion": (
            "algorithm:35",
            "mean_reversion",
            "ornstein",
            8,
        ),
    }

    for alg_key, (catalog_ref, family, subcategory, warmup_period) in expected.items():
        spec = get_alert_algorithm_spec_by_key(alg_key)

        assert spec.catalog_ref == catalog_ref
        assert spec.family == family
        assert spec.subcategory == subcategory
        assert spec.warmup_period == warmup_period
        assert spec.output_modes == ("signal", "score", "confidence")


def test_mean_reversion_wave_3_performance_smoke_on_fixture_repetition(
    tmp_path,
) -> None:
    algorithms = [
        (
            "intraday_vwap_reversion",
            {
                "entry_deviation_percent": 1.0,
                "exit_deviation_percent": 0.5,
                "min_session_bars": 2,
                "confirmation_bars": 1,
            },
        ),
        (
            "opening_gap_fade",
            {
                "min_gap_percent": 1.0,
                "exit_gap_fill_percent": 0.25,
                "min_session_bars": 2,
                "confirmation_bars": 1,
            },
        ),
        (
            "ornstein_uhlenbeck_reversion",
            {
                "window": 4,
                "entry_sigma": 0.5,
                "exit_sigma": 0.25,
                "min_mean_reversion_speed": 0.01,
                "confirmation_bars": 1,
            },
        ),
    ]

    for index, (alg_key, alg_param) in enumerate(algorithms):
        rows = (
            _build_intraday_mean_reversion_rows() * 300
            if alg_key in {"intraday_vwap_reversion", "opening_gap_fade"}
            else _load_mean_reversion_fixture_rows("one_overshoot.csv") * 300
        )
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
