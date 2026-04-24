from __future__ import annotations

from typing import Any

from trading_algos.alertgen.algorithms.stat_arb.relative_value_batch_helpers import (
    RelativeValueAlgorithmDefinition,
    build_basket_relative_value_algorithm,
)


def build_index_arbitrage_algorithm(
    *,
    algorithm_key: str,
    symbol: str,
    alg_param: dict[str, Any],
    report_base_path: str | None = None,
    sensor_config: dict[str, Any] | None = None,
):
    _ = report_base_path, sensor_config
    return build_basket_relative_value_algorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        alg_param=alg_param,
        definition=RelativeValueAlgorithmDefinition(
            alg_name="index_arbitrage",
            family="stat_arb",
            subcategory="index",
            catalog_ref="algorithm:42",
            entry_reason="index_arb_entry",
            hold_reason="index_arb_hold",
            exit_reason="index_arb_exit",
            idle_reason="no_entry",
        ),
    )
