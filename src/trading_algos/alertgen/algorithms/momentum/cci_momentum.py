from __future__ import annotations

from trading_algos.alertgen.algorithms.momentum.base import BaseMomentumAlertAlgorithm
from trading_algos.alertgen.algorithms.momentum.momentum_helpers import (
    MomentumSignalState,
    clamp_unit,
)
from trading_algos.alertgen.shared_utils.common import TREND
from trading_algos.alertgen.shared_utils.indicators import commodity_channel_index


class CCIMomentumAlertAlgorithm(BaseMomentumAlertAlgorithm):
    catalog_ref = "algorithm:23"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        window: int = 20,
        bullish_threshold: float = 100.0,
        bearish_threshold: float = -100.0,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.window = window
        self.bullish_threshold = float(bullish_threshold)
        self.bearish_threshold = float(bearish_threshold)
        super().__init__(
            f"cci_momentum_window={window}",
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
            "bullish_threshold": self.bullish_threshold,
            "bearish_threshold": self.bearish_threshold,
        }

    def _calculate_state(self) -> MomentumSignalState:
        highs = [float(item["High"]) for item in self.data_list]
        lows = [float(item["Low"]) for item in self.data_list]
        closes = [float(item["Close"]) for item in self.data_list]
        cci_values = commodity_channel_index(highs, lows, closes, self.window)
        cci_value = cci_values[-1]
        self.latest_data_modifiable["cci_value"] = cci_value
        if cci_value is None:
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
        bullish = cci_value >= self.bullish_threshold
        bearish = cci_value <= self.bearish_threshold
        scale = max(abs(self.bullish_threshold), abs(self.bearish_threshold), 100.0)
        return MomentumSignalState(
            regime=TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score=clamp_unit(cci_value / scale),
            bullish=bullish,
            bearish=bearish,
            primary_value=cci_value,
            signal_value=None,
            threshold_value=self.bullish_threshold
            if bullish
            else self.bearish_threshold,
            aligned_count=1 if bullish or bearish else 0,
            reason_code="cci_bullish"
            if bullish
            else "cci_bearish"
            if bearish
            else "cci_inside_threshold",
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "CCI",
                "y": [item.get("cci_value") for item in self.data_list],
                "line": {"color": "#7f7f7f"},
            }
        ]
