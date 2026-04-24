from __future__ import annotations

from typing import Any

from trading_algos.alertgen.algorithms.stat_arb.base import BaseStatArbAlertAlgorithm
from trading_algos.alertgen.algorithms.stat_arb.helpers import (
    StatArbRow,
    basket_snapshot,
)
from trading_algos.contracts.multi_leg_output import MultiLegPosition
from trading_algos.data.panel_dataset import MultiAssetPanel
from trading_algos.rebalance.calendar import select_rebalance_timestamps


class BasketStatisticalArbitrageAlertAlgorithm(BaseStatArbAlertAlgorithm):
    catalog_ref = "algorithm:40"


def build_basket_statistical_arbitrage_algorithm(
    *,
    algorithm_key: str,
    symbol: str,
    alg_param: dict[str, Any],
    report_base_path: str | None = None,
    sensor_config: dict[str, Any] | None = None,
) -> BasketStatisticalArbitrageAlertAlgorithm:
    _ = report_base_path, sensor_config
    panel = MultiAssetPanel.from_rows(list(alg_param["rows"]))
    base_symbol = str(alg_param["base_symbol"])
    basket_symbols = list(alg_param["basket_symbols"])
    basket_weights = alg_param.get("basket_weights")
    lookback_window = int(alg_param["lookback_window"])
    entry_zscore = float(alg_param["entry_zscore"])
    exit_zscore = float(alg_param["exit_zscore"])
    minimum_history = int(alg_param["minimum_history"])
    schedule = select_rebalance_timestamps(
        panel.timestamps(), frequency=str(alg_param["rebalance_frequency"])
    )
    rows: list[StatArbRow] = []
    is_active = False
    normalized_weights = None
    if basket_weights is not None:
        weight_sum = sum(float(weight) for weight in basket_weights)
        normalized_weights = [float(weight) / weight_sum for weight in basket_weights]
    for timestamp in schedule:
        snapshot = basket_snapshot(
            panel,
            timestamp=timestamp,
            base_symbol=base_symbol,
            basket_symbols=basket_symbols,
            basket_weights=normalized_weights,
            lookback_window=lookback_window,
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
            reason = "basket_entry"
        elif is_active and zscore is not None and abs(zscore) > exit_zscore:
            reason = "basket_hold"
        elif is_active:
            is_active = False
            reason = "basket_exit"
        if is_active:
            base_side = "short" if snapshot.spread_value >= 0.0 else "long"
            hedge_side = "long" if base_side == "short" else "short"
            basket_leg_weights = normalized_weights or [
                1.0 / len(basket_symbols)
            ] * len(basket_symbols)
            legs = (
                MultiLegPosition(symbol=base_symbol, side=base_side, weight=1.0),
                *tuple(
                    MultiLegPosition(
                        symbol=basket_symbol,
                        side=hedge_side,
                        weight=basket_leg_weight,
                        quantity_scale=basket_leg_weight,
                    )
                    for basket_symbol, basket_leg_weight in zip(
                        basket_symbols, basket_leg_weights, strict=True
                    )
                ),
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
                    "basket_symbols": tuple(basket_symbols),
                    "basket_weights": tuple(normalized_weights or []),
                    "minimum_history": minimum_history,
                    "entry_zscore": entry_zscore,
                    "exit_zscore": exit_zscore,
                    "mean_spread": snapshot.mean_spread,
                    "spread_volatility": snapshot.spread_volatility,
                    "zscore": zscore,
                    "hedge_ratio": snapshot.hedge_ratio,
                    "selected_symbol": f"{base_symbol}/basket",
                },
            )
        )
    return BasketStatisticalArbitrageAlertAlgorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        alg_name="basket_statistical_arbitrage",
        family="stat_arb",
        subcategory="basket",
        rows=rows,
    )
