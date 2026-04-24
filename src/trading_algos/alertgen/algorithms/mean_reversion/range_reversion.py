from __future__ import annotations

from trading_algos.alertgen.algorithms.mean_reversion.base import (
    BaseMeanReversionAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.mean_reversion.mean_reversion_helpers import (
    MeanReversionSignalState,
    normalized_distance_from_midpoint,
)
from trading_algos.alertgen.shared_utils.common import TREND
from trading_algos.alertgen.shared_utils.indicators import rolling_high, rolling_low


class RangeReversionAlertAlgorithm(BaseMeanReversionAlertAlgorithm):
    catalog_ref = "algorithm:34"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        window: int = 20,
        entry_band_fraction: float = 0.2,
        exit_band_fraction: float = 0.5,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.window = window
        self.entry_band_fraction = float(entry_band_fraction)
        self.exit_band_fraction = float(exit_band_fraction)
        super().__init__(
            f"range_reversion_window={window}",
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return self.window

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "window": self.window,
            "entry_band_fraction": self.entry_band_fraction,
            "exit_band_fraction": self.exit_band_fraction,
            "indicator": "range_position",
        }

    def _calculate_state(self) -> MeanReversionSignalState:
        highs = [float(item["High"]) for item in self.data_list]
        lows = [float(item["Low"]) for item in self.data_list]
        closes = [float(item["Close"]) for item in self.data_list]
        upper_values = rolling_high(highs, self.window)
        lower_values = rolling_low(lows, self.window)
        upper_band = upper_values[-1]
        lower_band = lower_values[-1]
        close_value = closes[-1]
        range_position = None
        midpoint = None
        if (
            upper_band is not None
            and lower_band is not None
            and upper_band > lower_band
        ):
            midpoint = (upper_band + lower_band) / 2.0
            range_position = (close_value - lower_band) / (upper_band - lower_band)
        self.latest_data_modifiable["range_upper"] = upper_band
        self.latest_data_modifiable["range_lower"] = lower_band
        self.latest_data_modifiable["range_midpoint"] = midpoint
        self.latest_data_modifiable["range_position"] = range_position
        if range_position is None or midpoint is None:
            return MeanReversionSignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                bullish=False,
                bearish=False,
                primary_value=None,
                signal_value=midpoint,
                threshold_value=self.entry_band_fraction,
                exit_value=self.exit_band_fraction,
                aligned_count=0,
                reason_code="warmup_pending",
            )
        bullish = range_position <= self.entry_band_fraction
        bearish = range_position >= 1.0 - self.entry_band_fraction
        return MeanReversionSignalState(
            regime=TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score=normalized_distance_from_midpoint(
                range_position,
                lower_bound=0.0,
                upper_bound=1.0,
            ),
            bullish=bullish,
            bearish=bearish,
            primary_value=range_position,
            signal_value=midpoint,
            threshold_value=(
                self.entry_band_fraction if bullish else 1.0 - self.entry_band_fraction
            ),
            exit_value=self.exit_band_fraction,
            aligned_count=1 if bullish or bearish else 0,
            reason_code=(
                "range_support_reversion"
                if bullish
                else "range_resistance_reversion"
                if bearish
                else "range_midzone"
            ),
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "Range Upper",
                "y": [item.get("range_upper") for item in self.data_list],
                "line": {"color": "#d62728"},
            },
            {
                "name": "Range Midpoint",
                "y": [item.get("range_midpoint") for item in self.data_list],
                "line": {"color": "#ff7f0e"},
            },
            {
                "name": "Range Lower",
                "y": [item.get("range_lower") for item in self.data_list],
                "line": {"color": "#2ca02c"},
            },
        ]
