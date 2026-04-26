from __future__ import annotations

from trading_algos.alertgen.algorithms.fundamental_ml_composite.model_helpers import (
    build_fundamental_model_algorithm,
)


def build_ensemble_voting_strategy(symbol, report_base_path, alg_param, **_kwargs):
    del report_base_path
    return build_fundamental_model_algorithm(
        algorithm_key="ensemble_voting_strategy",
        symbol=symbol,
        alg_name="ensemble_voting_strategy",
        subcategory="ensemble",
        alg_param=alg_param,
        factor_name="ensemble_voting",
        field_names=tuple(alg_param["field_names"]),
        higher_is_better=True,
        catalog_ref="algorithm:93",
        field_weights=alg_param.get("field_weights"),
        threshold=float(alg_param.get("vote_threshold", 0.5)),
        extra_diagnostics={"signal_source": "ensemble_members"},
    )
