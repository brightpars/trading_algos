from __future__ import annotations

from typing import Any

from trading_algos.alertgen.algorithms.stat_arb.base import BaseStatArbAlertAlgorithm
from trading_algos.alertgen.algorithms.stat_arb.helpers import (
    StatArbRow,
    build_pair_legs,
    pair_snapshot,
)
from trading_algos.contracts.multi_leg_output import MultiLegPosition
from trading_algos.data.panel_dataset import MultiAssetPanel
from trading_algos.rebalance.calendar import select_rebalance_timestamps


class PairsTradingDistanceMethodAlertAlgorithm(BaseStatArbAlertAlgorithm):
    catalog_ref = "algorithm:38"


def build_pairs_trading_distance_method_algorithm(
    *,
    algorithm_key: str,
    symbol: str,
    alg_param: dict[str, Any],
    report_base_path: str | None = None,
    sensor_config: dict[str, Any] | None = None,
) -> PairsTradingDistanceMethodAlertAlgorithm:
    _ = report_base_path, sensor_config
    panel = MultiAssetPanel.from_rows(list(alg_param["rows"]))
    base_symbol = str(alg_param["base_symbol"])
    quote_symbol = str(alg_param["quote_symbol"])
    lookback_window = int(alg_param["lookback_window"])
    entry_zscore = float(alg_param["entry_zscore"])
    exit_zscore = float(alg_param["exit_zscore"])
    minimum_history = int(alg_param["minimum_history"])
    schedule = select_rebalance_timestamps(
        panel.timestamps(), frequency=str(alg_param["rebalance_frequency"])
    )
    rows: list[StatArbRow] = []
    is_active = False
    for timestamp in schedule:
        snapshot = pair_snapshot(
            panel,
            timestamp=timestamp,
            base_symbol=base_symbol,
            quote_symbol=quote_symbol,
            lookback_window=lookback_window,
            hedge_ratio_method=str(alg_param["hedge_ratio_method"]),
        )
        if snapshot is None:
            rows.append(
                StatArbRow(
                    timestamp=timestamp,
                    spread_value=0.0,
                    zscore=None,
                    hedge_ratio=1.0,
                    legs=(),
                    diagnostics={
                        "selection_reason": "warmup_pending",
                        "warmup_ready": False,
                        "minimum_history": minimum_history,
                    },
                )
            )
            continue
        zscore = snapshot.zscore
        reason = "no_entry"
        legs: tuple[MultiLegPosition, ...] = ()
        if zscore is not None and abs(zscore) >= entry_zscore:
            is_active = True
            reason = "entry_signal"
        elif is_active and zscore is not None and abs(zscore) > exit_zscore:
            reason = "holding_convergence"
        elif is_active:
            is_active = False
            reason = "exit_signal"
        if is_active:
            legs = build_pair_legs(
                base_symbol=base_symbol,
                quote_symbol=quote_symbol,
                hedge_ratio=snapshot.hedge_ratio,
                spread_value=snapshot.spread_value,
            )
        rows.append(
            StatArbRow(
                timestamp=timestamp,
                spread_value=snapshot.spread_value,
                zscore=zscore,
                hedge_ratio=snapshot.hedge_ratio,
                legs=legs,
                diagnostics={
                    "selection_reason": reason,
                    "warmup_ready": True,
                    "base_symbol": base_symbol,
                    "quote_symbol": quote_symbol,
                    "minimum_history": minimum_history,
                    "entry_zscore": entry_zscore,
                    "exit_zscore": exit_zscore,
                    "mean_spread": snapshot.mean_spread,
                    "spread_volatility": snapshot.spread_volatility,
                    "zscore": zscore,
                    "hedge_ratio": snapshot.hedge_ratio,
                    "selected_symbol": f"{base_symbol}/{quote_symbol}",
                },
            )
        )
    return PairsTradingDistanceMethodAlertAlgorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        alg_name="pairs_trading_distance_method",
        family="stat_arb",
        subcategory="pairs",
        rows=rows,
    )
