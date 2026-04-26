from __future__ import annotations

from trading_algos.alertgen.algorithms.fundamental_ml_composite.model_helpers import (
    build_fundamental_model_algorithm,
)


def build_machine_learning_regressor(symbol, report_base_path, alg_param, **_kwargs):
    del report_base_path
    return build_fundamental_model_algorithm(
        algorithm_key="machine_learning_regressor",
        symbol=symbol,
        alg_name="machine_learning_regressor",
        subcategory="machine",
        alg_param=alg_param,
        factor_name="machine_learning_regressor",
        field_names=tuple(alg_param["field_names"]),
        higher_is_better=True,
        catalog_ref="algorithm:91",
        field_weights=alg_param.get("field_weights"),
        threshold=float(alg_param.get("return_threshold", 0.0)),
        extra_diagnostics={"signal_source": "feature_regressor"},
    )
