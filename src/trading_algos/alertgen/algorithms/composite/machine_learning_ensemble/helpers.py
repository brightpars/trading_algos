from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from trading_algos.alertgen.algorithms.composite.rule_based_combination.helpers import (
    AlignedCompositeInputRow,
    align_child_outputs,
    build_child_contribution_rows,
    clamp_confidence,
    clamp_score,
    direction_to_signal_label,
    evaluate_child_row_warmup,
)
from trading_algos.alertgen.contracts.outputs import (
    AlertAlgorithmOutput,
    AlertSeriesPoint,
    NormalizedChildOutput,
)
from trading_algos.alertgen.shared_utils.models import (
    AlgorithmDecision,
    AlgorithmMetadata,
)


@dataclass(frozen=True)
class EnsembleAggregateDecision:
    score: float
    confidence: float
    direction: int
    diagnostics: dict[str, Any]


def build_prediction_rows(
    raw_rows: Sequence[dict[str, Any]],
) -> tuple[AlignedCompositeInputRow, ...]:
    return align_child_outputs(list(raw_rows))


def extract_numeric_mapping(
    value: Any,
    *,
    label: str,
) -> dict[str, float]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a dict")
    normalized: dict[str, float] = {}
    for key, raw_item in value.items():
        normalized[str(key)] = float(raw_item)
    return normalized


def compute_weighted_child_score(
    row: AlignedCompositeInputRow,
    *,
    child_weights: Mapping[str, float] | None = None,
    confidence_power: float = 1.0,
) -> tuple[float, float, list[dict[str, Any]]]:
    total_weight = 0.0
    weighted_score_sum = 0.0
    weighted_confidence_sum = 0.0
    contributions: list[dict[str, Any]] = []
    for index, child in enumerate(row.child_outputs, start=1):
        base_weight = (
            1.0
            if child_weights is None
            else float(child_weights.get(child.child_key, 1.0))
        )
        confidence = clamp_confidence(child.confidence)
        confidence_weight = (
            confidence**confidence_power if confidence_power > 0.0 else 1.0
        )
        effective_weight = max(base_weight, 0.0) * confidence_weight
        child_score = clamp_score(child.score)
        weighted_score_sum += effective_weight * child_score
        weighted_confidence_sum += effective_weight * confidence
        total_weight += effective_weight
        contributions.append(
            {
                "child_key": child.child_key,
                "child_index": index,
                "base_weight": base_weight,
                "effective_weight": effective_weight,
                "score": child_score,
                "confidence": confidence,
                "signal_label": child.signal_label,
            }
        )
    if total_weight <= 0.0:
        return 0.0, 0.0, contributions
    return (
        clamp_score(weighted_score_sum / total_weight),
        clamp_confidence(weighted_confidence_sum / total_weight),
        contributions,
    )


def resolve_direction(
    *, score: float, buy_threshold: float, sell_threshold: float
) -> tuple[int, str]:
    if score >= buy_threshold:
        return 1, "threshold_buy"
    if score <= sell_threshold:
        return -1, "threshold_sell"
    return 0, "inside_neutral_band"


