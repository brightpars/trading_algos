from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from trading_algos.alertgen.algorithms.stat_arb.base import BaseStatArbAlertAlgorithm
from trading_algos.alertgen.algorithms.stat_arb.helpers import (
    StatArbRow,
    basket_snapshot,
    build_basket_legs,
    build_pair_legs,
    build_triangular_legs,
    curve_snapshot,
    evaluate_spread_state,
    kalman_pair_snapshot,
    pair_snapshot,
    required_history,
    triangular_snapshot,
)
from trading_algos.contracts.multi_leg_output import MultiLegPosition
from trading_algos.data.panel_dataset import MultiAssetPanel
from trading_algos.rebalance.calendar import select_rebalance_timestamps


@dataclass(frozen=True)
class RelativeValueAlgorithmDefinition:
    alg_name: str
    family: str
    subcategory: str
    catalog_ref: str
    entry_reason: str
    hold_reason: str
    exit_reason: str
    idle_reason: str


def _warmup_row(
    *, timestamp: str, minimum_history: int, warmup_period: int
) -> StatArbRow:
    return StatArbRow(
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
            "active_legs": 0,
        },
    )


def _append_pair_like_row(
    *,
    rows: list[StatArbRow],
    timestamp: str,
    definition: RelativeValueAlgorithmDefinition,
    snapshot: Any,
    is_active: bool,
    base_symbol: str,
    quote_symbol: str,
    minimum_history: int,
    warmup_period: int,
    entry_zscore: float,
    exit_zscore: float,
    extra_diagnostics: dict[str, object] | None = None,
) -> bool:
    zscore = snapshot.zscore
    decision = evaluate_spread_state(
        zscore=zscore,
        entry_zscore=entry_zscore,
        exit_zscore=exit_zscore,
        was_active=is_active,
        entry_reason=definition.entry_reason,
        hold_reason=definition.hold_reason,
        exit_reason=definition.exit_reason,
        idle_reason=definition.idle_reason,
    )
    is_active = decision.is_active
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
                "selection_reason": decision.reason,
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
                "carry_adjustment": snapshot.carry_adjustment,
                "spread_direction": "positive"
                if snapshot.spread_value >= 0.0
                else "negative",
                "active_legs": len(legs),
                "selected_symbol": f"{base_symbol}/{quote_symbol}",
                **(extra_diagnostics or {}),
            },
        )
    )
    return is_active


def build_pair_relative_value_algorithm(
    *,
    algorithm_key: str,
    symbol: str,
    alg_param: dict[str, Any],
    definition: RelativeValueAlgorithmDefinition,
    snapshot_builder: Callable[[MultiAssetPanel, str], Any | None],
) -> BaseStatArbAlertAlgorithm:
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
                _warmup_row(
                    timestamp=timestamp,
                    minimum_history=minimum_history,
                    warmup_period=warmup_period,
                )
            )
            continue
        snapshot = snapshot_builder(panel, timestamp)
        if snapshot is None:
            rows.append(
                _warmup_row(
                    timestamp=timestamp,
                    minimum_history=minimum_history,
                    warmup_period=warmup_period,
                )
            )
            continue
        is_active = _append_pair_like_row(
            rows=rows,
            timestamp=timestamp,
            definition=definition,
            snapshot=snapshot,
            is_active=is_active,
            base_symbol=base_symbol,
            quote_symbol=quote_symbol,
            minimum_history=minimum_history,
            warmup_period=warmup_period,
            entry_zscore=entry_zscore,
            exit_zscore=exit_zscore,
        )
    algorithm = BaseStatArbAlertAlgorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        alg_name=definition.alg_name,
        family=definition.family,
        subcategory=definition.subcategory,
        rows=rows,
    )
    algorithm.catalog_ref = definition.catalog_ref
    return algorithm


