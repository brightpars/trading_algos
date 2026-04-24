from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from trading_algos.contracts.multi_leg_output import MultiLegPosition
from trading_algos.data.panel_dataset import MultiAssetPanel, PanelRow
from trading_algos.relative_value.hedge_ratio import (
    RelativeValueSnapshot,
    kalman_hedge_ratios,
    normalize_spread,
    rolling_zscore,
    spread_series_from_ratios,
    spread_series,
    static_hedge_ratio,
)


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class StatArbRow:
    timestamp: str
    spread_value: float
    zscore: float | None
    hedge_ratio: float
    legs: tuple[MultiLegPosition, ...]
    diagnostics: dict[str, object]


@dataclass(frozen=True)
class StatArbDecision:
    is_active: bool
    reason: str


def required_history(*, lookback_window: int, minimum_history: int) -> int:
    return max(lookback_window, minimum_history)


def evaluate_spread_state(
    *,
    zscore: float | None,
    entry_zscore: float,
    exit_zscore: float,
    was_active: bool,
    entry_reason: str,
    hold_reason: str,
    exit_reason: str,
    idle_reason: str,
) -> StatArbDecision:
    if zscore is not None and abs(zscore) >= entry_zscore:
        return StatArbDecision(is_active=True, reason=entry_reason)
    if was_active and zscore is not None and abs(zscore) > exit_zscore:
        return StatArbDecision(is_active=True, reason=hold_reason)
    if was_active:
        return StatArbDecision(is_active=False, reason=exit_reason)
    return StatArbDecision(is_active=False, reason=idle_reason)


def pair_snapshot(
    panel: MultiAssetPanel,
    *,
    timestamp: str,
    base_symbol: str,
    quote_symbol: str,
    lookback_window: int,
    hedge_ratio_method: str,
) -> RelativeValueSnapshot | None:
    base_rows = panel.rows_for_symbol_until(base_symbol, timestamp=timestamp)
    quote_rows = panel.rows_for_symbol_until(quote_symbol, timestamp=timestamp)
    if len(base_rows) < lookback_window or len(quote_rows) < lookback_window:
        return None
    base_prices = [row.close for row in base_rows[-lookback_window:]]
    quote_prices = [row.close for row in quote_rows[-lookback_window:]]
    hedge_ratio = 1.0
    if hedge_ratio_method in {"ratio", "ols"}:
        hedge_ratio = static_hedge_ratio(base_prices, quote_prices)
    spreads = spread_series(base_prices, quote_prices, hedge_ratio=hedge_ratio)
    zscores = rolling_zscore(spreads, lookback_window)
    mean_spread = sum(spreads) / len(spreads)
    spread_volatility = (
        sum((value - mean_spread) ** 2 for value in spreads) / len(spreads)
    ) ** 0.5
    return RelativeValueSnapshot(
        hedge_ratio=hedge_ratio,
        spread_value=spreads[-1],
        zscore=zscores[-1],
        mean_spread=mean_spread,
        spread_volatility=spread_volatility,
    )


def kalman_pair_snapshot(
    panel: MultiAssetPanel,
    *,
    timestamp: str,
    base_symbol: str,
    quote_symbol: str,
    lookback_window: int,
    process_variance: float,
    observation_variance: float,
) -> RelativeValueSnapshot | None:
    base_rows = panel.rows_for_symbol_until(base_symbol, timestamp=timestamp)
    quote_rows = panel.rows_for_symbol_until(quote_symbol, timestamp=timestamp)
    if len(base_rows) < lookback_window or len(quote_rows) < lookback_window:
        return None
    base_prices = [row.close for row in base_rows[-lookback_window:]]
    quote_prices = [row.close for row in quote_rows[-lookback_window:]]
    hedge_ratios = kalman_hedge_ratios(
        base_prices,
        quote_prices,
        process_variance=process_variance,
        observation_variance=observation_variance,
    )
    spreads = spread_series_from_ratios(
        base_prices,
        quote_prices,
        hedge_ratios=hedge_ratios,
    )
    realized_spreads = [spread for spread in spreads if spread is not None]
    if not realized_spreads:
        return None
    zscores = rolling_zscore(realized_spreads, lookback_window)
    mean_spread = sum(realized_spreads) / len(realized_spreads)
    spread_volatility = (
        sum((value - mean_spread) ** 2 for value in realized_spreads)
        / len(realized_spreads)
    ) ** 0.5
    latest_spread = realized_spreads[-1]
    latest_ratio = hedge_ratios[-1]
    if latest_ratio is None:
        return None
    latest_zscore = zscores[-1]
    if latest_zscore is None:
        latest_zscore = normalize_spread(
            latest_spread,
            mean_spread=mean_spread,
            spread_volatility=spread_volatility,
        )
    return RelativeValueSnapshot(
        hedge_ratio=latest_ratio,
        spread_value=latest_spread,
        zscore=latest_zscore,
        mean_spread=mean_spread,
        spread_volatility=spread_volatility,
    )


