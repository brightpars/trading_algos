from trading_algos.algorithmspec import AlertAlgorithmSpec, register_algorithm
from trading_algos.alertgen.algorithms.pattern_price_action.breakout_retest import (
    BreakoutRetestAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.pattern_price_action.gap_and_go import (
    GapAndGoAlertAlgorithm,
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
from trading_algos.alertgen.algorithms.pattern_price_action.trendline_break_strategy import (
    TrendlineBreakStrategyAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.pattern_price_action.volatility_squeeze_breakout import (
    VolatilitySqueezeBreakoutAlertAlgorithm,
)
from trading_algos.alertgen.core.validation import (
    require_breakout_retest_param,
    require_gap_and_go_param,
    require_inside_bar_breakout_param,
    require_opening_range_breakout_param,
    require_pivot_point_strategy_param,
    require_support_resistance_bounce_param,
    require_trendline_break_strategy_param,
    require_volatility_squeeze_breakout_param,
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


def _build_gap_and_go(symbol, report_base_path, alg_param, **_kwargs):
    return GapAndGoAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        gap_threshold=alg_param["gap_threshold"],
        continuation_threshold=alg_param["continuation_threshold"],
        volume_window=alg_param["volume_window"],
        relative_volume_threshold=alg_param["relative_volume_threshold"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def _build_trendline_break_strategy(symbol, report_base_path, alg_param, **_kwargs):
    return TrendlineBreakStrategyAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        trendline_window=alg_param["trendline_window"],
        break_buffer=alg_param["break_buffer"],
        slope_tolerance=alg_param["slope_tolerance"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def _build_volatility_squeeze_breakout(symbol, report_base_path, alg_param, **_kwargs):
    return VolatilitySqueezeBreakoutAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        squeeze_window=alg_param["squeeze_window"],
        bollinger_multiplier=alg_param["bollinger_multiplier"],
        keltner_multiplier=alg_param["keltner_multiplier"],
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
        AlertAlgorithmSpec(
            key="gap_and_go",
            name="Gap-and-Go",
            catalog_ref="algorithm:75",
            builder=_build_gap_and_go,
            default_param={
                "gap_threshold": 0.15,
                "continuation_threshold": 0.05,
                "volume_window": 3,
                "relative_volume_threshold": 1.0,
                "confirmation_bars": 1,
            },
            param_normalizer=require_gap_and_go_param,
            description="Buy after an opening gap is followed by same-bar continuation with volume confirmation.",
            param_schema=(
                {
                    "key": "gap_threshold",
                    "label": "Gap threshold",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Minimum opening gap above the prior close.",
                },
                {
                    "key": "continuation_threshold",
                    "label": "Continuation threshold",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Minimum close above the open needed to confirm continuation.",
                },
                {
                    "key": "volume_window",
                    "label": "Volume window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Lookback bars used for relative-volume confirmation.",
                },
                {
                    "key": "relative_volume_threshold",
                    "label": "Relative volume threshold",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Minimum relative volume required to confirm the gap continuation.",
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
            tags=("pattern", "gap", "continuation"),
            category="pattern_price_action",
            family="pattern_price_action",
            subcategory="gap",
            warmup_period=5,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="trendline_break_strategy",
            name="Trendline Break Strategy",
            catalog_ref="algorithm:76",
            builder=_build_trendline_break_strategy,
            default_param={
                "trendline_window": 5,
                "break_buffer": 0.1,
                "slope_tolerance": 0.0,
                "confirmation_bars": 1,
            },
            param_normalizer=require_trendline_break_strategy_param,
            description="Buy when price breaks above a downward-sloping fitted trendline.",
            param_schema=(
                {
                    "key": "trendline_window",
                    "label": "Trendline window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Bars used to fit the local trendline.",
                },
                {
                    "key": "break_buffer",
                    "label": "Break buffer",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Minimum distance above the trendline required for a valid break.",
                },
                {
                    "key": "slope_tolerance",
                    "label": "Slope tolerance",
                    "type": "number",
                    "required": True,
                    "description": "Maximum allowed fitted slope for the trendline to count as descending/flat.",
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
            tags=("pattern", "trendline", "breakout"),
            category="pattern_price_action",
            family="pattern_price_action",
            subcategory="trendline",
            warmup_period=5,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="volatility_squeeze_breakout",
            name="Volatility Squeeze Breakout",
            catalog_ref="algorithm:77",
            builder=_build_volatility_squeeze_breakout,
            default_param={
                "squeeze_window": 5,
                "bollinger_multiplier": 2.0,
                "keltner_multiplier": 1.5,
                "breakout_buffer": 0.05,
                "confirmation_bars": 1,
            },
            param_normalizer=require_volatility_squeeze_breakout_param,
            description="Buy when price breaks above Bollinger resistance after a prior squeeze inside the Keltner envelope.",
            param_schema=(
                {
                    "key": "squeeze_window",
                    "label": "Squeeze window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Lookback bars used to compute the squeeze state.",
                },
                {
                    "key": "bollinger_multiplier",
                    "label": "Bollinger multiplier",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Standard deviation multiplier for Bollinger bands.",
                },
                {
                    "key": "keltner_multiplier",
                    "label": "Keltner multiplier",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "ATR multiplier for Keltner channels.",
                },
                {
                    "key": "breakout_buffer",
                    "label": "Breakout buffer",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Minimum distance above the Bollinger upper band required for breakout confirmation.",
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
            tags=("pattern", "volatility", "squeeze"),
            category="pattern_price_action",
            family="pattern_price_action",
            subcategory="volatility",
            warmup_period=6,
            output_modes=("signal", "score", "confidence"),
        ),
    ]
    for spec in specs:
        register_algorithm(spec)
