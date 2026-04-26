from __future__ import annotations

from trading_algos.alertgen.algorithms.pattern_price_action.base import (
    BasePatternAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.pattern_price_action.pattern_helpers import (
    PatternSignalState,
    relative_volume,
    scale_score,
)
from trading_algos.alertgen.shared_utils.common import TREND


class GapAndGoAlertAlgorithm(BasePatternAlertAlgorithm):
    catalog_ref = "algorithm:75"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        gap_threshold: float = 0.15,
        continuation_threshold: float = 0.05,
        volume_window: int = 3,
        relative_volume_threshold: float = 1.0,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.gap_threshold = float(gap_threshold)
        self.continuation_threshold = float(continuation_threshold)
        self.volume_window = int(volume_window)
        self.relative_volume_threshold = float(relative_volume_threshold)
        super().__init__(
            f"gap_and_go_gap={gap_threshold}",
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return self.volume_window + 2

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "gap_threshold": self.gap_threshold,
            "continuation_threshold": self.continuation_threshold,
            "volume_window": self.volume_window,
            "relative_volume_threshold": self.relative_volume_threshold,
            "pattern_type": "gap_and_go",
        }

    def _state_annotations(self) -> dict[str, object]:
        return {
            "gap_size": self.latest_data_modifiable.get("gap_size"),
            "continuation_amount": self.latest_data_modifiable.get(
                "continuation_amount"
            ),
            "relative_volume": self.latest_data_modifiable.get("relative_volume"),
            "gap_detected": self.latest_data_modifiable.get("gap_detected"),
            "continuation_confirmed": self.latest_data_modifiable.get(
                "continuation_confirmed"
            ),
        }

    def _calculate_state(self) -> PatternSignalState:
        if len(self.data_list) < self.minimum_history():
            return PatternSignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                bullish=False,
                bearish=False,
                primary_value=None,
                signal_value=None,
                threshold_value=self.gap_threshold,
                exit_value=None,
                aligned_count=0,
                reason_code="warmup_pending",
            )

        previous = self.data_list[-2]
        latest = self.data_list[-1]
        previous_close = float(previous["Close"])
        open_value = float(latest["Open"])
        close_value = float(latest["Close"])
        volumes = [float(item["Volume"]) for item in self.data_list]
        gap_size = open_value - previous_close
        continuation_amount = close_value - open_value
        rel_volume = relative_volume(volumes, self.volume_window)
        gap_detected = gap_size >= self.gap_threshold
        volume_confirmed = (
            rel_volume is not None and rel_volume >= self.relative_volume_threshold
        )
        continuation_confirmed = (
            gap_detected
            and continuation_amount >= self.continuation_threshold
            and close_value > open_value
            and volume_confirmed
        )

        self.latest_data_modifiable["gap_size"] = gap_size
        self.latest_data_modifiable["continuation_amount"] = continuation_amount
        self.latest_data_modifiable["relative_volume"] = rel_volume
        self.latest_data_modifiable["gap_detected"] = gap_detected
        self.latest_data_modifiable["continuation_confirmed"] = continuation_confirmed

        if continuation_confirmed:
            reason_code = "gap_and_go_bullish"
            aligned_count = 3
        elif gap_detected and not volume_confirmed:
            reason_code = "gap_detected_volume_missing"
            aligned_count = 1
        elif gap_detected:
            reason_code = "gap_detected_waiting_continuation"
            aligned_count = 2
        else:
            reason_code = "awaiting_gap"
            aligned_count = 0

        return PatternSignalState(
            regime=TREND.UP if continuation_confirmed else TREND.UNKNOWN,
            score=scale_score(
                max(gap_size, 0.0) + max(continuation_amount, 0.0),
                max(self.gap_threshold + self.continuation_threshold, 1e-9),
            ),
            bullish=continuation_confirmed,
            bearish=False,
            primary_value=gap_size,
            signal_value=continuation_amount,
            threshold_value=self.gap_threshold,
            exit_value=rel_volume,
            aligned_count=aligned_count,
            reason_code=reason_code,
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "Gap Size",
                "y": [item.get("gap_size") for item in self.data_list],
                "line": {"color": "#ff7f0e"},
            },
            {
                "name": "Relative Volume",
                "y": [item.get("relative_volume") for item in self.data_list],
                "line": {"color": "#2ca02c"},
                "yaxis": "y2",
            },
        ]
