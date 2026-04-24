from __future__ import annotations

from typing import Any, cast

from trading_algos.alertgen.algorithms.execution.base import (
    BaseExecutionAlertAlgorithm,
    ExecutionMetrics,
)


class ImplementationShortfallArrivalPriceAlertAlgorithm(BaseExecutionAlertAlgorithm):
    catalog_ref = "algorithm:97"

    def __init__(
        self,
        *,
        symbol: str,
        rows: list[dict[str, object]],
        parent_order: dict[str, object],
        urgency: float = 0.5,
        arrival_price: float = 0.0,
    ) -> None:
        self.urgency = float(urgency)
        self.arrival_price = float(arrival_price)
        super().__init__(
            algorithm_key="implementation_shortfall_arrival_price",
            symbol=symbol,
            subcategory="implementation",
            rows=cast(list[dict[str, Any]], rows),
            parent_order=cast(dict[str, Any], parent_order),
        )

    def _target_quantities(self) -> list[float]:
        quantity = float(self.parent_order["quantity"])
        if len(self.rows) == 1:
            return [quantity]
        weights = [
            self.urgency + ((len(self.rows) - index - 1) / max(len(self.rows) - 1, 1))
            for index, _ in enumerate(self.rows)
        ]
        total = sum(weights)
        cumulative = 0.0
        result: list[float] = []
        for weight in weights:
            cumulative += quantity * weight / total
            result.append(cumulative)
        return result

    def _row_reason(
        self, metrics: ExecutionMetrics, target_qty: float, achieved_qty: float
    ) -> str:
        if (
            self.arrival_price
            and metrics.reference_price > self.arrival_price
            and self.parent_order["side"] == "buy"
        ):
            return "arrival_price_slippage_risk"
        return "implementation_shortfall_active"


def build_implementation_shortfall_arrival_price_algorithm(
    *, symbol: str, alg_param: dict[str, object], **_: object
) -> ImplementationShortfallArrivalPriceAlertAlgorithm:
    return ImplementationShortfallArrivalPriceAlertAlgorithm(
        symbol=symbol,
        rows=cast(list[dict[str, object]], alg_param["rows"]),
        parent_order=cast(dict[str, object], alg_param["parent_order"]),
        urgency=float(cast(float, alg_param["urgency"])),
        arrival_price=float(cast(float, alg_param["arrival_price"])),
    )
