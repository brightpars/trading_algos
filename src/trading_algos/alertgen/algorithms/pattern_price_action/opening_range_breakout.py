from __future__ import annotations

from trading_algos.alertgen.algorithms.pattern_price_action.base import (
    BasePatternAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.pattern_price_action.pattern_helpers import (
    PatternSignalState,
    parse_session_label,
    parse_timestamp,
    scale_score,
)
from trading_algos.alertgen.shared_utils.common import TREND


class OpeningRangeBreakoutAlertAlgorithm(BasePatternAlertAlgorithm):
    catalog_ref = "algorithm:73"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        opening_range_minutes: int = 15,
        breakout_buffer: float = 0.2,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.opening_range_minutes = opening_range_minutes
        self.breakout_buffer = float(breakout_buffer)
        super().__init__(
            f"opening_range_breakout_minutes={opening_range_minutes}",
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return 2

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "opening_range_minutes": self.opening_range_minutes,
            "breakout_buffer": self.breakout_buffer,
            "pattern_type": "opening_range_breakout",
        }

    def _state_annotations(self) -> dict[str, object]:
        return {
            "opening_range_high": self.latest_data_modifiable.get("opening_range_high"),
            "opening_range_low": self.latest_data_modifiable.get("opening_range_low"),
            "opening_range_complete": self.latest_data_modifiable.get(
                "opening_range_complete"
            ),
            "breakout_distance": self.latest_data_modifiable.get("breakout_distance"),
        }

    def _calculate_state(self) -> PatternSignalState:
        latest = self.data_list[-1]
        latest_timestamp = parse_timestamp(str(latest["ts"]))
        session_label = parse_session_label(str(latest["ts"]))
        session_rows = [
            item
            for item in self.data_list
            if parse_session_label(str(item["ts"])) == session_label
        ]
        session_start = parse_timestamp(str(session_rows[0]["ts"]))
        opening_rows = [
            item
            for item in session_rows
            if (parse_timestamp(str(item["ts"])) - session_start).total_seconds()
            < self.opening_range_minutes * 60
        ]
        opening_range_complete = len(opening_rows) < len(session_rows)
        opening_range_high = max(float(item["High"]) for item in opening_rows)
        opening_range_low = min(float(item["Low"]) for item in opening_rows)
        close_value = float(latest["Close"])
        breakout_distance = close_value - opening_range_high
        bullish = (
            opening_range_complete
            and close_value >= opening_range_high + self.breakout_buffer
        )
        self.latest_data_modifiable["opening_range_high"] = opening_range_high
        self.latest_data_modifiable["opening_range_low"] = opening_range_low
        self.latest_data_modifiable["opening_range_complete"] = opening_range_complete
        self.latest_data_modifiable["breakout_distance"] = breakout_distance
        self.latest_data_modifiable["session_label"] = session_label
        self.latest_data_modifiable["session_minute"] = int(
            (latest_timestamp - session_start).total_seconds() / 60
        )

        if not opening_range_complete:
            return PatternSignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                bullish=False,
                bearish=False,
                primary_value=breakout_distance,
                signal_value=opening_range_high,
                threshold_value=self.breakout_buffer,
                exit_value=opening_range_low,
                aligned_count=0,
                reason_code="opening_range_pending",
            )

        return PatternSignalState(
            regime=TREND.UP if bullish else TREND.UNKNOWN,
            score=scale_score(breakout_distance, max(self.breakout_buffer, 1e-9)),
            bullish=bullish,
            bearish=False,
            primary_value=breakout_distance,
            signal_value=opening_range_high,
            threshold_value=self.breakout_buffer,
            exit_value=opening_range_low,
            aligned_count=2 if bullish else 0,
            reason_code="opening_range_breakout_bullish"
            if bullish
            else "awaiting_opening_breakout",
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "Opening Range High",
                "y": [item.get("opening_range_high") for item in self.data_list],
                "line": {"color": "#ff7f0e"},
            },
            {
                "name": "Opening Range Low",
                "y": [item.get("opening_range_low") for item in self.data_list],
                "line": {"color": "#1f77b4"},
            },
        ]
