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
from trading_algos.alertgen.core.validation import (
    require_period_param,
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


def register_trend_alert_algorithms() -> None:
    specs = [
        AlertAlgorithmSpec(
            key="boundary_breakout",
            name="Boundary Breakout",
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
