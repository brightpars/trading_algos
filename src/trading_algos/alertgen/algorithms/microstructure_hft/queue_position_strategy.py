from __future__ import annotations

from typing import Any, cast

from trading_algos.alertgen.algorithms.microstructure_hft.base import (
    BaseMicrostructureAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.microstructure_hft.helpers import (
    MicrostructureMetrics,
)


class QueuePositionStrategyAlertAlgorithm(BaseMicrostructureAlertAlgorithm):
    catalog_ref = "algorithm:66"

    def __init__(
        self,
        *,
        symbol: str,
        rows: list[dict[str, object]],
        own_order_rows: list[dict[str, object]],
        keep_threshold: float = 0.4,
        cancel_threshold: float = 0.2,
    ) -> None:
        self.keep_threshold = float(keep_threshold)
        self.cancel_threshold = float(cancel_threshold)
        super().__init__(
            algorithm_key="queue_position_strategy",
            symbol=symbol,
            subcategory="queue",
            rows=cast(list[dict[str, Any]], rows),
            own_order_rows=cast(list[dict[str, Any]], own_order_rows),
        )

    def _evaluate_row(self, metrics: MicrostructureMetrics, *, index: int):
        if metrics.queue_fill_probability >= self.keep_threshold:
            return (
                "buy",
                metrics.queue_fill_probability,
                metrics.queue_fill_probability,
                ("queue_priority_improving",),
                {"action": "keep_resting"},
            )
        if metrics.queue_fill_probability <= self.cancel_threshold:
            return (
                "sell",
                -1.0 + metrics.queue_fill_probability,
                1.0 - metrics.queue_fill_probability,
                ("cancel_replace_required",),
                {"action": "cancel_or_amend"},
            )
        return "neutral", 0.0, 0.2, ("queue_wait",), {"action": "wait"}


def build_queue_position_strategy_algorithm(
    *, symbol: str, alg_param: dict[str, object], **_: object
) -> QueuePositionStrategyAlertAlgorithm:
    return QueuePositionStrategyAlertAlgorithm(
        symbol=symbol,
        rows=cast(list[dict[str, object]], alg_param["rows"]),
        own_order_rows=cast(list[dict[str, object]], alg_param["own_order_rows"]),
        keep_threshold=float(cast(float, alg_param["keep_threshold"])),
        cancel_threshold=float(cast(float, alg_param["cancel_threshold"])),
    )
