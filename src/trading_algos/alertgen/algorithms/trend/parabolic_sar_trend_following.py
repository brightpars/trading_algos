from __future__ import annotations

from trading_algos.alertgen.algorithms.trend.moving_average_base import (
    BaseMovingAverageTrendAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.moving_average_helpers import (
    TrendSignalState,
    clamp_unit,
)
from trading_algos.alertgen.shared_utils.common import TREND
from trading_algos.alertgen.shared_utils.indicators import parabolic_sar


class ParabolicSARTrendFollowingAlertAlgorithm(BaseMovingAverageTrendAlertAlgorithm):
    catalog_ref = "algorithm:9"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        step: float = 0.02,
        max_step: float = 0.2,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.step = float(step)
        self.max_step = float(max_step)
        super().__init__(
            f"parabolic_sar_trend_following_step={step}_max={max_step}",
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            minimum_spread=0.0,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return 2

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "step": self.step,
            "max_step": self.max_step,
            "indicator": "parabolic_sar",
        }

    def _calculate_state(self) -> TrendSignalState:
        if len(self.data_list) < self.minimum_history():
            self.latest_data_modifiable["parabolic_sar"] = None
            return TrendSignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                spread=None,
                aligned_count=0,
                bullish=False,
                bearish=False,
                reason_code="warmup_pending",
            )
        highs = [float(item["High"]) for item in self.data_list]
        lows = [float(item["Low"]) for item in self.data_list]
        closes = [float(item["Close"]) for item in self.data_list]
        sar_values = parabolic_sar(highs, lows, step=self.step, max_step=self.max_step)
        sar_value = sar_values[-1]
        close_value = closes[-1]
        self.latest_data_modifiable["parabolic_sar"] = sar_value
        if sar_value is None:
            return TrendSignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                spread=None,
                aligned_count=0,
                bullish=False,
                bearish=False,
                reason_code="warmup_pending",
            )
        spread = close_value - sar_value
        bullish = spread > 0.0
        bearish = spread < 0.0
        scale = max(abs(close_value), 1e-9)
        return TrendSignalState(
            regime=TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score=clamp_unit(spread / scale),
            spread=spread,
            aligned_count=1 if bullish or bearish else 0,
            bullish=bullish,
            bearish=bearish,
            reason_code=(
                "parabolic_sar_bullish"
                if bullish
                else "parabolic_sar_bearish"
                if bearish
                else "parabolic_sar_flat"
            ),
            primary_value=close_value,
            signal_value=sar_value,
            threshold_value=0.0,
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "Parabolic SAR",
                "y": [item.get("parabolic_sar") for item in self.data_list],
                "line": {"color": "#ff9896"},
            }
        ]
