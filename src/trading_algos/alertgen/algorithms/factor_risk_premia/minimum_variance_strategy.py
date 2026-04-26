from __future__ import annotations

from trading_algos.alertgen.algorithms.factor_risk_premia.base import (
    build_factor_portfolio_algorithm,
)


def build_minimum_variance_strategy(symbol, report_base_path, alg_param, **_kwargs):
    del report_base_path
    algorithm = build_factor_portfolio_algorithm(
        algorithm_key="minimum_variance_strategy",
        symbol=symbol,
        alg_name="minimum_variance_strategy",
        subcategory="minimum",
        alg_param=alg_param,
        factor_name="minimum_variance",
        field_names=tuple(alg_param["field_names"]),
        higher_is_better=False,
        weighting_mode=str(alg_param.get("weighting_mode", "inverse_metric")),
    )
    algorithm.catalog_ref = "algorithm:101"
    return algorithm
