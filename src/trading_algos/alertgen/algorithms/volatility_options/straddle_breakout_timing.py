from __future__ import annotations

from trading_algos.alertgen.algorithms.volatility_options.options_surface_algorithm import (
    BaseOptionsSurfaceAlgorithm,
)
from trading_algos.alertgen.algorithms.volatility_options.options_surface_helpers import (
    OptionSurfaceDecisionMetrics,
)


class StraddleBreakoutTimingAlgorithm(BaseOptionsSurfaceAlgorithm):
    catalog_ref = "algorithm:61"

    def __init__(
        self,
        *,
        symbol: str,
        rows: list[dict[str, object]],
        move_threshold: float = 0.01,
    ) -> None:
        self.move_threshold = float(move_threshold)
        super().__init__(
            algorithm_key="straddle_breakout_timing",
            symbol=symbol,
            family="volatility_options",
            subcategory="straddle",
            rows=rows,
        )

    def _evaluate_row(
        self, metrics: OptionSurfaceDecisionMetrics, *, index: int
    ) -> tuple[str, float, float, tuple[str, ...], dict[str, object]]:
        gap = metrics.expected_move_gap
        signal_label = "neutral"
        score = 0.0
        reason_code = "straddle_timing_wait"
        if gap >= self.move_threshold:
            signal_label = "buy"
            score = min(1.0, gap / max(self.move_threshold, 1e-6))
            reason_code = "straddle_breakout_long_vol"
        confidence = min(1.0, abs(score))
        return (
            signal_label,
            score,
            confidence,
            (reason_code,),
            {
                "move_threshold": self.move_threshold,
                "expected_move_gap": gap,
            },
        )


def build_straddle_breakout_timing_algorithm(
    *, symbol: str, alg_param: dict[str, object], **_: object
) -> StraddleBreakoutTimingAlgorithm:
    return StraddleBreakoutTimingAlgorithm(
        symbol=symbol,
        rows=list(alg_param["rows"]),
        move_threshold=float(alg_param["move_threshold"]),
    )