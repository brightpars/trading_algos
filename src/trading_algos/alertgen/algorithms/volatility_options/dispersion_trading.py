from __future__ import annotations

from trading_algos.alertgen.algorithms.volatility_options.options_surface_algorithm import (
    BaseOptionsSurfaceAlgorithm,
)
from trading_algos.alertgen.algorithms.volatility_options.options_surface_helpers import (
    OptionSurfaceDecisionMetrics,
)


class DispersionTradingAlgorithm(BaseOptionsSurfaceAlgorithm):
    catalog_ref = "algorithm:58"

    def __init__(
        self,
        *,
        symbol: str,
        rows: list[dict[str, object]],
        entry_threshold: float = 0.02,
    ) -> None:
        self.entry_threshold = float(entry_threshold)
        super().__init__(
            algorithm_key="dispersion_trading",
            symbol=symbol,
            family="volatility_options",
            subcategory="dispersion",
            rows=rows,
        )

    def _selection_mode(self) -> str:
        return "dispersion"

    def _evaluate_row(
        self, metrics: OptionSurfaceDecisionMetrics, *, index: int
    ) -> tuple[str, float, float, tuple[str, ...], dict[str, object]]:
        gap = metrics.dispersion_gap
        signal_label = "neutral"
        score = 0.0
        reason_code = "dispersion_neutral"
        if gap >= self.entry_threshold:
            signal_label = "sell"
            score = -min(1.0, gap / max(self.entry_threshold, 1e-6))
            reason_code = "dispersion_short_index_vol"
        elif gap <= -self.entry_threshold:
            signal_label = "buy"
            score = min(1.0, abs(gap) / max(self.entry_threshold, 1e-6))
            reason_code = "dispersion_long_index_vol"
        confidence = min(1.0, abs(score))
        return (
            signal_label,
            score,
            confidence,
            (reason_code,),
            {
                "entry_threshold": self.entry_threshold,
                "dispersion_metric": gap,
            },
        )


def build_dispersion_trading_algorithm(
    *, symbol: str, alg_param: dict[str, object], **_: object
) -> DispersionTradingAlgorithm:
    return DispersionTradingAlgorithm(
        symbol=symbol,
        rows=list(alg_param["rows"]),
        entry_threshold=float(alg_param["entry_threshold"]),
    )