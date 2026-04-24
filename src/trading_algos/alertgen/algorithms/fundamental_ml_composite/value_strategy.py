from __future__ import annotations

from trading_algos.alertgen.algorithms.factor_risk_premia.base import (
    build_factor_portfolio_algorithm,
)


def build_value_strategy(symbol, report_base_path, alg_param, **_kwargs):
    del report_base_path
    algorithm = build_factor_portfolio_algorithm(
        algorithm_key="value_strategy",
        symbol=symbol,
        alg_name="value_strategy",
        subcategory="value",
        family="fundamental_ml_composite",
        alg_param=alg_param,
        factor_name="value",
        field_names=tuple(alg_param["field_names"]),
        higher_is_better=False,
    )
    algorithm.catalog_ref = "algorithm:86"
    return algorithm
