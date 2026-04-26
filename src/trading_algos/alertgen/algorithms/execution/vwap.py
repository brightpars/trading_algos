from __future__ import annotations

from typing import Any, cast

from trading_algos.alertgen.algorithms.execution.base import BaseExecutionAlertAlgorithm


class VWAPAlertAlgorithm(BaseExecutionAlertAlgorithm):
    catalog_ref = "algorithm:95"

    def __init__(
        self,
        *,
        symbol: str,
        rows: list[dict[str, object]],
        parent_order: dict[str, object],
        volume_curve: list[float],
    ) -> None:
        self.volume_curve = [float(value) for value in volume_curve]
        super().__init__(
            algorithm_key="vwap",
            symbol=symbol,
            subcategory="vwap",
            rows=cast(list[dict[str, Any]], rows),
            parent_order=cast(dict[str, Any], parent_order),
        )

    def _target_quantities(self) -> list[float]:
        quantity = float(self.parent_order["quantity"])
        total_curve = sum(self.volume_curve)
        cumulative = 0.0
        targets: list[float] = []
        for weight in self.volume_curve:
            cumulative += (
                0.0 if total_curve <= 0.0 else quantity * (weight / total_curve)
            )
            targets.append(cumulative)
        return targets


def build_vwap_algorithm(
    *, symbol: str, alg_param: dict[str, object], **_: object
) -> VWAPAlertAlgorithm:
    return VWAPAlertAlgorithm(
        symbol=symbol,
        rows=cast(list[dict[str, object]], alg_param["rows"]),
        parent_order=cast(dict[str, object], alg_param["parent_order"]),
        volume_curve=cast(list[float], alg_param["volume_curve"]),
    )
