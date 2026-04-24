from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Sequence


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def _stddev(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    center = _mean(values)
    variance = sum((value - center) ** 2 for value in values) / len(values)
    return sqrt(variance)


def static_hedge_ratio(
    base_prices: Sequence[float], hedge_prices: Sequence[float]
) -> float:
    if len(base_prices) != len(hedge_prices):
        raise ValueError("relative_value: hedge ratio inputs must have equal length")
    if len(base_prices) < 2:
        return 1.0
    hedge_mean = _mean(hedge_prices)
    base_mean = _mean(base_prices)
    numerator = sum(
        (hedge_price - hedge_mean) * (base_price - base_mean)
        for base_price, hedge_price in zip(base_prices, hedge_prices, strict=True)
    )
    denominator = sum((hedge_price - hedge_mean) ** 2 for hedge_price in hedge_prices)
    if denominator == 0.0:
        return 1.0
    return numerator / denominator


def spread_series(
    base_prices: Sequence[float],
    hedge_prices: Sequence[float],
    *,
    hedge_ratio: float,
) -> list[float]:
    if len(base_prices) != len(hedge_prices):
        raise ValueError("relative_value: spread inputs must have equal length")
    return [
        base_price - hedge_ratio * hedge_price
        for base_price, hedge_price in zip(base_prices, hedge_prices, strict=True)
    ]


def rolling_zscore(values: Sequence[float], window: int) -> list[float | None]:
    result: list[float | None] = []
    for index in range(len(values)):
        if index + 1 < window:
            result.append(None)
            continue
        segment = values[index + 1 - window : index + 1]
        stdev = _stddev(segment)
        if stdev == 0.0:
            result.append(0.0)
            continue
        result.append((segment[-1] - _mean(segment)) / stdev)
    return result


@dataclass(frozen=True)
class RelativeValueSnapshot:
    hedge_ratio: float
    spread_value: float
    zscore: float | None
    mean_spread: float
    spread_volatility: float
