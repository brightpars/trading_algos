from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence


def clamp_unit(value: float) -> float:
    if value < -1.0:
        return -1.0
    if value > 1.0:
        return 1.0
    return value


def confirmation_state(previous_count: int, *, condition_met: bool) -> int:
    return previous_count + 1 if condition_met else 0


def scale_score(raw_value: float, scale: float) -> float:
    if scale <= 0.0:
        return 0.0
    return clamp_unit(raw_value / scale)


def clamp_range(value: float, minimum: float, maximum: float) -> float:
    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value


def centered_oscillator_score(
    value: float, *, center: float, lower_bound: float, upper_bound: float
) -> float:
    if upper_bound <= lower_bound:
        return 0.0
    midpoint = center
    if value <= midpoint:
        scale = max(midpoint - lower_bound, 0.0)
    else:
        scale = max(upper_bound - midpoint, 0.0)
    if scale <= 0.0:
        return 0.0
    return clamp_unit((midpoint - value) / scale)


def normalized_distance_from_midpoint(
    value: float, *, lower_bound: float, upper_bound: float
) -> float:
    if upper_bound <= lower_bound:
        return 0.0
    midpoint = (lower_bound + upper_bound) / 2.0
    half_width = (upper_bound - lower_bound) / 2.0
    if half_width <= 0.0:
        return 0.0
    return clamp_unit((midpoint - value) / half_width)


def parse_session_label(timestamp: str) -> str:
    normalized = timestamp.replace("T", " ")
    return normalized.split(" ", 1)[0]


def parse_timestamp(timestamp: str) -> datetime:
    return datetime.fromisoformat(timestamp.replace("Z", ""))


def cumulative_session_vwap(
    timestamps: Sequence[str],
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    volumes: Sequence[float],
) -> list[float | None]:
    if not (len(timestamps) == len(highs) == len(lows) == len(closes) == len(volumes)):
        raise ValueError("session_vwap inputs must have equal length")
    result: list[float | None] = []
    current_session: str | None = None
    cumulative_price_volume = 0.0
    cumulative_volume = 0.0
    for timestamp, high, low, close, volume in zip(
        timestamps,
        highs,
        lows,
        closes,
        volumes,
        strict=False,
    ):
        session_label = parse_session_label(timestamp)
        if session_label != current_session:
            current_session = session_label
            cumulative_price_volume = 0.0
            cumulative_volume = 0.0
        typical_price = (high + low + close) / 3.0
        cumulative_price_volume += typical_price * volume
        cumulative_volume += volume
        result.append(
            None
            if cumulative_volume <= 0.0
            else cumulative_price_volume / cumulative_volume
        )
    return result


def normalized_gap_fill_progress(
    *,
    prior_close: float | None,
    opening_price: float,
    current_price: float,
) -> float | None:
    if prior_close is None or prior_close == opening_price:
        return None
    return (current_price - opening_price) / (prior_close - opening_price)


def rolling_ou_reversion_ratio(
    values: Sequence[float],
    window: int,
) -> tuple[
    list[float | None], list[float | None], list[float | None], list[float | None]
]:
    if window <= 1:
        raise ValueError("window must be > 1")
    mean_reversion_speed: list[float | None] = []
    equilibrium_values: list[float | None] = []
    residual_values: list[float | None] = []
    normalized_residuals: list[float | None] = []
    for index in range(len(values)):
        if index + 1 < window:
            mean_reversion_speed.append(None)
            equilibrium_values.append(None)
            residual_values.append(None)
            normalized_residuals.append(None)
            continue
        chunk = [float(value) for value in values[index - window + 1 : index + 1]]
        x_values = chunk[:-1]
        y_values = chunk[1:]
        x_mean = sum(x_values) / float(len(x_values))
        y_mean = sum(y_values) / float(len(y_values))
        denominator = sum((value - x_mean) ** 2 for value in x_values)
        if denominator <= 0.0:
            mean_reversion_speed.append(None)
            equilibrium_values.append(None)
            residual_values.append(None)
            normalized_residuals.append(None)
            continue
        beta = (
            sum(
                (x_value - x_mean) * (y_value - y_mean)
                for x_value, y_value in zip(x_values, y_values, strict=False)
            )
            / denominator
        )
        alpha = y_mean - (beta * x_mean)
        kappa = 1.0 - beta
        if kappa <= 0.0:
            mean_reversion_speed.append(None)
            equilibrium_values.append(None)
            residual_values.append(None)
            normalized_residuals.append(None)
            continue
        equilibrium = alpha / kappa
        residual = chunk[-1] - equilibrium
        centered_residuals = [value - equilibrium for value in chunk]
        residual_variance = sum(value * value for value in centered_residuals) / float(
            len(centered_residuals)
        )
        residual_std = residual_variance**0.5
        mean_reversion_speed.append(kappa)
        equilibrium_values.append(equilibrium)
        residual_values.append(residual)
        normalized_residuals.append(
            None if residual_std <= 0.0 else residual / residual_std
        )
    return (
        mean_reversion_speed,
        equilibrium_values,
        residual_values,
        normalized_residuals,
    )


@dataclass(frozen=True)
class MeanReversionSignalState:
    regime: str
    score: float
    bullish: bool
    bearish: bool
    primary_value: float | None
    signal_value: float | None
    threshold_value: float | None
    exit_value: float | None
    aligned_count: int
    reason_code: str
