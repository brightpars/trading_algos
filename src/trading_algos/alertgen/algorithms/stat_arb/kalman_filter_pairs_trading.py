from __future__ import annotations

from typing import Any

from trading_algos.alertgen.algorithms.stat_arb.relative_value_batch_helpers import (
    RelativeValueAlgorithmDefinition,
    build_kalman_relative_value_algorithm,
)


class KalmanFilterPairsTradingAlertAlgorithm:
    catalog_ref = "algorithm:41"


def build_kalman_filter_pairs_trading_algorithm(
    *,
    algorithm_key: str,
    symbol: str,
    alg_param: dict[str, Any],
    report_base_path: str | None = None,
    sensor_config: dict[str, Any] | None = None,
):
    _ = report_base_path, sensor_config
    return build_kalman_relative_value_algorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        alg_param=alg_param,
        definition=RelativeValueAlgorithmDefinition(
            alg_name="kalman_filter_pairs_trading",
            family="stat_arb",
            subcategory="kalman",
            catalog_ref="algorithm:41",
            entry_reason="kalman_entry",
            hold_reason="kalman_hold",
            exit_reason="kalman_exit",
            idle_reason="no_entry",
        ),
    )
