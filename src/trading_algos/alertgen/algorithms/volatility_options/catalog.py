from trading_algos.algorithmspec import AlertAlgorithmSpec, register_algorithm
from trading_algos.alertgen.algorithms.volatility_options.atr_channel_breakout import (
    ATRChannelBreakoutAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.volatility_options.volatility_breakout import (
    VolatilityBreakoutAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.volatility_options.volatility_mean_reversion import (
    VolatilityMeanReversionAlertAlgorithm,
)
from trading_algos.alertgen.core.validation import (
    require_atr_channel_breakout_param,
    require_volatility_breakout_param,
    require_volatility_mean_reversion_param,
)


def _build_volatility_breakout(symbol, report_base_path, alg_param, **_kwargs):
    return VolatilityBreakoutAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        atr_window=alg_param["atr_window"],
        compression_window=alg_param["compression_window"],
        compression_threshold=alg_param["compression_threshold"],
        breakout_lookback=alg_param["breakout_lookback"],
        breakout_buffer=alg_param["breakout_buffer"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def _build_atr_channel_breakout(symbol, report_base_path, alg_param, **_kwargs):
    return ATRChannelBreakoutAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        channel_window=alg_param["channel_window"],
        atr_window=alg_param["atr_window"],
        atr_multiplier=alg_param["atr_multiplier"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def _build_volatility_mean_reversion(symbol, report_base_path, alg_param, **_kwargs):
    return VolatilityMeanReversionAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        volatility_window=alg_param["volatility_window"],
        baseline_window=alg_param["baseline_window"],
        high_threshold=alg_param["high_threshold"],
        low_threshold=alg_param["low_threshold"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def register_volatility_options_alert_algorithms() -> None:
    specs = [
        AlertAlgorithmSpec(
            key="volatility_breakout",
            name="Volatility Breakout",
            catalog_ref="algorithm:52",
            builder=_build_volatility_breakout,
            default_param={
                "atr_window": 5,
                "compression_window": 5,
                "compression_threshold": 2.0,
                "breakout_lookback": 5,
                "breakout_buffer": 0.1,
                "confirmation_bars": 1,
            },
            param_normalizer=require_volatility_breakout_param,
            description="Trade upside breakouts after a compressed volatility regime expands.",
            param_schema=(
                {
                    "key": "atr_window",
                    "label": "ATR window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Lookback used for average true range.",
                },
                {
                    "key": "compression_window",
                    "label": "Compression window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Lookback used to measure rolling compression range.",
                },
                {
                    "key": "compression_threshold",
                    "label": "Compression threshold",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Maximum range-to-ATR ratio considered compressed.",
                },
                {
                    "key": "breakout_lookback",
                    "label": "Breakout lookback",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Lookback used to set the breakout reference high.",
                },
                {
                    "key": "breakout_buffer",
                    "label": "Breakout buffer",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Minimum price buffer above the breakout level.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Consecutive breakout bars required before confirmation.",
                },
            ),
            tags=("volatility", "breakout", "compression"),
            category="volatility_options",
            family="volatility_options",
            subcategory="volatility",
            warmup_period=6,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="atr_channel_breakout",
            name="ATR Channel Breakout",
            catalog_ref="algorithm:53",
            builder=_build_atr_channel_breakout,
            default_param={
                "channel_window": 5,
                "atr_window": 5,
                "atr_multiplier": 1.0,
                "confirmation_bars": 1,
            },
            param_normalizer=require_atr_channel_breakout_param,
            description="Break out when price closes beyond dynamic ATR-based channel bands.",
            param_schema=(
                {
                    "key": "channel_window",
                    "label": "Channel window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Lookback used for the channel midpoint.",
                },
                {
                    "key": "atr_window",
                    "label": "ATR window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Lookback used for average true range.",
                },
                {
                    "key": "atr_multiplier",
                    "label": "ATR multiplier",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "ATR multiple used to widen channel bands.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Consecutive channel breaks required before confirmation.",
                },
            ),
            tags=("volatility", "atr", "channel"),
            category="volatility_options",
            family="volatility_options",
            subcategory="atr",
            warmup_period=5,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="volatility_mean_reversion",
            name="Volatility Mean Reversion",
            catalog_ref="algorithm:54",
            builder=_build_volatility_mean_reversion,
            default_param={
                "volatility_window": 5,
                "baseline_window": 8,
                "high_threshold": 1.2,
                "low_threshold": 0.8,
                "confirmation_bars": 1,
            },
            param_normalizer=require_volatility_mean_reversion_param,
            description="Fade unusually high or low realized volatility back toward its local baseline.",
            param_schema=(
                {
                    "key": "volatility_window",
                    "label": "Volatility window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Lookback used for realized volatility.",
                },
                {
                    "key": "baseline_window",
                    "label": "Baseline window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Lookback used for the volatility baseline average.",
                },
                {
                    "key": "high_threshold",
                    "label": "High threshold",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Volatility ratio above which volatility is considered elevated.",
                },
                {
                    "key": "low_threshold",
                    "label": "Low threshold",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Volatility ratio below which volatility is considered depressed.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Consecutive ratio extremes required before confirmation.",
                },
            ),
            tags=("volatility", "mean-reversion", "realized-vol"),
            category="volatility_options",
            family="volatility_options",
            subcategory="volatility",
            warmup_period=13,
            output_modes=("signal", "score", "confidence"),
        ),
    ]
    for spec in specs:
        register_algorithm(spec)
