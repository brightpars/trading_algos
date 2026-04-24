from trading_algos.algorithmspec import AlertAlgorithmSpec, register_algorithm
from trading_algos.alertgen.algorithms.pattern_price_action.breakout_retest import (
    BreakoutRetestAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.pattern_price_action.inside_bar_breakout import (
    InsideBarBreakoutAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.pattern_price_action.opening_range_breakout import (
    OpeningRangeBreakoutAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.pattern_price_action.pivot_point_strategy import (
    PivotPointStrategyAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.pattern_price_action.support_resistance_bounce import (
    SupportResistanceBounceAlertAlgorithm,
)
from trading_algos.alertgen.core.validation import (
    require_breakout_retest_param,
    require_inside_bar_breakout_param,
    require_opening_range_breakout_param,
    require_pivot_point_strategy_param,
    require_support_resistance_bounce_param,
)


def _build_support_resistance_bounce(symbol, report_base_path, alg_param, **_kwargs):
    return SupportResistanceBounceAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        level_window=alg_param["level_window"],
        touch_tolerance=alg_param["touch_tolerance"],
        rejection_min_close_delta=alg_param["rejection_min_close_delta"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def _build_breakout_retest(symbol, report_base_path, alg_param, **_kwargs):
    return BreakoutRetestAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        breakout_window=alg_param["breakout_window"],
        breakout_buffer=alg_param["breakout_buffer"],
        retest_tolerance=alg_param["retest_tolerance"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def _build_pivot_point_strategy(symbol, report_base_path, alg_param, **_kwargs):
    return PivotPointStrategyAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        pivot_lookback=alg_param["pivot_lookback"],
        level_tolerance=alg_param["level_tolerance"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def _build_opening_range_breakout(symbol, report_base_path, alg_param, **_kwargs):
    return OpeningRangeBreakoutAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        opening_range_minutes=alg_param["opening_range_minutes"],
        breakout_buffer=alg_param["breakout_buffer"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def _build_inside_bar_breakout(symbol, report_base_path, alg_param, **_kwargs):
    return InsideBarBreakoutAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        breakout_buffer=alg_param["breakout_buffer"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def register_pattern_price_action_alert_algorithms() -> None:
    specs = [
        AlertAlgorithmSpec(
            key="support_resistance_bounce",
            name="Support and Resistance Bounce",
            catalog_ref="algorithm:70",
            builder=_build_support_resistance_bounce,
            default_param={
                "level_window": 5,
                "touch_tolerance": 0.3,
                "rejection_min_close_delta": 0.2,
                "confirmation_bars": 1,
            },
            param_normalizer=require_support_resistance_bounce_param,
            description="Buy after a support touch is followed by a clear bullish rejection.",
            param_schema=(
                {
                    "key": "level_window",
                    "label": "Level window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Lookback bars used to derive the support level.",
                },
                {
                    "key": "touch_tolerance",
                    "label": "Touch tolerance",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Maximum distance from support that still counts as a touch.",
                },
                {
                    "key": "rejection_min_close_delta",
                    "label": "Rejection close delta",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Minimum close above support required to confirm rejection.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Consecutive bullish bars required before confirmation.",
                },
            ),
            tags=("pattern", "support", "bounce"),
            category="pattern_price_action",
            family="pattern_price_action",
            subcategory="support_resistance",
            warmup_period=6,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="breakout_retest",
            name="Breakout Retest",
            catalog_ref="algorithm:71",
            builder=_build_breakout_retest,
            default_param={
                "breakout_window": 5,
                "breakout_buffer": 0.2,
                "retest_tolerance": 0.3,
                "confirmation_bars": 1,
            },
            param_normalizer=require_breakout_retest_param,
            description="Buy after a breakout is followed by a successful retest of the broken level.",
            param_schema=(
                {
                    "key": "breakout_window",
                    "label": "Breakout window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Lookback bars used to define the breakout level.",
                },
                {
                    "key": "breakout_buffer",
                    "label": "Breakout buffer",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Minimum margin above the prior high to count as breakout.",
                },
                {
                    "key": "retest_tolerance",
                    "label": "Retest tolerance",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Maximum retest deviation from the breakout level.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Consecutive bullish bars required before confirmation.",
                },
            ),
            tags=("pattern", "breakout", "retest"),
            category="pattern_price_action",
            family="pattern_price_action",
            subcategory="breakout",
            warmup_period=7,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="pivot_point_strategy",
            name="Pivot Point Strategy",
            catalog_ref="algorithm:72",
            builder=_build_pivot_point_strategy,
            default_param={
                "pivot_lookback": 3,
                "level_tolerance": 0.4,
                "confirmation_bars": 1,
            },
            param_normalizer=require_pivot_point_strategy_param,
            description="Buy when price is supported near a derived pivot or support level.",
            param_schema=(
                {
                    "key": "pivot_lookback",
                    "label": "Pivot lookback",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Bars used to derive pivot high/low/close inputs.",
                },
                {
                    "key": "level_tolerance",
                    "label": "Level tolerance",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Maximum deviation from the nearest pivot level.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Consecutive bullish bars required before confirmation.",
                },
            ),
            tags=("pattern", "pivot", "levels"),
            category="pattern_price_action",
            family="pattern_price_action",
            subcategory="pivot",
            warmup_period=4,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="opening_range_breakout",
            name="Opening Range Breakout",
            catalog_ref="algorithm:73",
            builder=_build_opening_range_breakout,
            default_param={
                "opening_range_minutes": 15,
                "breakout_buffer": 0.2,
                "confirmation_bars": 1,
            },
            param_normalizer=require_opening_range_breakout_param,
            description="Buy when price breaks above a completed opening range.",
            param_schema=(
                {
                    "key": "opening_range_minutes",
                    "label": "Opening range minutes",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Minutes used to freeze the opening range.",
                },
                {
                    "key": "breakout_buffer",
                    "label": "Breakout buffer",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Minimum distance above the range high to count as breakout.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Consecutive bullish bars required before confirmation.",
                },
            ),
            tags=("pattern", "opening-range", "intraday"),
            category="pattern_price_action",
            family="pattern_price_action",
            subcategory="opening",
            warmup_period=2,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="inside_bar_breakout",
            name="Inside Bar Breakout",
            catalog_ref="algorithm:74",
            builder=_build_inside_bar_breakout,
            default_param={
                "breakout_buffer": 0.1,
                "confirmation_bars": 1,
            },
            param_normalizer=require_inside_bar_breakout_param,
            description="Buy when a completed inside bar resolves above the mother bar high.",
            param_schema=(
                {
                    "key": "breakout_buffer",
                    "label": "Breakout buffer",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Minimum distance above the mother high to count as breakout.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Consecutive bullish bars required before confirmation.",
                },
            ),
            tags=("pattern", "inside-bar", "breakout"),
            category="pattern_price_action",
            family="pattern_price_action",
            subcategory="inside",
            warmup_period=3,
            output_modes=("signal", "score", "confidence"),
        ),
    ]
    for spec in specs:
        register_algorithm(spec)
