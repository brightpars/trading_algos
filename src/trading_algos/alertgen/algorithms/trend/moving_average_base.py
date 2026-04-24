from __future__ import annotations

from abc import ABC, abstractmethod

from trading_algos.alertgen.algorithms.trend.moving_average_helpers import (
    TrendSignalState,
    confirmation_state,
)
from trading_algos.alertgen.core.base import BaseAlertAlgorithm
from trading_algos.alertgen.shared_utils.common import TREND


class BaseMovingAverageTrendAlertAlgorithm(BaseAlertAlgorithm, ABC):
    def __init__(
        self,
        alg_name: str,
        *,
        symbol: str,
        report_base_path: str,
        date_str: str = "",
        evaluate_window_len: int = 5,
        minimum_spread: float = 0.0,
        confirmation_bars: int = 1,
    ) -> None:
        super().__init__(
            alg_name,
            symbol,
            date_str,
            evaluate_window_len,
            report_base_path,
        )
        self.minimum_spread = float(minimum_spread)
        self.confirmation_bars = int(confirmation_bars)
        self._bullish_confirmation_count = 0
        self._bearish_confirmation_count = 0

    @abstractmethod
    def _calculate_state(self) -> TrendSignalState:
        """Return the current moving-average state for the latest bar."""

    @abstractmethod
    def _chart_series(self) -> list[dict[str, object]]:
        """Extra chart series for algorithm diagnostics."""

    def _record_state(self, state: TrendSignalState) -> None:
        self.latest_data_modifiable["trend_score"] = state.score
        self.latest_data_modifiable["aligned_count"] = state.aligned_count
        self.latest_data_modifiable["minimum_spread"] = self.minimum_spread
        self.latest_data_modifiable["confirmation_bars"] = self.confirmation_bars
        self.latest_data_modifiable["bullish_setup"] = state.bullish
        self.latest_data_modifiable["bearish_setup"] = state.bearish
        self.latest_data_modifiable["bullish_confirmed"] = False
        self.latest_data_modifiable["bearish_confirmed"] = False
        self.latest_data_modifiable["regime_label"] = state.regime
        if state.spread is not None:
            self.latest_data_modifiable["spread_value"] = state.spread

    def trend_prediction_logic(self) -> None:
        state = self._calculate_state()
        self._record_state(state)
        self._bullish_confirmation_count = confirmation_state(
            self._bullish_confirmation_count,
            condition_met=state.bullish,
        )
        self._bearish_confirmation_count = confirmation_state(
            self._bearish_confirmation_count,
            condition_met=state.bearish,
        )
        bullish_confirmed = self._bullish_confirmation_count >= self.confirmation_bars
        bearish_confirmed = self._bearish_confirmation_count >= self.confirmation_bars
        self.latest_data_modifiable["bullish_confirmation_count"] = (
            self._bullish_confirmation_count
        )
        self.latest_data_modifiable["bearish_confirmation_count"] = (
            self._bearish_confirmation_count
        )
        self.latest_data_modifiable["bullish_confirmed"] = bullish_confirmed
        self.latest_data_modifiable["bearish_confirmed"] = bearish_confirmed
        if bullish_confirmed and not bearish_confirmed:
            self.latest_predicted_trend = TREND.UP
        elif bearish_confirmed and not bullish_confirmed:
            self.latest_predicted_trend = TREND.DOWN
        else:
            self.latest_predicted_trend = TREND.UNKNOWN

    def interactive_report_payloads(self):
        title = f"specific_{self.alg_name}_{self.data_name}"
        payload = self._build_default_signal_chart_payload(
            title=title,
            extra_series=self._chart_series(),
        )
        return [(payload, title)] if payload else []
