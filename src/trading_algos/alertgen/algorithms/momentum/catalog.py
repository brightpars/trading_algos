from trading_algos.algorithmspec import AlertAlgorithmSpec, register_algorithm
from trading_algos.alertgen.algorithms.momentum.accelerating_momentum import (
    AcceleratingMomentumAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.momentum.cci_momentum import (
    CCIMomentumAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.momentum.kst_know_sure_thing import (
    KSTKnowSureThingAlertAlgorithm,
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
from trading_algos.alertgen.algorithms.momentum.volume_confirmed_momentum import (
    VolumeConfirmedMomentumAlertAlgorithm,
)
from trading_algos.alertgen.core.validation import (
    require_accelerating_momentum_param,
    require_cci_momentum_param,
    require_kst_momentum_param,
    require_roc_momentum_param,
    require_rsi_momentum_param,
    require_stochastic_momentum_param,
    require_volume_confirmed_momentum_param,
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


def _build_kst_know_sure_thing(symbol, report_base_path, alg_param, **_kwargs):
    return KSTKnowSureThingAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        roc_windows=alg_param["roc_windows"],
        smoothing_windows=alg_param["smoothing_windows"],
        signal_window=alg_param["signal_window"],
        entry_mode=alg_param["entry_mode"],
        confirmation_bars=alg_param["confirmation_bars"],
    )


def _build_volume_confirmed_momentum(symbol, report_base_path, alg_param, **_kwargs):
    return VolumeConfirmedMomentumAlertAlgorithm(
        symbol,
        report_base_path=report_base_path,
        momentum_window=alg_param["momentum_window"],
        volume_window=alg_param["volume_window"],
        relative_volume_threshold=alg_param["relative_volume_threshold"],
        signal_threshold=alg_param["signal_threshold"],
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
        AlertAlgorithmSpec(
            key="kst_know_sure_thing",
            name="KST (Know Sure Thing)",
            catalog_ref="algorithm:24",
            builder=_build_kst_know_sure_thing,
            default_param={
                "roc_windows": [3, 4, 5, 6],
                "smoothing_windows": [3, 3, 3, 3],
                "signal_window": 4,
                "entry_mode": "signal_cross",
                "confirmation_bars": 1,
            },
            param_normalizer=require_kst_momentum_param,
            description="Multi-horizon momentum oscillator from weighted smoothed ROC components.",
            param_schema=(
                {
                    "key": "roc_windows",
                    "label": "ROC windows",
                    "type": "integer_list",
                    "required": True,
                    "description": "Lookback windows for each ROC component.",
                },
                {
                    "key": "smoothing_windows",
                    "label": "Smoothing windows",
                    "type": "integer_list",
                    "required": True,
                    "description": "Smoothing windows applied to each ROC component.",
                },
                {
                    "key": "signal_window",
                    "label": "Signal window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Moving-average window for the KST signal line.",
                },
                {
                    "key": "entry_mode",
                    "label": "Entry mode",
                    "type": "string",
                    "required": True,
                    "enum": ["signal_cross", "zero_cross"],
                    "description": "How bullish and bearish state is interpreted from KST output.",
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
            tags=("momentum", "kst"),
            category="momentum",
            family="momentum",
            subcategory="kst",
            warmup_period=13,
            output_modes=("signal", "score", "confidence"),
        ),
        AlertAlgorithmSpec(
            key="volume_confirmed_momentum",
            name="Volume-Confirmed Momentum",
            catalog_ref="algorithm:25",
            builder=_build_volume_confirmed_momentum,
            default_param={
                "momentum_window": 3,
                "volume_window": 5,
                "relative_volume_threshold": 1.0,
                "signal_threshold": 1.0,
                "confirmation_bars": 1,
            },
            param_normalizer=require_volume_confirmed_momentum_param,
            description="Momentum signal that requires relative-volume confirmation.",
            param_schema=(
                {
                    "key": "momentum_window",
                    "label": "Momentum window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Lookback window for the base momentum signal.",
                },
                {
                    "key": "volume_window",
                    "label": "Volume window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Lookback window for average volume baseline.",
                },
                {
                    "key": "relative_volume_threshold",
                    "label": "Relative volume threshold",
                    "type": "number",
                    "required": True,
                    "description": "Minimum relative volume required to confirm momentum.",
                },
                {
                    "key": "signal_threshold",
                    "label": "Signal threshold",
                    "type": "number",
                    "required": True,
                    "description": "Absolute momentum threshold required before confirmation.",
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
            tags=("momentum", "volume"),
            category="momentum",
            family="momentum",
            subcategory="volume",
            warmup_period=5,
            output_modes=("signal", "score", "confidence"),
        ),
    ]
    for spec in specs:
        register_algorithm(spec)
