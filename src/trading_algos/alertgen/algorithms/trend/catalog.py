from trading_algos.algorithmspec import AlertAlgorithmSpec, register_algorithm
from trading_algos.alertgen.algorithms.trend.boundary_breakout import (
    BoundaryBreakoutAlertAlgorithm,
    DoubleRedConfirmationAlertAlgorithm,
    LowAnchoredBoundaryBreakoutAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.channel_breakout import (
    CloseHighChannelBreakoutAlertAlgorithm,
    RollingChannelBreakoutAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.exponential_moving_average_crossover import (
    ExponentialMovingAverageCrossoverAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.moving_average_ribbon_trend import (
    MovingAverageRibbonTrendAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.price_vs_moving_average import (
    PriceVsMovingAverageAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.simple_moving_average_crossover import (
    SimpleMovingAverageCrossoverAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.triple_moving_average_crossover import (
    TripleMovingAverageCrossoverAlertAlgorithm,
)
from trading_algos.alertgen.core.validation import (
    require_fast_medium_slow_window_param,
    require_price_vs_ma_param,
    require_period_param,
    require_ribbon_param,
    require_short_long_window_param,
    require_window_param,
)


def _build_boundary_breakout(symbol, report_base_path, **_kwargs):
    return BoundaryBreakoutAlertAlgorithm(symbol, report_base_path=report_base_path)


def _build_double_red_confirmation(symbol, report_base_path, **_kwargs):
    return DoubleRedConfirmationAlertAlgorithm(
        symbol, report_base_path=report_base_path
    )


def _build_low_anchored_boundary_breakout(symbol, report_base_path, **_kwargs):
    return LowAnchoredBoundaryBreakoutAlertAlgorithm(
        symbol, report_base_path=report_base_path
    )


def _build_rolling_channel_breakout(symbol, report_base_path, alg_param, **_kwargs):
    return RollingChannelBreakoutAlertAlgorithm(
        symbol, report_base_path=report_base_path, wlen=alg_param["window"]
    )


def _build_close_high_channel_breakout(symbol, report_base_path, alg_param, **_kwargs):
    return CloseHighChannelBreakoutAlertAlgorithm(
        symbol, report_base_path=report_base_path, wlen=alg_param["window"]
    )


def _build_simple_moving_average_crossover(
    symbol, report_base_path, alg_param, **_kwargs
):
    return SimpleMovingAverageCrossoverAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        short_window=alg_param["short_window"],
        long_window=alg_param["long_window"],
        minimum_spread=alg_param["minimum_spread"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def _build_exponential_moving_average_crossover(
    symbol, report_base_path, alg_param, **_kwargs
):
    return ExponentialMovingAverageCrossoverAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        short_window=alg_param["short_window"],
        long_window=alg_param["long_window"],
        minimum_spread=alg_param["minimum_spread"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def _build_triple_moving_average_crossover(
    symbol, report_base_path, alg_param, **_kwargs
):
    return TripleMovingAverageCrossoverAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        fast_window=alg_param["fast_window"],
        medium_window=alg_param["medium_window"],
        slow_window=alg_param["slow_window"],
        minimum_spread=alg_param["minimum_spread"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def _build_price_vs_moving_average(symbol, report_base_path, alg_param, **_kwargs):
    return PriceVsMovingAverageAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        window=alg_param["window"],
        average_type=alg_param["average_type"],
        minimum_spread=alg_param["minimum_spread"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def _build_moving_average_ribbon_trend(symbol, report_base_path, alg_param, **_kwargs):
    return MovingAverageRibbonTrendAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        windows=alg_param["windows"],
        minimum_spread=alg_param["minimum_spread"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def register_trend_alert_algorithms() -> None:
    specs = [
        AlertAlgorithmSpec(
            key="simple_moving_average_crossover",
            name="Simple Moving Average Crossover",
            catalog_ref="algorithm:1",
            builder=_build_simple_moving_average_crossover,
            default_param={
                "short_window": 5,
                "long_window": 20,
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
            param_normalizer=require_short_long_window_param,
            description="Buy when a short simple moving average rises above a longer simple moving average.",
            param_schema=(
                {
                    "key": "short_window",
                    "label": "Short window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Lookback for the fast simple moving average.",
                },
                {
                    "key": "long_window",
                    "label": "Long window",
                    "type": "integer",
                    "required": True,
                    "minimum": 2,
                    "description": "Lookback for the slow simple moving average.",
                },
                {
                    "key": "minimum_spread",
                    "label": "Minimum spread",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Minimum fast-minus-slow spread required before a crossover is considered active.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Number of consecutive bars required before a bullish or bearish crossover is confirmed.",
                },
            ),
            tags=("moving-average", "crossover", "trend"),
            category="trend",
            family="trend",
            subcategory="simple",
            warmup_period=20,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="exponential_moving_average_crossover",
            name="Exponential Moving Average Crossover",
            catalog_ref="algorithm:2",
            builder=_build_exponential_moving_average_crossover,
            default_param={
                "short_window": 5,
                "long_window": 20,
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
            param_normalizer=require_short_long_window_param,
            description="Buy when a short exponential moving average rises above a longer exponential moving average.",
            param_schema=(
                {
                    "key": "short_window",
                    "label": "Short window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Lookback for the fast exponential moving average.",
                },
                {
                    "key": "long_window",
                    "label": "Long window",
                    "type": "integer",
                    "required": True,
                    "minimum": 2,
                    "description": "Lookback for the slow exponential moving average.",
                },
                {
                    "key": "minimum_spread",
                    "label": "Minimum spread",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Minimum EMA spread required before the trend flips.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Number of consecutive bars required to confirm the EMA crossover.",
                },
            ),
            tags=("moving-average", "crossover", "trend", "ema"),
            category="trend",
            family="trend",
            subcategory="exponential",
            warmup_period=20,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="triple_moving_average_crossover",
            name="Triple Moving Average Crossover",
            catalog_ref="algorithm:3",
            builder=_build_triple_moving_average_crossover,
            default_param={
                "fast_window": 5,
                "medium_window": 10,
                "slow_window": 20,
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
            param_normalizer=require_fast_medium_slow_window_param,
            description="Require fast, medium, and slow moving averages to align before switching trend state.",
            param_schema=(
                {
                    "key": "fast_window",
                    "label": "Fast window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Lookback for the fastest moving average.",
                },
                {
                    "key": "medium_window",
                    "label": "Medium window",
                    "type": "integer",
                    "required": True,
                    "minimum": 2,
                    "description": "Lookback for the middle moving average.",
                },
                {
                    "key": "slow_window",
                    "label": "Slow window",
                    "type": "integer",
                    "required": True,
                    "minimum": 3,
                    "description": "Lookback for the slowest moving average.",
                },
                {
                    "key": "minimum_spread",
                    "label": "Minimum spread",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Minimum separation required between neighboring averages before the ribbon is considered aligned.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Number of consecutive aligned bars required before a signal is confirmed.",
                },
            ),
            tags=("moving-average", "crossover", "trend", "triple"),
            category="trend",
            family="trend",
            subcategory="triple",
            warmup_period=20,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="price_vs_moving_average",
            name="Price vs Moving Average",
            catalog_ref="algorithm:4",
            builder=_build_price_vs_moving_average,
            default_param={
                "window": 20,
                "average_type": "sma",
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
            param_normalizer=require_price_vs_ma_param,
            description="Emit a trend regime when price stays above or below a configurable moving average.",
            param_schema=(
                {
                    "key": "window",
                    "label": "Window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Lookback used to compute the reference moving average.",
                },
                {
                    "key": "average_type",
                    "label": "Average type",
                    "type": "string",
                    "required": True,
                    "enum": ["sma", "ema"],
                    "description": "Whether to compare price to a simple or exponential moving average.",
                },
                {
                    "key": "minimum_spread",
                    "label": "Minimum spread",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Minimum price-minus-average spread required to confirm the regime.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Number of consecutive bars required before price-vs-average state is confirmed.",
                },
            ),
            tags=("moving-average", "trend", "price"),
            category="trend",
            family="trend",
            subcategory="price",
            warmup_period=20,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="moving_average_ribbon_trend",
            name="Moving Average Ribbon Trend",
            catalog_ref="algorithm:5",
            builder=_build_moving_average_ribbon_trend,
            default_param={
                "windows": [5, 10, 20, 30],
                "minimum_spread": 0.0,
                "confirmation_bars": 1,
            },
            param_normalizer=require_ribbon_param,
            description="Use an ordered ribbon of moving averages to detect aligned trend regimes and ribbon strength.",
            param_schema=(
                {
                    "key": "windows",
                    "label": "Windows",
                    "type": "array",
                    "required": True,
                    "minItems": 3,
                    "description": "Ascending moving-average windows used to build the trend ribbon.",
                },
                {
                    "key": "minimum_spread",
                    "label": "Minimum spread",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Minimum separation required between neighboring ribbon averages.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Number of consecutive aligned ribbon bars required before a signal is confirmed.",
                },
            ),
            tags=("moving-average", "ribbon", "trend"),
            category="trend",
            family="trend",
            subcategory="moving",
            warmup_period=30,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="boundary_breakout",
            name="Boundary Breakout",
            catalog_ref="algorithm:6",
            builder=_build_boundary_breakout,
            default_param={"period": 5},
            param_normalizer=require_period_param,
            description="Boundary breakout algorithm using candle close direction.",
            param_schema=(
                {
                    "key": "period",
                    "label": "Period",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Number of candles used for the breakout lookback window.",
                },
            ),
            tags=("breakout", "baseline"),
            category="breakout",
            family="trend",
            subcategory="boundary_breakout",
            warmup_period=2,
        ),
        AlertAlgorithmSpec(
            key="double_red_confirmation",
            name="Double Red Confirmation",
            catalog_ref="algorithm:7",
            builder=_build_double_red_confirmation,
            default_param={"period": 5},
            param_normalizer=require_period_param,
            description="Boundary breakout variant with extra red-candle confirmation.",
            param_schema=(
                {
                    "key": "period",
                    "label": "Period",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Number of candles used before the red confirmation check is evaluated.",
                },
            ),
            tags=("breakout", "confirmation"),
            category="breakout",
            family="trend",
            subcategory="boundary_breakout",
            warmup_period=2,
        ),
        AlertAlgorithmSpec(
            key="low_anchored_boundary_breakout",
            name="Low-Anchored Boundary Breakout",
            catalog_ref="algorithm:6",
            builder=_build_low_anchored_boundary_breakout,
            default_param={"period": 5},
            param_normalizer=require_period_param,
            description="Boundary breakout variant with low-based high-boundary break detection.",
            param_schema=(
                {
                    "key": "period",
                    "label": "Period",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Lookback period used to anchor the breakout boundary on recent lows.",
                },
            ),
            tags=("breakout", "confirmation"),
            category="breakout",
            family="trend",
            subcategory="boundary_breakout",
            warmup_period=2,
        ),
        AlertAlgorithmSpec(
            key="rolling_channel_breakout",
            name="Rolling Channel Breakout",
            catalog_ref="algorithm:7",
            builder=_build_rolling_channel_breakout,
            default_param={"window": 20},
            param_normalizer=require_window_param,
            description="Rolling average channel breakout over low/high values.",
            param_schema=(
                {
                    "key": "window",
                    "label": "Window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Rolling window length used to calculate the breakout channel.",
                },
            ),
            tags=("channel", "moving-average"),
            category="channel",
            family="trend",
            subcategory="channel_breakout",
            warmup_period=20,
        ),
        AlertAlgorithmSpec(
            key="close_high_channel_breakout",
            name="Close/High Channel Breakout",
            catalog_ref="algorithm:7",
            builder=_build_close_high_channel_breakout,
            default_param={"window": 20},
            param_normalizer=require_window_param,
            description="Rolling channel breakout variant using close/high averages.",
            param_schema=(
                {
                    "key": "window",
                    "label": "Window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Rolling window length used for close/high channel averages.",
                },
            ),
            tags=("channel", "moving-average"),
            category="channel",
            family="trend",
            subcategory="channel_breakout",
            warmup_period=20,
        ),
    ]
    for spec in specs:
        register_algorithm(spec)