def build_basket_relative_value_algorithm(
    *,
    algorithm_key: str,
    symbol: str,
    alg_param: dict[str, Any],
    definition: RelativeValueAlgorithmDefinition,
) -> BaseStatArbAlertAlgorithm:
    panel = MultiAssetPanel.from_rows(list(alg_param["rows"]))
    base_symbol = str(alg_param["base_symbol"])
    basket_symbols = list(alg_param["basket_symbols"])
    basket_weights = alg_param.get("basket_weights")
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
    normalized_weights = None
    if basket_weights is not None:
        weight_sum = sum(float(weight) for weight in basket_weights)
        normalized_weights = [float(weight) / weight_sum for weight in basket_weights]
    rows: list[StatArbRow] = []
    is_active = False
    for timestamp in schedule:
        history_lengths = [
            len(panel.rows_for_symbol_until(asset, timestamp=timestamp))
            for asset in [base_symbol, *basket_symbols]
        ]
        if min(history_lengths) < warmup_period:
            rows.append(
                _warmup_row(
                    timestamp=timestamp,
                    minimum_history=minimum_history,
                    warmup_period=warmup_period,
                )
            )
            continue
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
                _warmup_row(
                    timestamp=timestamp,
                    minimum_history=minimum_history,
                    warmup_period=warmup_period,
                )
            )
            continue
        decision = evaluate_spread_state(
            zscore=snapshot.zscore,
            entry_zscore=entry_zscore,
            exit_zscore=exit_zscore,
            was_active=is_active,
            entry_reason=definition.entry_reason,
            hold_reason=definition.hold_reason,
            exit_reason=definition.exit_reason,
            idle_reason=definition.idle_reason,
        )
        is_active = decision.is_active
        legs: tuple[MultiLegPosition, ...] = ()
        basket_leg_weights = normalized_weights or [1.0 / len(basket_symbols)] * len(
            basket_symbols
        )
        if is_active:
            legs = build_basket_legs(
                base_symbol=base_symbol,
                basket_symbols=basket_symbols,
                basket_weights=basket_leg_weights,
                spread_value=snapshot.spread_value,
            )
        rows.append(
            StatArbRow(
                timestamp=timestamp,
                spread_value=snapshot.spread_value,
                zscore=snapshot.zscore,
                hedge_ratio=snapshot.hedge_ratio,
                legs=legs,
                diagnostics={
                    "selection_reason": decision.reason,
                    "warmup_ready": True,
                    "base_symbol": base_symbol,
                    "basket_symbols": tuple(basket_symbols),
                    "basket_weights": tuple(basket_leg_weights),
                    "minimum_history": minimum_history,
                    "warmup_period": warmup_period,
                    "entry_zscore": entry_zscore,
                    "exit_zscore": exit_zscore,
                    "mean_spread": snapshot.mean_spread,
                    "spread_volatility": snapshot.spread_volatility,
                    "zscore": snapshot.zscore,
                    "hedge_ratio": snapshot.hedge_ratio,
                    "carry_adjustment": snapshot.carry_adjustment,
                    "spread_direction": "positive"
                    if snapshot.spread_value >= 0.0
                    else "negative",
                    "active_legs": len(legs),
                    "selected_symbol": f"{base_symbol}/basket",
                },
            )
        )
    algorithm = BaseStatArbAlertAlgorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        alg_name=definition.alg_name,
        family=definition.family,
        subcategory=definition.subcategory,
        rows=rows,
    )
    algorithm.catalog_ref = definition.catalog_ref
    return algorithm


