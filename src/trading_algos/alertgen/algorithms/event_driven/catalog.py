from trading_algos.algorithmspec import AlertAlgorithmSpec, register_algorithm
from trading_algos.alertgen.algorithms.event_driven.earnings_announcement_premium import (
    build_earnings_announcement_premium_algorithm,
)
from trading_algos.alertgen.algorithms.event_driven.etf_rebalancing_anticipation_front_run_strategy import (
    build_etf_rebalancing_anticipation_front_run_strategy_algorithm,
)
from trading_algos.alertgen.algorithms.event_driven.index_rebalancing_effect_strategy import (
    build_index_rebalancing_effect_strategy_algorithm,
)
from trading_algos.alertgen.algorithms.event_driven.pead_post_earnings_announcement_drift import (
    build_post_earnings_announcement_drift_algorithm,
)
from trading_algos.alertgen.algorithms.event_driven.pre_earnings_announcement_drift import (
    build_pre_earnings_announcement_drift_algorithm,
)
from trading_algos.alertgen.core.validation import (
    require_single_asset_event_window_param,
)


def _event_window_param_schema(*, include_expected_direction_field: bool = False):
    schema: list[dict[str, object]] = [
        {
            "key": "rows",
            "label": "Rows",
            "type": "object_list",
            "required": True,
            "description": "Single-symbol rows containing ts, symbol, close, and optional supporting fields.",
        },
        {
            "key": "event_rows",
            "label": "Event rows",
            "type": "object_list",
            "required": True,
            "description": "Point-in-time event rows containing symbol and event_timestamp.",
        },
        {
            "key": "event_value_field",
            "label": "Event value field",
            "type": "string",
            "required": True,
            "description": "Event field used as the normalized event score.",
        },
        {
            "key": "pre_event_window_days",
            "label": "Pre-event window days",
            "type": "integer",
            "required": False,
            "minimum": 0,
            "description": "Number of days before the public event timestamp when the signal can activate.",
        },
        {
            "key": "post_event_window_days",
            "label": "Post-event window days",
            "type": "integer",
            "required": False,
            "minimum": 0,
            "description": "Number of days after the public event timestamp when the signal can remain active.",
        },
        {
            "key": "bullish_phase",
            "label": "Bullish phase",
            "type": "string",
            "required": False,
            "enum": ["pre_event", "post_event"],
            "description": "Event phase that can emit a buy signal.",
        },
        {
            "key": "minimum_score_threshold",
            "label": "Minimum score threshold",
            "type": "number",
            "required": False,
            "minimum": 0,
            "description": "Minimum event score magnitude required before a window becomes actionable.",
        },
    ]
    if include_expected_direction_field:
        schema.append(
            {
                "key": "expected_direction_field",
                "label": "Expected direction field",
                "type": "string",
                "required": False,
                "description": "Event field that declares whether expected rebalance flow is buy or sell.",
            }
        )
    return tuple(schema)


def _build_pead(symbol, report_base_path, alg_param, **_kwargs):
    del report_base_path
    return build_post_earnings_announcement_drift_algorithm(
        algorithm_key="post_earnings_announcement_drift",
        symbol=symbol,
        alg_param=alg_param,
    )


def _build_pre_earnings(symbol, report_base_path, alg_param, **_kwargs):
    del report_base_path
    return build_pre_earnings_announcement_drift_algorithm(
        algorithm_key="pre_earnings_announcement_drift",
        symbol=symbol,
        alg_param=alg_param,
    )


def _build_earnings_premium(symbol, report_base_path, alg_param, **_kwargs):
    del report_base_path
    return build_earnings_announcement_premium_algorithm(
        algorithm_key="earnings_announcement_premium",
        symbol=symbol,
        alg_param=alg_param,
    )


def _build_index_rebalance(symbol, report_base_path, alg_param, **_kwargs):
    del report_base_path
    return build_index_rebalancing_effect_strategy_algorithm(
        algorithm_key="index_rebalancing_effect_strategy",
        symbol=symbol,
        alg_param=alg_param,
    )


def _build_etf_rebalance(symbol, report_base_path, alg_param, **_kwargs):
    del report_base_path
    return build_etf_rebalancing_anticipation_front_run_strategy_algorithm(
        algorithm_key="etf_rebalancing_anticipation_front_run_strategy",
        symbol=symbol,
        alg_param=alg_param,
    )


