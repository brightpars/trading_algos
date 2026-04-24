from __future__ import annotations

from trading_algos.alertgen.algorithms.momentum.base import BaseMomentumAlertAlgorithm
from trading_algos.alertgen.algorithms.momentum.momentum_helpers import (
    MomentumSignalState,
    clamp_unit,
    simple_average,
    weighted_sum_components,
)
from trading_algos.alertgen.shared_utils.common import TREND
from trading_algos.alertgen.shared_utils.indicators import rate_of_change


class KSTKnowSureThingAlertAlgorithm(BaseMomentumAlertAlgorithm):
    catalog_ref = "algorithm:24"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        roc_windows: list[int],
        smoothing_windows: list[int],
        signal_window: int = 9,
        entry_mode: str = "signal_cross",
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.roc_windows = roc_windows
        self.smoothing_windows = smoothing_windows
        self.signal_window = signal_window
        self.entry_mode = entry_mode
        self.weights = [float(index + 1) for index in range(len(self.roc_windows))]
        super().__init__(
            (
                "kst_know_sure_thing"
                f"_roc={','.join(str(value) for value in roc_windows)}"
                f"_smooth={','.join(str(value) for value in smoothing_windows)}"
            ),
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return (
            max(
                roc_window + smoothing_window
                for roc_window, smoothing_window in zip(
                    self.roc_windows, self.smoothing_windows, strict=True
                )
            )
            + self.signal_window
        )

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "roc_windows": tuple(self.roc_windows),
            "smoothing_windows": tuple(self.smoothing_windows),
            "signal_window": self.signal_window,
            "entry_mode": self.entry_mode,
            "indicator": "kst",
        }

    def _calculate_state(self) -> MomentumSignalState:
        if len(self.data_list) < self.minimum_history():
            return MomentumSignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                bullish=False,
                bearish=False,
                primary_value=None,
                signal_value=None,
                threshold_value=0.0,
                aligned_count=0,
                reason_code="warmup_pending",
            )
        closes = [float(item["Close"]) for item in self.data_list]
        component_series: list[list[float | None]] = []
        component_values: list[float | None] = []
        for index, (roc_window, smoothing_window) in enumerate(
            zip(self.roc_windows, self.smoothing_windows, strict=True), start=1
        ):
            roc_series = rate_of_change(closes, roc_window)
            smooth_series = simple_average(roc_series, smoothing_window)
            component_series.append(smooth_series)
            component_value = smooth_series[-1]
            component_values.append(component_value)
            self.latest_data_modifiable[f"kst_component_{index}"] = component_value
        kst_series = weighted_sum_components(component_series, weights=self.weights)
        signal_series = simple_average(kst_series, self.signal_window)
        kst_value = kst_series[-1] if kst_series else None
        signal_value = signal_series[-1] if signal_series else None
        spread_value = (
            None
            if kst_value is None or signal_value is None
            else kst_value - signal_value
        )
        self.latest_data_modifiable["kst_value"] = kst_value
        self.latest_data_modifiable["kst_signal"] = signal_value
        self.latest_data_modifiable["kst_spread"] = spread_value
        if kst_value is None or signal_value is None or spread_value is None:
            return MomentumSignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                bullish=False,
                bearish=False,
                primary_value=None,
                signal_value=None,
                threshold_value=0.0,
                aligned_count=0,
                reason_code="warmup_pending",
            )
        bullish = kst_value > 0.0 and (
            self.entry_mode == "zero_cross"
            or signal_value >= 0.0
            or kst_value >= signal_value
        )
        bearish = kst_value < 0.0 and (
            self.entry_mode == "zero_cross"
            or signal_value <= 0.0
            or kst_value <= signal_value
        )
        scale = max(abs(kst_value), abs(signal_value), 1.0)
        return MomentumSignalState(
            regime=TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score=clamp_unit(spread_value / scale),
            bullish=bullish,
            bearish=bearish,
            primary_value=kst_value,
            signal_value=signal_value,
            threshold_value=0.0,
            aligned_count=sum(value is not None for value in component_values),
            reason_code=(
                "kst_bullish_signal_cross"
                if bullish
                else "kst_bearish_signal_cross"
                if bearish
                else "kst_inside_threshold"
            ),
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "KST",
                "y": [item.get("kst_value") for item in self.data_list],
                "line": {"color": "#ff7f0e"},
            },
            {
                "name": "KST signal",
                "y": [item.get("kst_signal") for item in self.data_list],
                "line": {"color": "#9467bd"},
            },
            {
                "name": "KST spread",
                "y": [item.get("kst_spread") for item in self.data_list],
                "line": {"color": "#2ca02c"},
            },
        ]
