from __future__ import annotations

from trading_algos.alertgen.algorithms.factor_risk_premia.base import (
    build_factor_portfolio_algorithm,
)


def build_earnings_stability_low_earnings_variability(
    symbol, report_base_path, alg_param, **_kwargs
):
    del report_base_path
    algorithm = build_factor_portfolio_algorithm(
        algorithm_key="earnings_stability_low_earnings_variability",
        symbol=symbol,
        alg_name="earnings_stability_low_earnings_variability",
        subcategory="earnings",
        alg_param=alg_param,
        factor_name="earnings_stability",
        field_names=tuple(alg_param["field_names"]),
        higher_is_better=True,
        field_weights=alg_param.get("field_weights"),
    )
    algorithm.catalog_ref = "algorithm:114"
    return algorithm
