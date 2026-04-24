from __future__ import annotations

from trading_algos.alertgen.algorithms.trend.moving_average_base import (
    BaseMovingAverageTrendAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.moving_average_helpers import (
    AverageType,
    TrendSignalState,
    average_label,
    minimum_history_for_windows,
    moving_average,
)
from trading_algos.alertgen.shared_utils.common import TREND


class PriceVsMovingAverageAlertAlgorithm(BaseMovingAverageTrendAlertAlgorithm):
    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        window: int = 20,
        average_type: AverageType = "sma",
        minimum_spread: float = 0.0,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.window = window
        self.average_type = average_type
        super().__init__(
            f"price_vs_{average_type}_moving_average_window={window}",
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            minimum_spread=minimum_spread,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return minimum_history_for_windows(self.window)

    def _calculate_state(self) -> TrendSignalState:
        closes = [float(item["Close"]) for item in self.data_list]
        ma_values = moving_average(closes, self.window, self.average_type)
        ma_value = ma_values[-1]
        close_value = closes[-1]
        field_name = f"{self.average_type}_window"
        self.latest_data_modifiable[field_name] = ma_value
        if ma_value is None:
            return TrendSignalState(TREND.UNKNOWN, 0.0, None, 0, False, False)
        spread = close_value - ma_value
        bullish = spread > self.minimum_spread
        bearish = spread < -self.minimum_spread
        score = 0.0 if ma_value == 0.0 else max(-1.0, min(1.0, spread / ma_value))
        return TrendSignalState(
            TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score,
            spread,
            1 if bullish or bearish else 0,
            bullish,
            bearish,
        )

    def _chart_series(self) -> list[dict[str, object]]:
        field_name = f"{self.average_type}_window"
        return [
            {
                "name": f"Price vs {average_label(self.average_type)}",
                "y": [item.get(field_name) for item in self.data_list],
                "line": {"color": "orange"},
            }
        ]
