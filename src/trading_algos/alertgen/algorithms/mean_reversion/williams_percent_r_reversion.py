from __future__ import annotations

from trading_algos.alertgen.algorithms.mean_reversion.base import (
    BaseMeanReversionAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.mean_reversion.mean_reversion_helpers import (
    MeanReversionSignalState,
    centered_oscillator_score,
)
from trading_algos.alertgen.shared_utils.common import TREND
from trading_algos.alertgen.shared_utils.indicators import williams_percent_r


class WilliamsPercentRReversionAlertAlgorithm(BaseMeanReversionAlertAlgorithm):
    catalog_ref = "algorithm:31"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        window: int = 14,
        oversold_threshold: float = -80.0,
        overbought_threshold: float = -20.0,
        exit_threshold: float = -50.0,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.window = window
        self.oversold_threshold = float(oversold_threshold)
        self.overbought_threshold = float(overbought_threshold)
        self.exit_threshold = float(exit_threshold)
        super().__init__(
            f"williams_percent_r_reversion_window={window}",
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
            "oversold_threshold": self.oversold_threshold,
            "overbought_threshold": self.overbought_threshold,
            "exit_threshold": self.exit_threshold,
            "indicator": "williams_percent_r",
        }

    def _calculate_state(self) -> MeanReversionSignalState:
        highs = [float(item["High"]) for item in self.data_list]
        lows = [float(item["Low"]) for item in self.data_list]
        closes = [float(item["Close"]) for item in self.data_list]
        values = williams_percent_r(highs, lows, closes, self.window)
        wr_value = values[-1]
        self.latest_data_modifiable["williams_percent_r"] = wr_value
        if wr_value is None:
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
        bullish = wr_value <= self.oversold_threshold
        bearish = wr_value >= self.overbought_threshold
        return MeanReversionSignalState(
            regime=TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score=centered_oscillator_score(
                wr_value,
                center=self.exit_threshold,
                lower_bound=-100.0,
                upper_bound=0.0,
            ),
            bullish=bullish,
            bearish=bearish,
            primary_value=wr_value,
            signal_value=None,
            threshold_value=(
                self.oversold_threshold if bullish else self.overbought_threshold
            ),
            exit_value=self.exit_threshold,
            aligned_count=1 if bullish or bearish else 0,
            reason_code=(
                "williams_percent_r_oversold"
                if bullish
                else "williams_percent_r_overbought"
                if bearish
                else "williams_percent_r_neutral"
            ),
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "Williams %R",
                "y": [item.get("williams_percent_r") for item in self.data_list],
                "line": {"color": "#9467bd"},
            }
        ]
