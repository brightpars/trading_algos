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


def rolling_hedge_ratio(
    base_prices: Sequence[float],
    hedge_prices: Sequence[float],
    *,
    window: int,
) -> list[float | None]:
    if window <= 0:
        raise ValueError("relative_value: rolling hedge ratio window must be > 0")
    if len(base_prices) != len(hedge_prices):
        raise ValueError("relative_value: hedge ratio inputs must have equal length")
    ratios: list[float | None] = []
    for index in range(len(base_prices)):
        if index + 1 < window:
            ratios.append(None)
            continue
        ratios.append(
            static_hedge_ratio(
                base_prices[index + 1 - window : index + 1],
                hedge_prices[index + 1 - window : index + 1],
            )
        )
    return ratios


def kalman_hedge_ratios(
    base_prices: Sequence[float],
    hedge_prices: Sequence[float],
    *,
    process_variance: float,
    observation_variance: float,
    initial_ratio: float = 1.0,
) -> list[float]:
    if len(base_prices) != len(hedge_prices):
        raise ValueError("relative_value: hedge ratio inputs must have equal length")
    if process_variance < 0.0:
        raise ValueError("relative_value: process variance must be >= 0")
    if observation_variance <= 0.0:
        raise ValueError("relative_value: observation variance must be > 0")
    estimate = initial_ratio
    error_covariance = 1.0
    ratios: list[float] = []
    for base_price, hedge_price in zip(base_prices, hedge_prices, strict=True):
        predicted_estimate = estimate
        predicted_covariance = error_covariance + process_variance
        observation_scale = hedge_price * hedge_price
        innovation_covariance = (
            observation_scale * predicted_covariance + observation_variance
        )
        if innovation_covariance <= 0.0:
            ratios.append(predicted_estimate)
            estimate = predicted_estimate
            error_covariance = predicted_covariance
            continue
        kalman_gain = predicted_covariance * hedge_price / innovation_covariance
        innovation = base_price - predicted_estimate * hedge_price
        estimate = predicted_estimate + kalman_gain * innovation
        error_covariance = max(
            (1.0 - kalman_gain * hedge_price) * predicted_covariance,
            1e-12,
        )
        ratios.append(estimate)
    return ratios


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


def spread_series_from_ratios(
    base_prices: Sequence[float],
    hedge_prices: Sequence[float],
    *,
    hedge_ratios: Sequence[float | None],
) -> list[float | None]:
    if len(base_prices) != len(hedge_prices) or len(base_prices) != len(hedge_ratios):
        raise ValueError(
            "relative_value: spread inputs and hedge ratios must have equal length"
        )
    spreads: list[float | None] = []
    for base_price, hedge_price, hedge_ratio in zip(
        base_prices, hedge_prices, hedge_ratios, strict=True
    ):
        if hedge_ratio is None:
            spreads.append(None)
            continue
        spreads.append(base_price - hedge_ratio * hedge_price)
    return spreads


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


def normalize_spread(
    spread_value: float,
    *,
    mean_spread: float,
    spread_volatility: float,
) -> float:
    if spread_volatility == 0.0:
        return 0.0
    return (spread_value - mean_spread) / spread_volatility


@dataclass(frozen=True)
class RelativeValueSnapshot:
    hedge_ratio: float
    spread_value: float
    zscore: float | None
    mean_spread: float
    spread_volatility: float
    carry_adjustment: float = 0.0
