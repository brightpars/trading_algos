from __future__ import annotations

from trading_algos.alertgen.algorithms.volatility_options.options_surface_algorithm import (
    BaseOptionsSurfaceAlgorithm,
)
from trading_algos.alertgen.algorithms.volatility_options.options_surface_helpers import (
    OptionSurfaceDecisionMetrics,
)


class SkewTradingAlgorithm(BaseOptionsSurfaceAlgorithm):
    catalog_ref = "algorithm:59"

    def __init__(
        self,
        *,
        symbol: str,
        rows: list[dict[str, object]],
        entry_threshold: float = 0.02,
    ) -> None:
        self.entry_threshold = float(entry_threshold)
        super().__init__(
            algorithm_key="skew_trading",
            symbol=symbol,
            family="volatility_options",
            subcategory="skew",
            rows=rows,
        )

    def _selection_mode(self) -> str:
        return "skew"

    def _evaluate_row(
        self, metrics: OptionSurfaceDecisionMetrics, *, index: int
    ) -> tuple[str, float, float, tuple[str, ...], dict[str, object]]:
        skew = metrics.put_call_skew
        signal_label = "neutral"
        score = 0.0
        reason_code = "skew_neutral"
        if skew >= self.entry_threshold:
            signal_label = "sell"
            score = -min(1.0, skew / max(self.entry_threshold, 1e-6))
            reason_code = "skew_short_put_richness"
        elif skew <= -self.entry_threshold:
            signal_label = "buy"
            score = min(1.0, abs(skew) / max(self.entry_threshold, 1e-6))
            reason_code = "skew_long_put_richness"
        confidence = min(1.0, abs(score))
        return (
            signal_label,
            score,
            confidence,
            (reason_code,),
            {
                "entry_threshold": self.entry_threshold,
                "skew_metric": skew,
            },
        )


def build_skew_trading_algorithm(
    *, symbol: str, alg_param: dict[str, object], **_: object
) -> SkewTradingAlgorithm:
    return SkewTradingAlgorithm(
        symbol=symbol,
        rows=list(alg_param["rows"]),
        entry_threshold=float(alg_param["entry_threshold"]),
    )