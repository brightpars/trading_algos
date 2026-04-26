from trading_algos.algorithmspec import AlertAlgorithmSpec, register_algorithm
from trading_algos.alertgen.algorithms.cross_asset_macro_carry.carry_trade_fx_rates import (
    build_carry_trade_fx_rates_algorithm,
)
from trading_algos.alertgen.algorithms.cross_asset_macro_carry.commodity_term_structure_roll_yield import (
    build_commodity_term_structure_roll_yield_algorithm,
)
from trading_algos.alertgen.algorithms.cross_asset_macro_carry.curve_roll_down_strategy import (
    build_curve_roll_down_strategy_algorithm,
)
from trading_algos.alertgen.algorithms.cross_asset_macro_carry.earnings_drift_post_event_momentum import (
    build_earnings_drift_post_event_momentum_algorithm,
)
from trading_algos.alertgen.algorithms.cross_asset_macro_carry.intermarket_confirmation import (
    build_intermarket_confirmation_algorithm,
)
from trading_algos.alertgen.algorithms.cross_asset_macro_carry.risk_on_risk_off_regime import (
    build_risk_on_risk_off_regime_algorithm,
)
from trading_algos.alertgen.algorithms.cross_asset_macro_carry.seasonality_calendar_effects import (
    build_seasonality_calendar_effects_algorithm,
)
from trading_algos.alertgen.algorithms.cross_asset_macro_carry.yield_curve_steepener_flattener import (
    build_yield_curve_steepener_flattener_algorithm,
)
from trading_algos.alertgen.core.validation import (
    require_cross_asset_ranking_param,
    require_event_driven_param,
    require_multi_leg_rebalance_param,
    require_seasonality_calendar_param,
)


def _cross_asset_param_schema() -> tuple[dict[str, object], ...]:
    return (
        {
            "key": "rows",
            "label": "Rows",
            "type": "object_list",
            "required": True,
            "description": "Panel rows containing ts, symbol, close, and cross-asset metric fields.",
        },
        {
            "key": "field_names",
            "label": "Field names",
            "type": "string_list",
            "required": True,
            "description": "Fields averaged into the cross-asset score.",
        },
        {
            "key": "rebalance_frequency",
            "label": "Rebalance frequency",
            "type": "string",
            "required": True,
            "enum": ["monthly", "weekly", "all"],
            "description": "Schedule used to sample rebalance dates.",
        },
        {
            "key": "top_n",
            "label": "Top N",
            "type": "integer",
            "required": True,
            "minimum": 1,
            "description": "Number of highest-scoring assets to select.",
        },
        {
            "key": "bottom_n",
            "label": "Bottom N",
            "type": "integer",
            "required": False,
            "minimum": 0,
            "description": "Number of weakest assets to short when long_only is false.",
        },
        {
            "key": "long_only",
            "label": "Long only",
            "type": "boolean",
            "required": True,
            "description": "Whether the strategy allocates only to long positions.",
        },
        {
            "key": "minimum_universe_size",
            "label": "Minimum universe size",
            "type": "integer",
            "required": True,
            "minimum": 1,
            "description": "Minimum scored assets required before the rebalance is actionable.",
        },
    )


def _multi_leg_param_schema() -> tuple[dict[str, object], ...]:
    return (
        *_cross_asset_param_schema(),
        {
            "key": "front_leg_field",
            "label": "Front leg field",
            "type": "string",
            "required": True,
            "description": "Metric field for the front or near leg.",
        },
        {
            "key": "back_leg_field",
            "label": "Back leg field",
            "type": "string",
            "required": True,
            "description": "Metric field for the back or far leg.",
        },
    )


def _event_param_schema() -> tuple[dict[str, object], ...]:
    return (
        *_cross_asset_param_schema(),
        {
            "key": "event_rows",
            "label": "Event rows",
            "type": "object_list",
            "required": True,
            "description": "Point-in-time event rows containing symbol and event_timestamp.",
        },
        {
            "key": "post_event_window_days",
            "label": "Post-event window days",
            "type": "integer",
            "required": True,
            "minimum": 1,
            "description": "Maximum trading-window length after the event becomes public.",
        },
        {
            "key": "surprise_field",
            "label": "Surprise field",
            "type": "string",
            "required": False,
            "description": "Event field used as the drift-ranking score.",
        },
    )


def _build_carry_trade(symbol, report_base_path, alg_param, **_kwargs):
    del report_base_path
    return build_carry_trade_fx_rates_algorithm(
        algorithm_key="carry_trade_fx_rates",
        symbol=symbol,
        alg_param=alg_param,
    )


def _build_yield_curve(symbol, report_base_path, alg_param, **_kwargs):
    del report_base_path
    return build_yield_curve_steepener_flattener_algorithm(
        algorithm_key="yield_curve_steepener_flattener",
        symbol=symbol,
        alg_param=alg_param,
    )


