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


class StackingMetaLearningAlertAlgorithm(BaseMachineLearningEnsembleAlertAlgorithm):
    catalog_ref = "combination:10"

    def __init__(
        self, *, algorithm_key: str, symbol: str, params: dict[str, Any]
    ) -> None:
        super().__init__(
            algorithm_key=algorithm_key,
            symbol=symbol,
            rows=build_prediction_rows(list(params["rows"])),
            params=params,
            subcategory="stacking",
        )

    def evaluate_row(self, row) -> EnsembleAggregateDecision:
        meta_feature_weights = extract_numeric_mapping(
            row.metadata.get("meta_features"),
            label=f"{self.algorithm_key} meta_features",
        )
        child_meta_weights = extract_numeric_mapping(
            self.params.get("meta_model_weights"),
            label=f"{self.algorithm_key} meta_model_weights",
        )
        score, confidence, weighted_children = compute_weighted_child_score(
            row,
            child_weights=child_meta_weights or None,
            confidence_power=float(self.params.get("confidence_power", 1.0)),
        )
        intercept = float(self.params.get("meta_bias", 0.0))
        feature_adjustment = sum(meta_feature_weights.values()) * float(
            self.params.get("meta_feature_scale", 0.0)
        )
        score = max(-1.0, min(1.0, score + intercept + feature_adjustment))
        direction, decision_reason = resolve_direction(
            score=score,
            buy_threshold=float(self.params["buy_threshold"]),
            sell_threshold=float(self.params["sell_threshold"]),
        )
        diagnostics = {
            "aggregation_method": "stacking_meta_model",
            "decision_reason": decision_reason,
            "meta_bias": intercept,
            "meta_feature_scale": float(self.params.get("meta_feature_scale", 0.0)),
            "meta_feature_values": meta_feature_weights,
            "weighted_children": weighted_children,
            "raw_ensemble_score": score,
        }
        return EnsembleAggregateDecision(
            score=score,
            confidence=confidence,
            direction=direction,
            diagnostics=diagnostics,
        )


def build_stacking_meta_learning_algorithm(
    *, algorithm_key: str, symbol: str, alg_param: dict[str, Any], **_kwargs: Any
) -> StackingMetaLearningAlertAlgorithm:
    return StackingMetaLearningAlertAlgorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        params=alg_param,
    )
