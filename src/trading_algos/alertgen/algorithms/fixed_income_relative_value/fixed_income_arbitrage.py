from __future__ import annotations

from typing import Any

from trading_algos.alertgen.algorithms.stat_arb.relative_value_batch_helpers import (
    RelativeValueAlgorithmDefinition,
    build_curve_relative_value_algorithm,
)


def build_fixed_income_arbitrage_algorithm(
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
            alg_name="fixed_income_arbitrage",
            family="fixed_income_relative_value",
            subcategory="fixed",
            catalog_ref="algorithm:115",
            entry_reason="fixed_income_arb_entry",
            hold_reason="fixed_income_arb_hold",
            exit_reason="fixed_income_arb_exit",
            idle_reason="no_entry",
        ),
    )
