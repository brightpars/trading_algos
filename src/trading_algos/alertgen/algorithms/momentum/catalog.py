from trading_algos.algorithmspec import AlertAlgorithmSpec, register_algorithm
from trading_algos.alertgen.algorithms.momentum.accelerating_momentum import (
    AcceleratingMomentumAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.momentum.cross_sectional_momentum import (
    build_cross_sectional_momentum_algorithm,
)
from trading_algos.alertgen.algorithms.momentum.cci_momentum import (
    CCIMomentumAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.momentum.dual_momentum import (
    build_dual_momentum_algorithm,
)
from trading_algos.alertgen.algorithms.momentum.kst_know_sure_thing import (
    KSTKnowSureThingAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.momentum.rate_of_change_momentum import (
    RateOfChangeMomentumAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.momentum.relative_strength_momentum import (
    build_relative_strength_momentum_algorithm,
)
from trading_algos.alertgen.algorithms.momentum.residual_momentum import (
    build_residual_momentum_algorithm,
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
    require_cross_sectional_momentum_param,
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


def _build_cross_sectional_momentum(symbol, report_base_path, alg_param, **_kwargs):
    del report_base_path
    return build_cross_sectional_momentum_algorithm(
        algorithm_key="cross_sectional_momentum",
        symbol=symbol,
        alg_name="cross_sectional_momentum",
        subcategory="cross",
        alg_param=alg_param,
    )


def _build_relative_strength_momentum(symbol, report_base_path, alg_param, **_kwargs):
    del report_base_path
    algorithm = build_relative_strength_momentum_algorithm(
        algorithm_key="relative_strength_momentum",
        symbol=symbol,
        alg_param=alg_param,
    )
    algorithm.catalog_ref = "algorithm:17"
    return algorithm


def _build_dual_momentum(symbol, report_base_path, alg_param, **_kwargs):
    del report_base_path
    algorithm = build_dual_momentum_algorithm(
        algorithm_key="dual_momentum",
        symbol=symbol,
        alg_param=alg_param,
    )
    algorithm.catalog_ref = "algorithm:18"
    return algorithm


def _build_residual_momentum(symbol, report_base_path, alg_param, **_kwargs):
    del report_base_path
    algorithm = build_residual_momentum_algorithm(
        algorithm_key="residual_momentum",
        symbol=symbol,
        alg_param=alg_param,
    )
    algorithm.catalog_ref = "algorithm:19"
    return algorithm


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
            key="cross_sectional_momentum",
            name="Cross-Sectional Momentum",
            catalog_ref="algorithm:16",
            builder=_build_cross_sectional_momentum,
            default_param={
                "rows": [],
                "lookback_window": 3,
                "top_n": 2,
                "bottom_n": 0,
                "rebalance_frequency": "monthly",
                "long_only": True,
                "score_adjustments": {},
            },
            param_normalizer=require_cross_sectional_momentum_param,
            description="Rank a universe by trailing returns and select the strongest assets on rebalance dates.",
            param_schema=(
                {
                    "key": "rows",
                    "label": "Rows",
                    "type": "object_list",
                    "required": True,
                    "description": "Panel rows containing ts, symbol, and close values.",
                },
                {
                    "key": "lookback_window",
                    "label": "Lookback window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Trailing return lookback in bars.",
                },
                {
                    "key": "top_n",
                    "label": "Top N",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Number of winners to select.",
                },
                {
                    "key": "bottom_n",
                    "label": "Bottom N",
                    "type": "integer",
                    "required": False,
                    "minimum": 0,
                    "description": "Number of losers to short when long_only is false.",
                },
                {
                    "key": "rebalance_frequency",
                    "label": "Rebalance frequency",
                    "type": "string",
                    "required": True,
                    "enum": ["monthly", "weekly", "all"],
                    "description": "Schedule used to sample rebalance dates.",
                },
                {
                    "key": "long_only",
                    "label": "Long only",
                    "type": "boolean",
                    "required": True,
                    "description": "Whether the strategy only allocates to winners.",
                },
                {
                    "key": "score_adjustments",
                    "label": "Score adjustments",
                    "type": "object",
                    "required": False,
                    "description": "Optional per-symbol additive adjustments used by specialized variants.",
                },
                {
                    "key": "absolute_momentum_threshold",
                    "label": "Absolute momentum threshold",
                    "type": "number",
                    "required": False,
                    "description": "Optional minimum score gate before an asset can be selected.",
                },
                {
                    "key": "defensive_symbol",
                    "label": "Defensive symbol",
                    "type": "string",
                    "required": False,
                    "description": "Optional fallback symbol when no asset passes the gate.",
                },
            ),
            tags=("momentum", "cross_sectional", "rebalance"),
            category="momentum",
            family="momentum",
            subcategory="cross",
            warmup_period=4,
            input_domains=("multi_asset_ohlcv",),
            asset_scope="universe",
            output_modes=("ranking", "selection", "diagnostics"),
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
            key="relative_strength_momentum",
            name="Relative Strength Momentum",
            catalog_ref="algorithm:17",
            builder=_build_relative_strength_momentum,
            default_param={
                "rows": [],
                "lookback_window": 3,
                "top_n": 2,
                "bottom_n": 0,
                "rebalance_frequency": "monthly",
                "long_only": True,
                "score_adjustments": {},
            },
            param_normalizer=require_cross_sectional_momentum_param,
            description="Select assets with the strongest recent performance relative to peers.",
            param_schema=(
                {
                    "key": "rows",
                    "label": "Rows",
                    "type": "object_list",
                    "required": True,
                    "description": "Panel rows containing ts, symbol, and close values.",
                },
                {
                    "key": "lookback_window",
                    "label": "Lookback window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Trailing return lookback in bars.",
                },
                {
                    "key": "top_n",
                    "label": "Top N",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Number of strongest assets to select.",
                },
                {
                    "key": "bottom_n",
                    "label": "Bottom N",
                    "type": "integer",
                    "required": False,
                    "minimum": 0,
                    "description": "Number of weak assets to short when long_only is false.",
                },
                {
                    "key": "rebalance_frequency",
                    "label": "Rebalance frequency",
                    "type": "string",
                    "required": True,
                    "enum": ["monthly", "weekly", "all"],
                    "description": "Schedule used to sample rebalance dates.",
                },
                {
                    "key": "long_only",
                    "label": "Long only",
                    "type": "boolean",
                    "required": True,
                    "description": "Whether the strategy only allocates to winners.",
                },
                {
                    "key": "score_adjustments",
                    "label": "Score adjustments",
                    "type": "object",
                    "required": False,
                    "description": "Optional per-symbol additive adjustments.",
                },
            ),
            tags=("momentum", "relative_strength", "rebalance"),
            category="momentum",
            family="momentum",
            subcategory="relative",
            warmup_period=4,
            input_domains=("multi_asset_ohlcv",),
            asset_scope="universe",
            output_modes=("ranking", "selection", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="dual_momentum",
            name="Dual Momentum",
            catalog_ref="algorithm:18",
            builder=_build_dual_momentum,
            default_param={
                "rows": [],
                "lookback_window": 3,
                "top_n": 1,
                "bottom_n": 0,
                "rebalance_frequency": "monthly",
                "long_only": True,
                "score_adjustments": {},
                "absolute_momentum_threshold": 0.0,
                "defensive_symbol": "BIL",
            },
            param_normalizer=require_cross_sectional_momentum_param,
            description="Combine cross-sectional ranking with an absolute momentum gate and optional defensive allocation.",
            param_schema=(
                {
                    "key": "rows",
                    "label": "Rows",
                    "type": "object_list",
                    "required": True,
                    "description": "Panel rows containing ts, symbol, and close values.",
                },
                {
                    "key": "lookback_window",
                    "label": "Lookback window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Trailing return lookback in bars.",
                },
                {
                    "key": "top_n",
                    "label": "Top N",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Number of strongest assets to select.",
                },
                {
                    "key": "rebalance_frequency",
                    "label": "Rebalance frequency",
                    "type": "string",
                    "required": True,
                    "enum": ["monthly", "weekly", "all"],
                    "description": "Schedule used to sample rebalance dates.",
                },
                {
                    "key": "long_only",
                    "label": "Long only",
                    "type": "boolean",
                    "required": True,
                    "description": "Whether the strategy only allocates to winners.",
                },
                {
                    "key": "absolute_momentum_threshold",
                    "label": "Absolute momentum threshold",
                    "type": "number",
                    "required": False,
                    "description": "Minimum score required before selecting risk assets.",
                },
                {
                    "key": "defensive_symbol",
                    "label": "Defensive symbol",
                    "type": "string",
                    "required": False,
                    "description": "Fallback defensive holding when no asset passes the gate.",
                },
                {
                    "key": "score_adjustments",
                    "label": "Score adjustments",
                    "type": "object",
                    "required": False,
                    "description": "Optional per-symbol additive adjustments.",
                },
            ),
            tags=("momentum", "dual", "rebalance"),
            category="momentum",
            family="momentum",
            subcategory="dual",
            warmup_period=4,
            input_domains=("multi_asset_ohlcv",),
            asset_scope="universe",
            output_modes=("ranking", "selection", "diagnostics"),
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
        AlertAlgorithmSpec(
            key="residual_momentum",
            name="Residual Momentum",
            catalog_ref="algorithm:19",
            builder=_build_residual_momentum,
            default_param={
                "rows": [],
                "lookback_window": 3,
                "top_n": 2,
                "bottom_n": 0,
                "rebalance_frequency": "monthly",
                "long_only": True,
                "score_adjustments": {},
            },
            param_normalizer=require_cross_sectional_momentum_param,
            description="Rank assets by adjusted momentum scores after removing simple residual effects.",
            param_schema=(
                {
                    "key": "rows",
                    "label": "Rows",
                    "type": "object_list",
                    "required": True,
                    "description": "Panel rows containing ts, symbol, and close values.",
                },
                {
                    "key": "lookback_window",
                    "label": "Lookback window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Trailing return lookback in bars.",
                },
                {
                    "key": "top_n",
                    "label": "Top N",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Number of strongest assets to select.",
                },
                {
                    "key": "bottom_n",
                    "label": "Bottom N",
                    "type": "integer",
                    "required": False,
                    "minimum": 0,
                    "description": "Number of weak assets to short when long_only is false.",
                },
                {
                    "key": "rebalance_frequency",
                    "label": "Rebalance frequency",
                    "type": "string",
                    "required": True,
                    "enum": ["monthly", "weekly", "all"],
                    "description": "Schedule used to sample rebalance dates.",
                },
                {
                    "key": "long_only",
                    "label": "Long only",
                    "type": "boolean",
                    "required": True,
                    "description": "Whether the strategy only allocates to winners.",
                },
                {
                    "key": "score_adjustments",
                    "label": "Score adjustments",
                    "type": "object",
                    "required": False,
                    "description": "Optional per-symbol additive residual adjustments.",
                },
            ),
            tags=("momentum", "residual", "rebalance"),
            category="momentum",
            family="momentum",
            subcategory="residual",
            warmup_period=4,
            input_domains=("multi_asset_ohlcv",),
            asset_scope="universe",
            output_modes=("ranking", "selection", "diagnostics"),
        ),
    ]
    for spec in specs:
        register_algorithm(spec)
