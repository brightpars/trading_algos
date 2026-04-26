from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable


def simple_moving_average(values: list[float], window: int) -> float | None:
    if window <= 0 or len(values) < window:
        return None
    chunk = values[-window:]
    return sum(chunk) / float(window)


def sample_standard_deviation(values: list[float], window: int) -> float | None:
    if window <= 1 or len(values) < window:
        return None
    chunk = values[-window:]
    mean_value = sum(chunk) / float(window)
    variance = sum((value - mean_value) ** 2 for value in chunk) / float(window)
    return variance**0.5


def average_true_range(
    highs: list[float], lows: list[float], closes: list[float], window: int
) -> float | None:
    if window <= 0 or len(highs) < window or len(lows) < window or len(closes) < window:
        return None
    start_index = len(closes) - window
    true_ranges: list[float] = []
    for index in range(start_index, len(closes)):
        high_value = highs[index]
        low_value = lows[index]
        previous_close = closes[index - 1] if index > 0 else closes[index]
        true_ranges.append(
            max(
                high_value - low_value,
                abs(high_value - previous_close),
                abs(low_value - previous_close),
            )
        )
    return sum(true_ranges) / float(window)


def rolling_linear_regression(values: list[float]) -> tuple[float, float] | None:
    if len(values) < 2:
        return None
    x_values = [float(index) for index in range(len(values))]
    x_mean = sum(x_values) / float(len(x_values))
    y_mean = sum(values) / float(len(values))
    numerator = sum(
        (x_value - x_mean) * (y_value - y_mean)
        for x_value, y_value in zip(x_values, values, strict=False)
    )
    denominator = sum((x_value - x_mean) ** 2 for x_value in x_values)
    if denominator == 0.0:
        return None
    slope = numerator / denominator
    intercept = y_mean - (slope * x_mean)
    return slope, intercept


def project_linear_value(*, slope: float, intercept: float, index: int) -> float:
    return intercept + (slope * float(index))


def relative_volume(volumes: list[float], window: int) -> float | None:
    baseline = (
        simple_moving_average(volumes[:-1], window) if len(volumes) >= 2 else None
    )
    if baseline is None or baseline <= 0.0:
        return None
    return volumes[-1] / baseline


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


def rolling_level(values: list[float], window: int, *, mode: str) -> float | None:
    if len(values) < window or window <= 0:
        return None
    chunk = values[-window:]
    return min(chunk) if mode == "min" else max(chunk)


def parse_session_label(timestamp: str) -> str:
    normalized = timestamp.replace("T", " ")
    return normalized.split(" ", 1)[0]


def parse_timestamp(timestamp: str) -> datetime:
    return datetime.fromisoformat(timestamp.replace("Z", ""))


def classic_pivot_levels(high: float, low: float, close: float) -> dict[str, float]:
    pivot = (high + low + close) / 3.0
    range_value = high - low
    return {
        "pivot": pivot,
        "support_1": (2.0 * pivot) - high,
        "resistance_1": (2.0 * pivot) - low,
        "support_2": pivot - range_value,
        "resistance_2": pivot + range_value,
    }


def nearest_level(
    price: float, levels: Iterable[tuple[str, float]]
) -> tuple[str, float] | None:
    best_name: str | None = None
    best_value: float | None = None
    best_distance: float | None = None
    for name, level in levels:
        distance = abs(price - level)
        if best_distance is None or distance < best_distance:
            best_name = name
            best_value = level
            best_distance = distance
    if best_name is None or best_value is None:
        return None
    return best_name, best_value


@dataclass(frozen=True)
class PatternSignalState:
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
