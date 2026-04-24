from __future__ import annotations

from typing import Any, cast

from trading_algos.alertgen.algorithms.microstructure_hft.base import (
    BaseMicrostructureAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.microstructure_hft.helpers import (
    MicrostructureMetrics,
)


class InventorySkewedMarketMakingAlertAlgorithm(BaseMicrostructureAlertAlgorithm):
    catalog_ref = "algorithm:63"

    def __init__(
        self,
        *,
        symbol: str,
        rows: list[dict[str, object]],
        own_order_rows: list[dict[str, object]],
        inventory_target: float = 0.0,
        skew_sensitivity: float = 0.01,
    ) -> None:
        self.inventory_target = float(inventory_target)
        self.skew_sensitivity = float(skew_sensitivity)
        super().__init__(
            algorithm_key="inventory_skewed_market_making",
            symbol=symbol,
            subcategory="inventory",
            rows=cast(list[dict[str, Any]], rows),
            own_order_rows=cast(list[dict[str, Any]], own_order_rows),
        )

    def _evaluate_row(self, metrics: MicrostructureMetrics, *, index: int):
        gap = self.inventory_target - metrics.inventory
        if abs(gap) <= self.skew_sensitivity:
            return "neutral", 0.0, 0.2, ("inventory_on_target",), {"inventory_gap": gap}
        signal = "buy" if gap > 0 else "sell"
        score = max(-1.0, min(1.0, gap / max(self.skew_sensitivity, 1e-9)))
        return (
            signal,
            score,
            min(1.0, abs(score)),
            ("inventory_skew_active",),
            {"inventory_gap": gap},
        )


def build_inventory_skewed_market_making_algorithm(
    *, symbol: str, alg_param: dict[str, object], **_: object
) -> InventorySkewedMarketMakingAlertAlgorithm:
    return InventorySkewedMarketMakingAlertAlgorithm(
        symbol=symbol,
        rows=cast(list[dict[str, object]], alg_param["rows"]),
        own_order_rows=cast(list[dict[str, object]], alg_param["own_order_rows"]),
        inventory_target=float(cast(float, alg_param["inventory_target"])),
        skew_sensitivity=float(cast(float, alg_param["skew_sensitivity"])),
    )
