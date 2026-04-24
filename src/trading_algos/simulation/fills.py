from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FillEstimate:
    requested_quantity: float
    filled_quantity: float
    fill_ratio: float


def estimate_child_fill(
    *, requested_quantity: float, available_quantity: float, aggressiveness: float = 1.0
) -> FillEstimate:
    capped_aggressiveness = max(0.0, min(1.0, aggressiveness))
    fillable = max(0.0, min(float(requested_quantity), float(available_quantity)))
    filled = fillable * capped_aggressiveness
    ratio = 0.0 if requested_quantity <= 0.0 else filled / float(requested_quantity)
    return FillEstimate(
        requested_quantity=float(requested_quantity),
        filled_quantity=filled,
        fill_ratio=max(0.0, min(1.0, ratio)),
    )