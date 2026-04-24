from __future__ import annotations

from trading_algos.alertgen.algorithms.volatility_options.base import (
    BaseVolatilityAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.volatility_options.volatility_helpers import (
    VolatilitySignalState,
    scale_score,
)
from trading_algos.alertgen.shared_utils.common import TREND
from trading_algos.alertgen.shared_utils.indicators import (
    compression_ratio,
    rolling_high,
)


class VolatilityBreakoutAlertAlgorithm(BaseVolatilityAlertAlgorithm):
    catalog_ref = "algorithm:52"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        atr_window: int = 5,
        compression_window: int = 5,
        compression_threshold: float = 2.0,
        breakout_lookback: int = 5,
        breakout_buffer: float = 0.1,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.atr_window = atr_window
        self.compression_window = compression_window
        self.compression_threshold = float(compression_threshold)
        self.breakout_lookback = breakout_lookback
        self.breakout_buffer = float(breakout_buffer)
        super().__init__(
            f"volatility_breakout_atr={atr_window}_compression={compression_window}",
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return max(self.atr_window, self.compression_window, self.breakout_lookback) + 1

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "atr_window": self.atr_window,
            "compression_window": self.compression_window,
            "compression_threshold": self.compression_threshold,
            "breakout_lookback": self.breakout_lookback,
            "breakout_buffer": self.breakout_buffer,
            "indicator": "compression_breakout",
        }

    def _state_annotations(self) -> dict[str, object]:
        return {
            "atr_value": self.latest_data_modifiable.get("atr_value"),
            "compression_range": self.latest_data_modifiable.get("compression_range"),
            "compression_ratio": self.latest_data_modifiable.get("compression_ratio"),
            "compression_flag": self.latest_data_modifiable.get("compression_flag"),
            "breakout_level": self.latest_data_modifiable.get("breakout_level"),
        }

    def _calculate_state(self) -> VolatilitySignalState:
        highs = [float(item["High"]) for item in self.data_list]
        lows = [float(item["Low"]) for item in self.data_list]
        closes = [float(item["Close"]) for item in self.data_list]
        atr_values, range_values, ratio_values = compression_ratio(
            highs,
            lows,
            closes,
            atr_window=self.atr_window,
            compression_window=self.compression_window,
        )
        breakout_highs = rolling_high(highs, self.breakout_lookback)
        atr_value = atr_values[-1]
        range_value = range_values[-1]
        ratio_value = ratio_values[-1]
        breakout_level = breakout_highs[-2] if len(breakout_highs) >= 2 else None
        close_value = closes[-1]
        compression_flag = (
            ratio_value is not None and ratio_value <= self.compression_threshold
        )
        bullish = False
        if breakout_level is not None:
            bullish = close_value >= (breakout_level + self.breakout_buffer) and any(
                bool(item.get("compression_flag"))
                for item in self.data_list[-self.compression_window : -1]
            )
        self.latest_data_modifiable["atr_value"] = atr_value
        self.latest_data_modifiable["compression_range"] = range_value
        self.latest_data_modifiable["compression_ratio"] = ratio_value
        self.latest_data_modifiable["compression_flag"] = compression_flag
        self.latest_data_modifiable["breakout_level"] = breakout_level
        if ratio_value is None or breakout_level is None:
            return VolatilitySignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                bullish=False,
                bearish=False,
                primary_value=None,
                signal_value=breakout_level,
                threshold_value=self.compression_threshold,
                exit_value=None,
                aligned_count=0,
                reason_code="warmup_pending",
            )
        return VolatilitySignalState(
            regime=TREND.UP if bullish else TREND.UNKNOWN,
            score=scale_score(
                self.compression_threshold - ratio_value, self.compression_threshold
            ),
            bullish=bullish,
            bearish=False,
            primary_value=ratio_value,
            signal_value=breakout_level,
            threshold_value=self.compression_threshold,
            exit_value=None,
            aligned_count=2 if bullish and compression_flag else 1 if bullish else 0,
            reason_code="volatility_breakout_up"
            if bullish
            else "compression_detected"
            if compression_flag
            else "awaiting_breakout",
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "Breakout Level",
                "y": [item.get("breakout_level") for item in self.data_list],
                "line": {"color": "#ff7f0e"},
            },
            {
                "name": "Compression Ratio",
                "y": [item.get("compression_ratio") for item in self.data_list],
                "line": {"color": "#2ca02c"},
                "yaxis": "y2",
            },
        ]