def _build_curve_roll_down(symbol, report_base_path, alg_param, **_kwargs):
    del report_base_path
    return build_curve_roll_down_strategy_algorithm(
        algorithm_key="curve_roll_down_strategy",
        symbol=symbol,
        alg_param=alg_param,
    )


def _build_commodity_roll_yield(symbol, report_base_path, alg_param, **_kwargs):
    del report_base_path
    return build_commodity_term_structure_roll_yield_algorithm(
        algorithm_key="commodity_term_structure_roll_yield",
        symbol=symbol,
        alg_param=alg_param,
    )


def _build_risk_on_off(symbol, report_base_path, alg_param, **_kwargs):
    del report_base_path
    return build_risk_on_risk_off_regime_algorithm(
        algorithm_key="risk_on_risk_off_regime",
        symbol=symbol,
        alg_param=alg_param,
    )


def _build_intermarket_confirmation(symbol, report_base_path, alg_param, **_kwargs):
    del report_base_path
    return build_intermarket_confirmation_algorithm(
        algorithm_key="intermarket_confirmation",
        symbol=symbol,
        alg_param=alg_param,
    )


def _build_seasonality(symbol, report_base_path, alg_param, **_kwargs):
    del report_base_path
    return build_seasonality_calendar_effects_algorithm(
        algorithm_key="seasonality_calendar_effects",
        symbol=symbol,
        alg_param=alg_param,
    )


def _build_earnings_drift(symbol, report_base_path, alg_param, **_kwargs):
    del report_base_path
    return build_earnings_drift_post_event_momentum_algorithm(
        algorithm_key="earnings_drift_post_event_momentum",
        symbol=symbol,
        alg_param=alg_param,
    )


