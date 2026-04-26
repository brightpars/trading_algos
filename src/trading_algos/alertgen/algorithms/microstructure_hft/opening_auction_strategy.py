from __future__ import annotations

from typing import Any, cast

from trading_algos.alertgen.algorithms.microstructure_hft.base import (
    BaseMicrostructureAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.microstructure_hft.helpers import (
    MicrostructureMetrics,
)


class OpeningAuctionStrategyAlertAlgorithm(BaseMicrostructureAlertAlgorithm):
    catalog_ref = "algorithm:68"

    def __init__(
        self,
        *,
        symbol: str,
        rows: list[dict[str, object]],
        own_order_rows: list[dict[str, object]],
        auction_threshold: float = 50.0,
    ) -> None:
        self.auction_threshold = float(auction_threshold)
        super().__init__(
            algorithm_key="opening_auction_strategy",
            symbol=symbol,
            subcategory="opening",
            rows=cast(list[dict[str, Any]], rows),
            own_order_rows=cast(list[dict[str, Any]], own_order_rows),
        )

    def _evaluate_row(self, metrics: MicrostructureMetrics, *, index: int):
        if metrics.session_phase != "opening":
            return "neutral", 0.0, 0.0, ("outside_opening_auction",), {}
        if metrics.auction_imbalance >= self.auction_threshold:
            return "buy", 1.0, 0.9, ("opening_auction_buy_pressure",), {}
        if metrics.auction_imbalance <= -self.auction_threshold:
            return "sell", -1.0, 0.9, ("opening_auction_sell_pressure",), {}
        return "neutral", 0.0, 0.1, ("opening_auction_balanced",), {}


def build_opening_auction_strategy_algorithm(
    *, symbol: str, alg_param: dict[str, object], **_: object
) -> OpeningAuctionStrategyAlertAlgorithm:
    return OpeningAuctionStrategyAlertAlgorithm(
        symbol=symbol,
        rows=cast(list[dict[str, object]], alg_param["rows"]),
        own_order_rows=cast(list[dict[str, object]], alg_param["own_order_rows"]),
        auction_threshold=float(cast(float, alg_param["auction_threshold"])),
    )
