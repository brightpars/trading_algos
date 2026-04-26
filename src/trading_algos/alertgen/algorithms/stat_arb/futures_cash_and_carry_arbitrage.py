from __future__ import annotations

from typing import Any

from trading_algos.alertgen.algorithms.stat_arb.relative_value_batch_helpers import (
    RelativeValueAlgorithmDefinition,
    build_curve_relative_value_algorithm,
)


def build_futures_cash_and_carry_arbitrage_algorithm(
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
            alg_name="futures_cash_and_carry_arbitrage",
            family="stat_arb",
            subcategory="futures",
            catalog_ref="algorithm:47",
            entry_reason="cash_carry_entry",
            hold_reason="cash_carry_hold",
            exit_reason="cash_carry_exit",
            idle_reason="carry_below_threshold",
        ),
    )
