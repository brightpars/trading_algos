from __future__ import annotations

from typing import Any, cast

from trading_algos.alertgen.algorithms.volatility_options.options_surface_algorithm import (
    BaseOptionsSurfaceAlgorithm,
)
from trading_algos.alertgen.algorithms.volatility_options.options_surface_helpers import (
    OptionSurfaceDecisionMetrics,
)


class TermStructureTradingAlgorithm(BaseOptionsSurfaceAlgorithm):
    catalog_ref = "algorithm:60"

    def __init__(
        self,
        *,
        symbol: str,
        rows: list[dict[str, object]],
        entry_threshold: float = 0.02,
    ) -> None:
        self.entry_threshold = float(entry_threshold)
        super().__init__(
            algorithm_key="term_structure_trading",
            symbol=symbol,
            family="volatility_options",
            subcategory="term",
            rows=rows,
        )

    def _selection_mode(self) -> str:
        return "term"

    def _evaluate_row(
        self, metrics: OptionSurfaceDecisionMetrics, *, index: int
    ) -> tuple[str, float, float, tuple[str, ...], dict[str, object]]:
        slope = metrics.term_structure_slope
        signal_label = "neutral"
        score = 0.0
        reason_code = "term_structure_neutral"
        if slope >= self.entry_threshold:
            signal_label = "sell"
            score = -min(1.0, slope / max(self.entry_threshold, 1e-6))
            reason_code = "term_structure_short_front"
        elif slope <= -self.entry_threshold:
            signal_label = "buy"
            score = min(1.0, abs(slope) / max(self.entry_threshold, 1e-6))
            reason_code = "term_structure_long_front"
        confidence = min(1.0, abs(score))
        return (
            signal_label,
            score,
            confidence,
            (reason_code,),
            {
                "entry_threshold": self.entry_threshold,
                "slope_metric": slope,
            },
        )


def build_term_structure_trading_algorithm(
    *, symbol: str, alg_param: dict[str, object], **_: object
) -> TermStructureTradingAlgorithm:
    rows = cast(list[dict[str, Any]], alg_param["rows"])
    return TermStructureTradingAlgorithm(
        symbol=symbol,
        rows=rows,
        entry_threshold=float(cast(float, alg_param["entry_threshold"])),
    )