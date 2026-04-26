from __future__ import annotations

from typing import Any

from trading_algos.alertgen.algorithms.stat_arb.relative_value_batch_helpers import (
    RelativeValueAlgorithmDefinition,
    build_triangular_relative_value_algorithm,
)


def build_triangular_arbitrage_fx_crypto_algorithm(
    *,
    algorithm_key: str,
    symbol: str,
    alg_param: dict[str, Any],
    report_base_path: str | None = None,
    sensor_config: dict[str, Any] | None = None,
):
    _ = report_base_path, sensor_config
    return build_triangular_relative_value_algorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        alg_param=alg_param,
        definition=RelativeValueAlgorithmDefinition(
            alg_name="triangular_arbitrage_fx_crypto",
            family="stat_arb",
            subcategory="triangular",
            catalog_ref="algorithm:49",
            entry_reason="triangular_arb_entry",
            hold_reason="triangular_arb_hold",
            exit_reason="triangular_arb_exit",
            idle_reason="no_entry",
        ),
    )
