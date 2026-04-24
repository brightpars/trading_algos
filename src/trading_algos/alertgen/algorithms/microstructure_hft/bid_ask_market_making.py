from __future__ import annotations

from typing import Any, cast

from trading_algos.alertgen.algorithms.microstructure_hft.base import (
    BaseMicrostructureAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.microstructure_hft.helpers import (
    MicrostructureMetrics,
)


class BidAskMarketMakingAlertAlgorithm(BaseMicrostructureAlertAlgorithm):
    catalog_ref = "algorithm:62"

    def __init__(
        self,
        *,
        symbol: str,
        rows: list[dict[str, object]],
        own_order_rows: list[dict[str, object]],
        min_spread: float = 0.01,
        inventory_limit: float = 100.0,
    ) -> None:
        self.min_spread = float(min_spread)
        self.inventory_limit = float(inventory_limit)
        super().__init__(
            algorithm_key="bid_ask_market_making",
            symbol=symbol,
            subcategory="bid",
            rows=cast(list[dict[str, Any]], rows),
            own_order_rows=cast(list[dict[str, Any]], own_order_rows),
        )

    def _evaluate_row(self, metrics: MicrostructureMetrics, *, index: int):
        if metrics.spread < self.min_spread:
            return "neutral", 0.0, 0.0, ("spread_too_tight",), {"quote_mode": "idle"}
        if abs(metrics.inventory) > self.inventory_limit:
            signal = "sell" if metrics.inventory > 0 else "buy"
            return (
                signal,
                0.5 if signal == "buy" else -0.5,
                0.5,
                ("inventory_rebalance",),
                {"quote_mode": "inventory_rebalance"},
            )
        return "neutral", 0.1, 0.4, ("quote_both_sides",), {"quote_mode": "two_sided"}


def build_bid_ask_market_making_algorithm(
    *, symbol: str, alg_param: dict[str, object], **_: object
) -> BidAskMarketMakingAlertAlgorithm:
    return BidAskMarketMakingAlertAlgorithm(
        symbol=symbol,
        rows=cast(list[dict[str, object]], alg_param["rows"]),
        own_order_rows=cast(list[dict[str, object]], alg_param["own_order_rows"]),
        min_spread=float(cast(float, alg_param["min_spread"])),
        inventory_limit=float(cast(float, alg_param["inventory_limit"])),
    )
