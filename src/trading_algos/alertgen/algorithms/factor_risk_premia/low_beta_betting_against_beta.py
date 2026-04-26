from __future__ import annotations

from trading_algos.alertgen.algorithms.factor_risk_premia.base import (
    build_factor_portfolio_algorithm,
)


def build_low_beta_betting_against_beta(symbol, report_base_path, alg_param, **_kwargs):
    del report_base_path
    algorithm = build_factor_portfolio_algorithm(
        algorithm_key="low_beta_betting_against_beta",
        symbol=symbol,
        alg_name="low_beta_betting_against_beta",
        subcategory="low",
        alg_param=alg_param,
        factor_name="low_beta",
        field_names=tuple(alg_param["field_names"]),
        higher_is_better=False,
    )
    algorithm.catalog_ref = "algorithm:103"
    return algorithm
