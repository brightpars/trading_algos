from __future__ import annotations

from typing import Any, cast

from trading_algos.alertgen.algorithms.microstructure_hft.base import (
    BaseMicrostructureAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.microstructure_hft.helpers import (
    MicrostructureMetrics,
)


class MicropriceStrategyAlertAlgorithm(BaseMicrostructureAlertAlgorithm):
    catalog_ref = "algorithm:65"

    def __init__(
        self,
        *,
        symbol: str,
        rows: list[dict[str, object]],
        own_order_rows: list[dict[str, object]],
        edge_threshold: float = 0.005,
    ) -> None:
        self.edge_threshold = float(edge_threshold)
        super().__init__(
            algorithm_key="microprice_strategy",
            symbol=symbol,
            subcategory="microprice",
            rows=cast(list[dict[str, Any]], rows),
            own_order_rows=cast(list[dict[str, Any]], own_order_rows),
        )

    def _evaluate_row(self, metrics: MicrostructureMetrics, *, index: int):
        if metrics.microprice_edge >= self.edge_threshold:
            return (
                "buy",
                min(1.0, metrics.microprice_edge / self.edge_threshold),
                0.7,
                ("microprice_above_mid",),
                {},
            )
        if metrics.microprice_edge <= -self.edge_threshold:
            return (
                "sell",
                max(-1.0, metrics.microprice_edge / self.edge_threshold),
                0.7,
                ("microprice_below_mid",),
                {},
            )
        return "neutral", 0.0, 0.1, ("microprice_balanced",), {}


def build_microprice_strategy_algorithm(
    *, symbol: str, alg_param: dict[str, object], **_: object
) -> MicropriceStrategyAlertAlgorithm:
    return MicropriceStrategyAlertAlgorithm(
        symbol=symbol,
        rows=cast(list[dict[str, object]], alg_param["rows"]),
        own_order_rows=cast(list[dict[str, object]], alg_param["own_order_rows"]),
        edge_threshold=float(cast(float, alg_param["edge_threshold"])),
    )
