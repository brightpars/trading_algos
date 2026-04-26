from __future__ import annotations

from trading_algos.alertgen.algorithms.volatility_options.base import (
    BaseVolatilityAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.volatility_options.volatility_helpers import (
    VolatilitySignalState,
    scale_score,
)
from trading_algos.alertgen.shared_utils.common import TREND
from trading_algos.alertgen.shared_utils.indicators import (
    average_true_range,
    rolling_mean,
)


class ATRChannelBreakoutAlertAlgorithm(BaseVolatilityAlertAlgorithm):
    catalog_ref = "algorithm:53"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        channel_window: int = 5,
        atr_window: int = 5,
        atr_multiplier: float = 1.0,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.channel_window = channel_window
        self.atr_window = atr_window
        self.atr_multiplier = float(atr_multiplier)
        super().__init__(
            f"atr_channel_breakout_channel={channel_window}_atr={atr_window}",
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return max(self.channel_window, self.atr_window)

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "channel_window": self.channel_window,
            "atr_window": self.atr_window,
            "atr_multiplier": self.atr_multiplier,
            "indicator": "atr_channel",
        }

    def _state_annotations(self) -> dict[str, object]:
        return {
            "atr_value": self.latest_data_modifiable.get("atr_value"),
            "channel_mid": self.latest_data_modifiable.get("channel_mid"),
            "upper_band": self.latest_data_modifiable.get("upper_band"),
            "lower_band": self.latest_data_modifiable.get("lower_band"),
        }

    def _calculate_state(self) -> VolatilitySignalState:
        highs = [float(item["High"]) for item in self.data_list]
        lows = [float(item["Low"]) for item in self.data_list]
        closes = [float(item["Close"]) for item in self.data_list]
        atr_values = average_true_range(highs, lows, closes, self.atr_window)
        channel_mid_values = rolling_mean(closes, self.channel_window)
        atr_value = atr_values[-1]
        channel_mid = channel_mid_values[-1]
        close_value = closes[-1]
        upper_band = None
        lower_band = None
        if atr_value is not None and channel_mid is not None:
            upper_band = channel_mid + (atr_value * self.atr_multiplier)
            lower_band = channel_mid - (atr_value * self.atr_multiplier)
        self.latest_data_modifiable["atr_value"] = atr_value
        self.latest_data_modifiable["channel_mid"] = channel_mid
        self.latest_data_modifiable["upper_band"] = upper_band
        self.latest_data_modifiable["lower_band"] = lower_band
        if upper_band is None or lower_band is None:
            return VolatilitySignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                bullish=False,
                bearish=False,
                primary_value=None,
                signal_value=channel_mid,
                threshold_value=self.atr_multiplier,
                exit_value=None,
                aligned_count=0,
                reason_code="warmup_pending",
            )
        bullish = close_value >= upper_band
        bearish = close_value <= lower_band
        distance = 0.0
        if atr_value not in (None, 0.0) and channel_mid is not None:
            assert atr_value is not None
            distance = (close_value - channel_mid) / atr_value
        return VolatilitySignalState(
            regime=TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score=scale_score(distance, max(self.atr_multiplier, 1.0)),
            bullish=bullish,
            bearish=bearish,
            primary_value=distance,
            signal_value=channel_mid,
            threshold_value=self.atr_multiplier if bullish else -self.atr_multiplier,
            exit_value=0.0,
            aligned_count=1 if bullish or bearish else 0,
            reason_code=(
                "atr_channel_breakout_up"
                if bullish
                else "atr_channel_breakout_down"
                if bearish
                else "atr_channel_inside_bands"
            ),
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "Channel Mid",
                "y": [item.get("channel_mid") for item in self.data_list],
                "line": {"color": "#9467bd"},
            },
            {
                "name": "Upper Band",
                "y": [item.get("upper_band") for item in self.data_list],
                "line": {"color": "#2ca02c"},
            },
            {
                "name": "Lower Band",
                "y": [item.get("lower_band") for item in self.data_list],
                "line": {"color": "#d62728"},
            },
        ]
