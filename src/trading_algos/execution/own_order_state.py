from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OwnOrderState:
    timestamp: str
    symbol: str
    side: str
    resting_quantity: float
    queue_ahead: float
    traded_volume_since_update: float
    cancel_replace_count: int = 0


def own_order_state_from_mapping(row: dict[str, Any]) -> OwnOrderState:
    return OwnOrderState(
        timestamp=str(row.get("ts") or row.get("timestamp") or ""),
        symbol=str(row.get("symbol") or "UNKNOWN"),
        side=str(row.get("side") or "buy"),
        resting_quantity=float(row.get("resting_quantity") or 0.0),
        queue_ahead=float(row.get("queue_ahead") or 0.0),
        traded_volume_since_update=float(row.get("traded_volume_since_update") or 0.0),
        cancel_replace_count=int(row.get("cancel_replace_count") or 0),
    )


def estimate_fill_probability(state: OwnOrderState) -> float:
    denominator = max(state.queue_ahead + state.resting_quantity, 1e-9)
    progress = min(1.0, max(0.0, state.traded_volume_since_update / denominator))
    penalty = min(0.5, state.cancel_replace_count * 0.05)
    return max(0.0, min(1.0, progress - penalty))
