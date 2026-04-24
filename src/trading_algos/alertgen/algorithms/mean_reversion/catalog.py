from trading_algos.algorithmspec import AlertAlgorithmSpec, register_algorithm
from trading_algos.alertgen.algorithms.mean_reversion.bollinger_bands_reversion import (
    BollingerBandsReversionAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.mean_reversion.cci_reversion import (
    CCIReversionAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.mean_reversion.rsi_reversion import (
    RSIReversionAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.mean_reversion.stochastic_reversion import (
    StochasticReversionAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.mean_reversion.z_score_mean_reversion import (
    ZScoreMeanReversionAlertAlgorithm,
)
from trading_algos.alertgen.core.validation import (
    require_bollinger_reversion_param,
    require_cci_reversion_param,
    require_rsi_reversion_param,
    require_stochastic_reversion_param,
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
    ]
    for spec in specs:
        register_algorithm(spec)
