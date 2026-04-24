from __future__ import annotations

from abc import ABC, abstractmethod

from trading_algos.alertgen.algorithms.mean_reversion.mean_reversion_helpers import (
    MeanReversionSignalState,
    confirmation_state,
)
from trading_algos.alertgen.core.base import BaseAlertAlgorithm
from trading_algos.alertgen.shared_utils.common import TREND
from trading_algos.alertgen.shared_utils.models import AlgorithmDecision
from trading_algos.alertgen.contracts.outputs import NormalizedChildOutput


class BaseMeanReversionAlertAlgorithm(BaseAlertAlgorithm, ABC):
    def __init__(
        self,
        alg_name: str,
        *,
        symbol: str,
        report_base_path: str,
        date_str: str = "",
        evaluate_window_len: int = 5,
        confirmation_bars: int = 1,
    ) -> None:
        super().__init__(
            alg_name,
            symbol,
            date_str,
            evaluate_window_len,
            report_base_path,
        )
        self.confirmation_bars = int(confirmation_bars)
        self._bullish_confirmation_count = 0
        self._bearish_confirmation_count = 0

    @abstractmethod
    def _calculate_state(self) -> MeanReversionSignalState:
        """Return the current mean-reversion state for the latest bar."""

    @abstractmethod
    def _chart_series(self) -> list[dict[str, object]]:
        """Extra chart series for algorithm diagnostics."""

    def _parameter_annotations(self) -> dict[str, object]:
        return {}

    def _reason_codes(self, state: MeanReversionSignalState) -> tuple[str, ...]:
        if state.primary_value is None:
            return ("warmup_pending",)
        reason_codes = [state.reason_code, f"regime={state.regime}"]
        if state.aligned_count > 0:
            reason_codes.append(f"aligned_count={state.aligned_count}")
        return tuple(reason_codes)

    def _decision_annotations(self) -> dict[str, object]:
        annotations: dict[str, object] = {
            "alg_name": self.alg_name,
            "catalog_ref": getattr(self, "catalog_ref", None),
            "family": "mean_reversion",
            "reporting_mode": self.reporting_mode(),
            "regime_label": self.latest_data_modifiable.get(
                "regime_label", TREND.UNKNOWN
            ),
            "trend_score": self.latest_data_modifiable.get("trend_score", 0.0),
            "primary_value": self.latest_data_modifiable.get("primary_value"),
            "signal_value": self.latest_data_modifiable.get("signal_value"),
            "threshold_value": self.latest_data_modifiable.get("threshold_value"),
            "exit_value": self.latest_data_modifiable.get("exit_value"),
            "reason_codes": tuple(self.latest_data_modifiable.get("reason_codes", ())),
            "aligned_count": self.latest_data_modifiable.get("aligned_count", 0),
            "confirmation_bars": self.confirmation_bars,
            "bullish_setup": self.latest_data_modifiable.get("bullish_setup", False),
            "bearish_setup": self.latest_data_modifiable.get("bearish_setup", False),
            "bullish_confirmed": self.latest_data_modifiable.get(
                "bullish_confirmed", False
            ),
            "bearish_confirmed": self.latest_data_modifiable.get(
                "bearish_confirmed", False
            ),
            "bullish_confirmation_count": self.latest_data_modifiable.get(
                "bullish_confirmation_count", 0
            ),
            "bearish_confirmation_count": self.latest_data_modifiable.get(
                "bearish_confirmation_count", 0
            ),
            "warmup_period": self.minimum_history(),
            "warmup_ready": len(self.data_list) >= self.minimum_history(),
        }
        annotations.update(self._parameter_annotations())
        return annotations

    def _record_state(self, state: MeanReversionSignalState) -> None:
        self.latest_data_modifiable["trend_score"] = state.score
        self.latest_data_modifiable["aligned_count"] = state.aligned_count
        self.latest_data_modifiable["confirmation_bars"] = self.confirmation_bars
        self.latest_data_modifiable["bullish_setup"] = state.bullish
        self.latest_data_modifiable["bearish_setup"] = state.bearish
        self.latest_data_modifiable["bullish_confirmed"] = False
        self.latest_data_modifiable["bearish_confirmed"] = False
        self.latest_data_modifiable["regime_label"] = state.regime
        self.latest_data_modifiable["reason_codes"] = self._reason_codes(state)
        self.latest_data_modifiable["primary_value"] = state.primary_value
        self.latest_data_modifiable["signal_value"] = state.signal_value
        self.latest_data_modifiable["threshold_value"] = state.threshold_value
        self.latest_data_modifiable["exit_value"] = state.exit_value

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

    def _normalized_child_outputs(self) -> tuple[NormalizedChildOutput, ...]:
        decision = self.current_decision()
        signal_label = (
            "buy"
            if decision.buy_signal
            else "sell"
            if decision.sell_signal
            else "neutral"
        )
        direction = 1 if decision.buy_signal else -1 if decision.sell_signal else 0
        diagnostics = {
            "symbol": self.symbol,
            "warmup_period": self.minimum_history(),
            "evaluate_window_len": self.evaluate_window_len,
            "family": self.output_family(),
            "reporting_mode": self.reporting_mode(),
        }
        diagnostics.update(decision.annotations)
        reason_codes = tuple(diagnostics.keys())
        raw_score = diagnostics.get("trend_score", 0.0)
        score = float(raw_score) if isinstance(raw_score, (int, float)) else 0.0
        if score < -1.0:
            score = -1.0
        elif score > 1.0:
            score = 1.0
        return (
            NormalizedChildOutput(
                child_key=self.alg_name,
                output_kind="composite_child",
                signal_label=signal_label,
                score=score,
                confidence=max(0.0, min(1.0, decision.confidence / 10.0)),
                regime_label=decision.trend,
                direction=direction,
                diagnostics=diagnostics,
                reason_codes=reason_codes,
            ),
        )
