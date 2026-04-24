from __future__ import annotations

from typing import Any, cast

from trading_algos.alertgen.algorithms.volatility_options.options_surface_algorithm import (
    BaseOptionsSurfaceAlgorithm,
)
from trading_algos.alertgen.algorithms.volatility_options.options_surface_helpers import (
    OptionSurfaceDecisionMetrics,
)


class DeltaNeutralVolatilityTradingAlgorithm(BaseOptionsSurfaceAlgorithm):
    catalog_ref = "algorithm:55"

    def __init__(
        self,
        *,
        symbol: str,
        rows: list[dict[str, object]],
        iv_rv_threshold: float = 0.05,
        min_gamma: float = 0.0,
        target_delta_band: float = 0.1,
    ) -> None:
        self.iv_rv_threshold = float(iv_rv_threshold)
        self.min_gamma = float(min_gamma)
        self.target_delta_band = float(target_delta_band)
        super().__init__(
            algorithm_key="delta_neutral_volatility_trading",
            symbol=symbol,
            family="volatility_options",
            subcategory="delta",
            rows=rows,
        )

    def _hedge_band(self) -> float:
        return self.target_delta_band

    def _evaluate_row(
        self, metrics: OptionSurfaceDecisionMetrics, *, index: int
    ) -> tuple[str, float, float, tuple[str, ...], dict[str, object]]:
        long_vol = metrics.iv_rv_gap <= -self.iv_rv_threshold and metrics.net_gamma >= self.min_gamma
        short_vol = metrics.iv_rv_gap >= self.iv_rv_threshold and metrics.net_gamma >= self.min_gamma
        near_neutral = not metrics.hedge_rebalance_required
        score = 0.0
        signal_label = "neutral"
        reason_code = "delta_neutral_wait"
        if long_vol and near_neutral:
            signal_label = "buy"
            score = min(1.0, abs(metrics.iv_rv_gap) / max(self.iv_rv_threshold, 1e-6))
            reason_code = "delta_neutral_long_vol"
        elif short_vol and near_neutral:
            signal_label = "sell"
            score = -min(1.0, abs(metrics.iv_rv_gap) / max(self.iv_rv_threshold, 1e-6))
            reason_code = "delta_neutral_short_vol"
        elif not near_neutral:
            reason_code = "delta_rehedge_required"
        elif metrics.net_gamma < self.min_gamma:
            reason_code = "insufficient_gamma"
        confidence = min(1.0, abs(score))
        return (
            signal_label,
            score,
            confidence,
            (reason_code,),
            {
                "iv_rv_threshold": self.iv_rv_threshold,
                "min_gamma": self.min_gamma,
                "target_delta_band": self.target_delta_band,
                "delta_neutral": near_neutral,
                "hedge_rebalance_required": metrics.hedge_rebalance_required,
            },
        )


def build_delta_neutral_volatility_trading_algorithm(
    *, symbol: str, alg_param: dict[str, object], **_: object
) -> DeltaNeutralVolatilityTradingAlgorithm:
    rows = cast(list[dict[str, Any]], alg_param["rows"])
    return DeltaNeutralVolatilityTradingAlgorithm(
        symbol=symbol,
        rows=rows,
        iv_rv_threshold=float(cast(float, alg_param["iv_rv_threshold"])),
        min_gamma=float(cast(float, alg_param["min_gamma"])),
        target_delta_band=float(cast(float, alg_param["target_delta_band"])),
    )