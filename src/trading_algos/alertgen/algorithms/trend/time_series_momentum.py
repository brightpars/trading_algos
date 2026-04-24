from __future__ import annotations

from trading_algos.alertgen.algorithms.trend.moving_average_base import (
    BaseMovingAverageTrendAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.moving_average_helpers import (
    TrendSignalState,
    safe_relative_score,
)
from trading_algos.alertgen.shared_utils.common import TREND
from trading_algos.alertgen.shared_utils.indicators import rate_of_change


class TimeSeriesMomentumAlertAlgorithm(BaseMovingAverageTrendAlertAlgorithm):
    catalog_ref = "algorithm:14"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        window: int = 20,
        return_threshold: float = 0.0,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.window = window
        self.return_threshold = float(return_threshold)
        super().__init__(
            f"time_series_momentum_window={window}",
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            minimum_spread=return_threshold,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return self.window + 1

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "window": self.window,
            "return_threshold": self.return_threshold,
            "indicator": "time_series_momentum",
        }

    def _calculate_state(self) -> TrendSignalState:
        closes = [float(item["Close"]) for item in self.data_list]
        roc_values = rate_of_change(closes, self.window)
        roc_value = roc_values[-1]
        self.latest_data_modifiable["tsmom_return"] = roc_value
        if roc_value is None:
            return TrendSignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                spread=None,
                aligned_count=0,
                bullish=False,
                bearish=False,
                reason_code="warmup_pending",
            )
        bullish = roc_value > self.return_threshold
        bearish = roc_value < -self.return_threshold
        return TrendSignalState(
            regime=TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score=safe_relative_score(roc_value, 100.0),
            spread=roc_value,
            aligned_count=1 if bullish or bearish else 0,
            bullish=bullish,
            bearish=bearish,
            reason_code=(
                "time_series_momentum_bullish"
                if bullish
                else "time_series_momentum_bearish"
                if bearish
                else "time_series_momentum_inside_threshold"
            ),
            primary_value=roc_value,
            signal_value=roc_value,
            threshold_value=self.return_threshold,
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "TSMOM return",
                "y": [item.get("tsmom_return") for item in self.data_list],
                "line": {"color": "#17becf"},
            }
        ]
