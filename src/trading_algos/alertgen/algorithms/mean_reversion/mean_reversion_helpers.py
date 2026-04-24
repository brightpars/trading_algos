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
