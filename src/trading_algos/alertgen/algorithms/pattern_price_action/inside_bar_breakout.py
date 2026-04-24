from __future__ import annotations

from trading_algos.alertgen.algorithms.pattern_price_action.base import (
    BasePatternAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.pattern_price_action.pattern_helpers import (
    PatternSignalState,
    scale_score,
)
from trading_algos.alertgen.shared_utils.common import TREND


class InsideBarBreakoutAlertAlgorithm(BasePatternAlertAlgorithm):
    catalog_ref = "algorithm:74"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        breakout_buffer: float = 0.1,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.breakout_buffer = float(breakout_buffer)
        super().__init__(
            f"inside_bar_breakout_buffer={breakout_buffer}",
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return 3

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "breakout_buffer": self.breakout_buffer,
            "pattern_type": "inside_bar_breakout",
        }

    def _state_annotations(self) -> dict[str, object]:
        return {
            "mother_high": self.latest_data_modifiable.get("mother_high"),
            "mother_low": self.latest_data_modifiable.get("mother_low"),
            "inside_bar_detected": self.latest_data_modifiable.get(
                "inside_bar_detected"
            ),
            "breakout_distance": self.latest_data_modifiable.get("breakout_distance"),
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
                threshold_value=self.breakout_buffer,
                exit_value=None,
                aligned_count=0,
                reason_code="warmup_pending",
            )

        mother_bar = self.data_list[-3]
        inside_bar = self.data_list[-2]
        latest = self.data_list[-1]
        mother_high = float(mother_bar["High"])
        mother_low = float(mother_bar["Low"])
        inside_high = float(inside_bar["High"])
        inside_low = float(inside_bar["Low"])
        close_value = float(latest["Close"])
        inside_bar_detected = inside_high <= mother_high and inside_low >= mother_low
        breakout_distance = close_value - mother_high
        bullish = (
            inside_bar_detected and close_value >= mother_high + self.breakout_buffer
        )
        self.latest_data_modifiable["mother_high"] = mother_high
        self.latest_data_modifiable["mother_low"] = mother_low
        self.latest_data_modifiable["inside_bar_detected"] = inside_bar_detected
        self.latest_data_modifiable["breakout_distance"] = breakout_distance

        if bullish:
            reason_code = "inside_bar_breakout_bullish"
            aligned_count = 2
        elif inside_bar_detected:
            reason_code = "inside_bar_waiting_breakout"
            aligned_count = 1
        else:
            reason_code = "inside_bar_not_detected"
            aligned_count = 0

        return PatternSignalState(
            regime=TREND.UP if bullish else TREND.UNKNOWN,
            score=scale_score(breakout_distance, max(self.breakout_buffer, 1e-9)),
            bullish=bullish,
            bearish=False,
            primary_value=breakout_distance,
            signal_value=mother_high,
            threshold_value=self.breakout_buffer,
            exit_value=mother_low,
            aligned_count=aligned_count,
            reason_code=reason_code,
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "Mother High",
                "y": [item.get("mother_high") for item in self.data_list],
                "line": {"color": "#ff7f0e"},
            },
            {
                "name": "Mother Low",
                "y": [item.get("mother_low") for item in self.data_list],
                "line": {"color": "#1f77b4"},
            },
        ]
