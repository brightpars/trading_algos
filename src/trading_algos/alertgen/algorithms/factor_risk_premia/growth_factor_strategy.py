from __future__ import annotations

from trading_algos.alertgen.algorithms.factor_risk_premia.base import (
    build_factor_portfolio_algorithm,
)


def build_growth_factor_strategy(symbol, report_base_path, alg_param, **_kwargs):
    del report_base_path
    algorithm = build_factor_portfolio_algorithm(
        algorithm_key="growth_factor_strategy",
        symbol=symbol,
        alg_name="growth_factor_strategy",
        subcategory="growth",
        alg_param=alg_param,
        factor_name="growth",
        field_names=tuple(alg_param["field_names"]),
        higher_is_better=True,
    )
    algorithm.catalog_ref = "algorithm:108"
    return algorithm