def build_triangular_relative_value_algorithm(
    *,
    algorithm_key: str,
    symbol: str,
    alg_param: dict[str, Any],
    definition: RelativeValueAlgorithmDefinition,
) -> BaseStatArbAlertAlgorithm:
    panel = MultiAssetPanel.from_rows(list(alg_param["rows"]))
    base_symbol = str(alg_param["base_symbol"])
    cross_symbol = str(alg_param["cross_symbol"])
    implied_symbol = str(alg_param["implied_symbol"])
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
        history_lengths = [
            len(panel.rows_for_symbol_until(asset, timestamp=timestamp))
            for asset in (base_symbol, cross_symbol, implied_symbol)
        ]
        if min(history_lengths) < warmup_period:
            rows.append(
                _warmup_row(
                    timestamp=timestamp,
                    minimum_history=minimum_history,
                    warmup_period=warmup_period,
                )
            )
            continue
        snapshot = triangular_snapshot(
            panel,
            timestamp=timestamp,
            base_symbol=base_symbol,
            cross_symbol=cross_symbol,
            implied_symbol=implied_symbol,
            lookback_window=lookback_window,
        )
        if snapshot is None:
            rows.append(
                _warmup_row(
                    timestamp=timestamp,
                    minimum_history=minimum_history,
                    warmup_period=warmup_period,
                )
            )
            continue
        decision = evaluate_spread_state(
            zscore=snapshot.zscore,
            entry_zscore=entry_zscore,
            exit_zscore=exit_zscore,
            was_active=is_active,
            entry_reason=definition.entry_reason,
            hold_reason=definition.hold_reason,
            exit_reason=definition.exit_reason,
            idle_reason=definition.idle_reason,
        )
        is_active = decision.is_active
        legs: tuple[MultiLegPosition, ...] = ()
        if is_active:
            legs = build_triangular_legs(
                base_symbol=base_symbol,
                cross_symbol=cross_symbol,
                implied_symbol=implied_symbol,
                spread_value=snapshot.spread_value,
            )
        rows.append(
            StatArbRow(
                timestamp=timestamp,
                spread_value=snapshot.spread_value,
                zscore=snapshot.zscore,
                hedge_ratio=snapshot.hedge_ratio,
                legs=legs,
                diagnostics={
                    "selection_reason": decision.reason,
                    "warmup_ready": True,
                    "base_symbol": base_symbol,
                    "cross_symbol": cross_symbol,
                    "implied_symbol": implied_symbol,
                    "minimum_history": minimum_history,
                    "warmup_period": warmup_period,
                    "entry_zscore": entry_zscore,
                    "exit_zscore": exit_zscore,
                    "mean_spread": snapshot.mean_spread,
                    "spread_volatility": snapshot.spread_volatility,
                    "zscore": snapshot.zscore,
                    "hedge_ratio": snapshot.hedge_ratio,
                    "carry_adjustment": snapshot.carry_adjustment,
                    "spread_direction": "positive"
                    if snapshot.spread_value >= 0.0
                    else "negative",
                    "active_legs": len(legs),
                    "selected_symbol": f"{base_symbol}/{cross_symbol}/{implied_symbol}",
                },
            )
        )
    algorithm = BaseStatArbAlertAlgorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        alg_name=definition.alg_name,
        family=definition.family,
        subcategory=definition.subcategory,
        rows=rows,
    )
    algorithm.catalog_ref = definition.catalog_ref
    return algorithm


def build_kalman_relative_value_algorithm(
    *,
    algorithm_key: str,
    symbol: str,
    alg_param: dict[str, Any],
    definition: RelativeValueAlgorithmDefinition,
) -> BaseStatArbAlertAlgorithm:
    process_variance = float(alg_param["process_variance"])
    observation_variance = float(alg_param["observation_variance"])
    return build_pair_relative_value_algorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        alg_param=alg_param,
        definition=definition,
        snapshot_builder=lambda panel, timestamp: kalman_pair_snapshot(
            panel,
            timestamp=timestamp,
            base_symbol=str(alg_param["base_symbol"]),
            quote_symbol=str(alg_param["quote_symbol"]),
            lookback_window=int(alg_param["lookback_window"]),
            process_variance=process_variance,
            observation_variance=observation_variance,
        ),
    )


def build_curve_relative_value_algorithm(
    *,
    algorithm_key: str,
    symbol: str,
    alg_param: dict[str, Any],
    definition: RelativeValueAlgorithmDefinition,
) -> BaseStatArbAlertAlgorithm:
    return build_pair_relative_value_algorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        alg_param=alg_param,
        definition=definition,
        snapshot_builder=lambda panel, timestamp: curve_snapshot(
            panel,
            timestamp=timestamp,
            long_symbol=str(alg_param["base_symbol"]),
            short_symbol=str(alg_param["quote_symbol"]),
            lookback_window=int(alg_param["lookback_window"]),
            hedge_ratio_method=str(alg_param.get("hedge_ratio_method", "ratio")),
            carry_field=alg_param.get("carry_field"),
            carry_weight=float(alg_param.get("carry_weight", 1.0)),
        ),
    )


def build_simple_pair_relative_value_algorithm(
    *,
    algorithm_key: str,
    symbol: str,
    alg_param: dict[str, Any],
    definition: RelativeValueAlgorithmDefinition,
) -> BaseStatArbAlertAlgorithm:
    return build_pair_relative_value_algorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        alg_param=alg_param,
        definition=definition,
        snapshot_builder=lambda panel, timestamp: pair_snapshot(
            panel,
            timestamp=timestamp,
            base_symbol=str(alg_param["base_symbol"]),
            quote_symbol=str(alg_param["quote_symbol"]),
            lookback_window=int(alg_param["lookback_window"]),
            hedge_ratio_method=str(alg_param.get("hedge_ratio_method", "ratio")),
        ),
    )
