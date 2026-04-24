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


class ExponentialMovingAverageCrossoverAlertAlgorithm(
    BaseMovingAverageTrendAlertAlgorithm
):
    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        short_window: int = 10,
        long_window: int = 30,
        minimum_spread: float = 0.0,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.short_window = short_window
        self.long_window = long_window
        super().__init__(
            (
                "exponential_moving_average_crossover"
                f"_short={short_window}_long={long_window}"
            ),
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            minimum_spread=minimum_spread,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return minimum_history_for_windows(self.short_window, self.long_window)

    def _calculate_state(self) -> TrendSignalState:
        closes = [float(item["Close"]) for item in self.data_list]
        short_values = moving_average(closes, self.short_window, "ema")
        long_values = moving_average(closes, self.long_window, "ema")
        short_value = short_values[-1]
        long_value = long_values[-1]
        self.latest_data_modifiable["ema_short"] = short_value
        self.latest_data_modifiable["ema_long"] = long_value
        if short_value is None or long_value is None:
            return TrendSignalState(TREND.UNKNOWN, 0.0, None, 0, False, False)
        spread = short_value - long_value
        bullish = spread > self.minimum_spread
        bearish = spread < -self.minimum_spread
        score = 0.0 if long_value == 0.0 else max(-1.0, min(1.0, spread / long_value))
        return TrendSignalState(
            TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score,
            spread,
            2 if bullish or bearish else 0,
            bullish,
            bearish,
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "EMA short",
                "y": [item.get("ema_short") for item in self.data_list],
                "line": {"color": "orange"},
            },
            {
                "name": "EMA long",
                "y": [item.get("ema_long") for item in self.data_list],
                "line": {"color": "purple"},
            },
        ]