class BaseMachineLearningEnsembleAlertAlgorithm:
    catalog_ref = ""
    family = "machine_learning_ensemble"
    reporting_mode = "composite_trace"

    def __init__(
        self,
        *,
        algorithm_key: str,
        symbol: str,
        rows: tuple[AlignedCompositeInputRow, ...],
        params: dict[str, Any],
        subcategory: str,
    ) -> None:
        self.algorithm_key = algorithm_key
        self.alg_name = algorithm_key
        self.symbol = symbol
        self.rows = rows
        self.params = params
        self.subcategory = subcategory
        self.evaluate_window_len = 1
        self.date = ""
        self.eval_dict: dict[str, Any] = {}
        self.latest_predicted_trend = "neutral"
        self.latest_predicted_trend_confidence = 0.0

    def minimum_history(self) -> int:
        return int(self.params.get("min_history", 1))

    def _required_child_count(self) -> int:
        configured = self.params.get("expected_child_count")
        if configured is not None:
            return int(configured)
        if not self.rows:
            return 0
        return max(len(row.child_outputs) for row in self.rows)

    def algorithm_metadata(self) -> dict[str, Any]:
        return AlgorithmMetadata(
            alg_name=self.alg_name,
            symbol=self.symbol,
            date=self.date,
            evaluate_window_len=self.evaluate_window_len,
        ).to_dict()

    def current_decision(self) -> AlgorithmDecision:
        return AlgorithmDecision(
            trend=self.latest_predicted_trend,
            confidence=self.latest_predicted_trend_confidence,
            buy_signal=self.latest_predicted_trend == "buy",
            sell_signal=self.latest_predicted_trend == "sell",
            no_signal=self.latest_predicted_trend == "neutral",
            annotations={"alg_name": self.alg_name},
        )

    def process_list(self, _data_list: list[dict[str, Any]]) -> None:
        output = self.normalized_output()
        if not output.points:
            self.latest_predicted_trend = "neutral"
            self.latest_predicted_trend_confidence = 0.0
            return
        latest = output.points[-1]
        self.latest_predicted_trend = latest.signal_label
        self.latest_predicted_trend_confidence = float(latest.confidence or 0.0)

    def evaluate_row(self, row: AlignedCompositeInputRow) -> EnsembleAggregateDecision:
        raise NotImplementedError

    def interactive_report_payloads(self) -> list[tuple[dict[str, Any], str]]:
        output = self.normalized_output()
        payload = {
            "algorithm_key": self.algorithm_key,
            "data": output.to_dict(),
            "summary": output.summary_metrics,
        }
        return [(payload, f"composite_report_{self.algorithm_key}_{self.symbol}")]

    def normalized_output(self) -> AlertAlgorithmOutput:
        points: list[AlertSeriesPoint] = []
        derived_series: dict[str, list[Any]] = {
            "buy_signal": [],
            "sell_signal": [],
            "composite_score": [],
            "child_count": [],
            "expected_child_count": [],
            "warmup_ready": [],
            "decision_reason": [],
        }
        child_outputs: list[NormalizedChildOutput] = []
        reason_counts: dict[str, int] = {}
        required_child_count = self._required_child_count()
        min_history = self.minimum_history()
        for index, row in enumerate(self.rows, start=1):
            warmup_state = evaluate_child_row_warmup(
                row,
                required_child_count=required_child_count,
            )
            history_ready = index >= min_history
            if warmup_state.is_ready and history_ready:
                decision = self.evaluate_row(row)
                signal_label = direction_to_signal_label(decision.direction)
                diagnostics = {
                    **decision.diagnostics,
                    **warmup_state.diagnostics,
                    "warmup_ready": True,
                    "history_ready": True,
                    "timestamp": row.timestamp,
                }
                reason_codes = (str(decision.diagnostics["decision_reason"]),)
                score = decision.score
                confidence = decision.confidence
            else:
                reason_code = (
                    warmup_state.reason_code
                    if not warmup_state.is_ready
                    else "warmup_pending"
                )
                diagnostics = {
                    "decision_reason": reason_code,
                    "child_contributions": build_child_contribution_rows(
                        row.child_outputs
                    ),
                    **warmup_state.diagnostics,
                    "warmup_ready": False,
                    "history_ready": history_ready,
                    "timestamp": row.timestamp,
                }
                signal_label = "neutral"
                reason_codes = (reason_code,)
                score = 0.0
                confidence = 0.0
            decision_reason = str(reason_codes[0])
            reason_counts[decision_reason] = reason_counts.get(decision_reason, 0) + 1
            points.append(
                AlertSeriesPoint(
                    timestamp=row.timestamp,
                    signal_label=signal_label,
                    score=score,
                    confidence=confidence,
                    diagnostics=diagnostics,
                    reason_codes=reason_codes,
                )
            )
            derived_series["buy_signal"].append(signal_label == "buy")
            derived_series["sell_signal"].append(signal_label == "sell")
            derived_series["composite_score"].append(score)
            derived_series["child_count"].append(diagnostics["actual_child_count"])
            derived_series["expected_child_count"].append(
                diagnostics["expected_child_count"]
            )
            derived_series["warmup_ready"].append(diagnostics["warmup_ready"])
            derived_series["decision_reason"].append(decision_reason)
            child_outputs.extend(row.child_outputs)
        return AlertAlgorithmOutput(
            algorithm_key=self.algorithm_key,
            points=tuple(points),
            derived_series=derived_series,
            summary_metrics={
                "point_count": len(points),
                "buy_points": sum(1 for point in points if point.signal_label == "buy"),
                "sell_points": sum(
                    1 for point in points if point.signal_label == "sell"
                ),
                "neutral_points": sum(
                    1 for point in points if point.signal_label == "neutral"
                ),
                "decision_reason_counts": reason_counts,
            },
            metadata={
                "family": self.family,
                "subcategory": self.subcategory,
                "catalog_ref": self.catalog_ref,
                "supports_composition": True,
                "output_contract_version": "1.0",
                "warmup_period": min_history,
                "reporting_mode": self.reporting_mode,
                "params": dict(self.params),
            },
            child_outputs=tuple(child_outputs),
        )
