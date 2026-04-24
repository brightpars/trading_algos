from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


def clamp_unit(value: float) -> float:
    if value < -1.0:
        return -1.0
    if value > 1.0:
        return 1.0
    return value


def confirmation_state(previous_count: int, *, condition_met: bool) -> int:
    return previous_count + 1 if condition_met else 0


def simple_average(values: Sequence[float | None], window: int) -> list[float | None]:
    if window <= 0:
        raise ValueError("window must be positive")
    result: list[float | None] = []
    running_values: list[float] = []
    for value in values:
        if value is None:
            running_values.clear()
            result.append(None)
            continue
        running_values.append(value)
        if len(running_values) > window:
            running_values.pop(0)
        if len(running_values) == window:
            result.append(sum(running_values) / window)
        else:
            result.append(None)
    return result


def weighted_sum_components(
    components: list[list[float | None]], *, weights: list[float]
) -> list[float | None]:
    if len(components) != len(weights):
        raise ValueError("components and weights must have equal length")
    if not components:
        return []
    component_length = len(components[0])
    if any(len(component) != component_length for component in components):
        raise ValueError("all components must have equal length")
    result: list[float | None] = []
    for index in range(component_length):
        values = [component[index] for component in components]
        if any(value is None for value in values):
            result.append(None)
            continue
        total = 0.0
        for value, weight in zip(values, weights, strict=True):
            assert value is not None
            total += value * weight
        result.append(total)
    return result


def relative_volume(
    volumes: list[float], *, window: int
) -> tuple[list[float | None], list[float | None]]:
    averages = simple_average(volumes, window)
    rel_volume: list[float | None] = []
    for volume, baseline in zip(volumes, averages, strict=True):
        if baseline is None or baseline == 0.0:
            rel_volume.append(None)
            continue
        rel_volume.append(volume / baseline)
    return averages, rel_volume


@dataclass(frozen=True)
class MomentumSignalState:
    regime: str
    score: float
    bullish: bool
    bearish: bool
    primary_value: float | None
    signal_value: float | None
    threshold_value: float | None
    aligned_count: int
    reason_code: str
