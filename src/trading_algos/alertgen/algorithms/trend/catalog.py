from trading_algos.algorithmspec import AlertAlgorithmSpec, register_algorithm
from trading_algos.alertgen.algorithms.trend.boundary_breakout import (
    BoundaryBreakoutAlertAlgorithm,
    DoubleRedConfirmationAlertAlgorithm,
    LowAnchoredBoundaryBreakoutAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.breakout_donchian_channel import (
    BreakoutDonchianChannelAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.channel_breakout_with_confirmation import (
    ChannelBreakoutWithConfirmationAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.channel_breakout import (
    CloseHighChannelBreakoutAlertAlgorithm,
    RollingChannelBreakoutAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.adx_trend_filter import (
    ADXTrendFilterAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.exponential_moving_average_crossover import (
    ExponentialMovingAverageCrossoverAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.moving_average_ribbon_trend import (
    MovingAverageRibbonTrendAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.parabolic_sar_trend_following import (
    ParabolicSARTrendFollowingAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.price_vs_moving_average import (
    PriceVsMovingAverageAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.simple_moving_average_crossover import (
    SimpleMovingAverageCrossoverAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.supertrend import (
    SuperTrendAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.triple_moving_average_crossover import (
    TripleMovingAverageCrossoverAlertAlgorithm,
)
from trading_algos.alertgen.core.validation import (
    require_adx_trend_filter_param,
    require_breakout_donchian_param,
    require_channel_confirmation_param,
    require_fast_medium_slow_window_param,
    require_parabolic_sar_param,
    require_price_vs_ma_param,
    require_period_param,
    require_ribbon_param,
    require_short_long_window_param,
    require_supertrend_param,
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


def _build_breakout_donchian_channel(symbol, report_base_path, alg_param, **_kwargs):
    return BreakoutDonchianChannelAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        window=alg_param["window"],
        minimum_breakout=alg_param["minimum_breakout"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def _build_channel_breakout_with_confirmation(
    symbol, report_base_path, alg_param, **_kwargs
):
    return ChannelBreakoutWithConfirmationAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        window=alg_param["window"],
        breakout_threshold=alg_param["breakout_threshold"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def _build_adx_trend_filter(symbol, report_base_path, alg_param, **_kwargs):
    return ADXTrendFilterAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        window=alg_param["window"],
        adx_threshold=alg_param["adx_threshold"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def _build_parabolic_sar_trend_following(
    symbol, report_base_path, alg_param, **_kwargs
):
    return ParabolicSARTrendFollowingAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        step=alg_param["step"],
        max_step=alg_param["max_step"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def _build_supertrend(symbol, report_base_path, alg_param, **_kwargs):
    return SuperTrendAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        window=alg_param["window"],
        multiplier=alg_param["multiplier"],
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
            key="breakout_donchian_channel",
            name="Breakout (Donchian Channel)",
            catalog_ref="algorithm:6",
            builder=_build_breakout_donchian_channel,
            default_param={
                "window": 20,
                "minimum_breakout": 0.0,
                "confirmation_bars": 1,
            },
            param_normalizer=require_breakout_donchian_param,
            description="Buy on breakouts above the prior Donchian upper band and sell on breaks below the lower band.",
            param_schema=(
                {
                    "key": "window",
                    "label": "Window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Lookback used to form the Donchian channel.",
                },
                {
                    "key": "minimum_breakout",
                    "label": "Minimum breakout",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Minimum amount price must exceed the prior channel boundary before triggering.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Number of consecutive breakout bars required before the state is confirmed.",
                },
            ),
            tags=("trend", "breakout", "donchian"),
            category="trend",
            family="trend",
            subcategory="breakout",
            warmup_period=20,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="channel_breakout_with_confirmation",
            name="Channel Breakout with Confirmation",
            catalog_ref="algorithm:7",
            builder=_build_channel_breakout_with_confirmation,
            default_param={
                "window": 20,
                "breakout_threshold": 0.0,
                "confirmation_bars": 2,
            },
            param_normalizer=require_channel_confirmation_param,
            description="Require a channel breakout to persist across confirmation bars before switching trend state.",
            param_schema=(
                {
                    "key": "window",
                    "label": "Window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Lookback used to form the confirmation channel.",
                },
                {
                    "key": "breakout_threshold",
                    "label": "Breakout threshold",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Minimum distance beyond the channel boundary before a breakout counts toward confirmation.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Number of consecutive breakout bars required before the breakout is confirmed.",
                },
            ),
            tags=("trend", "channel", "confirmation"),
            category="trend",
            family="trend",
            subcategory="channel",
            warmup_period=20,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="adx_trend_filter",
            name="ADX Trend Filter",
            catalog_ref="algorithm:8",
            builder=_build_adx_trend_filter,
            default_param={
                "window": 14,
                "adx_threshold": 25.0,
                "confirmation_bars": 1,
            },
            param_normalizer=require_adx_trend_filter_param,
            description="Emit bullish or bearish trend states only when ADX exceeds the configured threshold and directional movement agrees.",
            param_schema=(
                {
                    "key": "window",
                    "label": "Window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Lookback used to compute ADX and directional indicators.",
                },
                {
                    "key": "adx_threshold",
                    "label": "ADX threshold",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Minimum ADX value required before the trend filter allows a directional state.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Number of consecutive bars required before the ADX-filtered state is confirmed.",
                },
            ),
            tags=("trend", "adx", "filter"),
            category="trend",
            family="trend",
            subcategory="adx",
            warmup_period=27,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="parabolic_sar_trend_following",
            name="Parabolic SAR Trend Following",
            catalog_ref="algorithm:9",
            builder=_build_parabolic_sar_trend_following,
            default_param={
                "step": 0.02,
                "max_step": 0.2,
                "confirmation_bars": 1,
            },
            param_normalizer=require_parabolic_sar_param,
            description="Follow the Parabolic SAR direction and flip the trend regime when price crosses the SAR level.",
            param_schema=(
                {
                    "key": "step",
                    "label": "Step",
                    "type": "number",
                    "required": True,
                    "minimum": 0.000001,
                    "description": "Acceleration factor increment used by the Parabolic SAR calculation.",
                },
                {
                    "key": "max_step",
                    "label": "Max step",
                    "type": "number",
                    "required": True,
                    "minimum": 0.000001,
                    "description": "Maximum acceleration factor allowed by the Parabolic SAR calculation.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Number of consecutive bars required before the SAR state is confirmed.",
                },
            ),
            tags=("trend", "parabolic-sar"),
            category="trend",
            family="trend",
            subcategory="parabolic",
            warmup_period=2,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="supertrend",
            name="SuperTrend",
            catalog_ref="algorithm:10",
            builder=_build_supertrend,
            default_param={
                "window": 10,
                "multiplier": 3.0,
                "confirmation_bars": 1,
            },
            param_normalizer=require_supertrend_param,
            description="Trend regime based on ATR-derived bands and direction flips.",
            param_schema=(
                {
                    "key": "window",
                    "label": "Window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "ATR lookback used to build the SuperTrend bands.",
                },
                {
                    "key": "multiplier",
                    "label": "Multiplier",
                    "type": "number",
                    "required": True,
                    "minimum": 0.000001,
                    "description": "ATR multiplier used to offset the SuperTrend bands.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Number of consecutive bars required before the SuperTrend direction is confirmed.",
                },
            ),
            tags=("trend", "supertrend", "atr"),
            category="trend",
            family="trend",
            subcategory="supertrend",
            warmup_period=10,
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
