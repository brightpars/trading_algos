from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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
class WeightedBlendDecision:
    score: float
    direction: int
    confidence: float
    diagnostics: dict[str, Any]


def evaluate_weighted_blend_row(
    row: AlignedCompositeInputRow,
    *,
    weights: dict[str, float],
    buy_threshold: float,
    sell_threshold: float,
) -> WeightedBlendDecision:
    weighted_terms: list[dict[str, Any]] = []
    total_score = 0.0
    confidence_weight_sum = 0.0
    weighted_confidence_total = 0.0

    for child in row.child_outputs:
        weight = float(weights.get(child.child_key, 0.0))
        child_score = clamp_score(child.score)
        contribution = weight * child_score
        total_score += contribution
        child_confidence = clamp_confidence(child.confidence)
        abs_weight = abs(weight)
        confidence_weight_sum += abs_weight
        weighted_confidence_total += abs_weight * child_confidence
        weighted_terms.append(
            {
                "child_key": child.child_key,
                "weight": weight,
                "score": child_score,
                "contribution": contribution,
                "signal_label": child.signal_label,
            }
        )

    clipped_score = clamp_score(total_score)
    if clipped_score >= buy_threshold:
        direction = 1
        decision_reason = "threshold_buy"
    elif clipped_score <= sell_threshold:
        direction = -1
        decision_reason = "threshold_sell"
    else:
        direction = 0
        decision_reason = "inside_neutral_band"

    confidence = (
        weighted_confidence_total / confidence_weight_sum
        if confidence_weight_sum > 0.0
        else 0.0
    )
    diagnostics = {
        "weighted_score": clipped_score,
        "raw_weighted_score": total_score,
        "buy_threshold": buy_threshold,
        "sell_threshold": sell_threshold,
        "decision_reason": decision_reason,
        "weighted_terms": weighted_terms,
        "child_contributions": build_child_contribution_rows(row.child_outputs),
    }
    return WeightedBlendDecision(
        score=clipped_score,
        direction=direction,
        confidence=clamp_confidence(confidence),
        diagnostics=diagnostics,
    )


