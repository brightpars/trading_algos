from __future__ import annotations

from typing import Any, cast

from trading_algos.alertgen.algorithms.volatility_options.options_surface_algorithm import (
    BaseOptionsSurfaceAlgorithm,
)
from trading_algos.alertgen.algorithms.volatility_options.options_surface_helpers import (
    OptionSurfaceDecisionMetrics,
)


class GammaScalpingAlgorithm(BaseOptionsSurfaceAlgorithm):
    catalog_ref = "algorithm:56"

    def __init__(
        self,
        *,
        symbol: str,
        rows: list[dict[str, object]],
        rebalance_band: float = 0.1,
        min_gamma: float = 0.0,
        scalp_threshold: float = 0.01,
    ) -> None:
        self.rebalance_band = float(rebalance_band)
        self.min_gamma = float(min_gamma)
        self.scalp_threshold = float(scalp_threshold)
        super().__init__(
            algorithm_key="gamma_scalping",
            symbol=symbol,
            family="volatility_options",
            subcategory="gamma",
            rows=rows,
        )

    def _hedge_band(self) -> float:
        return self.rebalance_band

    def _evaluate_row(
        self, metrics: OptionSurfaceDecisionMetrics, *, index: int
    ) -> tuple[str, float, float, tuple[str, ...], dict[str, object]]:
        delta_outside_band = metrics.hedge_rebalance_required
        rich_gamma = metrics.net_gamma >= self.min_gamma
        move_large_enough = abs(metrics.expected_move_gap) >= self.scalp_threshold
        signal_label = "neutral"
        score = 0.0
        reason_code = "gamma_scalping_hold"
        if rich_gamma and delta_outside_band and move_large_enough:
            signal_label = "buy"
            score = min(1.0, abs(metrics.expected_move_gap) / max(self.scalp_threshold, 1e-6))
            reason_code = "gamma_scalping_rehedge"
        elif not rich_gamma:
            reason_code = "gamma_too_low"
        elif not delta_outside_band:
            reason_code = "delta_inside_band"
        confidence = min(1.0, abs(score))
        return (
            signal_label,
            score,
            confidence,
            (reason_code,),
            {
                "rebalance_band": self.rebalance_band,
                "min_gamma": self.min_gamma,
                "scalp_threshold": self.scalp_threshold,
                "delta_outside_band": delta_outside_band,
                "hedge_rebalance_required": metrics.hedge_rebalance_required,
            },
        )


def build_gamma_scalping_algorithm(
    *, symbol: str, alg_param: dict[str, object], **_: object
) -> GammaScalpingAlgorithm:
    rows = cast(list[dict[str, Any]], alg_param["rows"])
    return GammaScalpingAlgorithm(
        symbol=symbol,
        rows=rows,
        rebalance_band=float(cast(float, alg_param["rebalance_band"])),
        min_gamma=float(cast(float, alg_param["min_gamma"])),
        scalp_threshold=float(cast(float, alg_param["scalp_threshold"])),
    )