def register_event_driven_alert_algorithms() -> None:
    specs = [
        AlertAlgorithmSpec(
            key="post_earnings_announcement_drift",
            name="Post-Earnings Announcement Drift (PEAD)",
            catalog_ref="algorithm:117",
            builder=_build_pead,
            default_param={
                "rows": [],
                "event_rows": [],
                "event_value_field": "surprise",
                "post_event_window_days": 2,
                "pre_event_window_days": 0,
                "bullish_phase": "post_event",
                "minimum_score_threshold": 0.0,
            },
            param_normalizer=require_single_asset_event_window_param,
            description="Trade positive post-earnings drift only after the announcement becomes public.",
            param_schema=_event_window_param_schema(),
            tags=("event", "earnings", "post_event"),
            category="event_driven",
            family="event_driven",
            subcategory="earnings",
            warmup_period=1,
            input_domains=("event_calendar", "single_asset_ohlcv"),
            asset_scope="single_asset",
            output_modes=("event_window_signal", "event_metadata", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="pre_earnings_announcement_drift",
            name="Pre-Earnings Announcement Drift",
            catalog_ref="algorithm:118",
            builder=_build_pre_earnings,
            default_param={
                "rows": [],
                "event_rows": [],
                "event_value_field": "pre_drift_score",
                "pre_event_window_days": 2,
                "post_event_window_days": 0,
                "bullish_phase": "pre_event",
                "minimum_score_threshold": 0.0,
            },
            param_normalizer=require_single_asset_event_window_param,
            description="Activate in the days before earnings when a positive pre-announcement drift score is present.",
            param_schema=_event_window_param_schema(),
            tags=("event", "earnings", "pre_event"),
            category="event_driven",
            family="event_driven",
            subcategory="pre",
            warmup_period=1,
            input_domains=("event_calendar", "single_asset_ohlcv"),
            asset_scope="single_asset",
            output_modes=("event_window_signal", "event_metadata", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="earnings_announcement_premium",
            name="Earnings Announcement Premium",
            catalog_ref="algorithm:119",
            builder=_build_earnings_premium,
            default_param={
                "rows": [],
                "event_rows": [],
                "event_value_field": "premium_score",
                "pre_event_window_days": 1,
                "post_event_window_days": 1,
                "bullish_phase": "post_event",
                "minimum_score_threshold": 0.0,
            },
            param_normalizer=require_single_asset_event_window_param,
            description="Express a simple earnings-window premium by activating around scheduled earnings with a positive premium score.",
            param_schema=_event_window_param_schema(),
            tags=("event", "earnings", "premium"),
            category="event_driven",
            family="event_driven",
            subcategory="earnings",
            warmup_period=1,
            input_domains=("event_calendar", "single_asset_ohlcv"),
            asset_scope="single_asset",
            output_modes=("event_window_signal", "event_metadata", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="index_rebalancing_effect_strategy",
            name="Index Rebalancing Effect Strategy",
            catalog_ref="algorithm:120",
            builder=_build_index_rebalance,
            default_param={
                "rows": [],
                "event_rows": [],
                "event_value_field": "expected_flow",
                "expected_direction_field": "expected_direction",
                "pre_event_window_days": 2,
                "post_event_window_days": 1,
                "bullish_phase": "pre_event",
                "minimum_score_threshold": 0.0,
            },
            param_normalizer=require_single_asset_event_window_param,
            description="Trade positive expected buy pressure before and around known index rebalance windows.",
            param_schema=_event_window_param_schema(
                include_expected_direction_field=True
            ),
            tags=("event", "index", "rebalance"),
            category="event_driven",
            family="event_driven",
            subcategory="index",
            warmup_period=1,
            input_domains=("event_calendar", "single_asset_ohlcv"),
            asset_scope="single_asset",
            output_modes=("event_window_signal", "event_metadata", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="etf_rebalancing_anticipation_front_run_strategy",
            name="ETF Rebalancing Anticipation / Front-Run Strategy",
            catalog_ref="algorithm:121",
            builder=_build_etf_rebalance,
            default_param={
                "rows": [],
                "event_rows": [],
                "event_value_field": "expected_flow",
                "expected_direction_field": "expected_direction",
                "pre_event_window_days": 3,
                "post_event_window_days": 0,
                "bullish_phase": "pre_event",
                "minimum_score_threshold": 0.0,
            },
            param_normalizer=require_single_asset_event_window_param,
            description="Anticipate transparent ETF rebalance buy flow before the forced trading window.",
            param_schema=_event_window_param_schema(
                include_expected_direction_field=True
            ),
            tags=("event", "etf", "rebalance"),
            category="event_driven",
            family="event_driven",
            subcategory="etf",
            warmup_period=1,
            input_domains=("event_calendar", "single_asset_ohlcv"),
            asset_scope="single_asset",
            output_modes=("event_window_signal", "event_metadata", "diagnostics"),
        ),
    ]
    for spec in specs:
        register_algorithm(spec)
