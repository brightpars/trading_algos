from __future__ import annotations

from trading_algos.alertgen.algorithms.trend.moving_average_base import (
    BaseMovingAverageTrendAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.moving_average_helpers import (
    TrendSignalState,
    clamp_unit,
)
from trading_algos.alertgen.shared_utils.common import TREND
from trading_algos.alertgen.shared_utils.indicators import supertrend


class SuperTrendAlertAlgorithm(BaseMovingAverageTrendAlertAlgorithm):
    catalog_ref = "algorithm:10"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        window: int = 10,
        multiplier: float = 3.0,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.window = window
        self.multiplier = float(multiplier)
        super().__init__(
            f"supertrend_window={window}_multiplier={multiplier}",
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            minimum_spread=0.0,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return self.window

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "window": self.window,
            "multiplier": self.multiplier,
            "indicator": "supertrend",
        }

    def _calculate_state(self) -> TrendSignalState:
        highs = [float(item["High"]) for item in self.data_list]
        lows = [float(item["Low"]) for item in self.data_list]
        closes = [float(item["Close"]) for item in self.data_list]
        upper_band, lower_band, direction = supertrend(
            highs, lows, closes, self.window, self.multiplier
        )
        upper_value = upper_band[-1]
        lower_value = lower_band[-1]
        direction_value = direction[-1]
        close_value = closes[-1]
        self.latest_data_modifiable["supertrend_upper"] = upper_value
        self.latest_data_modifiable["supertrend_lower"] = lower_value
        self.latest_data_modifiable["supertrend_direction"] = direction_value
        if upper_value is None or lower_value is None or direction_value is None:
            return TrendSignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                spread=None,
                aligned_count=0,
                bullish=False,
                bearish=False,
                reason_code="warmup_pending",
            )
        bullish = direction_value > 0
        bearish = direction_value < 0
        reference_band = lower_value if bullish else upper_value
        spread = close_value - reference_band
        scale = max(abs(close_value), 1e-9)
        return TrendSignalState(
            regime=TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score=clamp_unit(spread / scale),
            spread=spread,
            aligned_count=1 if bullish or bearish else 0,
            bullish=bullish,
            bearish=bearish,
            reason_code=(
                "supertrend_bullish"
                if bullish
                else "supertrend_bearish"
                if bearish
                else "supertrend_neutral"
            ),
            primary_value=close_value,
            signal_value=float(direction_value),
            threshold_value=self.multiplier,
            upper_band=upper_value,
            lower_band=lower_value,
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "SuperTrend upper",
                "y": [item.get("supertrend_upper") for item in self.data_list],
                "line": {"color": "#9467bd"},
            },
            {
                "name": "SuperTrend lower",
                "y": [item.get("supertrend_lower") for item in self.data_list],
                "line": {"color": "#2ca02c"},
            },
        ]
