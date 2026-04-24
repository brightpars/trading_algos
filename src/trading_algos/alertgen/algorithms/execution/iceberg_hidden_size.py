from __future__ import annotations

from typing import Any, cast

from trading_algos.alertgen.algorithms.execution.base import BaseExecutionAlertAlgorithm


class IcebergHiddenSizeAlertAlgorithm(BaseExecutionAlertAlgorithm):
    catalog_ref = "algorithm:98"

    def __init__(
        self,
        *,
        symbol: str,
        rows: list[dict[str, object]],
        parent_order: dict[str, object],
        display_quantity: int,
    ) -> None:
        self.display_quantity = int(display_quantity)
        super().__init__(
            algorithm_key="iceberg_hidden_size",
            symbol=symbol,
            subcategory="iceberg",
            rows=cast(list[dict[str, Any]], rows),
            parent_order=cast(dict[str, Any], parent_order),
        )

    def _target_quantities(self) -> list[float]:
        cumulative = 0.0
        quantity = float(self.parent_order["quantity"])
        result: list[float] = []
        for _ in self.rows:
            cumulative = min(quantity, cumulative + self.display_quantity)
            result.append(cumulative)
        return result


def build_iceberg_hidden_size_algorithm(
    *, symbol: str, alg_param: dict[str, object], **_: object
) -> IcebergHiddenSizeAlertAlgorithm:
    return IcebergHiddenSizeAlertAlgorithm(
        symbol=symbol,
        rows=cast(list[dict[str, object]], alg_param["rows"]),
        parent_order=cast(dict[str, object], alg_param["parent_order"]),
        display_quantity=int(cast(int, alg_param["display_quantity"])),
    )
