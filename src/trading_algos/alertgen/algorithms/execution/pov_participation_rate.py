from __future__ import annotations

from typing import Any, cast

from trading_algos.alertgen.algorithms.execution.base import BaseExecutionAlertAlgorithm


class POVParticipationRateAlertAlgorithm(BaseExecutionAlertAlgorithm):
    catalog_ref = "algorithm:96"

    def __init__(
        self,
        *,
        symbol: str,
        rows: list[dict[str, object]],
        parent_order: dict[str, object],
        participation_rate: float,
    ) -> None:
        self.participation_rate = float(participation_rate)
        super().__init__(
            algorithm_key="pov_participation_rate",
            symbol=symbol,
            subcategory="pov",
            rows=cast(list[dict[str, Any]], rows),
            parent_order=cast(dict[str, Any], parent_order),
        )

    def _target_quantities(self) -> list[float]:
        cumulative = 0.0
        quantity = float(self.parent_order["quantity"])
        targets: list[float] = []
        for row in self.rows:
            cumulative = min(
                quantity,
                cumulative + float(row["available_volume"]) * self.participation_rate,
            )
            targets.append(cumulative)
        return targets


def build_pov_participation_rate_algorithm(
    *, symbol: str, alg_param: dict[str, object], **_: object
) -> POVParticipationRateAlertAlgorithm:
    return POVParticipationRateAlertAlgorithm(
        symbol=symbol,
        rows=cast(list[dict[str, object]], alg_param["rows"]),
        parent_order=cast(dict[str, object], alg_param["parent_order"]),
        participation_rate=float(cast(float, alg_param["participation_rate"])),
    )
