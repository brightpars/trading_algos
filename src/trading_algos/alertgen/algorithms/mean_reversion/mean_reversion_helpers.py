from __future__ import annotations

from dataclasses import dataclass


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
