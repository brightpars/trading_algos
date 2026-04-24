from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from trading_algos.execution.own_order_state import (
    OwnOrderState,
    estimate_fill_probability,
)
from trading_algos.market_data.order_book import (
    OrderBookSnapshot,
    imbalance_ratio,
    microprice,
)


@dataclass(frozen=True)
class MicrostructureMetrics:
    timestamp: str
    symbol: str
    midprice: float
    spread: float
    imbalance: float
    microprice: float
    microprice_edge: float
    inventory: float
    queue_fill_probability: float
    auction_imbalance: float
    auction_phase: str
    session_phase: str


def build_microstructure_metrics(
    snapshot: OrderBookSnapshot,
    own_state: OwnOrderState | None,
) -> MicrostructureMetrics:
    fill_probability = (
        0.0 if own_state is None else estimate_fill_probability(own_state)
    )
    inventory = 0.0 if own_state is None else own_state.resting_quantity
    microprice_value = microprice(snapshot)
    return MicrostructureMetrics(
        timestamp=snapshot.timestamp,
        symbol=snapshot.symbol,
        midprice=snapshot.midprice,
        spread=snapshot.spread,
        imbalance=imbalance_ratio(snapshot),
        microprice=microprice_value,
        microprice_edge=microprice_value - snapshot.midprice,
        inventory=inventory,
        queue_fill_probability=fill_probability,
        auction_imbalance=snapshot.auction_imbalance,
        auction_phase=snapshot.auction_phase,
        session_phase=snapshot.session_phase,
    )


def clamp_score(value: float) -> float:
    return max(-1.0, min(1.0, value))


def default_reason_payload(reason_code: str, **kwargs: Any) -> dict[str, Any]:
    payload = {"decision_reason": reason_code}
    payload.update(kwargs)
    return payload
