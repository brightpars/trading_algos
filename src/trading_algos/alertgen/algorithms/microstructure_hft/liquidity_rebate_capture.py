from __future__ import annotations

from typing import Any, cast

from trading_algos.alertgen.algorithms.microstructure_hft.base import (
    BaseMicrostructureAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.microstructure_hft.helpers import (
    MicrostructureMetrics,
)


class LiquidityRebateCaptureAlertAlgorithm(BaseMicrostructureAlertAlgorithm):
    catalog_ref = "algorithm:67"

    def __init__(
        self,
        *,
        symbol: str,
        rows: list[dict[str, object]],
        own_order_rows: list[dict[str, object]],
        maker_rebate: float = 0.002,
        adverse_selection_buffer: float = 0.001,
    ) -> None:
        self.maker_rebate = float(maker_rebate)
        self.adverse_selection_buffer = float(adverse_selection_buffer)
        super().__init__(
            algorithm_key="liquidity_rebate_capture",
            symbol=symbol,
            subcategory="liquidity",
            rows=cast(list[dict[str, Any]], rows),
            own_order_rows=cast(list[dict[str, Any]], own_order_rows),
        )

    def _evaluate_row(self, metrics: MicrostructureMetrics, *, index: int):
        maker_edge = (
            metrics.spread
            + self.maker_rebate
            - abs(metrics.microprice_edge)
            - self.adverse_selection_buffer
        )
        if maker_edge <= 0.0:
            return (
                "neutral",
                0.0,
                0.1,
                ("maker_edge_negative",),
                {"maker_edge": maker_edge},
            )
        signal = "buy" if metrics.imbalance >= 0.0 else "sell"
        score = min(1.0, maker_edge / max(self.maker_rebate, 1e-9))
        if signal == "sell":
            score = -score
        return (
            signal,
            score,
            min(1.0, abs(score)),
            ("rebate_capture_setup",),
            {"maker_edge": maker_edge},
        )


def build_liquidity_rebate_capture_algorithm(
    *, symbol: str, alg_param: dict[str, object], **_: object
) -> LiquidityRebateCaptureAlertAlgorithm:
    return LiquidityRebateCaptureAlertAlgorithm(
        symbol=symbol,
        rows=cast(list[dict[str, object]], alg_param["rows"]),
        own_order_rows=cast(list[dict[str, object]], alg_param["own_order_rows"]),
        maker_rebate=float(cast(float, alg_param["maker_rebate"])),
        adverse_selection_buffer=float(
            cast(float, alg_param["adverse_selection_buffer"])
        ),
    )
