from __future__ import annotations

from trading_algos.alertgen.algorithms.mean_reversion.base import (
    BaseMeanReversionAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.mean_reversion.mean_reversion_helpers import (
    MeanReversionSignalState,
    parse_session_label,
    scale_score,
)
from trading_algos.alertgen.shared_utils.common import TREND


class OpeningGapFadeAlertAlgorithm(BaseMeanReversionAlertAlgorithm):
    catalog_ref = "algorithm:33"

    def __init__(
        self,
        symbol: str,
        report_base_path: str,
        *,
        min_gap_percent: float = 1.0,
        exit_gap_fill_percent: float = 0.25,
        min_session_bars: int = 2,
        confirmation_bars: int = 1,
        date_str: str = "",
        evaluate_window_len: int = 5,
    ) -> None:
        self.min_gap_percent = float(min_gap_percent)
        self.exit_gap_fill_percent = float(exit_gap_fill_percent)
        self.min_session_bars = int(min_session_bars)
        super().__init__(
            "opening_gap_fade",
            symbol=symbol,
            report_base_path=report_base_path,
            date_str=date_str,
            evaluate_window_len=evaluate_window_len,
            confirmation_bars=confirmation_bars,
        )

    def minimum_history(self) -> int:
        return self.min_session_bars + 1

    def _parameter_annotations(self) -> dict[str, object]:
        return {
            "min_gap_percent": self.min_gap_percent,
            "exit_gap_fill_percent": self.exit_gap_fill_percent,
            "min_session_bars": self.min_session_bars,
            "indicator": "opening_gap_percent",
        }

    def _state_annotations(self) -> dict[str, object]:
        return {
            "session_label": self.latest_data_modifiable.get("session_label"),
            "session_bar_index": self.latest_data_modifiable.get("session_bar_index"),
            "opening_gap_percent": self.latest_data_modifiable.get(
                "opening_gap_percent"
            ),
            "prior_session_close": self.latest_data_modifiable.get(
                "prior_session_close"
            ),
            "gap_fill_progress": self.latest_data_modifiable.get("gap_fill_progress"),
        }

    def _calculate_state(self) -> MeanReversionSignalState:
        latest = self.data_list[-1]
        latest_session = parse_session_label(str(latest["ts"]))
        session_rows = [
            item
            for item in self.data_list
            if parse_session_label(str(item["ts"])) == latest_session
        ]
        session_bar_index = len(session_rows)
        opening_row = session_rows[0]

        prior_session_rows = [
            item
            for item in self.data_list[:-session_bar_index]
            if parse_session_label(str(item["ts"])) != latest_session
        ]
        prior_session_close = (
            float(prior_session_rows[-1]["Close"]) if prior_session_rows else None
        )
        opening_price = float(opening_row["Open"])
        close_value = float(latest["Close"])
        gap_percent = None
        gap_fill_progress = None
        if prior_session_close not in (None, 0.0):
            assert prior_session_close is not None
            gap_percent = (
                (opening_price - prior_session_close) / prior_session_close
            ) * 100.0
            gap_fill_progress = (
                (close_value - prior_session_close)
                / (opening_price - prior_session_close)
                if opening_price != prior_session_close
                else 0.0
            )

        self.latest_data_modifiable["session_label"] = latest_session
        self.latest_data_modifiable["session_bar_index"] = session_bar_index
        self.latest_data_modifiable["opening_gap_percent"] = gap_percent
        self.latest_data_modifiable["prior_session_close"] = prior_session_close
        self.latest_data_modifiable["gap_fill_progress"] = gap_fill_progress

        if (
            gap_percent is None
            or gap_fill_progress is None
            or session_bar_index < self.min_session_bars
        ):
            return MeanReversionSignalState(
                regime=TREND.UNKNOWN,
                score=0.0,
                bullish=False,
                bearish=False,
                primary_value=None,
                signal_value=prior_session_close,
                threshold_value=self.min_gap_percent,
                exit_value=self.exit_gap_fill_percent,
                aligned_count=0,
                reason_code="warmup_pending",
            )

        bullish = gap_percent < 0.0 and abs(gap_percent) >= self.min_gap_percent
        bearish = gap_percent > 0.0 and abs(gap_percent) >= self.min_gap_percent
        score = 0.0
        if bullish:
            score = scale_score(abs(gap_percent), self.min_gap_percent)
        elif bearish:
            score = -scale_score(abs(gap_percent), self.min_gap_percent)

        return MeanReversionSignalState(
            regime=TREND.UP if bullish else TREND.DOWN if bearish else TREND.UNKNOWN,
            score=score,
            bullish=bullish,
            bearish=bearish,
            primary_value=gap_percent,
            signal_value=prior_session_close,
            threshold_value=(
                -self.min_gap_percent if bullish else self.min_gap_percent
            ),
            exit_value=self.exit_gap_fill_percent,
            aligned_count=1 if bullish or bearish else 0,
            reason_code=(
                "gap_down_fade"
                if bullish
                else "gap_up_fade"
                if bearish
                else "gap_below_threshold"
            ),
        )

    def _chart_series(self) -> list[dict[str, object]]:
        return [
            {
                "name": "Prior Session Close",
                "y": [item.get("prior_session_close") for item in self.data_list],
                "line": {"color": "#ff7f0e"},
            },
            {
                "name": "Opening Gap %",
                "y": [item.get("opening_gap_percent") for item in self.data_list],
                "line": {"color": "#2ca02c"},
                "yaxis": "y2",
            },
        ]
