from __future__ import annotations

from trading_algos.alertgen.algorithms.mean_reversion.base import (
    BaseMeanReversionAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.mean_reversion.mean_reversion_helpers import (
    MeanReversionSignalState,
    scale_score,
)
from trading_algos.alertgen.shared_utils.common import TREND
from trading_algos.alertgen.shared_utils.indicators import relative_strength_index


class RSIReversionAlertAlgorithm(BaseMeanReversionAlertAlgorithm):
    catalog_ref = "algorithm:28"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        window: int = 14,
        oversold_threshold: float = 30.0,
        overbought_threshold: float = 70.0,
        exit_threshold: float = 50.0,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.window = window
        self.oversold_threshold = float(oversold_threshold)
        self.overbought_threshold = float(overbought_threshold)
        self.exit_threshold = float(exit_threshold)
        super().__init__(
            f"rsi_reversion_window={window}",
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
            "oversold_threshold": self.oversold_threshold,
            "overbought_threshold": self.overbought_threshold,
            "exit_threshold": self.exit_threshold,
        }

    def _calculate_state(self) -> MeanReversionSignalState:
        closes = [float(item["Close"]) for item in self.data_list]
        rsi_values = relative_strength_index(closes, self.window)
        rsi_value = rsi_values[-1]
        self.latest_data_modifiable["rsi_value"] = rsi_value
        if rsi_value is None:
            return MeanReversionSignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                bullish=False,
                bearish=False,
                primary_value=None,
                signal_value=None,
                threshold_value=self.oversold_threshold,
                exit_value=self.exit_threshold,
                aligned_count=0,
                reason_code="warmup_pending",
            )
        bullish = rsi_value <= self.oversold_threshold
        bearish = rsi_value >= self.overbought_threshold
        centered_reversion = 50.0 - rsi_value
        return MeanReversionSignalState(
            regime=TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score=scale_score(centered_reversion, 50.0),
            bullish=bullish,
            bearish=bearish,
            primary_value=rsi_value,
            signal_value=None,
            threshold_value=(
                self.oversold_threshold if bullish else self.overbought_threshold
            ),
            exit_value=self.exit_threshold,
            aligned_count=1 if bullish or bearish else 0,
            reason_code=(
                "rsi_oversold"
                if bullish
                else "rsi_overbought"
                if bearish
                else "rsi_neutral"
            ),
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "RSI",
                "y": [item.get("rsi_value") for item in self.data_list],
                "line": {"color": "#d62728"},
            }
        ]
