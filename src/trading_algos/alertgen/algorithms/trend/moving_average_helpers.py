from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from trading_algos.alertgen.shared_utils.indicators import (
    exponential_moving_average,
    simple_moving_average,
)


AverageType = Literal["sma", "ema"]


def moving_average(
    values: list[float], window: int, average_type: AverageType
) -> list[float | None]:
    if average_type == "ema":
        return exponential_moving_average(values, window)
    return simple_moving_average(values, window)


def average_label(average_type: AverageType) -> str:
    return average_type.upper()


def confirmation_state(previous_count: int, *, condition_met: bool) -> int:
    return previous_count + 1 if condition_met else 0


def minimum_history_for_windows(*windows: int) -> int:
    return max(windows)


@dataclass(frozen=True)
class TrendSignalState:
    regime: str
    score: float
    spread: float | None
    aligned_count: int
    bullish: bool
    bearish: bool
