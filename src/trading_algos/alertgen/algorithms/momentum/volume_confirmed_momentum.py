from __future__ import annotations

from trading_algos.alertgen.algorithms.momentum.base import BaseMomentumAlertAlgorithm
from trading_algos.alertgen.algorithms.momentum.momentum_helpers import (
    MomentumSignalState,
    clamp_unit,
    relative_volume,
)
from trading_algos.alertgen.shared_utils.common import TREND
from trading_algos.alertgen.shared_utils.indicators import rate_of_change


class VolumeConfirmedMomentumAlertAlgorithm(BaseMomentumAlertAlgorithm):
    catalog_ref = "algorithm:25"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        momentum_window: int = 5,
        volume_window: int = 10,
        relative_volume_threshold: float = 1.2,
        signal_threshold: float = 2.0,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.momentum_window = momentum_window
        self.volume_window = volume_window
        self.relative_volume_threshold = float(relative_volume_threshold)
        self.signal_threshold = float(signal_threshold)
        super().__init__(
            (f"volume_confirmed_momentum_mom={momentum_window}_vol={volume_window}"),
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return max(self.momentum_window + 1, self.volume_window)

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "momentum_window": self.momentum_window,
            "volume_window": self.volume_window,
            "relative_volume_threshold": self.relative_volume_threshold,
            "signal_threshold": self.signal_threshold,
            "indicator": "volume_confirmed_momentum",
        }

    def _calculate_state(self) -> MomentumSignalState:
        closes = [float(item["Close"]) for item in self.data_list]
        volumes = [float(item.get("Volume", 1.0)) for item in self.data_list]
        roc_series = rate_of_change(closes, self.momentum_window)
        volume_average, relative_volume_series = relative_volume(
            volumes, window=self.volume_window
        )
        momentum_value = roc_series[-1]
        volume_baseline = volume_average[-1]
        relative_volume_value = relative_volume_series[-1]
        self.latest_data_modifiable["momentum_value"] = momentum_value
        self.latest_data_modifiable["volume_baseline"] = volume_baseline
        self.latest_data_modifiable["relative_volume_value"] = relative_volume_value
        if momentum_value is None or relative_volume_value is None:
            return MomentumSignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                bullish=False,
                bearish=False,
                primary_value=None,
                signal_value=None,
                threshold_value=self.signal_threshold,
                aligned_count=0,
                reason_code="warmup_pending",
            )
        bullish = (
            momentum_value >= self.signal_threshold
            and relative_volume_value >= self.relative_volume_threshold
        )
        bearish = (
            momentum_value <= -self.signal_threshold
            and relative_volume_value >= self.relative_volume_threshold
        )
        scale = max(abs(self.signal_threshold), 1.0)
        score = clamp_unit(momentum_value / scale)
        if relative_volume_value < self.relative_volume_threshold:
            score *= 0.5
        return MomentumSignalState(
            regime=TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score=score,
            bullish=bullish,
            bearish=bearish,
            primary_value=momentum_value,
            signal_value=relative_volume_value,
            threshold_value=self.relative_volume_threshold,
            aligned_count=2
            if relative_volume_value >= self.relative_volume_threshold
            else 1,
            reason_code=(
                "volume_confirmed_bullish"
                if bullish
                else "volume_confirmed_bearish"
                if bearish
                else "volume_confirmation_missing"
                if abs(momentum_value) >= self.signal_threshold
                else "momentum_inside_threshold"
            ),
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "Momentum",
                "y": [item.get("momentum_value") for item in self.data_list],
                "line": {"color": "#ff7f0e"},
            },
            {
                "name": "Relative volume",
                "y": [item.get("relative_volume_value") for item in self.data_list],
                "line": {"color": "#9467bd"},
            },
        ]
