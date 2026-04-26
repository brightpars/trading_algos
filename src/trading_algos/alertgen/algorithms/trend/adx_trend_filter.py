from __future__ import annotations

from trading_algos.alertgen.algorithms.trend.moving_average_base import (
    BaseMovingAverageTrendAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.moving_average_helpers import (
    TrendSignalState,
    clamp_unit,
)
from trading_algos.alertgen.shared_utils.common import TREND
from trading_algos.alertgen.shared_utils.indicators import directional_movement_index


class ADXTrendFilterAlertAlgorithm(BaseMovingAverageTrendAlertAlgorithm):
    catalog_ref = "algorithm:8"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        window: int = 14,
        adx_threshold: float = 25.0,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.window = window
        self.adx_threshold = float(adx_threshold)
        super().__init__(
            f"adx_trend_filter_window={window}",
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            minimum_spread=adx_threshold,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return self.window * 2 - 1

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "window": self.window,
            "adx_threshold": self.adx_threshold,
            "indicator": "adx",
        }

    def _calculate_state(self) -> TrendSignalState:
        highs = [float(item["High"]) for item in self.data_list]
        lows = [float(item["Low"]) for item in self.data_list]
        closes = [float(item["Close"]) for item in self.data_list]
        plus_di, minus_di, adx_values = directional_movement_index(
            highs, lows, closes, self.window
        )
        adx_value = adx_values[-1]
        plus_di_value = plus_di[-1]
        minus_di_value = minus_di[-1]
        self.latest_data_modifiable["adx_value"] = adx_value
        self.latest_data_modifiable["plus_di"] = plus_di_value
        self.latest_data_modifiable["minus_di"] = minus_di_value
        if adx_value is None or plus_di_value is None or minus_di_value is None:
            return TrendSignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                spread=None,
                aligned_count=0,
                bullish=False,
                bearish=False,
                reason_code="warmup_pending",
            )
        directional_spread = plus_di_value - minus_di_value
        bullish = adx_value >= self.adx_threshold and directional_spread > 0.0
        bearish = adx_value >= self.adx_threshold and directional_spread < 0.0
        return TrendSignalState(
            regime=TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score=clamp_unit(directional_spread / 100.0),
            spread=directional_spread,
            aligned_count=2 if bullish or bearish else 0,
            bullish=bullish,
            bearish=bearish,
            reason_code=(
                "adx_bullish_filter_pass"
                if bullish
                else "adx_bearish_filter_pass"
                if bearish
                else "adx_below_threshold"
                if adx_value < self.adx_threshold
                else "adx_direction_neutral"
            ),
            primary_value=adx_value,
            signal_value=directional_spread,
            threshold_value=self.adx_threshold,
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "ADX",
                "y": [item.get("adx_value") for item in self.data_list],
                "line": {"color": "#d62728"},
            },
            {
                "name": "+DI",
                "y": [item.get("plus_di") for item in self.data_list],
                "line": {"color": "#2ca02c"},
            },
            {
                "name": "-DI",
                "y": [item.get("minus_di") for item in self.data_list],
                "line": {"color": "#1f77b4"},
            },
        ]
