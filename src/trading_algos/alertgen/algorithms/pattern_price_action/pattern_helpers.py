from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable


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