def register_cross_asset_macro_carry_alert_algorithms() -> None:
    specs = [
        AlertAlgorithmSpec(
            key="carry_trade_fx_rates",
            name="Carry Trade (FX/Rates)",
            catalog_ref="algorithm:78",
            builder=_build_carry_trade,
            default_param={
                "rows": [],
                "field_names": ["carry", "yield_diff"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
            param_normalizer=require_cross_asset_ranking_param,
            description="Rank cross-asset instruments by carry metrics on rebalance dates.",
            param_schema=_cross_asset_param_schema(),
            tags=("cross_asset", "carry", "rebalance"),
            category="cross_asset_macro_carry",
            family="cross_asset_macro_carry",
            subcategory="carry",
            warmup_period=1,
            input_domains=("multi_asset_panel",),
            asset_scope="portfolio",
            output_modes=("ranking", "selection", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="yield_curve_steepener_flattener",
            name="Yield Curve Steepener/Flattener",
            catalog_ref="algorithm:79",
            builder=_build_yield_curve,
            default_param={
                "rows": [],
                "field_names": ["curve_2y10y"],
                "front_leg_field": "yield_2y",
                "back_leg_field": "yield_10y",
                "rebalance_frequency": "monthly",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 1,
            },
            param_normalizer=require_multi_leg_rebalance_param,
            description="Express a curve-slope view using paired front/back maturity legs.",
            param_schema=_multi_leg_param_schema(),
            tags=("cross_asset", "yield_curve", "multi_leg"),
            category="cross_asset_macro_carry",
            family="cross_asset_macro_carry",
            subcategory="yield",
            warmup_period=1,
            input_domains=("multi_asset_panel",),
            asset_scope="portfolio",
            output_modes=("ranking", "selection", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="curve_roll_down_strategy",
            name="Curve Roll-Down Strategy",
            catalog_ref="algorithm:80",
            builder=_build_curve_roll_down,
            default_param={
                "rows": [],
                "field_names": ["roll_down"],
                "front_leg_field": "front_roll",
                "back_leg_field": "back_roll",
                "rebalance_frequency": "monthly",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 1,
            },
            param_normalizer=require_multi_leg_rebalance_param,
            description="Capture curve roll-down value via a paired maturity spread.",
            param_schema=_multi_leg_param_schema(),
            tags=("cross_asset", "curve", "multi_leg"),
            category="cross_asset_macro_carry",
            family="cross_asset_macro_carry",
            subcategory="curve",
            warmup_period=1,
            input_domains=("multi_asset_panel",),
            asset_scope="portfolio",
            output_modes=("ranking", "selection", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="commodity_term_structure_roll_yield",
            name="Commodity Term Structure / Roll Yield",
            catalog_ref="algorithm:81",
            builder=_build_commodity_roll_yield,
            default_param={
                "rows": [],
                "field_names": ["roll_yield"],
                "front_leg_field": "near_contract",
                "back_leg_field": "far_contract",
                "rebalance_frequency": "monthly",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 1,
            },
            param_normalizer=require_multi_leg_rebalance_param,
            description="Capture commodity carry using near-versus-far curve structure.",
            param_schema=_multi_leg_param_schema(),
            tags=("cross_asset", "commodity", "multi_leg"),
            category="cross_asset_macro_carry",
            family="cross_asset_macro_carry",
            subcategory="commodity",
            warmup_period=1,
            input_domains=("multi_asset_panel",),
            asset_scope="portfolio",
            output_modes=("ranking", "selection", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="risk_on_risk_off_regime",
            name="Risk-On / Risk-Off Regime",
            catalog_ref="algorithm:82",
            builder=_build_risk_on_off,
            default_param={
                "rows": [],
                "field_names": ["risk_score", "credit_impulse"],
                "rebalance_frequency": "monthly",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 1,
            },
            param_normalizer=require_cross_asset_ranking_param,
            description="Classify the dominant cross-asset regime from synthetic risk appetite features.",
            param_schema=_cross_asset_param_schema(),
            tags=("cross_asset", "regime", "rebalance"),
            category="cross_asset_macro_carry",
            family="cross_asset_macro_carry",
            subcategory="risk",
            warmup_period=1,
            input_domains=("cross_asset_panel", "multi_asset_panel"),
            asset_scope="portfolio",
            output_modes=("regime", "signal", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="intermarket_confirmation",
            name="Intermarket Confirmation",
            catalog_ref="algorithm:83",
            builder=_build_intermarket_confirmation,
            default_param={
                "rows": [],
                "field_names": ["confirmation", "leader_return"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
            param_normalizer=require_cross_asset_ranking_param,
            description="Rank assets whose cross-market confirmation inputs align most strongly.",
            param_schema=_cross_asset_param_schema(),
            tags=("cross_asset", "intermarket", "rebalance"),
            category="cross_asset_macro_carry",
            family="cross_asset_macro_carry",
            subcategory="intermarket",
            warmup_period=1,
            input_domains=("multi_asset_panel",),
            asset_scope="portfolio",
            output_modes=("ranking", "selection", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="seasonality_calendar_effects",
            name="Seasonality / Calendar Effects",
            catalog_ref="algorithm:84",
            builder=_build_seasonality,
            default_param={
                "rows": [],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 1,
                "calendar_pattern": "turn_of_month",
            },
            param_normalizer=require_seasonality_calendar_param,
            description="Score assets during pre-defined calendar effect windows.",
            param_schema=(
                {
                    "key": "rows",
                    "label": "Rows",
                    "type": "object_list",
                    "required": True,
                    "description": "Price rows with timestamps and symbols.",
                },
                {
                    "key": "rebalance_frequency",
                    "label": "Rebalance frequency",
                    "type": "string",
                    "required": True,
                    "enum": ["monthly", "weekly", "all"],
                    "description": "Schedule used to sample rebalance dates.",
                },
                {
                    "key": "top_n",
                    "label": "Top N",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Number of assets to select during active windows.",
                },
                {
                    "key": "bottom_n",
                    "label": "Bottom N",
                    "type": "integer",
                    "required": False,
                    "minimum": 0,
                    "description": "Number of assets to short when long_only is false.",
                },
                {
                    "key": "long_only",
                    "label": "Long only",
                    "type": "boolean",
                    "required": True,
                    "description": "Whether the strategy allocates only to long positions.",
                },
                {
                    "key": "minimum_universe_size",
                    "label": "Minimum universe size",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Minimum universe size required before the window is actionable.",
                },
                {
                    "key": "calendar_pattern",
                    "label": "Calendar pattern",
                    "type": "string",
                    "required": True,
                    "enum": ["turn_of_month", "month_end", "monday", "friday"],
                    "description": "Calendar rule used to activate the strategy window.",
                },
            ),
            tags=("cross_asset", "calendar", "rebalance"),
            category="cross_asset_macro_carry",
            family="cross_asset_macro_carry",
            subcategory="seasonality",
            warmup_period=1,
            input_domains=("single_asset_ohlcv", "market_calendar"),
            asset_scope="portfolio",
            output_modes=("signal", "calendar_window", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="earnings_drift_post_event_momentum",
            name="Earnings Drift / Post-Event Momentum",
            catalog_ref="algorithm:85",
            builder=_build_earnings_drift,
            default_param={
                "rows": [],
                "event_rows": [],
                "field_names": ["surprise"],
                "rebalance_frequency": "monthly",
                "top_n": 1,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 1,
                "post_event_window_days": 2,
                "surprise_field": "surprise",
            },
            param_normalizer=require_event_driven_param,
            description="Rank symbols by most recent earnings surprise within a post-event holding window.",
            param_schema=_event_param_schema(),
            tags=("cross_asset", "event", "earnings"),
            category="cross_asset_macro_carry",
            family="cross_asset_macro_carry",
            subcategory="earnings",
            warmup_period=1,
            input_domains=("event_calendar", "single_asset_ohlcv"),
            asset_scope="portfolio",
            output_modes=("event_window_signal", "diagnostics"),
        ),
    ]
    for spec in specs:
        register_algorithm(spec)
