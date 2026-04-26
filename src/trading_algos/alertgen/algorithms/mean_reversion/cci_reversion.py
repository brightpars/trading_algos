from __future__ import annotations

from trading_algos.alertgen.algorithms.mean_reversion.base import (
    BaseMeanReversionAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.mean_reversion.mean_reversion_helpers import (
    MeanReversionSignalState,
    scale_score,
)
from trading_algos.alertgen.shared_utils.common import TREND
from trading_algos.alertgen.shared_utils.indicators import commodity_channel_index


class CCIReversionAlertAlgorithm(BaseMeanReversionAlertAlgorithm):
    catalog_ref = "algorithm:30"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        window: int = 20,
        oversold_threshold: float = -100.0,
        overbought_threshold: float = 100.0,
        exit_threshold: float = 0.0,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.window = window
        self.oversold_threshold = float(oversold_threshold)
        self.overbought_threshold = float(overbought_threshold)
        self.exit_threshold = float(exit_threshold)
        super().__init__(
            f"cci_reversion_window={window}",
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
        }

    def _calculate_state(self) -> MeanReversionSignalState:
        highs = [float(item["High"]) for item in self.data_list]
        lows = [float(item["Low"]) for item in self.data_list]
        closes = [float(item["Close"]) for item in self.data_list]
        cci_values = commodity_channel_index(highs, lows, closes, self.window)
        cci_value = cci_values[-1]
        self.latest_data_modifiable["cci_value"] = cci_value
        if cci_value is None:
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
        bullish = cci_value <= self.oversold_threshold
        bearish = cci_value >= self.overbought_threshold
        scale = max(abs(self.oversold_threshold), abs(self.overbought_threshold), 100.0)
        return MeanReversionSignalState(
            regime=TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score=scale_score(-cci_value, scale),
            bullish=bullish,
            bearish=bearish,
            primary_value=cci_value,
            signal_value=None,
            threshold_value=(
                self.oversold_threshold if bullish else self.overbought_threshold
            ),
            exit_value=self.exit_threshold,
            aligned_count=1 if bullish or bearish else 0,
            reason_code=(
                "cci_oversold"
                if bullish
                else "cci_overbought"
                if bearish
                else "cci_neutral"
            ),
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "CCI",
                "y": [item.get("cci_value") for item in self.data_list],
                "line": {"color": "#7f7f7f"},
            }
        ]
