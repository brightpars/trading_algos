from __future__ import annotations

from typing import Any, Mapping, Sequence

from trading_algos.alertgen.algorithms.factor_risk_premia.base import (
    FactorPortfolioAlertAlgorithm,
    build_factor_portfolio_algorithm,
)


def _as_float(value: object, *, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        return float(value)
    return default


def _apply_model_diagnostics(
    algorithm: FactorPortfolioAlertAlgorithm,
    *,
    model_type: str,
    threshold: float | None,
    extra_diagnostics: Mapping[str, object],
) -> FactorPortfolioAlertAlgorithm:
    for row in algorithm._rows:
        diagnostics = row.diagnostics
        selection_strength = _as_float(diagnostics.get("selection_strength", 0.0))
        top_ranked_score = _as_float(diagnostics.get("top_ranked_score", 0.0))
        diagnostics.update(dict(extra_diagnostics))
        diagnostics["model_type"] = model_type
        diagnostics["model_score"] = top_ranked_score
        diagnostics["model_confidence"] = selection_strength
        diagnostics["top_selection_strength"] = selection_strength
        if threshold is not None:
            diagnostics["decision_threshold"] = threshold
        if model_type == "machine_learning_classifier":
            effective_threshold = threshold if threshold is not None else 0.5
            diagnostics["predicted_probability"] = top_ranked_score
            diagnostics["threshold_gap"] = top_ranked_score - effective_threshold
            diagnostics["threshold_passed"] = top_ranked_score >= effective_threshold
            diagnostics["predicted_class"] = (
                "positive" if top_ranked_score >= effective_threshold else "negative"
            )
        elif model_type == "machine_learning_regressor":
            effective_threshold = threshold if threshold is not None else 0.0
            diagnostics["predicted_return"] = top_ranked_score
            diagnostics["threshold_gap"] = top_ranked_score - effective_threshold
            diagnostics["threshold_passed"] = top_ranked_score >= effective_threshold
            diagnostics["predicted_direction"] = (
                "positive" if top_ranked_score >= effective_threshold else "negative"
            )
        elif model_type == "regime_switching_strategy":
            effective_threshold = threshold if threshold is not None else 0.0
            diagnostics["regime_score"] = top_ranked_score
            diagnostics["threshold_gap"] = top_ranked_score - effective_threshold
            diagnostics["threshold_passed"] = top_ranked_score >= effective_threshold
            diagnostics["regime_label"] = (
                "risk_on" if top_ranked_score >= effective_threshold else "risk_off"
            )
            diagnostics["active_sleeve"] = diagnostics["regime_label"]
        elif model_type == "ensemble_voting_strategy":
            effective_threshold = threshold if threshold is not None else 0.5
            diagnostics["vote_strength"] = selection_strength
            diagnostics["member_count"] = len(algorithm.field_names)
            diagnostics["threshold_gap"] = selection_strength - effective_threshold
            diagnostics["threshold_passed"] = selection_strength >= effective_threshold
            diagnostics["vote_outcome"] = (
                "accept" if selection_strength >= effective_threshold else "reject"
            )
        elif model_type == "sentiment_strategy":
            effective_threshold = threshold if threshold is not None else 0.0
            diagnostics["sentiment_score"] = top_ranked_score
            diagnostics["threshold_gap"] = top_ranked_score - effective_threshold
            diagnostics["threshold_passed"] = top_ranked_score >= effective_threshold
            diagnostics["sentiment_label"] = (
                "bullish" if top_ranked_score >= effective_threshold else "bearish"
            )
    return algorithm


def build_fundamental_model_algorithm(
    *,
    algorithm_key: str,
    symbol: str,
    alg_name: str,
    subcategory: str,
    alg_param: dict[str, Any],
    factor_name: str,
    field_names: Sequence[str],
    higher_is_better: bool,
    catalog_ref: str,
    weighting_mode: str = "equal_weight",
    field_weights: Sequence[float] | None = None,
    lower_is_better_fields: Sequence[str] = (),
    target_value: float | None = None,
    threshold: float | None = None,
    extra_diagnostics: Mapping[str, object] | None = None,
) -> FactorPortfolioAlertAlgorithm:
    algorithm = build_factor_portfolio_algorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        alg_name=alg_name,
        subcategory=subcategory,
        family="fundamental_ml_composite",
        alg_param=alg_param,
        factor_name=factor_name,
        field_names=field_names,
        higher_is_better=higher_is_better,
        target_value=target_value,
        weighting_mode=weighting_mode,
        field_weights=field_weights,
        lower_is_better_fields=lower_is_better_fields,
    )
    algorithm.catalog_ref = catalog_ref
    return _apply_model_diagnostics(
        algorithm,
        model_type=algorithm_key,
        threshold=threshold,
        extra_diagnostics=extra_diagnostics or {},
    )
