from __future__ import annotations

from trading_algos.alertgen.algorithms.trend.moving_average_base import (
    BaseMovingAverageTrendAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.moving_average_helpers import (
    TrendSignalState,
    safe_relative_score,
)
from trading_algos.alertgen.shared_utils.common import TREND
from trading_algos.alertgen.shared_utils.indicators import rolling_linear_regression


class LinearRegressionTrendAlertAlgorithm(BaseMovingAverageTrendAlertAlgorithm):
    catalog_ref = "algorithm:13"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        window: int = 20,
        slope_threshold: float = 0.0,
        min_r_squared: float = 0.3,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.window = window
        self.slope_threshold = float(slope_threshold)
        self.min_r_squared = float(min_r_squared)
        super().__init__(
            f"linear_regression_trend_window={window}",
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            minimum_spread=slope_threshold,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return self.window

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "window": self.window,
            "slope_threshold": self.slope_threshold,
            "min_r_squared": self.min_r_squared,
            "indicator": "linear_regression",
        }

    def _calculate_state(self) -> TrendSignalState:
        closes = [float(item["Close"]) for item in self.data_list]
        slopes, intercepts, r_squared_values = rolling_linear_regression(
            closes, self.window
        )
        slope_value = slopes[-1]
        intercept_value = intercepts[-1]
        r_squared_value = r_squared_values[-1]
        self.latest_data_modifiable["regression_slope"] = slope_value
        self.latest_data_modifiable["regression_intercept"] = intercept_value
        self.latest_data_modifiable["regression_r_squared"] = r_squared_value
        if slope_value is None or intercept_value is None or r_squared_value is None:
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
            slope_value > self.slope_threshold and r_squared_value >= self.min_r_squared
        )
        bearish = (
            slope_value < -self.slope_threshold
            and r_squared_value >= self.min_r_squared
        )
        aligned_count = sum(
            (
                abs(slope_value) > self.slope_threshold,
                r_squared_value >= self.min_r_squared,
            )
        )
        return TrendSignalState(
            regime=TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score=safe_relative_score(slope_value, closes[-1]),
            spread=slope_value,
            aligned_count=aligned_count,
            bullish=bullish,
            bearish=bearish,
            reason_code=(
                "linear_regression_bullish"
                if bullish
                else "linear_regression_bearish"
                if bearish
                else "linear_regression_low_confidence"
                if r_squared_value < self.min_r_squared
                else "linear_regression_flat"
            ),
            primary_value=slope_value,
            signal_value=r_squared_value,
            threshold_value=self.slope_threshold,
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "Regression slope",
                "y": [item.get("regression_slope") for item in self.data_list],
                "line": {"color": "#9467bd"},
            },
            {
                "name": "Regression R²",
                "y": [item.get("regression_r_squared") for item in self.data_list],
                "line": {"color": "#8c564b"},
            },
        ]
