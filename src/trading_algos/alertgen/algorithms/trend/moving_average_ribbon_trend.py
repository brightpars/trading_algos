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


class MovingAverageRibbonTrendAlertAlgorithm(BaseMovingAverageTrendAlertAlgorithm):
    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        windows: list[int] | tuple[int, ...] = (5, 10, 20, 30),
        minimum_spread: float = 0.0,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.windows = list(windows)
        window_label = "-".join(str(window) for window in self.windows)
        super().__init__(
            f"moving_average_ribbon_trend_windows={window_label}",
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            minimum_spread=minimum_spread,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return minimum_history_for_windows(*self.windows)

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "average_type": "sma",
            "windows": tuple(self.windows),
        }

    def _calculate_state(self) -> TrendSignalState:
        closes = [float(item["Close"]) for item in self.data_list]
        latest_values: list[float] = []
        for window in self.windows:
            values = moving_average(closes, window, "sma")
            latest_value = values[-1]
            self.latest_data_modifiable[f"sma_{window}"] = latest_value
            if latest_value is None:
                return TrendSignalState(TREND.UNKNOWN, 0.0, None, 0, False, False)
            latest_values.append(latest_value)
        pair_spreads = [
            earlier - later for earlier, later in zip(latest_values, latest_values[1:])
        ]
        bullish = all(spread > self.minimum_spread for spread in pair_spreads)
        bearish = all(spread < -self.minimum_spread for spread in pair_spreads)
        ribbon_spread = latest_values[0] - latest_values[-1]
        base_value = latest_values[-1]
        score = (
            0.0
            if base_value == 0.0
            else max(-1.0, min(1.0, ribbon_spread / base_value))
        )
        return TrendSignalState(
            TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score,
            ribbon_spread,
            len(latest_values) if bullish or bearish else 0,
            bullish,
            bearish,
        )

    def _chart_series(self) -> list[dict[str, object]]:
        colours = ["#ff7f0e", "#2ca02c", "#1f77b4", "#9467bd", "#8c564b", "#e377c2"]
        return [
            {
                "name": f"SMA {window}",
                "y": [item.get(f"sma_{window}") for item in self.data_list],
                "line": {"color": colours[index % len(colours)]},
            }
            for index, window in enumerate(self.windows)
        ]
