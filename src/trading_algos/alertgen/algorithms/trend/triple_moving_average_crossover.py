from __future__ import annotations

from trading_algos.alertgen.algorithms.trend.moving_average_base import (
    BaseMovingAverageTrendAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.moving_average_helpers import (
    TrendSignalState,
    minimum_history_for_windows,
    moving_average,
)
from trading_algos.alertgen.shared_utils.common import TREND


class TripleMovingAverageCrossoverAlertAlgorithm(BaseMovingAverageTrendAlertAlgorithm):
    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        fast_window: int = 5,
        medium_window: int = 10,
        slow_window: int = 20,
        minimum_spread: float = 0.0,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.fast_window = fast_window
        self.medium_window = medium_window
        self.slow_window = slow_window
        super().__init__(
            (
                "triple_moving_average_crossover"
                f"_fast={fast_window}_medium={medium_window}_slow={slow_window}"
            ),
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            minimum_spread=minimum_spread,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return minimum_history_for_windows(
            self.fast_window,
            self.medium_window,
            self.slow_window,
        )

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "average_type": "sma",
            "fast_window": self.fast_window,
            "medium_window": self.medium_window,
            "slow_window": self.slow_window,
        }

    def _calculate_state(self) -> TrendSignalState:
        closes = [float(item["Close"]) for item in self.data_list]
        fast_values = moving_average(closes, self.fast_window, "sma")
        medium_values = moving_average(closes, self.medium_window, "sma")
        slow_values = moving_average(closes, self.slow_window, "sma")
        fast_value = fast_values[-1]
        medium_value = medium_values[-1]
        slow_value = slow_values[-1]
        self.latest_data_modifiable["sma_fast"] = fast_value
        self.latest_data_modifiable["sma_medium"] = medium_value
        self.latest_data_modifiable["sma_slow"] = slow_value
        if fast_value is None or medium_value is None or slow_value is None:
            return TrendSignalState(TREND.UNKNOWN, 0.0, None, 0, False, False)
        fast_medium_spread = fast_value - medium_value
        medium_slow_spread = medium_value - slow_value
        bullish = (
            fast_medium_spread > self.minimum_spread
            and medium_slow_spread > self.minimum_spread
        )
        bearish = (
            fast_medium_spread < -self.minimum_spread
            and medium_slow_spread < -self.minimum_spread
        )
        score = 0.0
        if slow_value != 0.0:
            score = max(
                -1.0,
                min(
                    1.0,
                    ((fast_value - slow_value) + (medium_value - slow_value))
                    / (2.0 * slow_value),
                ),
            )
        spread = fast_value - slow_value
        return TrendSignalState(
            TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score,
            spread,
            3 if bullish or bearish else 0,
            bullish,
            bearish,
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "SMA fast",
                "y": [item.get("sma_fast") for item in self.data_list],
                "line": {"color": "#ff7f0e"},
            },
            {
                "name": "SMA medium",
                "y": [item.get("sma_medium") for item in self.data_list],
                "line": {"color": "#2ca02c"},
            },
            {
                "name": "SMA slow",
                "y": [item.get("sma_slow") for item in self.data_list],
                "line": {"color": "#9467bd"},
            },
        ]
