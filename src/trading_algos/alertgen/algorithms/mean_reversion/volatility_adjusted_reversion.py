from __future__ import annotations

from trading_algos.alertgen.algorithms.mean_reversion.base import (
    BaseMeanReversionAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.mean_reversion.mean_reversion_helpers import (
    MeanReversionSignalState,
    scale_score,
)
from trading_algos.alertgen.shared_utils.common import TREND
from trading_algos.alertgen.shared_utils.indicators import (
    average_true_range,
    rolling_mean,
)


class VolatilityAdjustedReversionAlertAlgorithm(BaseMeanReversionAlertAlgorithm):
    catalog_ref = "algorithm:37"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        window: int = 20,
        atr_window: int = 14,
        entry_atr_multiple: float = 1.5,
        exit_atr_multiple: float = 0.5,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.window = window
        self.atr_window = atr_window
        self.entry_atr_multiple = float(entry_atr_multiple)
        self.exit_atr_multiple = float(exit_atr_multiple)
        super().__init__(
            f"volatility_adjusted_reversion_window={window}_atr={atr_window}",
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return max(self.window, self.atr_window)

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "window": self.window,
            "atr_window": self.atr_window,
            "entry_atr_multiple": self.entry_atr_multiple,
            "exit_atr_multiple": self.exit_atr_multiple,
            "indicator": "atr_distance",
        }

    def _state_annotations(self) -> dict[str, object]:
        return {
            "rolling_mean": self.latest_data_modifiable.get("rolling_mean"),
            "atr_value": self.latest_data_modifiable.get("atr_value"),
            "atr_distance": self.latest_data_modifiable.get("atr_distance"),
        }

    def _calculate_state(self) -> MeanReversionSignalState:
        highs = [float(item["High"]) for item in self.data_list]
        lows = [float(item["Low"]) for item in self.data_list]
        closes = [float(item["Close"]) for item in self.data_list]
        mean_values = rolling_mean(closes, self.window)
        atr_values = average_true_range(highs, lows, closes, self.atr_window)
        mean_value = mean_values[-1]
        atr_value = atr_values[-1]
        close_value = closes[-1]
        atr_distance = None
        if mean_value is not None and atr_value not in (None, 0.0):
            assert atr_value is not None
            atr_distance = (close_value - mean_value) / atr_value
        self.latest_data_modifiable["rolling_mean"] = mean_value
        self.latest_data_modifiable["atr_value"] = atr_value
        self.latest_data_modifiable["atr_distance"] = atr_distance
        if atr_distance is None:
            return MeanReversionSignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                bullish=False,
                bearish=False,
                primary_value=None,
                signal_value=mean_value,
                threshold_value=-self.entry_atr_multiple,
                exit_value=self.exit_atr_multiple,
                aligned_count=0,
                reason_code="warmup_pending",
            )
        bullish = atr_distance <= -self.entry_atr_multiple
        bearish = atr_distance >= self.entry_atr_multiple
        return MeanReversionSignalState(
            regime=TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score=scale_score(-atr_distance, self.entry_atr_multiple),
            bullish=bullish,
            bearish=bearish,
            primary_value=atr_distance,
            signal_value=mean_value,
            threshold_value=(
                -self.entry_atr_multiple if bullish else self.entry_atr_multiple
            ),
            exit_value=self.exit_atr_multiple,
            aligned_count=1 if bullish or bearish else 0,
            reason_code=(
                "volatility_adjusted_oversold"
                if bullish
                else "volatility_adjusted_overbought"
                if bearish
                else "volatility_adjusted_neutral"
            ),
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "Rolling Mean",
                "y": [item.get("rolling_mean") for item in self.data_list],
                "line": {"color": "#ff7f0e"},
            },
            {
                "name": "ATR Distance",
                "y": [item.get("atr_distance") for item in self.data_list],
                "line": {"color": "#17becf"},
                "yaxis": "y2",
            },
        ]
