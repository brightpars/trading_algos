from __future__ import annotations

from trading_algos.alertgen.algorithms.fundamental_ml_composite.model_helpers import (
    build_fundamental_model_algorithm,
)


def build_regime_switching_strategy(symbol, report_base_path, alg_param, **_kwargs):
    del report_base_path
    return build_fundamental_model_algorithm(
        algorithm_key="regime_switching_strategy",
        symbol=symbol,
        alg_name="regime_switching_strategy",
        subcategory="regime",
        alg_param=alg_param,
        factor_name="regime_switching",
        field_names=tuple(alg_param["field_names"]),
        higher_is_better=True,
        catalog_ref="algorithm:92",
        field_weights=alg_param.get("field_weights"),
        threshold=float(alg_param.get("regime_threshold", 0.0)),
        extra_diagnostics={"signal_source": "regime_features"},
    )
