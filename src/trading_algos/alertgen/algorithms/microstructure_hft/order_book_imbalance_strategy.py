from __future__ import annotations

from typing import Any, cast

from trading_algos.alertgen.algorithms.microstructure_hft.base import (
    BaseMicrostructureAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.microstructure_hft.helpers import (
    MicrostructureMetrics,
)


class OrderBookImbalanceStrategyAlertAlgorithm(BaseMicrostructureAlertAlgorithm):
    catalog_ref = "algorithm:64"

    def __init__(
        self,
        *,
        symbol: str,
        rows: list[dict[str, object]],
        own_order_rows: list[dict[str, object]],
        imbalance_threshold: float = 0.2,
    ) -> None:
        self.imbalance_threshold = float(imbalance_threshold)
        super().__init__(
            algorithm_key="order_book_imbalance_strategy",
            symbol=symbol,
            subcategory="order",
            rows=cast(list[dict[str, Any]], rows),
            own_order_rows=cast(list[dict[str, Any]], own_order_rows),
        )

    def _evaluate_row(self, metrics: MicrostructureMetrics, *, index: int):
        if metrics.imbalance >= self.imbalance_threshold:
            return (
                "buy",
                min(1.0, metrics.imbalance / self.imbalance_threshold),
                min(1.0, abs(metrics.imbalance)),
                ("bid_depth_dominant",),
                {},
            )
        if metrics.imbalance <= -self.imbalance_threshold:
            return (
                "sell",
                max(-1.0, metrics.imbalance / self.imbalance_threshold),
                min(1.0, abs(metrics.imbalance)),
                ("ask_depth_dominant",),
                {},
            )
        return "neutral", 0.0, 0.1, ("imbalance_neutral",), {}


def build_order_book_imbalance_strategy_algorithm(
    *, symbol: str, alg_param: dict[str, object], **_: object
) -> OrderBookImbalanceStrategyAlertAlgorithm:
    return OrderBookImbalanceStrategyAlertAlgorithm(
        symbol=symbol,
        rows=cast(list[dict[str, object]], alg_param["rows"]),
        own_order_rows=cast(list[dict[str, object]], alg_param["own_order_rows"]),
        imbalance_threshold=float(cast(float, alg_param["imbalance_threshold"])),
    )
