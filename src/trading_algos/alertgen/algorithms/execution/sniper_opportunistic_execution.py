from __future__ import annotations

from typing import Any, cast

from trading_algos.alertgen.algorithms.execution.base import (
    BaseExecutionAlertAlgorithm,
    ExecutionMetrics,
)


class SniperOpportunisticExecutionAlertAlgorithm(BaseExecutionAlertAlgorithm):
    catalog_ref = "algorithm:99"

    def __init__(
        self,
        *,
        symbol: str,
        rows: list[dict[str, object]],
        parent_order: dict[str, object],
        spread_threshold: float = 0.02,
        volume_threshold: float = 0.0,
    ) -> None:
        self.spread_threshold = float(spread_threshold)
        self.volume_threshold = float(volume_threshold)
        super().__init__(
            algorithm_key="sniper_opportunistic_execution",
            symbol=symbol,
            subcategory="sniper",
            rows=cast(list[dict[str, Any]], rows),
            parent_order=cast(dict[str, Any], parent_order),
        )

    def _target_quantities(self) -> list[float]:
        quantity = float(self.parent_order["quantity"])
        triggered = 0.0
        result: list[float] = []
        for row in self.rows:
            if (
                float(row.get("spread", 0.0)) <= self.spread_threshold
                and float(row["available_volume"]) >= self.volume_threshold
            ):
                triggered = quantity
            result.append(triggered)
        return result

    def _row_reason(
        self, metrics: ExecutionMetrics, target_qty: float, achieved_qty: float
    ) -> str:
        return "sniper_triggered" if target_qty > 0.0 else "waiting_for_liquidity"


def build_sniper_opportunistic_execution_algorithm(
    *, symbol: str, alg_param: dict[str, object], **_: object
) -> SniperOpportunisticExecutionAlertAlgorithm:
    return SniperOpportunisticExecutionAlertAlgorithm(
        symbol=symbol,
        rows=cast(list[dict[str, object]], alg_param["rows"]),
        parent_order=cast(dict[str, object], alg_param["parent_order"]),
        spread_threshold=float(cast(float, alg_param["spread_threshold"])),
        volume_threshold=float(cast(float, alg_param["volume_threshold"])),
    )
