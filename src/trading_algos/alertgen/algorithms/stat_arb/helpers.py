from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from trading_algos.contracts.multi_leg_output import MultiLegPosition
from trading_algos.data.panel_dataset import MultiAssetPanel, PanelRow
from trading_algos.relative_value.hedge_ratio import (
    RelativeValueSnapshot,
    rolling_zscore,
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
            symbol=base_symbol, side=base_side, weight=1.0, quantity_scale=1.0
        ),
        MultiLegPosition(
            symbol=quote_symbol,
            side=quote_side,
            weight=abs(hedge_ratio),
            quantity_scale=abs(hedge_ratio),
        ),
    )
