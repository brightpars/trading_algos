from __future__ import annotations

from trading_algos.alertgen.algorithms.mean_reversion.base import (
    BaseMeanReversionAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.mean_reversion.mean_reversion_helpers import (
    MeanReversionSignalState,
    scale_score,
)
from trading_algos.alertgen.shared_utils.common import TREND
from trading_algos.alertgen.shared_utils.indicators import rolling_mean, rolling_std


class ZScoreMeanReversionAlertAlgorithm(BaseMeanReversionAlertAlgorithm):
    catalog_ref = "algorithm:26"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        window: int = 20,
        entry_zscore: float = 2.0,
        exit_zscore: float = 0.5,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.window = window
        self.entry_zscore = float(entry_zscore)
        self.exit_zscore = float(exit_zscore)
        super().__init__(
            f"z_score_mean_reversion_window={window}",
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
            "entry_zscore": self.entry_zscore,
            "exit_zscore": self.exit_zscore,
        }

    def _calculate_state(self) -> MeanReversionSignalState:
        closes = [float(item["Close"]) for item in self.data_list]
        mean_values = rolling_mean(closes, self.window)
        std_values = rolling_std(closes, self.window)
        mean_value = mean_values[-1]
        std_value = std_values[-1]
        close_value = closes[-1]
        zscore_value = None
        if mean_value is not None and std_value not in (None, 0.0):
            assert std_value is not None
            zscore_value = (close_value - mean_value) / std_value
        self.latest_data_modifiable["rolling_mean"] = mean_value
        self.latest_data_modifiable["rolling_std"] = std_value
        self.latest_data_modifiable["zscore_value"] = zscore_value
        if zscore_value is None:
            return MeanReversionSignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                bullish=False,
                bearish=False,
                primary_value=None,
                signal_value=mean_value,
                threshold_value=-self.entry_zscore,
                exit_value=self.exit_zscore,
                aligned_count=0,
                reason_code="warmup_pending",
            )
        bullish = zscore_value <= -self.entry_zscore
        bearish = zscore_value >= self.entry_zscore
        return MeanReversionSignalState(
            regime=TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score=scale_score(-zscore_value, self.entry_zscore),
            bullish=bullish,
            bearish=bearish,
            primary_value=zscore_value,
            signal_value=mean_value,
            threshold_value=-self.entry_zscore if bullish else self.entry_zscore,
            exit_value=self.exit_zscore,
            aligned_count=1 if bullish or bearish else 0,
            reason_code=(
                "zscore_oversold"
                if bullish
                else "zscore_overbought"
                if bearish
                else "zscore_inside_band"
            ),
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "Rolling Mean",
                "y": [item.get("rolling_mean") for item in self.data_list],
                "line": {"color": "#ff7f0e"},
            },
            {
                "name": "Z-Score",
                "y": [item.get("zscore_value") for item in self.data_list],
                "line": {"color": "#2ca02c"},
                "yaxis": "y2",
            },
        ]
