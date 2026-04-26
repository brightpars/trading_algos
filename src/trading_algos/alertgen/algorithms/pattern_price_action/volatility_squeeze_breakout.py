from __future__ import annotations

from trading_algos.alertgen.algorithms.pattern_price_action.base import (
    BasePatternAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.pattern_price_action.pattern_helpers import (
    PatternSignalState,
    average_true_range,
    sample_standard_deviation,
    scale_score,
    simple_moving_average,
)
from trading_algos.alertgen.shared_utils.common import TREND


class VolatilitySqueezeBreakoutAlertAlgorithm(BasePatternAlertAlgorithm):
    catalog_ref = "algorithm:77"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        squeeze_window: int = 5,
        bollinger_multiplier: float = 2.0,
        keltner_multiplier: float = 1.5,
        breakout_buffer: float = 0.05,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.squeeze_window = int(squeeze_window)
        self.bollinger_multiplier = float(bollinger_multiplier)
        self.keltner_multiplier = float(keltner_multiplier)
        self.breakout_buffer = float(breakout_buffer)
        super().__init__(
            f"volatility_squeeze_window={squeeze_window}",
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return self.squeeze_window + 1

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "squeeze_window": self.squeeze_window,
            "bollinger_multiplier": self.bollinger_multiplier,
            "keltner_multiplier": self.keltner_multiplier,
            "breakout_buffer": self.breakout_buffer,
            "pattern_type": "volatility_squeeze_breakout",
        }

    def _state_annotations(self) -> dict[str, object]:
        return {
            "bollinger_upper": self.latest_data_modifiable.get("bollinger_upper"),
            "bollinger_lower": self.latest_data_modifiable.get("bollinger_lower"),
            "keltner_upper": self.latest_data_modifiable.get("keltner_upper"),
            "keltner_lower": self.latest_data_modifiable.get("keltner_lower"),
            "squeeze_on": self.latest_data_modifiable.get("squeeze_on"),
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

        highs = [float(item["High"]) for item in self.data_list]
        lows = [float(item["Low"]) for item in self.data_list]
        closes = [float(item["Close"]) for item in self.data_list]
        middle_band = simple_moving_average(closes, self.squeeze_window)
        stdev = sample_standard_deviation(closes, self.squeeze_window)
        atr_value = average_true_range(highs, lows, closes, self.squeeze_window)

        if middle_band is None or stdev is None or atr_value is None:
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

        bollinger_upper = middle_band + (self.bollinger_multiplier * stdev)
        bollinger_lower = middle_band - (self.bollinger_multiplier * stdev)
        keltner_upper = middle_band + (self.keltner_multiplier * atr_value)
        keltner_lower = middle_band - (self.keltner_multiplier * atr_value)
        squeeze_on = (
            bollinger_upper <= keltner_upper and bollinger_lower >= keltner_lower
        )
        recent_squeeze = any(
            bool(item.get("squeeze_on"))
            for item in self.data_list[-self.squeeze_window : -1]
        )
        latest_close = closes[-1]
        breakout_distance = latest_close - bollinger_upper
        bullish = (
            recent_squeeze and latest_close >= bollinger_upper + self.breakout_buffer
        )

        self.latest_data_modifiable["bollinger_upper"] = bollinger_upper
        self.latest_data_modifiable["bollinger_lower"] = bollinger_lower
        self.latest_data_modifiable["keltner_upper"] = keltner_upper
        self.latest_data_modifiable["keltner_lower"] = keltner_lower
        self.latest_data_modifiable["squeeze_on"] = squeeze_on
        self.latest_data_modifiable["breakout_distance"] = breakout_distance

        if bullish:
            reason_code = "volatility_squeeze_breakout_bullish"
            aligned_count = 2
        elif squeeze_on:
            reason_code = "squeeze_active"
            aligned_count = 1
        else:
            reason_code = "awaiting_squeeze_breakout"
            aligned_count = 0

        return PatternSignalState(
            regime=TREND.UP if bullish else TREND.UNKNOWN,
            score=scale_score(breakout_distance, max(self.breakout_buffer, 1e-9)),
            bullish=bullish,
            bearish=False,
            primary_value=breakout_distance,
            signal_value=bollinger_upper,
            threshold_value=self.breakout_buffer,
            exit_value=keltner_upper,
            aligned_count=aligned_count,
            reason_code=reason_code,
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "Bollinger Upper",
                "y": [item.get("bollinger_upper") for item in self.data_list],
                "line": {"color": "#ff7f0e"},
            },
            {
                "name": "Keltner Upper",
                "y": [item.get("keltner_upper") for item in self.data_list],
                "line": {"color": "#2ca02c"},
            },
        ]
