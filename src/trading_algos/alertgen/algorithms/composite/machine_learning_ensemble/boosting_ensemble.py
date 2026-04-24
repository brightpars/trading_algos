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


class BoostingEnsembleAlertAlgorithm(BaseMachineLearningEnsembleAlertAlgorithm):
    catalog_ref = "combination:9"

    def __init__(
        self, *, algorithm_key: str, symbol: str, params: dict[str, Any]
    ) -> None:
        super().__init__(
            algorithm_key=algorithm_key,
            symbol=symbol,
            rows=build_prediction_rows(list(params["rows"])),
            params=params,
            subcategory="boosting",
        )

    def evaluate_row(self, row) -> EnsembleAggregateDecision:
        stage_weights = extract_numeric_mapping(
            self.params.get("stage_weights"),
            label=f"{self.algorithm_key} stage_weights",
        )
        score, confidence, weighted_children = compute_weighted_child_score(
            row,
            child_weights=stage_weights or None,
            confidence_power=float(self.params.get("confidence_power", 1.5)),
        )
        learning_rate = float(self.params.get("learning_rate", 1.0))
        score = max(-1.0, min(1.0, score * learning_rate))
        direction, decision_reason = resolve_direction(
            score=score,
            buy_threshold=float(self.params["buy_threshold"]),
            sell_threshold=float(self.params["sell_threshold"]),
        )
        diagnostics = {
            "aggregation_method": "boosting_weighted_stage_average",
            "decision_reason": decision_reason,
            "learning_rate": learning_rate,
            "weighted_children": weighted_children,
            "raw_ensemble_score": score,
        }
        return EnsembleAggregateDecision(
            score=score,
            confidence=confidence,
            direction=direction,
            diagnostics=diagnostics,
        )


def build_boosting_ensemble_algorithm(
    *, algorithm_key: str, symbol: str, alg_param: dict[str, Any], **_kwargs: Any
) -> BoostingEnsembleAlertAlgorithm:
    return BoostingEnsembleAlertAlgorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        params=alg_param,
    )
