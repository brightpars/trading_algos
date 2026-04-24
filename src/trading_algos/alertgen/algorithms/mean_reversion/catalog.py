from trading_algos.algorithmspec import AlertAlgorithmSpec, register_algorithm
from trading_algos.alertgen.algorithms.mean_reversion.bollinger_bands_reversion import (
    BollingerBandsReversionAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.mean_reversion.cci_reversion import (
    CCIReversionAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.mean_reversion.long_horizon_reversal import (
    LongHorizonReversalAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.mean_reversion.range_reversion import (
    RangeReversionAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.mean_reversion.rsi_reversion import (
    RSIReversionAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.mean_reversion.stochastic_reversion import (
    StochasticReversionAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.mean_reversion.volatility_adjusted_reversion import (
    VolatilityAdjustedReversionAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.mean_reversion.williams_percent_r_reversion import (
    WilliamsPercentRReversionAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.mean_reversion.z_score_mean_reversion import (
    ZScoreMeanReversionAlertAlgorithm,
)
from trading_algos.alertgen.core.validation import (
    require_bollinger_reversion_param,
    require_cci_reversion_param,
    require_long_horizon_reversal_param,
    require_range_reversion_param,
    require_rsi_reversion_param,
    require_stochastic_reversion_param,
    require_volatility_adjusted_reversion_param,
    require_williams_percent_r_reversion_param,
    require_zscore_mean_reversion_param,
)


def _build_zscore_mean_reversion(symbol, report_base_path, alg_param, **_kwargs):
    return ZScoreMeanReversionAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        window=alg_param["window"],
        entry_zscore=alg_param["entry_zscore"],
        exit_zscore=alg_param["exit_zscore"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def _build_bollinger_bands_reversion(symbol, report_base_path, alg_param, **_kwargs):
    return BollingerBandsReversionAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        window=alg_param["window"],
        std_multiplier=alg_param["std_multiplier"],
        exit_band_fraction=alg_param["exit_band_fraction"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def _build_rsi_reversion(symbol, report_base_path, alg_param, **_kwargs):
    return RSIReversionAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        window=alg_param["window"],
        oversold_threshold=alg_param["oversold_threshold"],
        overbought_threshold=alg_param["overbought_threshold"],
        exit_threshold=alg_param["exit_threshold"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def _build_stochastic_reversion(symbol, report_base_path, alg_param, **_kwargs):
    return StochasticReversionAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        k_window=alg_param["k_window"],
        d_window=alg_param["d_window"],
        oversold_threshold=alg_param["oversold_threshold"],
        overbought_threshold=alg_param["overbought_threshold"],
        exit_threshold=alg_param["exit_threshold"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def _build_cci_reversion(symbol, report_base_path, alg_param, **_kwargs):
    return CCIReversionAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        window=alg_param["window"],
        oversold_threshold=alg_param["oversold_threshold"],
        overbought_threshold=alg_param["overbought_threshold"],
        exit_threshold=alg_param["exit_threshold"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def _build_williams_percent_r_reversion(symbol, report_base_path, alg_param, **_kwargs):
    return WilliamsPercentRReversionAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        window=alg_param["window"],
        oversold_threshold=alg_param["oversold_threshold"],
        overbought_threshold=alg_param["overbought_threshold"],
        exit_threshold=alg_param["exit_threshold"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def _build_range_reversion(symbol, report_base_path, alg_param, **_kwargs):
    return RangeReversionAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        window=alg_param["window"],
        entry_band_fraction=alg_param["entry_band_fraction"],
        exit_band_fraction=alg_param["exit_band_fraction"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def _build_long_horizon_reversal(symbol, report_base_path, alg_param, **_kwargs):
    return LongHorizonReversalAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        window=alg_param["window"],
        entry_return_threshold=alg_param["entry_return_threshold"],
        exit_return_threshold=alg_param["exit_return_threshold"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def _build_volatility_adjusted_reversion(
    symbol, report_base_path, alg_param, **_kwargs
):
    return VolatilityAdjustedReversionAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        window=alg_param["window"],
        atr_window=alg_param["atr_window"],
        entry_atr_multiple=alg_param["entry_atr_multiple"],
        exit_atr_multiple=alg_param["exit_atr_multiple"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def register_mean_reversion_alert_algorithms() -> None:
    specs = [
        AlertAlgorithmSpec(
            key="z_score_mean_reversion",
            name="Z-Score Mean Reversion",
            catalog_ref="algorithm:26",
            builder=_build_zscore_mean_reversion,
            default_param={
                "window": 20,
                "entry_zscore": 2.0,
                "exit_zscore": 0.5,
                "confirmation_bars": 1,
            },
            param_normalizer=require_zscore_mean_reversion_param,
            description="Fade price stretches away from a rolling mean using z-score thresholds.",
            param_schema=(
                {
                    "key": "window",
                    "label": "Window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Rolling lookback window for mean and standard deviation.",
                },
                {
                    "key": "entry_zscore",
                    "label": "Entry z-score",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Absolute z-score required to trigger a reversion setup.",
                },
                {
                    "key": "exit_zscore",
                    "label": "Exit z-score",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Absolute z-score considered close enough to mean for exit diagnostics.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Consecutive extreme bars required before confirmation.",
                },
            ),
            tags=("mean-reversion", "zscore"),
            category="mean_reversion",
            family="mean_reversion",
            subcategory="z",
            warmup_period=20,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="bollinger_bands_reversion",
            name="Bollinger Bands Reversion",
            catalog_ref="algorithm:27",
            builder=_build_bollinger_bands_reversion,
            default_param={
                "window": 20,
                "std_multiplier": 2.0,
                "exit_band_fraction": 0.25,
                "confirmation_bars": 1,
            },
            param_normalizer=require_bollinger_reversion_param,
            description="Fade closes outside Bollinger Bands back toward the middle band.",
            param_schema=(
                {
                    "key": "window",
                    "label": "Window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Rolling lookback for the Bollinger band center and width.",
                },
                {
                    "key": "std_multiplier",
                    "label": "Standard deviation multiplier",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Band width multiplier applied to rolling standard deviation.",
                },
                {
                    "key": "exit_band_fraction",
                    "label": "Exit band fraction",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Normalized distance from the center band considered near-mean for diagnostics.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Consecutive band breaches required before confirmation.",
                },
            ),
            tags=("mean-reversion", "bollinger"),
            category="mean_reversion",
            family="mean_reversion",
            subcategory="bollinger",
            warmup_period=20,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="rsi_reversion",
            name="RSI Reversion",
            catalog_ref="algorithm:28",
            builder=_build_rsi_reversion,
            default_param={
                "window": 14,
                "oversold_threshold": 30.0,
                "overbought_threshold": 70.0,
                "exit_threshold": 50.0,
                "confirmation_bars": 1,
            },
            param_normalizer=require_rsi_reversion_param,
            description="Use RSI oversold and overbought extremes as mean-reversion setups.",
            param_schema=(
                {
                    "key": "window",
                    "label": "Window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "RSI lookback window.",
                },
                {
                    "key": "oversold_threshold",
                    "label": "Oversold threshold",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "maximum": 100.0,
                    "description": "RSI level at or below which long reversion setups become active.",
                },
                {
                    "key": "overbought_threshold",
                    "label": "Overbought threshold",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "maximum": 100.0,
                    "description": "RSI level at or above which short reversion setups become active.",
                },
                {
                    "key": "exit_threshold",
                    "label": "Exit threshold",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "maximum": 100.0,
                    "description": "RSI level considered close enough to neutral for exit diagnostics.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Consecutive extreme RSI bars required before confirmation.",
                },
            ),
            tags=("mean-reversion", "rsi"),
            category="mean_reversion",
            family="mean_reversion",
            subcategory="rsi",
            warmup_period=15,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="stochastic_reversion",
            name="Stochastic Reversion",
            catalog_ref="algorithm:29",
            builder=_build_stochastic_reversion,
            default_param={
                "k_window": 14,
                "d_window": 3,
                "oversold_threshold": 20.0,
                "overbought_threshold": 80.0,
                "exit_threshold": 50.0,
                "confirmation_bars": 1,
            },
            param_normalizer=require_stochastic_reversion_param,
            description="Use stochastic oscillator extremes and K/D alignment for mean-reversion setups.",
            param_schema=(
                {
                    "key": "k_window",
                    "label": "K window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Lookback for stochastic %K.",
                },
                {
                    "key": "d_window",
                    "label": "D window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Smoothing window for stochastic %D.",
                },
                {
                    "key": "oversold_threshold",
                    "label": "Oversold threshold",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "maximum": 100.0,
                    "description": "Stochastic level at or below which long reversion setups become active.",
                },
                {
                    "key": "overbought_threshold",
                    "label": "Overbought threshold",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "maximum": 100.0,
                    "description": "Stochastic level at or above which short reversion setups become active.",
                },
                {
                    "key": "exit_threshold",
                    "label": "Exit threshold",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "maximum": 100.0,
                    "description": "Stochastic level considered close enough to neutral for exit diagnostics.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Consecutive extreme stochastic bars required before confirmation.",
                },
            ),
            tags=("mean-reversion", "stochastic"),
            category="mean_reversion",
            family="mean_reversion",
            subcategory="stochastic",
            warmup_period=16,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="cci_reversion",
            name="CCI Reversion",
            catalog_ref="algorithm:30",
            builder=_build_cci_reversion,
            default_param={
                "window": 20,
                "oversold_threshold": -100.0,
                "overbought_threshold": 100.0,
                "exit_threshold": 0.0,
                "confirmation_bars": 1,
            },
            param_normalizer=require_cci_reversion_param,
            description="Fade CCI extremes back toward neutral territory.",
            param_schema=(
                {
                    "key": "window",
                    "label": "Window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "CCI lookback window.",
                },
                {
                    "key": "oversold_threshold",
                    "label": "Oversold threshold",
                    "type": "number",
                    "required": True,
                    "description": "CCI level at or below which long reversion setups become active.",
                },
                {
                    "key": "overbought_threshold",
                    "label": "Overbought threshold",
                    "type": "number",
                    "required": True,
                    "description": "CCI level at or above which short reversion setups become active.",
                },
                {
                    "key": "exit_threshold",
                    "label": "Exit threshold",
                    "type": "number",
                    "required": True,
                    "description": "CCI level considered close enough to neutral for exit diagnostics.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Consecutive extreme CCI bars required before confirmation.",
                },
            ),
            tags=("mean-reversion", "cci"),
            category="mean_reversion",
            family="mean_reversion",
            subcategory="cci",
            warmup_period=20,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="williams_percent_r_reversion",
            name="Williams %R Reversion",
            catalog_ref="algorithm:31",
            builder=_build_williams_percent_r_reversion,
            default_param={
                "window": 14,
                "oversold_threshold": -80.0,
                "overbought_threshold": -20.0,
                "exit_threshold": -50.0,
                "confirmation_bars": 1,
            },
            param_normalizer=require_williams_percent_r_reversion_param,
            description="Fade Williams %R oversold and overbought extremes back toward the middle of the range.",
            param_schema=(
                {
                    "key": "window",
                    "label": "Window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Williams %R lookback window.",
                },
                {
                    "key": "oversold_threshold",
                    "label": "Oversold threshold",
                    "type": "number",
                    "required": True,
                    "minimum": -100.0,
                    "maximum": 0.0,
                    "description": "Williams %R level at or below which long reversion setups become active.",
                },
                {
                    "key": "overbought_threshold",
                    "label": "Overbought threshold",
                    "type": "number",
                    "required": True,
                    "minimum": -100.0,
                    "maximum": 0.0,
                    "description": "Williams %R level at or above which short reversion setups become active.",
                },
                {
                    "key": "exit_threshold",
                    "label": "Exit threshold",
                    "type": "number",
                    "required": True,
                    "minimum": -100.0,
                    "maximum": 0.0,
                    "description": "Williams %R level considered close enough to neutral for exit diagnostics.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Consecutive extreme Williams %R bars required before confirmation.",
                },
            ),
            tags=("mean-reversion", "williams-percent-r"),
            category="mean_reversion",
            family="mean_reversion",
            subcategory="williams",
            warmup_period=14,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="range_reversion",
            name="Range Reversion",
            catalog_ref="algorithm:34",
            builder=_build_range_reversion,
            default_param={
                "window": 20,
                "entry_band_fraction": 0.2,
                "exit_band_fraction": 0.5,
                "confirmation_bars": 1,
            },
            param_normalizer=require_range_reversion_param,
            description="Fade moves toward the edges of a rolling trading range back toward its midpoint.",
            param_schema=(
                {
                    "key": "window",
                    "label": "Window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Rolling lookback for the range high and low.",
                },
                {
                    "key": "entry_band_fraction",
                    "label": "Entry band fraction",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "maximum": 0.5,
                    "description": "Fraction of the range near support or resistance that triggers a reversion setup.",
                },
                {
                    "key": "exit_band_fraction",
                    "label": "Exit band fraction",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "maximum": 0.5,
                    "description": "Fractional distance from the midpoint considered close enough for exit diagnostics.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Consecutive range-edge bars required before confirmation.",
                },
            ),
            tags=("mean-reversion", "range"),
            category="mean_reversion",
            family="mean_reversion",
            subcategory="range",
            warmup_period=20,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="long_horizon_reversal",
            name="Long-Horizon Reversal",
            catalog_ref="algorithm:36",
            builder=_build_long_horizon_reversal,
            default_param={
                "window": 63,
                "entry_return_threshold": 10.0,
                "exit_return_threshold": 3.0,
                "confirmation_bars": 1,
            },
            param_normalizer=require_long_horizon_reversal_param,
            description="Fade large multi-week or multi-month trailing returns as a contrarian reversal setup.",
            param_schema=(
                {
                    "key": "window",
                    "label": "Window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Trailing return lookback window.",
                },
                {
                    "key": "entry_return_threshold",
                    "label": "Entry return threshold",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Absolute trailing return magnitude that triggers a reversal setup.",
                },
                {
                    "key": "exit_return_threshold",
                    "label": "Exit return threshold",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Trailing return magnitude considered close enough to neutral for exit diagnostics.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Consecutive extreme trailing-return bars required before confirmation.",
                },
            ),
            tags=("mean-reversion", "long-horizon", "contrarian"),
            category="mean_reversion",
            family="mean_reversion",
            subcategory="long",
            warmup_period=64,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="volatility_adjusted_reversion",
            name="Volatility-Adjusted Reversion",
            catalog_ref="algorithm:37",
            builder=_build_volatility_adjusted_reversion,
            default_param={
                "window": 20,
                "atr_window": 14,
                "entry_atr_multiple": 1.5,
                "exit_atr_multiple": 0.5,
                "confirmation_bars": 1,
            },
            param_normalizer=require_volatility_adjusted_reversion_param,
            description="Fade price deviations from a rolling mean after normalizing the move by ATR.",
            param_schema=(
                {
                    "key": "window",
                    "label": "Mean window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Rolling lookback for the mean anchor.",
                },
                {
                    "key": "atr_window",
                    "label": "ATR window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "ATR lookback window used for volatility normalization.",
                },
                {
                    "key": "entry_atr_multiple",
                    "label": "Entry ATR multiple",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "Absolute ATR-normalized distance required to trigger a reversion setup.",
                },
                {
                    "key": "exit_atr_multiple",
                    "label": "Exit ATR multiple",
                    "type": "number",
                    "required": True,
                    "minimum": 0.0,
                    "description": "ATR-normalized distance considered close enough to mean for exit diagnostics.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Consecutive ATR-normalized extremes required before confirmation.",
                },
            ),
            tags=("mean-reversion", "volatility-adjusted", "atr"),
            category="mean_reversion",
            family="mean_reversion",
            subcategory="volatility",
            warmup_period=20,
            output_modes=("signal", "score", "confidence"),
        ),
    ]
    for spec in specs:
        register_algorithm(spec)
