from __future__ import annotations

from trading_algos.alertgen.algorithms.factor_risk_premia.base import (
    build_factor_portfolio_algorithm,
)


def build_quality_strategy(symbol, report_base_path, alg_param, **_kwargs):
    del report_base_path
    algorithm = build_factor_portfolio_algorithm(
        algorithm_key="quality_strategy",
        symbol=symbol,
        alg_name="quality_strategy",
        subcategory="quality",
        family="fundamental_ml_composite",
        alg_param=alg_param,
        factor_name="quality",
        field_names=tuple(alg_param["field_names"]),
        higher_is_better=True,
    )
    algorithm.catalog_ref = "algorithm:87"
    return algorithm
