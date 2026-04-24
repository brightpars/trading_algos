from __future__ import annotations

from trading_algos.alertgen.algorithms.mean_reversion.base import (
    BaseMeanReversionAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.mean_reversion.mean_reversion_helpers import (
    MeanReversionSignalState,
    scale_score,
)
from trading_algos.alertgen.shared_utils.common import TREND
from trading_algos.alertgen.shared_utils.indicators import rolling_mean, rolling_std


class BollingerBandsReversionAlertAlgorithm(BaseMeanReversionAlertAlgorithm):
    catalog_ref = "algorithm:27"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        window: int = 20,
        std_multiplier: float = 2.0,
        exit_band_fraction: float = 0.25,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.window = window
        self.std_multiplier = float(std_multiplier)
        self.exit_band_fraction = float(exit_band_fraction)
        super().__init__(
            f"bollinger_bands_reversion_window={window}",
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
            "std_multiplier": self.std_multiplier,
            "exit_band_fraction": self.exit_band_fraction,
        }

    def _calculate_state(self) -> MeanReversionSignalState:
        closes = [float(item["Close"]) for item in self.data_list]
        middle_band_values = rolling_mean(closes, self.window)
        std_values = rolling_std(closes, self.window)
        middle_band = middle_band_values[-1]
        std_value = std_values[-1]
        close_value = closes[-1]
        upper_band = None
        lower_band = None
        band_position = None
        if middle_band is not None and std_value is not None:
            upper_band = middle_band + (self.std_multiplier * std_value)
            lower_band = middle_band - (self.std_multiplier * std_value)
            band_width = upper_band - lower_band
            if band_width > 0.0:
                band_position = ((close_value - lower_band) / band_width) * 2.0 - 1.0
        self.latest_data_modifiable["middle_band"] = middle_band
        self.latest_data_modifiable["upper_band"] = upper_band
        self.latest_data_modifiable["lower_band"] = lower_band
        self.latest_data_modifiable["band_position"] = band_position
        if band_position is None:
            return MeanReversionSignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                bullish=False,
                bearish=False,
                primary_value=None,
                signal_value=middle_band,
                threshold_value=-1.0,
                exit_value=self.exit_band_fraction,
                aligned_count=0,
                reason_code="warmup_pending",
            )
        bullish = close_value <= lower_band if lower_band is not None else False
        bearish = close_value >= upper_band if upper_band is not None else False
        return MeanReversionSignalState(
            regime=TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score=scale_score(-band_position, 1.0),
            bullish=bullish,
            bearish=bearish,
            primary_value=band_position,
            signal_value=middle_band,
            threshold_value=-1.0 if bullish else 1.0,
            exit_value=self.exit_band_fraction,
            aligned_count=1 if bullish or bearish else 0,
            reason_code=(
                "bollinger_below_lower_band"
                if bullish
                else "bollinger_above_upper_band"
                if bearish
                else "bollinger_inside_bands"
            ),
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "Middle Band",
                "y": [item.get("middle_band") for item in self.data_list],
                "line": {"color": "#ff7f0e"},
            },
            {
                "name": "Upper Band",
                "y": [item.get("upper_band") for item in self.data_list],
                "line": {"color": "#d62728"},
            },
            {
                "name": "Lower Band",
                "y": [item.get("lower_band") for item in self.data_list],
                "line": {"color": "#2ca02c"},
            },
        ]
