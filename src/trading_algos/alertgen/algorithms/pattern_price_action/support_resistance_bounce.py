from __future__ import annotations

from trading_algos.alertgen.algorithms.pattern_price_action.base import (
    BasePatternAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.pattern_price_action.pattern_helpers import (
    PatternSignalState,
    scale_score,
)
from trading_algos.alertgen.shared_utils.common import TREND


class SupportResistanceBounceAlertAlgorithm(BasePatternAlertAlgorithm):
    catalog_ref = "algorithm:70"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        level_window: int = 5,
        touch_tolerance: float = 0.3,
        rejection_min_close_delta: float = 0.2,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.level_window = level_window
        self.touch_tolerance = float(touch_tolerance)
        self.rejection_min_close_delta = float(rejection_min_close_delta)
        super().__init__(
            (f"support_resistance_bounce_window={level_window}_tol={touch_tolerance}"),
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return self.level_window + 1

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "level_window": self.level_window,
            "touch_tolerance": self.touch_tolerance,
            "rejection_min_close_delta": self.rejection_min_close_delta,
            "pattern_type": "support_bounce",
        }

    def _state_annotations(self) -> dict[str, object]:
        return {
            "support_level": self.latest_data_modifiable.get("support_level"),
            "touch_distance": self.latest_data_modifiable.get("touch_distance"),
            "rejection_strength": self.latest_data_modifiable.get("rejection_strength"),
            "support_touched": self.latest_data_modifiable.get("support_touched"),
            "rejection_confirmed": self.latest_data_modifiable.get(
                "rejection_confirmed"
            ),
        }

    def _calculate_state(self) -> PatternSignalState:
        if len(self.data_list) < self.minimum_history():
            return PatternSignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                bullish=False,
                bearish=False,
                primary_value=None,
                signal_value=None,
                threshold_value=self.touch_tolerance,
                exit_value=None,
                aligned_count=0,
                reason_code="warmup_pending",
            )

        lookback = self.data_list[-self.level_window - 1 : -1]
        support_level = min(float(item["Low"]) for item in lookback)
        latest = self.data_list[-1]
        low_value = float(latest["Low"])
        close_value = float(latest["Close"])
        open_value = float(latest["Open"])
        touch_distance = low_value - support_level
        rejection_strength = close_value - support_level
        support_touched = abs(touch_distance) <= self.touch_tolerance
        rejection_confirmed = (
            support_touched
            and close_value >= support_level + self.rejection_min_close_delta
            and close_value > open_value
        )
        self.latest_data_modifiable["support_level"] = support_level
        self.latest_data_modifiable["touch_distance"] = touch_distance
        self.latest_data_modifiable["rejection_strength"] = rejection_strength
        self.latest_data_modifiable["support_touched"] = support_touched
        self.latest_data_modifiable["rejection_confirmed"] = rejection_confirmed

        if rejection_confirmed:
            reason_code = "support_rejection_bullish"
            aligned_count = 2
        elif support_touched:
            reason_code = "support_touch_waiting_rejection"
            aligned_count = 1
        else:
            reason_code = "awaiting_support_touch"
            aligned_count = 0

        return PatternSignalState(
            regime=TREND.UP if rejection_confirmed else TREND.UNKNOWN,
            score=scale_score(rejection_strength, max(self.touch_tolerance, 1e-9)),
            bullish=rejection_confirmed,
            bearish=False,
            primary_value=rejection_strength,
            signal_value=support_level,
            threshold_value=self.rejection_min_close_delta,
            exit_value=touch_distance,
            aligned_count=aligned_count,
            reason_code=reason_code,
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "Support Level",
                "y": [item.get("support_level") for item in self.data_list],
                "line": {"color": "#2ca02c"},
            }
        ]
