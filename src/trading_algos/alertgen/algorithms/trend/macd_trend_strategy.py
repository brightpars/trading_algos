from __future__ import annotations

from trading_algos.alertgen.algorithms.trend.moving_average_base import (
    BaseMovingAverageTrendAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.moving_average_helpers import (
    TrendSignalState,
    minimum_history_for_windows,
    safe_relative_score,
)
from trading_algos.alertgen.shared_utils.common import TREND
from trading_algos.alertgen.shared_utils.indicators import macd


class MACDTrendStrategyAlertAlgorithm(BaseMovingAverageTrendAlertAlgorithm):
    catalog_ref = "algorithm:12"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        fast_window: int = 12,
        slow_window: int = 26,
        signal_window: int = 9,
        histogram_threshold: float = 0.0,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.fast_window = fast_window
        self.slow_window = slow_window
        self.signal_window = signal_window
        self.histogram_threshold = float(histogram_threshold)
        super().__init__(
            (
                "macd_trend_strategy"
                f"_fast={fast_window}_slow={slow_window}_signal={signal_window}"
            ),
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            minimum_spread=histogram_threshold,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return minimum_history_for_windows(
            self.fast_window,
            self.slow_window,
            self.signal_window,
        )

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "fast_window": self.fast_window,
            "slow_window": self.slow_window,
            "signal_window": self.signal_window,
            "histogram_threshold": self.histogram_threshold,
            "indicator": "macd",
        }

    def _calculate_state(self) -> TrendSignalState:
        closes = [float(item["Close"]) for item in self.data_list]
        macd_line, signal_line, histogram = macd(
            closes,
            fast_window=self.fast_window,
            slow_window=self.slow_window,
            signal_window=self.signal_window,
        )
        macd_value = macd_line[-1]
        signal_value = signal_line[-1]
        histogram_value = histogram[-1]
        self.latest_data_modifiable["macd_line"] = macd_value
        self.latest_data_modifiable["macd_signal"] = signal_value
        self.latest_data_modifiable["macd_histogram"] = histogram_value
        if macd_value is None or signal_value is None or histogram_value is None:
            return TrendSignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                spread=None,
                aligned_count=0,
                bullish=False,
                bearish=False,
                reason_code="warmup_pending",
            )
        bullish = (
            macd_value > signal_value and histogram_value > self.histogram_threshold
        )
        bearish = (
            macd_value < signal_value and histogram_value < -self.histogram_threshold
        )
        aligned_count = sum((macd_value > signal_value, histogram_value > 0.0))
        return TrendSignalState(
            regime=TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score=safe_relative_score(histogram_value, closes[-1]),
            spread=histogram_value,
            aligned_count=aligned_count,
            bullish=bullish,
            bearish=bearish,
            reason_code=(
                "macd_bullish_crossover"
                if bullish
                else "macd_bearish_crossover"
                if bearish
                else "macd_inside_threshold"
            ),
            primary_value=macd_value,
            signal_value=signal_value,
            threshold_value=self.histogram_threshold,
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "MACD line",
                "y": [item.get("macd_line") for item in self.data_list],
                "line": {"color": "#1f77b4"},
            },
            {
                "name": "MACD signal",
                "y": [item.get("macd_signal") for item in self.data_list],
                "line": {"color": "#ff7f0e"},
            },
            {
                "name": "MACD histogram",
                "y": [item.get("macd_histogram") for item in self.data_list],
                "type": "bar",
                "marker": {"color": "#2ca02c"},
            },
        ]
