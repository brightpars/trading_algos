from __future__ import annotations

from typing import Any

from trading_algos.alertgen.algorithms.stat_arb.base import BaseStatArbAlertAlgorithm
from trading_algos.alertgen.algorithms.stat_arb.helpers import (
    StatArbRow,
    build_pair_legs,
    evaluate_spread_state,
    pair_snapshot,
    required_history,
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
    warmup_period = required_history(
        lookback_window=lookback_window,
        minimum_history=minimum_history,
    )
    schedule = select_rebalance_timestamps(
        panel.timestamps(), frequency=str(alg_param["rebalance_frequency"])
    )
    rows: list[StatArbRow] = []
    is_active = False
    for timestamp in schedule:
        base_history = panel.rows_for_symbol_until(base_symbol, timestamp=timestamp)
        quote_history = panel.rows_for_symbol_until(quote_symbol, timestamp=timestamp)
        if min(len(base_history), len(quote_history)) < warmup_period:
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
                        "warmup_period": warmup_period,
                    },
                )
            )
            continue
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
                        "warmup_period": warmup_period,
                    },
                )
            )
            continue
        zscore = snapshot.zscore
        decision = evaluate_spread_state(
            zscore=zscore,
            entry_zscore=entry_zscore,
            exit_zscore=exit_zscore,
            was_active=is_active,
            entry_reason="entry_signal",
            hold_reason="holding_convergence",
            exit_reason="exit_signal",
            idle_reason="no_entry",
        )
        is_active = decision.is_active
        reason = decision.reason
        legs: tuple[MultiLegPosition, ...] = ()
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
                    "warmup_period": warmup_period,
                    "entry_zscore": entry_zscore,
                    "exit_zscore": exit_zscore,
                    "mean_spread": snapshot.mean_spread,
                    "spread_volatility": snapshot.spread_volatility,
                    "zscore": zscore,
                    "hedge_ratio": snapshot.hedge_ratio,
                    "spread_direction": "positive"
                    if snapshot.spread_value >= 0.0
                    else "negative",
                    "active_legs": len(legs),
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
