from __future__ import annotations

from trading_algos.alertgen.algorithms.pattern_price_action.base import (
    BasePatternAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.pattern_price_action.pattern_helpers import (
    PatternSignalState,
    project_linear_value,
    rolling_linear_regression,
    scale_score,
)
from trading_algos.alertgen.shared_utils.common import TREND


class TrendlineBreakStrategyAlertAlgorithm(BasePatternAlertAlgorithm):
    catalog_ref = "algorithm:76"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        trendline_window: int = 5,
        break_buffer: float = 0.1,
        slope_tolerance: float = 0.0,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.trendline_window = int(trendline_window)
        self.break_buffer = float(break_buffer)
        self.slope_tolerance = float(slope_tolerance)
        super().__init__(
            f"trendline_break_window={trendline_window}",
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return self.trendline_window

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "trendline_window": self.trendline_window,
            "break_buffer": self.break_buffer,
            "slope_tolerance": self.slope_tolerance,
            "pattern_type": "trendline_break",
        }

    def _state_annotations(self) -> dict[str, object]:
        return {
            "trendline_level": self.latest_data_modifiable.get("trendline_level"),
            "trendline_slope": self.latest_data_modifiable.get("trendline_slope"),
            "trendline_intercept": self.latest_data_modifiable.get(
                "trendline_intercept"
            ),
            "break_distance": self.latest_data_modifiable.get("break_distance"),
            "trendline_break_detected": self.latest_data_modifiable.get(
                "trendline_break_detected"
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
                threshold_value=self.break_buffer,
                exit_value=None,
                aligned_count=0,
                reason_code="warmup_pending",
            )

        closes = [
            float(item["Close"]) for item in self.data_list[-self.trendline_window :]
        ]
        regression = rolling_linear_regression(closes)
        if regression is None:
            return PatternSignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                bullish=False,
                bearish=False,
                primary_value=None,
                signal_value=None,
                threshold_value=self.break_buffer,
                exit_value=None,
                aligned_count=0,
                reason_code="warmup_pending",
            )

        slope, intercept = regression
        trendline_level = project_linear_value(
            slope=slope,
            intercept=intercept,
            index=self.trendline_window - 1,
        )
        latest_close = closes[-1]
        break_distance = latest_close - trendline_level
        slope_supportive = slope <= self.slope_tolerance
        trendline_break_detected = (
            slope_supportive and break_distance >= self.break_buffer
        )

        self.latest_data_modifiable["trendline_level"] = trendline_level
        self.latest_data_modifiable["trendline_slope"] = slope
        self.latest_data_modifiable["trendline_intercept"] = intercept
        self.latest_data_modifiable["break_distance"] = break_distance
        self.latest_data_modifiable["trendline_break_detected"] = (
            trendline_break_detected
        )

        if trendline_break_detected:
            reason_code = "trendline_break_bullish"
            aligned_count = 2
        elif slope_supportive:
            reason_code = "awaiting_trendline_break"
            aligned_count = 1
        else:
            reason_code = "trendline_not_descending"
            aligned_count = 0

        return PatternSignalState(
            regime=TREND.UP if trendline_break_detected else TREND.UNKNOWN,
            score=scale_score(break_distance, max(self.break_buffer, 1e-9)),
            bullish=trendline_break_detected,
            bearish=False,
            primary_value=break_distance,
            signal_value=trendline_level,
            threshold_value=self.break_buffer,
            exit_value=slope,
            aligned_count=aligned_count,
            reason_code=reason_code,
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "Trendline Level",
                "y": [item.get("trendline_level") for item in self.data_list],
                "line": {"color": "#9467bd"},
            }
        ]
