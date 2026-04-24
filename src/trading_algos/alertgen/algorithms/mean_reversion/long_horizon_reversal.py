from __future__ import annotations

from trading_algos.alertgen.algorithms.mean_reversion.base import (
    BaseMeanReversionAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.mean_reversion.mean_reversion_helpers import (
    MeanReversionSignalState,
    scale_score,
)
from trading_algos.alertgen.shared_utils.common import TREND
from trading_algos.alertgen.shared_utils.indicators import rate_of_change


class LongHorizonReversalAlertAlgorithm(BaseMeanReversionAlertAlgorithm):
    catalog_ref = "algorithm:36"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        window: int = 63,
        entry_return_threshold: float = 10.0,
        exit_return_threshold: float = 3.0,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.window = window
        self.entry_return_threshold = float(entry_return_threshold)
        self.exit_return_threshold = float(exit_return_threshold)
        super().__init__(
            f"long_horizon_reversal_window={window}",
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
            "entry_return_threshold": self.entry_return_threshold,
            "exit_return_threshold": self.exit_return_threshold,
            "indicator": "rate_of_change",
        }

    def _calculate_state(self) -> MeanReversionSignalState:
        closes = [float(item["Close"]) for item in self.data_list]
        returns = rate_of_change(closes, self.window)
        return_value = returns[-1]
        self.latest_data_modifiable["long_horizon_return"] = return_value
        if return_value is None:
            return MeanReversionSignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                bullish=False,
                bearish=False,
                primary_value=None,
                signal_value=None,
                threshold_value=-self.entry_return_threshold,
                exit_value=self.exit_return_threshold,
                aligned_count=0,
                reason_code="warmup_pending",
            )
        bullish = return_value <= -self.entry_return_threshold
        bearish = return_value >= self.entry_return_threshold
        return MeanReversionSignalState(
            regime=TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score=scale_score(-return_value, self.entry_return_threshold),
            bullish=bullish,
            bearish=bearish,
            primary_value=return_value,
            signal_value=None,
            threshold_value=(
                -self.entry_return_threshold if bullish else self.entry_return_threshold
            ),
            exit_value=self.exit_return_threshold,
            aligned_count=1 if bullish or bearish else 0,
            reason_code=(
                "long_horizon_oversold"
                if bullish
                else "long_horizon_overbought"
                if bearish
                else "long_horizon_neutral"
            ),
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "Long-Horizon Return",
                "y": [item.get("long_horizon_return") for item in self.data_list],
                "line": {"color": "#8c564b"},
                "yaxis": "y2",
            }
        ]
