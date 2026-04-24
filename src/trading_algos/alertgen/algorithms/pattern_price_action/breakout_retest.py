from __future__ import annotations

from trading_algos.alertgen.algorithms.pattern_price_action.base import (
    BasePatternAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.pattern_price_action.pattern_helpers import (
    PatternSignalState,
    scale_score,
)
from trading_algos.alertgen.shared_utils.common import TREND


class BreakoutRetestAlertAlgorithm(BasePatternAlertAlgorithm):
    catalog_ref = "algorithm:71"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        breakout_window: int = 5,
        breakout_buffer: float = 0.2,
        retest_tolerance: float = 0.3,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.breakout_window = breakout_window
        self.breakout_buffer = float(breakout_buffer)
        self.retest_tolerance = float(retest_tolerance)
        super().__init__(
            f"breakout_retest_window={breakout_window}",
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return self.breakout_window + 2

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "breakout_window": self.breakout_window,
            "breakout_buffer": self.breakout_buffer,
            "retest_tolerance": self.retest_tolerance,
            "pattern_type": "breakout_retest",
        }

    def _state_annotations(self) -> dict[str, object]:
        return {
            "breakout_level": self.latest_data_modifiable.get("breakout_level"),
            "breakout_detected": self.latest_data_modifiable.get("breakout_detected"),
            "retest_distance": self.latest_data_modifiable.get("retest_distance"),
            "retest_confirmed": self.latest_data_modifiable.get("retest_confirmed"),
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
                threshold_value=self.retest_tolerance,
                exit_value=None,
                aligned_count=0,
                reason_code="warmup_pending",
            )

        lookback = self.data_list[-self.breakout_window - 2 : -2]
        breakout_level = max(float(item["High"]) for item in lookback)
        previous = self.data_list[-2]
        latest = self.data_list[-1]
        previous_close = float(previous["Close"])
        low_value = float(latest["Low"])
        close_value = float(latest["Close"])
        breakout_detected = previous_close >= breakout_level + self.breakout_buffer
        retest_distance = low_value - breakout_level
        retest_confirmed = (
            breakout_detected
            and abs(retest_distance) <= self.retest_tolerance
            and close_value >= breakout_level + self.breakout_buffer
        )
        self.latest_data_modifiable["breakout_level"] = breakout_level
        self.latest_data_modifiable["breakout_detected"] = breakout_detected
        self.latest_data_modifiable["retest_distance"] = retest_distance
        self.latest_data_modifiable["retest_confirmed"] = retest_confirmed

        if retest_confirmed:
            reason_code = "breakout_retest_bullish"
            aligned_count = 2
        elif breakout_detected:
            reason_code = "breakout_waiting_retest"
            aligned_count = 1
        else:
            reason_code = "awaiting_breakout"
            aligned_count = 0

        return PatternSignalState(
            regime=TREND.UP if retest_confirmed else TREND.UNKNOWN,
            score=scale_score(
                close_value - breakout_level, max(self.breakout_buffer, 1e-9)
            ),
            bullish=retest_confirmed,
            bearish=False,
            primary_value=close_value - breakout_level,
            signal_value=breakout_level,
            threshold_value=self.breakout_buffer,
            exit_value=retest_distance,
            aligned_count=aligned_count,
            reason_code=reason_code,
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "Breakout Level",
                "y": [item.get("breakout_level") for item in self.data_list],
                "line": {"color": "#ff7f0e"},
            }
        ]
