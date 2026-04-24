from __future__ import annotations

from typing import Any

from trading_algos.alertgen.algorithms.stat_arb.relative_value_batch_helpers import (
    RelativeValueAlgorithmDefinition,
    build_curve_relative_value_algorithm,
)


def build_swap_spread_arbitrage_algorithm(
    *,
    algorithm_key: str,
    symbol: str,
    alg_param: dict[str, Any],
    report_base_path: str | None = None,
    sensor_config: dict[str, Any] | None = None,
):
    _ = report_base_path, sensor_config
    return build_curve_relative_value_algorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        alg_param=alg_param,
        definition=RelativeValueAlgorithmDefinition(
            alg_name="swap_spread_arbitrage",
            family="fixed_income_relative_value",
            subcategory="swap",
            catalog_ref="algorithm:116",
            entry_reason="swap_spread_entry",
            hold_reason="swap_spread_hold",
            exit_reason="swap_spread_exit",
            idle_reason="no_entry",
        ),
    )
