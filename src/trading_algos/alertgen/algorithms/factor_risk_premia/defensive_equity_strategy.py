from __future__ import annotations

from trading_algos.alertgen.algorithms.factor_risk_premia.base import (
    build_factor_portfolio_algorithm,
)


def build_defensive_equity_strategy(symbol, report_base_path, alg_param, **_kwargs):
    del report_base_path
    algorithm = build_factor_portfolio_algorithm(
        algorithm_key="defensive_equity_strategy",
        symbol=symbol,
        alg_name="defensive_equity_strategy",
        subcategory="defensive",
        alg_param=alg_param,
        factor_name="defensive_equity",
        field_names=tuple(alg_param["field_names"]),
        higher_is_better=True,
        field_weights=alg_param.get("field_weights"),
        lower_is_better_fields=alg_param.get("lower_is_better_fields", ()),
    )
    algorithm.catalog_ref = "algorithm:104"
    return algorithm
