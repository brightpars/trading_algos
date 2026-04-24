from __future__ import annotations

from trading_algos.alertgen.algorithms.momentum.base import BaseMomentumAlertAlgorithm
from trading_algos.alertgen.algorithms.momentum.momentum_helpers import (
    MomentumSignalState,
    clamp_unit,
)
from trading_algos.alertgen.shared_utils.common import TREND
from trading_algos.alertgen.shared_utils.indicators import rate_of_change


class AcceleratingMomentumAlertAlgorithm(BaseMomentumAlertAlgorithm):
    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        fast_window: int = 5,
        slow_window: int = 10,
        acceleration_threshold: float = 1.0,
        bearish_threshold: float = -1.0,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.fast_window = fast_window
        self.slow_window = slow_window
        self.acceleration_threshold = float(acceleration_threshold)
        self.bearish_threshold = float(bearish_threshold)
        super().__init__(
            f"accelerating_momentum_fast={fast_window}_slow={slow_window}",
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return self.slow_window + 1

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "fast_window": self.fast_window,
            "slow_window": self.slow_window,
            "acceleration_threshold": self.acceleration_threshold,
            "bearish_threshold": self.bearish_threshold,
        }

    def _calculate_state(self) -> MomentumSignalState:
        closes = [float(item["Close"]) for item in self.data_list]
        fast_roc_values = rate_of_change(closes, self.fast_window)
        slow_roc_values = rate_of_change(closes, self.slow_window)
        fast_roc = fast_roc_values[-1]
        slow_roc = slow_roc_values[-1]
        acceleration = (
            None if fast_roc is None or slow_roc is None else fast_roc - slow_roc
        )
        self.latest_data_modifiable["fast_roc"] = fast_roc
        self.latest_data_modifiable["slow_roc"] = slow_roc
        self.latest_data_modifiable["acceleration_value"] = acceleration
        if acceleration is None or fast_roc is None or slow_roc is None:
            return MomentumSignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                bullish=False,
                bearish=False,
                primary_value=None,
                signal_value=None,
                threshold_value=self.acceleration_threshold,
                aligned_count=0,
                reason_code="warmup_pending",
            )
        bullish = fast_roc >= self.acceleration_threshold and slow_roc > 0.0
        bearish = fast_roc <= self.bearish_threshold and slow_roc < 0.0
        scale = max(
            abs(self.acceleration_threshold),
            abs(self.bearish_threshold),
            1.0,
        )
        return MomentumSignalState(
            regime=TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score=clamp_unit(fast_roc / scale),
            bullish=bullish,
            bearish=bearish,
            primary_value=fast_roc,
            signal_value=acceleration,
            threshold_value=self.acceleration_threshold
            if bullish
            else self.bearish_threshold,
            aligned_count=2 if bullish or bearish else 0,
            reason_code=(
                "acceleration_bullish"
                if bullish
                else "acceleration_bearish"
                if bearish
                else "acceleration_inside_threshold"
            ),
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "Fast ROC",
                "y": [item.get("fast_roc") for item in self.data_list],
                "line": {"color": "#ff7f0e"},
            },
            {
                "name": "Slow ROC",
                "y": [item.get("slow_roc") for item in self.data_list],
                "line": {"color": "#9467bd"},
            },
            {
                "name": "Acceleration",
                "y": [item.get("acceleration_value") for item in self.data_list],
                "line": {"color": "#2ca02c"},
            },
        ]