def basket_snapshot(
    panel: MultiAssetPanel,
    *,
    timestamp: str,
    base_symbol: str,
    basket_symbols: Sequence[str],
    basket_weights: Sequence[float] | None,
    lookback_window: int,
) -> RelativeValueSnapshot | None:
    base_rows = panel.rows_for_symbol_until(base_symbol, timestamp=timestamp)
    if len(base_rows) < lookback_window:
        return None
    component_rows: list[tuple[str, tuple[PanelRow, ...]]] = []
    for symbol in basket_symbols:
        rows = panel.rows_for_symbol_until(symbol, timestamp=timestamp)
        if len(rows) < lookback_window:
            return None
        component_rows.append((symbol, rows[-lookback_window:]))
    weights = (
        list(basket_weights)
        if basket_weights is not None
        else [1.0] * len(component_rows)
    )
    weight_sum = sum(weights)
    normalized_weights = [weight / weight_sum for weight in weights]
    base_prices = [row.close for row in base_rows[-lookback_window:]]
    basket_prices = [
        sum(
            normalized_weights[index] * component_rows[index][1][offset].close
            for index in range(len(component_rows))
        )
        for offset in range(lookback_window)
    ]
    hedge_ratio = 1.0
    spreads = spread_series(base_prices, basket_prices, hedge_ratio=hedge_ratio)
    zscores = rolling_zscore(spreads, lookback_window)
    mean_spread = sum(spreads) / len(spreads)
    spread_volatility = (
        sum((value - mean_spread) ** 2 for value in spreads) / len(spreads)
    ) ** 0.5
    return RelativeValueSnapshot(
        hedge_ratio=hedge_ratio,
        spread_value=spreads[-1],
        zscore=zscores[-1],
        mean_spread=mean_spread,
        spread_volatility=spread_volatility,
    )


def basis_snapshot(
    panel: MultiAssetPanel,
    *,
    timestamp: str,
    base_symbol: str,
    quote_symbol: str,
    lookback_window: int,
    basis_field: str,
    funding_field: str,
) -> RelativeValueSnapshot | None:
    snapshot = pair_snapshot(
        panel,
        timestamp=timestamp,
        base_symbol=base_symbol,
        quote_symbol=quote_symbol,
        lookback_window=lookback_window,
        hedge_ratio_method="ratio",
    )
    if snapshot is None:
        return None
    latest_rows = panel.latest_row_by_symbol_on(timestamp, (base_symbol, quote_symbol))
    quote_row = latest_rows.get(quote_symbol)
    if quote_row is None:
        return None
    extras = quote_row.extras or {}
    basis_value = _coerce_float(extras.get(basis_field)) or 0.0
    funding_value = _coerce_float(extras.get(funding_field)) or 0.0
    spread_value = snapshot.spread_value + basis_value + funding_value
    return RelativeValueSnapshot(
        hedge_ratio=snapshot.hedge_ratio,
        spread_value=spread_value,
        zscore=snapshot.zscore,
        mean_spread=snapshot.mean_spread,
        spread_volatility=snapshot.spread_volatility,
    )


def curve_snapshot(
    panel: MultiAssetPanel,
    *,
    timestamp: str,
    long_symbol: str,
    short_symbol: str,
    lookback_window: int,
    hedge_ratio_method: str,
    carry_field: str | None = None,
    carry_weight: float = 1.0,
) -> RelativeValueSnapshot | None:
    snapshot = pair_snapshot(
        panel,
        timestamp=timestamp,
        base_symbol=long_symbol,
        quote_symbol=short_symbol,
        lookback_window=lookback_window,
        hedge_ratio_method=hedge_ratio_method,
    )
    if snapshot is None:
        return None
    carry_adjustment = 0.0
    if carry_field is not None:
        latest_rows = panel.latest_row_by_symbol_on(
            timestamp, (long_symbol, short_symbol)
        )
        long_row = latest_rows.get(long_symbol)
        short_row = latest_rows.get(short_symbol)
        long_carry = (
            _coerce_float((long_row.extras or {}).get(carry_field))
            if long_row
            else None
        )
        short_carry = (
            _coerce_float((short_row.extras or {}).get(carry_field))
            if short_row
            else None
        )
        carry_adjustment = ((long_carry or 0.0) - (short_carry or 0.0)) * carry_weight
    return RelativeValueSnapshot(
        hedge_ratio=snapshot.hedge_ratio,
        spread_value=snapshot.spread_value + carry_adjustment,
        zscore=snapshot.zscore,
        mean_spread=snapshot.mean_spread,
        spread_volatility=snapshot.spread_volatility,
    )


