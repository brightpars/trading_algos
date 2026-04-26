from __future__ import annotations

from trading_algos.alertgen.algorithms.mean_reversion.base import (
    BaseMeanReversionAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.mean_reversion.mean_reversion_helpers import (
    MeanReversionSignalState,
    scale_score,
)
from trading_algos.alertgen.shared_utils.common import TREND
from trading_algos.alertgen.shared_utils.indicators import stochastic_oscillator


class StochasticReversionAlertAlgorithm(BaseMeanReversionAlertAlgorithm):
    catalog_ref = "algorithm:29"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        k_window: int = 14,
        d_window: int = 3,
        oversold_threshold: float = 20.0,
        overbought_threshold: float = 80.0,
        exit_threshold: float = 50.0,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.k_window = k_window
        self.d_window = d_window
        self.oversold_threshold = float(oversold_threshold)
        self.overbought_threshold = float(overbought_threshold)
        self.exit_threshold = float(exit_threshold)
        super().__init__(
            f"stochastic_reversion_k={k_window}_d={d_window}",
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return self.k_window + self.d_window - 1

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "k_window": self.k_window,
            "d_window": self.d_window,
            "oversold_threshold": self.oversold_threshold,
            "overbought_threshold": self.overbought_threshold,
            "exit_threshold": self.exit_threshold,
        }

    def _calculate_state(self) -> MeanReversionSignalState:
        highs = [float(item["High"]) for item in self.data_list]
        lows = [float(item["Low"]) for item in self.data_list]
        closes = [float(item["Close"]) for item in self.data_list]
        percent_k, percent_d = stochastic_oscillator(
            highs, lows, closes, self.k_window, self.d_window
        )
        k_value = percent_k[-1]
        d_value = percent_d[-1]
        self.latest_data_modifiable["stochastic_k"] = k_value
        self.latest_data_modifiable["stochastic_d"] = d_value
        if k_value is None or d_value is None:
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
        bullish = k_value <= self.oversold_threshold and k_value <= d_value
        bearish = k_value >= self.overbought_threshold and k_value >= d_value
        centered_reversion = 50.0 - k_value
        return MeanReversionSignalState(
            regime=TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score=scale_score(centered_reversion, 50.0),
            bullish=bullish,
            bearish=bearish,
            primary_value=k_value,
            signal_value=d_value,
            threshold_value=(
                self.oversold_threshold if bullish else self.overbought_threshold
            ),
            exit_value=self.exit_threshold,
            aligned_count=2 if bullish or bearish else 0,
            reason_code=(
                "stochastic_oversold"
                if bullish
                else "stochastic_overbought"
                if bearish
                else "stochastic_neutral"
            ),
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "%K",
                "y": [item.get("stochastic_k") for item in self.data_list],
                "line": {"color": "#17becf"},
            },
            {
                "name": "%D",
                "y": [item.get("stochastic_d") for item in self.data_list],
                "line": {"color": "#8c564b"},
            },
        ]
