from __future__ import annotations

from abc import ABC, abstractmethod

from trading_algos.alertgen.algorithms.trend.moving_average_helpers import (
    TrendSignalState,
    confirmation_state,
)
from trading_algos.alertgen.core.base import BaseAlertAlgorithm
from trading_algos.alertgen.shared_utils.common import TREND
from trading_algos.alertgen.shared_utils.models import AlgorithmDecision


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

    def _parameter_annotations(self) -> dict[str, object]:
        return {}

    def _state_annotations(self) -> dict[str, object]:
        return {}

    def _reason_codes(self, state: TrendSignalState) -> tuple[str, ...]:
        reason_codes: list[str] = []
        if state.primary_value is None and state.spread is None:
            reason_codes.append("warmup_pending")
            return tuple(reason_codes)
        if state.reason_code:
            reason_codes.append(state.reason_code)
        elif state.bullish:
            reason_codes.append("bullish_setup")
        elif state.bearish:
            reason_codes.append("bearish_setup")
        else:
            reason_codes.append("spread_inside_threshold")
        if state.aligned_count > 0:
            reason_codes.append(f"aligned_count={state.aligned_count}")
        reason_codes.append(f"regime={state.regime}")
        return tuple(reason_codes)

    def _decision_annotations(self) -> dict[str, object]:
        bullish_setup = self.latest_data_modifiable.get("bullish_setup", False)
        bearish_setup = self.latest_data_modifiable.get("bearish_setup", False)
        bullish_confirmed = self.latest_data_modifiable.get("bullish_confirmed", False)
        bearish_confirmed = self.latest_data_modifiable.get("bearish_confirmed", False)
        confirmation_state_label = "idle"
        if bullish_confirmed or bearish_confirmed:
            confirmation_state_label = "confirmed"
        elif bullish_setup or bearish_setup:
            confirmation_state_label = "pending"
        annotations: dict[str, object] = {
            "alg_name": self.alg_name,
            "catalog_ref": getattr(self, "catalog_ref", None),
            "family": "trend",
            "reporting_mode": self.reporting_mode(),
            "regime_label": self.latest_data_modifiable.get(
                "regime_label", TREND.UNKNOWN
            ),
            "trend_score": self.latest_data_modifiable.get("trend_score", 0.0),
            "primary_value": self.latest_data_modifiable.get("primary_value"),
            "signal_value": self.latest_data_modifiable.get("signal_value"),
            "threshold_value": self.latest_data_modifiable.get("threshold_value"),
            "spread_value": self.latest_data_modifiable.get("spread_value"),
            "reason_codes": tuple(self.latest_data_modifiable.get("reason_codes", ())),
            "aligned_count": self.latest_data_modifiable.get("aligned_count", 0),
            "minimum_spread": self.minimum_spread,
            "confirmation_bars": self.confirmation_bars,
            "bullish_setup": bullish_setup,
            "bearish_setup": bearish_setup,
            "bullish_confirmed": bullish_confirmed,
            "bearish_confirmed": bearish_confirmed,
            "bullish_confirmation_count": self.latest_data_modifiable.get(
                "bullish_confirmation_count", 0
            ),
            "bearish_confirmation_count": self.latest_data_modifiable.get(
                "bearish_confirmation_count", 0
            ),
            "confirmation_state_label": confirmation_state_label,
            "warmup_period": self.minimum_history(),
            "warmup_ready": len(self.data_list) >= self.minimum_history(),
        }
        annotations.update(self._parameter_annotations())
        annotations.update(self._state_annotations())
        return annotations

    def _record_state(self, state: TrendSignalState) -> None:
        self.latest_data_modifiable["trend_score"] = state.score
        self.latest_data_modifiable["aligned_count"] = state.aligned_count
        self.latest_data_modifiable["minimum_spread"] = self.minimum_spread
        self.latest_data_modifiable["confirmation_bars"] = self.confirmation_bars
        self.latest_data_modifiable["warmup_ready"] = (
            len(self.data_list) >= self.minimum_history()
        )
        self.latest_data_modifiable["bullish_setup"] = state.bullish
        self.latest_data_modifiable["bearish_setup"] = state.bearish
        self.latest_data_modifiable["bullish_confirmed"] = False
        self.latest_data_modifiable["bearish_confirmed"] = False
        self.latest_data_modifiable["confirmation_state_label"] = "idle"
        self.latest_data_modifiable["regime_label"] = state.regime
        self.latest_data_modifiable["reason_codes"] = self._reason_codes(state)
        self.latest_data_modifiable["primary_value"] = state.primary_value
        self.latest_data_modifiable["signal_value"] = state.signal_value
        self.latest_data_modifiable["threshold_value"] = state.threshold_value
        if state.spread is not None:
            self.latest_data_modifiable["spread_value"] = state.spread
        if state.upper_band is not None:
            self.latest_data_modifiable["upper_band"] = state.upper_band
        if state.lower_band is not None:
            self.latest_data_modifiable["lower_band"] = state.lower_band

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
        confirmation_state_label = "idle"
        if bullish_confirmed or bearish_confirmed:
            confirmation_state_label = "confirmed"
        elif state.bullish or state.bearish:
            confirmation_state_label = "pending"
        self.latest_data_modifiable["confirmation_state_label"] = (
            confirmation_state_label
        )
        reason_codes = list(tuple(self.latest_data_modifiable.get("reason_codes", ())))
        if bullish_confirmed or bearish_confirmed:
            reason_codes.append("confirmation_confirmed")
        elif state.bullish or state.bearish:
            reason_codes.append("confirmation_pending")
        self.latest_data_modifiable["reason_codes"] = tuple(reason_codes)
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

    def current_decision(self) -> AlgorithmDecision:
        return AlgorithmDecision(
            trend=self.latest_predicted_trend,
            confidence=self.latest_predicted_trend_confidence,
            buy_signal=self.latest_predicted_trend == TREND.UP,
            sell_signal=self.latest_predicted_trend == TREND.DOWN,
            buy_range_signal=self.latest_predicted_trend == TREND.RANGE_UP,
            sell_range_signal=self.latest_predicted_trend == TREND.RANGE_DOWN,
            no_signal=self.latest_predicted_trend not in [TREND.UP, TREND.DOWN],
            annotations=self._decision_annotations(),
        )

    def _normalized_signal_score(self, item: dict[str, object]) -> float:
        raw_score = item.get("trend_score", 0.0)
        if isinstance(raw_score, (int, float)):
            score = float(raw_score)
            if score < -1.0:
                return -1.0
            if score > 1.0:
                return 1.0
            return score
        return 0.0
