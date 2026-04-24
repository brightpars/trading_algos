from __future__ import annotations

from trading_algos.alertgen.algorithms.momentum.base import BaseMomentumAlertAlgorithm
from trading_algos.alertgen.algorithms.momentum.momentum_helpers import (
    MomentumSignalState,
    clamp_unit,
)
from trading_algos.alertgen.shared_utils.common import TREND
from trading_algos.alertgen.shared_utils.indicators import relative_strength_index


class RSIMomentumContinuationAlertAlgorithm(BaseMomentumAlertAlgorithm):
    catalog_ref = "algorithm:21"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        window: int = 14,
        bullish_threshold: float = 60.0,
        bearish_threshold: float = 40.0,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.window = window
        self.bullish_threshold = float(bullish_threshold)
        self.bearish_threshold = float(bearish_threshold)
        super().__init__(
            f"rsi_momentum_continuation_window={window}",
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return self.window + 1

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "window": self.window,
            "bullish_threshold": self.bullish_threshold,
            "bearish_threshold": self.bearish_threshold,
        }

    def _calculate_state(self) -> MomentumSignalState:
        closes = [float(item["Close"]) for item in self.data_list]
        rsi_values = relative_strength_index(closes, self.window)
        rsi_value = rsi_values[-1]
        self.latest_data_modifiable["rsi_value"] = rsi_value
        if rsi_value is None:
            return MomentumSignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                bullish=False,
                bearish=False,
                primary_value=None,
                signal_value=None,
                threshold_value=self.bullish_threshold,
                aligned_count=0,
                reason_code="warmup_pending",
            )
        bullish = rsi_value >= self.bullish_threshold
        bearish = rsi_value <= self.bearish_threshold
        centered_score = (rsi_value - 50.0) / 50.0
        return MomentumSignalState(
            regime=TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score=clamp_unit(centered_score),
            bullish=bullish,
            bearish=bearish,
            primary_value=rsi_value,
            signal_value=None,
            threshold_value=self.bullish_threshold
            if bullish
            else self.bearish_threshold,
            aligned_count=1 if bullish or bearish else 0,
            reason_code="rsi_bullish"
            if bullish
            else "rsi_bearish"
            if bearish
            else "rsi_inside_threshold",
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "RSI",
                "y": [item.get("rsi_value") for item in self.data_list],
                "line": {"color": "#d62728"},
            }
        ]
