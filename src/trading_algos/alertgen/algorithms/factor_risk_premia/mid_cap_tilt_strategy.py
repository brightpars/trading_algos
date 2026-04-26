from __future__ import annotations

from trading_algos.alertgen.algorithms.factor_risk_premia.base import (
    build_factor_portfolio_algorithm,
)


def build_mid_cap_tilt_strategy(symbol, report_base_path, alg_param, **_kwargs):
    del report_base_path
    algorithm = build_factor_portfolio_algorithm(
        algorithm_key="mid_cap_tilt_strategy",
        symbol=symbol,
        alg_name="mid_cap_tilt_strategy",
        subcategory="mid",
        alg_param=alg_param,
        factor_name="mid_cap_tilt",
        field_names=tuple(alg_param["field_names"]),
        higher_is_better=False,
        target_value=float(alg_param.get("target_value", 10.0)),
    )
    algorithm.catalog_ref = "algorithm:106"
    return algorithm
