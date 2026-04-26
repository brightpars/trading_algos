from __future__ import annotations

from trading_algos.alertgen.algorithms.factor_risk_premia.base import (
    build_factor_portfolio_algorithm,
)


def build_liquidity_factor_strategy(symbol, report_base_path, alg_param, **_kwargs):
    del report_base_path
    algorithm = build_factor_portfolio_algorithm(
        algorithm_key="liquidity_factor_strategy",
        symbol=symbol,
        alg_name="liquidity_factor_strategy",
        subcategory="liquidity",
        alg_param=alg_param,
        factor_name="liquidity",
        field_names=tuple(alg_param["field_names"]),
        higher_is_better=True,
    )
    algorithm.catalog_ref = "algorithm:109"
    return algorithm