def triangular_snapshot(
    panel: MultiAssetPanel,
    *,
    timestamp: str,
    base_symbol: str,
    cross_symbol: str,
    implied_symbol: str,
    lookback_window: int,
) -> RelativeValueSnapshot | None:
    base_rows = panel.rows_for_symbol_until(base_symbol, timestamp=timestamp)
    cross_rows = panel.rows_for_symbol_until(cross_symbol, timestamp=timestamp)
    implied_rows = panel.rows_for_symbol_until(implied_symbol, timestamp=timestamp)
    if min(len(base_rows), len(cross_rows), len(implied_rows)) < lookback_window:
        return None
    base_prices = [row.close for row in base_rows[-lookback_window:]]
    cross_prices = [row.close for row in cross_rows[-lookback_window:]]
    implied_prices = [row.close for row in implied_rows[-lookback_window:]]
    synthetic_prices = [
        left * right for left, right in zip(base_prices, cross_prices, strict=True)
    ]
    spreads = [
        observed - synthetic
        for observed, synthetic in zip(implied_prices, synthetic_prices, strict=True)
    ]
    zscores = rolling_zscore(spreads, lookback_window)
    mean_spread = sum(spreads) / len(spreads)
    spread_volatility = (
        sum((value - mean_spread) ** 2 for value in spreads) / len(spreads)
    ) ** 0.5
    return RelativeValueSnapshot(
        hedge_ratio=1.0,
        spread_value=spreads[-1],
        zscore=zscores[-1],
        mean_spread=mean_spread,
        spread_volatility=spread_volatility,
    )


def build_pair_legs(
    *,
    base_symbol: str,
    quote_symbol: str,
    hedge_ratio: float,
    spread_value: float,
) -> tuple[MultiLegPosition, ...]:
    if spread_value >= 0.0:
        base_side = "short"
        quote_side = "long"
    else:
        base_side = "long"
        quote_side = "short"
    return (
        MultiLegPosition(
            symbol=base_symbol,
            side=base_side,
            weight=1.0,
            quantity_scale=1.0,
            diagnostics={"role": "base_leg", "hedge_ratio_notional": 1.0},
        ),
        MultiLegPosition(
            symbol=quote_symbol,
            side=quote_side,
            weight=abs(hedge_ratio),
            quantity_scale=abs(hedge_ratio),
            diagnostics={
                "role": "hedge_leg",
                "hedge_ratio_notional": abs(hedge_ratio),
            },
        ),
    )


def build_basket_legs(
    *,
    base_symbol: str,
    basket_symbols: Sequence[str],
    basket_weights: Sequence[float],
    spread_value: float,
) -> tuple[MultiLegPosition, ...]:
    base_side = "short" if spread_value >= 0.0 else "long"
    hedge_side = "long" if base_side == "short" else "short"
    return (
        MultiLegPosition(
            symbol=base_symbol,
            side=base_side,
            weight=1.0,
            quantity_scale=1.0,
            diagnostics={"role": "base_leg", "basket_role": "anchor"},
        ),
        *tuple(
            MultiLegPosition(
                symbol=basket_symbol,
                side=hedge_side,
                weight=basket_weight,
                quantity_scale=basket_weight,
                diagnostics={
                    "role": "hedge_leg",
                    "basket_role": "component",
                    "basket_weight": basket_weight,
                },
            )
            for basket_symbol, basket_weight in zip(
                basket_symbols, basket_weights, strict=True
            )
        ),
    )


def build_triangular_legs(
    *,
    base_symbol: str,
    cross_symbol: str,
    implied_symbol: str,
    spread_value: float,
) -> tuple[MultiLegPosition, ...]:
    if spread_value >= 0.0:
        implied_side = "short"
        synthetic_side = "long"
    else:
        implied_side = "long"
        synthetic_side = "short"
    return (
        MultiLegPosition(
            symbol=base_symbol,
            side=synthetic_side,
            weight=1.0,
            quantity_scale=1.0,
            diagnostics={"role": "synthetic_leg", "triangle_component": "base"},
        ),
        MultiLegPosition(
            symbol=cross_symbol,
            side=synthetic_side,
            weight=1.0,
            quantity_scale=1.0,
            diagnostics={"role": "synthetic_leg", "triangle_component": "cross"},
        ),
        MultiLegPosition(
            symbol=implied_symbol,
            side=implied_side,
            weight=1.0,
            quantity_scale=1.0,
            diagnostics={"role": "hedge_leg", "triangle_component": "implied"},
        ),
    )
