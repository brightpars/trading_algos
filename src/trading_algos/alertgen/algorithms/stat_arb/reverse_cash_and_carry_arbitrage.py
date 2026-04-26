from __future__ import annotations

from typing import Any

from trading_algos.alertgen.algorithms.stat_arb.relative_value_batch_helpers import (
    RelativeValueAlgorithmDefinition,
    build_curve_relative_value_algorithm,
)


def build_reverse_cash_and_carry_arbitrage_algorithm(
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
            alg_name="reverse_cash_and_carry_arbitrage",
            family="stat_arb",
            subcategory="reverse",
            catalog_ref="algorithm:48",
            entry_reason="reverse_carry_entry",
            hold_reason="reverse_carry_hold",
            exit_reason="reverse_carry_exit",
            idle_reason="carry_below_threshold",
        ),
    )
