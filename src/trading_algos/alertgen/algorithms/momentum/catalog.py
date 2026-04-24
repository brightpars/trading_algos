from trading_algos.algorithmspec import AlertAlgorithmSpec, register_algorithm
from trading_algos.alertgen.algorithms.momentum.accelerating_momentum import (
    AcceleratingMomentumAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.momentum.cci_momentum import (
    CCIMomentumAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.momentum.rate_of_change_momentum import (
    RateOfChangeMomentumAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.momentum.rsi_momentum_continuation import (
    RSIMomentumContinuationAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.momentum.stochastic_momentum import (
    StochasticMomentumAlertAlgorithm,
)
from trading_algos.alertgen.core.validation import (
    require_accelerating_momentum_param,
    require_cci_momentum_param,
    require_roc_momentum_param,
    require_rsi_momentum_param,
    require_stochastic_momentum_param,
)


def _build_rate_of_change_momentum(symbol, report_base_path, alg_param, **_kwargs):
    return RateOfChangeMomentumAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        window=alg_param["window"],
        bullish_threshold=alg_param["bullish_threshold"],
        bearish_threshold=alg_param["bearish_threshold"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def _build_accelerating_momentum(symbol, report_base_path, alg_param, **_kwargs):
    return AcceleratingMomentumAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        fast_window=alg_param["fast_window"],
        slow_window=alg_param["slow_window"],
        acceleration_threshold=alg_param["acceleration_threshold"],
        bearish_threshold=alg_param["bearish_threshold"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def _build_rsi_momentum_continuation(symbol, report_base_path, alg_param, **_kwargs):
    return RSIMomentumContinuationAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        window=alg_param["window"],
        bullish_threshold=alg_param["bullish_threshold"],
        bearish_threshold=alg_param["bearish_threshold"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def _build_stochastic_momentum(symbol, report_base_path, alg_param, **_kwargs):
    return StochasticMomentumAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        k_window=alg_param["k_window"],
        d_window=alg_param["d_window"],
        bullish_threshold=alg_param["bullish_threshold"],
        bearish_threshold=alg_param["bearish_threshold"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def _build_cci_momentum(symbol, report_base_path, alg_param, **_kwargs):
    return CCIMomentumAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        window=alg_param["window"],
        bullish_threshold=alg_param["bullish_threshold"],
        bearish_threshold=alg_param["bearish_threshold"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def register_momentum_alert_algorithms() -> None:
    specs = [
        AlertAlgorithmSpec(
            key="rate_of_change_momentum",
            name="Rate of Change Momentum",
            catalog_ref="algorithm:15",
            builder=_build_rate_of_change_momentum,
            default_param={
                "window": 5,
                "bullish_threshold": 3.0,
                "bearish_threshold": -3.0,
                "confirmation_bars": 1,
            },
            param_normalizer=require_roc_momentum_param,
            description="Momentum signal from rate-of-change threshold breaks.",
            param_schema=(
                {
                    "key": "window",
                    "label": "Window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Lookback bars for rate of change.",
                },
                {
                    "key": "bullish_threshold",
                    "label": "Bullish threshold",
                    "type": "number",
                    "required": True,
                    "description": "Minimum ROC required for bullish momentum.",
                },
                {
                    "key": "bearish_threshold",
                    "label": "Bearish threshold",
                    "type": "number",
                    "required": True,
                    "description": "Maximum ROC required for bearish momentum.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Consecutive bars required before confirmation.",
                },
            ),
            tags=("momentum", "roc"),
            category="momentum",
            family="momentum",
            subcategory="rate",
            warmup_period=6,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="accelerating_momentum",
            name="Accelerating Momentum",
            catalog_ref="algorithm:20",
            builder=_build_accelerating_momentum,
            default_param={
                "fast_window": 3,
                "slow_window": 7,
                "acceleration_threshold": 1.0,
                "bearish_threshold": -1.0,
                "confirmation_bars": 1,
            },
            param_normalizer=require_accelerating_momentum_param,
            description="Momentum signal from fast-minus-slow ROC acceleration.",
            param_schema=(
                {
                    "key": "fast_window",
                    "label": "Fast window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Short ROC lookback.",
                },
                {
                    "key": "slow_window",
                    "label": "Slow window",
                    "type": "integer",
                    "required": True,
                    "minimum": 2,
                    "description": "Long ROC lookback.",
                },
                {
                    "key": "acceleration_threshold",
                    "label": "Acceleration threshold",
                    "type": "number",
                    "required": True,
                    "description": "Minimum acceleration required for bullish momentum.",
                },
                {
                    "key": "bearish_threshold",
                    "label": "Bearish threshold",
                    "type": "number",
                    "required": True,
                    "description": "Maximum acceleration required for bearish momentum.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Consecutive bars required before confirmation.",
                },
            ),
            tags=("momentum", "acceleration"),
            category="momentum",
            family="momentum",
            subcategory="accelerating",
            warmup_period=8,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="rsi_momentum_continuation",
            name="RSI Momentum Continuation",
            catalog_ref="algorithm:21",
            builder=_build_rsi_momentum_continuation,
            default_param={
                "window": 6,
                "bullish_threshold": 60.0,
                "bearish_threshold": 40.0,
                "confirmation_bars": 1,
            },
            param_normalizer=require_rsi_momentum_param,
            description="Continuation-style RSI thresholds for bullish and bearish momentum.",
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
                    "key": "bullish_threshold",
                    "label": "Bullish threshold",
                    "type": "number",
                    "required": True,
                    "description": "RSI threshold for bullish continuation.",
                },
                {
                    "key": "bearish_threshold",
                    "label": "Bearish threshold",
                    "type": "number",
                    "required": True,
                    "description": "RSI threshold for bearish continuation.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Consecutive bars required before confirmation.",
                },
            ),
            tags=("momentum", "rsi"),
            category="momentum",
            family="momentum",
            subcategory="rsi",
            warmup_period=7,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="stochastic_momentum",
            name="Stochastic Momentum",
            catalog_ref="algorithm:22",
            builder=_build_stochastic_momentum,
            default_param={
                "k_window": 5,
                "d_window": 3,
                "bullish_threshold": 60.0,
                "bearish_threshold": 40.0,
                "confirmation_bars": 1,
            },
            param_normalizer=require_stochastic_momentum_param,
            description="Momentum signal from stochastic continuation and K/D alignment.",
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
                    "key": "bullish_threshold",
                    "label": "Bullish threshold",
                    "type": "number",
                    "required": True,
                    "description": "Bullish threshold for %K.",
                },
                {
                    "key": "bearish_threshold",
                    "label": "Bearish threshold",
                    "type": "number",
                    "required": True,
                    "description": "Bearish threshold for %K.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Consecutive bars required before confirmation.",
                },
            ),
            tags=("momentum", "stochastic"),
            category="momentum",
            family="momentum",
            subcategory="stochastic",
            warmup_period=7,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="cci_momentum",
            name="CCI Momentum",
            catalog_ref="algorithm:23",
            builder=_build_cci_momentum,
            default_param={
                "window": 5,
                "bullish_threshold": 100.0,
                "bearish_threshold": -100.0,
                "confirmation_bars": 1,
            },
            param_normalizer=require_cci_momentum_param,
            description="Momentum signal from CCI continuation thresholds.",
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
                    "key": "bullish_threshold",
                    "label": "Bullish threshold",
                    "type": "number",
                    "required": True,
                    "description": "CCI threshold for bullish continuation.",
                },
                {
                    "key": "bearish_threshold",
                    "label": "Bearish threshold",
                    "type": "number",
                    "required": True,
                    "description": "CCI threshold for bearish continuation.",
                },
                {
                    "key": "confirmation_bars",
                    "label": "Confirmation bars",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Consecutive bars required before confirmation.",
                },
            ),
            tags=("momentum", "cci"),
            category="momentum",
            family="momentum",
            subcategory="cci",
            warmup_period=5,
            output_modes=("signal", "score", "confidence"),
        ),
    ]
    for spec in specs:
        register_algorithm(spec)
