from __future__ import annotations

from typing import Any, cast

from trading_algos.alertgen.algorithms.execution.base import (
    BaseExecutionAlertAlgorithm,
    ExecutionMetrics,
)


class TWAPAlertAlgorithm(BaseExecutionAlertAlgorithm):
    catalog_ref = "algorithm:94"

    def __init__(
        self,
        *,
        symbol: str,
        rows: list[dict[str, object]],
        parent_order: dict[str, object],
        intervals: int = 1,
        catch_up_factor: float = 1.0,
    ) -> None:
        self.intervals = int(intervals)
        self.catch_up_factor = float(catch_up_factor)
        super().__init__(
            algorithm_key="twap",
            symbol=symbol,
            subcategory="twap",
            rows=cast(list[dict[str, Any]], rows),
            parent_order=cast(dict[str, Any], parent_order),
        )

    def _target_quantities(self) -> list[float]:
        quantity = float(self.parent_order["quantity"])
        step = quantity / max(len(self.rows), 1)
        return [step * (index + 1) for index, _ in enumerate(self.rows)]

    def _row_reason(
        self, metrics: ExecutionMetrics, target_qty: float, achieved_qty: float
    ) -> str:
        return "catch_up_active" if achieved_qty < target_qty else "twap_on_schedule"

    def _extra_diagnostics(
        self, metrics: ExecutionMetrics, target_qty: float, achieved_qty: float
    ) -> dict[str, Any]:
        return {"catch_up_factor": self.catch_up_factor}


def build_twap_algorithm(
    *, symbol: str, alg_param: dict[str, object], **_: object
) -> TWAPAlertAlgorithm:
    return TWAPAlertAlgorithm(
        symbol=symbol,
        rows=cast(list[dict[str, object]], alg_param["rows"]),
        parent_order=cast(dict[str, object], alg_param["parent_order"]),
        intervals=int(cast(int, alg_param["intervals"])),
        catch_up_factor=float(cast(float, alg_param["catch_up_factor"])),
    )
