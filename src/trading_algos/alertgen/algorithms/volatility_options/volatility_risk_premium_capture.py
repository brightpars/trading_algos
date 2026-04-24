from __future__ import annotations

from typing import Any, cast

from trading_algos.alertgen.algorithms.volatility_options.options_surface_algorithm import (
    BaseOptionsSurfaceAlgorithm,
)
from trading_algos.alertgen.algorithms.volatility_options.options_surface_helpers import (
    OptionSurfaceDecisionMetrics,
)


class VolatilityRiskPremiumCaptureAlgorithm(BaseOptionsSurfaceAlgorithm):
    catalog_ref = "algorithm:57"

    def __init__(
        self,
        *,
        symbol: str,
        rows: list[dict[str, object]],
        premium_threshold: float = 0.05,
        policy: str = "short_vol",
    ) -> None:
        self.premium_threshold = float(premium_threshold)
        self.policy = policy
        super().__init__(
            algorithm_key="volatility_risk_premium_capture",
            symbol=symbol,
            family="volatility_options",
            subcategory="volatility",
            rows=rows,
        )

    def _evaluate_row(
        self, metrics: OptionSurfaceDecisionMetrics, *, index: int
    ) -> tuple[str, float, float, tuple[str, ...], dict[str, object]]:
        premium = metrics.iv_rv_gap
        signal_label = "neutral"
        score = 0.0
        reason_code = "premium_inside_band"
        if premium >= self.premium_threshold:
            if self.policy == "long_vol":
                signal_label = "neutral"
                score = 0.0
                reason_code = "premium_short_vol_filtered"
            elif self.policy == "balanced":
                signal_label = "sell"
                score = -min(1.0, premium / max(self.premium_threshold, 1e-6))
                reason_code = "premium_short_vol"
            else:
                signal_label = "sell"
                score = -min(1.0, premium / max(self.premium_threshold, 1e-6))
                reason_code = "premium_short_vol"
        elif premium <= -self.premium_threshold:
            if self.policy == "short_vol":
                signal_label = "neutral"
                score = 0.0
                reason_code = "premium_long_vol_filtered"
            else:
                signal_label = "buy"
                score = min(1.0, abs(premium) / max(self.premium_threshold, 1e-6))
                reason_code = "premium_long_vol"
        confidence = min(1.0, abs(score))
        return (
            signal_label,
            score,
            confidence,
            (reason_code,),
            {
                "premium_threshold": self.premium_threshold,
                "policy": self.policy,
                "premium_value": premium,
            },
        )


def build_volatility_risk_premium_capture_algorithm(
    *, symbol: str, alg_param: dict[str, object], **_: object
) -> VolatilityRiskPremiumCaptureAlgorithm:
    rows = cast(list[dict[str, Any]], alg_param["rows"])
    return VolatilityRiskPremiumCaptureAlgorithm(
        symbol=symbol,
        rows=rows,
        premium_threshold=float(cast(float, alg_param["premium_threshold"])),
        policy=str(alg_param["policy"]),
    )