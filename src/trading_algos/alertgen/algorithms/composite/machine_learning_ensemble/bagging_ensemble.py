from __future__ import annotations

from typing import Any

from trading_algos.alertgen.algorithms.composite.machine_learning_ensemble.helpers import (
    BaseMachineLearningEnsembleAlertAlgorithm,
    EnsembleAggregateDecision,
    build_prediction_rows,
    compute_weighted_child_score,
    extract_numeric_mapping,
    resolve_direction,
)


class BaggingEnsembleAlertAlgorithm(BaseMachineLearningEnsembleAlertAlgorithm):
    catalog_ref = "combination:8"

    def __init__(
        self, *, algorithm_key: str, symbol: str, params: dict[str, Any]
    ) -> None:
        super().__init__(
            algorithm_key=algorithm_key,
            symbol=symbol,
            rows=build_prediction_rows(list(params["rows"])),
            params=params,
            subcategory="bagging",
        )

    def evaluate_row(self, row) -> EnsembleAggregateDecision:
        child_weights = extract_numeric_mapping(
            self.params.get("child_weights"),
            label=f"{self.algorithm_key} child_weights",
        )
        score, confidence, weighted_children = compute_weighted_child_score(
            row,
            child_weights=child_weights or None,
            confidence_power=float(self.params.get("confidence_power", 1.0)),
        )
        score *= float(self.params.get("bootstrap_diversity_multiplier", 1.0))
        score = max(-1.0, min(1.0, score))
        direction, decision_reason = resolve_direction(
            score=score,
            buy_threshold=float(self.params["buy_threshold"]),
            sell_threshold=float(self.params["sell_threshold"]),
        )
        diagnostics = {
            "aggregation_method": "bagging_average",
            "decision_reason": decision_reason,
            "bootstrap_diversity_multiplier": float(
                self.params.get("bootstrap_diversity_multiplier", 1.0)
            ),
            "weighted_children": weighted_children,
            "raw_ensemble_score": score,
        }
        return EnsembleAggregateDecision(
            score=score,
            confidence=confidence,
            direction=direction,
            diagnostics=diagnostics,
        )


def build_bagging_ensemble_algorithm(
    *, algorithm_key: str, symbol: str, alg_param: dict[str, Any], **_kwargs: Any
) -> BaggingEnsembleAlertAlgorithm:
    return BaggingEnsembleAlertAlgorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        params=alg_param,
    )
