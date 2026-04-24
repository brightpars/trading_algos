from __future__ import annotations

from trading_algos.alertgen.algorithms.mean_reversion.base import (
    BaseMeanReversionAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.mean_reversion.mean_reversion_helpers import (
    MeanReversionSignalState,
    cumulative_session_vwap,
    parse_session_label,
    scale_score,
)
from trading_algos.alertgen.shared_utils.common import TREND


class IntradayVWAPReversionAlertAlgorithm(BaseMeanReversionAlertAlgorithm):
    catalog_ref = "algorithm:32"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        entry_deviation_percent: float = 1.5,
        exit_deviation_percent: float = 0.4,
        min_session_bars: int = 3,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.entry_deviation_percent = float(entry_deviation_percent)
        self.exit_deviation_percent = float(exit_deviation_percent)
        self.min_session_bars = int(min_session_bars)
        super().__init__(
            "intraday_vwap_reversion",
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return self.min_session_bars

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "entry_deviation_percent": self.entry_deviation_percent,
            "exit_deviation_percent": self.exit_deviation_percent,
            "min_session_bars": self.min_session_bars,
            "indicator": "session_vwap_deviation",
        }

    def _state_annotations(self) -> dict[str, object]:
        return {
            "session_label": self.latest_data_modifiable.get("session_label"),
            "session_bar_index": self.latest_data_modifiable.get("session_bar_index"),
            "session_vwap": self.latest_data_modifiable.get("session_vwap"),
            "vwap_deviation_percent": self.latest_data_modifiable.get(
                "vwap_deviation_percent"
            ),
        }

    def _calculate_state(self) -> MeanReversionSignalState:
        timestamps = [str(item["ts"]) for item in self.data_list]
        highs = [float(item["High"]) for item in self.data_list]
        lows = [float(item["Low"]) for item in self.data_list]
        closes = [float(item["Close"]) for item in self.data_list]
        volumes = [float(item.get("Volume", 0.0)) for item in self.data_list]
        vwap_values = cumulative_session_vwap(timestamps, highs, lows, closes, volumes)

        latest_timestamp = timestamps[-1]
        session_label = parse_session_label(latest_timestamp)
        session_bar_index = sum(
            1
            for timestamp in timestamps
            if parse_session_label(timestamp) == session_label
        )
        session_vwap = vwap_values[-1]
        close_value = closes[-1]
        deviation_percent = None
        if session_vwap not in (None, 0.0):
            assert session_vwap is not None
            deviation_percent = ((close_value - session_vwap) / session_vwap) * 100.0

        self.latest_data_modifiable["session_label"] = session_label
        self.latest_data_modifiable["session_bar_index"] = session_bar_index
        self.latest_data_modifiable["session_vwap"] = session_vwap
        self.latest_data_modifiable["vwap_deviation_percent"] = deviation_percent

        if deviation_percent is None or session_bar_index < self.min_session_bars:
            return MeanReversionSignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                bullish=False,
                bearish=False,
                primary_value=None,
                signal_value=session_vwap,
                threshold_value=-self.entry_deviation_percent,
                exit_value=self.exit_deviation_percent,
                aligned_count=0,
                reason_code="warmup_pending",
            )

        bullish = deviation_percent <= -self.entry_deviation_percent
        bearish = deviation_percent >= self.entry_deviation_percent
        return MeanReversionSignalState(
            regime=TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score=scale_score(-deviation_percent, self.entry_deviation_percent),
            bullish=bullish,
            bearish=bearish,
            primary_value=deviation_percent,
            signal_value=session_vwap,
            threshold_value=(
                -self.entry_deviation_percent
                if bullish
                else self.entry_deviation_percent
            ),
            exit_value=self.exit_deviation_percent,
            aligned_count=1 if bullish or bearish else 0,
            reason_code=(
                "vwap_below_session_mean"
                if bullish
                else "vwap_above_session_mean"
                if bearish
                else "vwap_near_session_mean"
            ),
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "Session VWAP",
                "y": [item.get("session_vwap") for item in self.data_list],
                "line": {"color": "#ff7f0e"},
            },
            {
                "name": "VWAP Deviation %",
                "y": [item.get("vwap_deviation_percent") for item in self.data_list],
                "line": {"color": "#17becf"},
                "yaxis": "y2",
            },
        ]