class WeightedLinearScoreBlendAlertAlgorithm:
    def __init__(
        self,
        *,
        algorithm_key: str,
        symbol: str,
        rows: tuple[AlignedCompositeInputRow, ...],
        params: dict[str, Any],
    ):
        self.algorithm_key = algorithm_key
        self.alg_name = algorithm_key
        self.symbol = symbol
        self.rows = rows
        self.params = params
        self.evaluate_window_len = 1
        self.date = ""
        self.eval_dict: dict[str, Any] = {}
        self.latest_predicted_trend = "neutral"
        self.latest_predicted_trend_confidence = 0.0

    def _required_child_count(self) -> int:
        configured = self.params.get("expected_child_count")
        if configured is not None:
            return int(configured)
        if not self.rows:
            return 0
        return max(len(row.child_outputs) for row in self.rows)

    def process_list(self, _data_list: list[dict[str, Any]]) -> None:
        output = self.normalized_output()
        if not output.points:
            self.latest_predicted_trend = "neutral"
            self.latest_predicted_trend_confidence = 0.0
            return
        latest = output.points[-1]
        self.latest_predicted_trend = latest.signal_label
        self.latest_predicted_trend_confidence = float(latest.confidence or 0.0)

    def algorithm_metadata(self) -> dict[str, Any]:
        return AlgorithmMetadata(
            alg_name=self.alg_name,
            symbol=self.symbol,
            date=self.date,
            evaluate_window_len=self.evaluate_window_len,
        ).to_dict()

    def minimum_history(self) -> int:
        return 1

    def current_decision(self) -> AlgorithmDecision:
        return AlgorithmDecision(
            trend=self.latest_predicted_trend,
            confidence=self.latest_predicted_trend_confidence,
            buy_signal=self.latest_predicted_trend == "buy",
            sell_signal=self.latest_predicted_trend == "sell",
            no_signal=self.latest_predicted_trend == "neutral",
            annotations={"alg_name": self.alg_name},
        )

    def interactive_report_payloads(self) -> list[tuple[dict[str, Any], str]]:
        output = self.normalized_output()
        payload = {
            "algorithm_key": self.algorithm_key,
            "data": output.to_dict(),
            "summary": output.summary_metrics,
        }
        return [(payload, f"composite_trace_{self.algorithm_key}_{self.symbol}")]

    def normalized_output(self) -> AlertAlgorithmOutput:
        points: list[AlertSeriesPoint] = []
        derived_series: dict[str, list[Any]] = {
            "buy_signal": [],
            "sell_signal": [],
            "composite_score": [],
            "raw_weighted_score": [],
            "child_count": [],
            "expected_child_count": [],
            "warmup_ready": [],
            "decision_reason": [],
        }
        child_outputs: list[NormalizedChildOutput] = []
        weights = {
            str(key): float(value) for key, value in self.params["weights"].items()
        }
        decision_reasons: dict[str, int] = {}
        required_child_count = self._required_child_count()
        for row in self.rows:
            warmup_state = evaluate_child_row_warmup(
                row,
                required_child_count=required_child_count,
            )
            if warmup_state.is_ready:
                decision = evaluate_weighted_blend_row(
                    row,
                    weights=weights,
                    buy_threshold=float(self.params["buy_threshold"]),
                    sell_threshold=float(self.params["sell_threshold"]),
                )
                signal_label = direction_to_signal_label(decision.direction)
                diagnostics = {
                    **decision.diagnostics,
                    **warmup_state.diagnostics,
                    "warmup_ready": True,
                    "timestamp": row.timestamp,
                }
                score = decision.score
                confidence = decision.confidence
                reason_codes = (str(decision.diagnostics["decision_reason"]),)
            else:
                signal_label = "neutral"
                diagnostics = {
                    "weighted_score": 0.0,
                    "raw_weighted_score": 0.0,
                    "buy_threshold": float(self.params["buy_threshold"]),
                    "sell_threshold": float(self.params["sell_threshold"]),
                    "decision_reason": warmup_state.reason_code,
                    "weighted_terms": [],
                    "child_contributions": build_child_contribution_rows(
                        row.child_outputs
                    ),
                    **warmup_state.diagnostics,
                    "warmup_ready": False,
                    "timestamp": row.timestamp,
                }
                score = 0.0
                confidence = 0.0
                reason_codes = (warmup_state.reason_code,)
            decision_reason = str(diagnostics["decision_reason"])
            decision_reasons[decision_reason] = (
                decision_reasons.get(decision_reason, 0) + 1
            )
            points.append(
                AlertSeriesPoint(
                    timestamp=row.timestamp,
                    signal_label=signal_label,
                    score=score,
                    confidence=confidence,
                    reason_codes=reason_codes,
                )
            )
            derived_series["buy_signal"].append(signal_label == "buy")
            derived_series["sell_signal"].append(signal_label == "sell")
            derived_series["composite_score"].append(score)
            derived_series["raw_weighted_score"].append(
                diagnostics["raw_weighted_score"]
            )
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
                "decision_reason_counts": decision_reasons,
            },
            metadata={
                "family": "rule_based_combination",
                "subcategory": "weighted",
                "catalog_ref": "combination:2",
                "supports_composition": True,
                "output_contract_version": "1.0",
                "warmup_period": self.minimum_history(),
                "reporting_mode": "composite_trace",
                "params": dict(self.params),
            },
            child_outputs=tuple(child_outputs),
        )


def build_weighted_linear_score_blend_algorithm(
    *,
    algorithm_key: str,
    symbol: str,
    alg_param: dict[str, Any],
    sensor_config: dict[str, Any] | None = None,
    **_kwargs: Any,
) -> WeightedLinearScoreBlendAlertAlgorithm:
    del sensor_config
    rows = align_child_outputs(list(alg_param["rows"]))
    return WeightedLinearScoreBlendAlertAlgorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        rows=rows,
        params=alg_param,
    )
