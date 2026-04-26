from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OrderBookLevel:
    price: float
    size: float


@dataclass(frozen=True)
class OrderBookSnapshot:
    timestamp: str
    symbol: str
    bid: OrderBookLevel
    ask: OrderBookLevel
    auction_imbalance: float = 0.0
    auction_phase: str = "continuous"
    session_phase: str = "continuous"

    @property
    def spread(self) -> float:
        return max(0.0, self.ask.price - self.bid.price)

    @property
    def midprice(self) -> float:
        return (self.bid.price + self.ask.price) / 2.0


def _require_float(value: Any, *, default: float = 0.0) -> float:
    if value is None:
        return default
    return float(value)


def snapshot_from_mapping(row: dict[str, Any]) -> OrderBookSnapshot:
    return OrderBookSnapshot(
        timestamp=str(row.get("ts") or row.get("timestamp") or ""),
        symbol=str(row.get("symbol") or "UNKNOWN"),
        bid=OrderBookLevel(
            price=_require_float(row.get("best_bid_price")),
            size=_require_float(row.get("best_bid_size")),
        ),
        ask=OrderBookLevel(
            price=_require_float(row.get("best_ask_price")),
            size=_require_float(row.get("best_ask_size")),
        ),
        auction_imbalance=_require_float(row.get("auction_imbalance")),
        auction_phase=str(
            row.get("auction_phase") or row.get("session_phase") or "continuous"
        ),
        session_phase=str(
            row.get("session_phase") or row.get("auction_phase") or "continuous"
        ),
    )


def imbalance_ratio(snapshot: OrderBookSnapshot) -> float:
    total = snapshot.bid.size + snapshot.ask.size
    if total <= 0.0:
        return 0.0
    return (snapshot.bid.size - snapshot.ask.size) / total


def microprice(snapshot: OrderBookSnapshot) -> float:
    total = snapshot.bid.size + snapshot.ask.size
    if total <= 0.0:
        return snapshot.midprice
    return (
        snapshot.ask.price * snapshot.bid.size + snapshot.bid.price * snapshot.ask.size
    ) / total
