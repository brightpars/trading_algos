from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class MultiLegPosition:
    symbol: str
    side: str
    weight: float
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.side not in {"long", "short", "neutral"}:
            raise ValueError("side must be one of long, short, neutral")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MultiLegRebalancePoint:
    timestamp: str
    spread_value: float
    legs: tuple[MultiLegPosition, ...]
    hedge_ratio: float = 1.0
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["legs"] = [leg.to_dict() for leg in self.legs]
        return payload


@dataclass(frozen=True)
class MultiLegOutput:
    algorithm_key: str
    rebalances: tuple[MultiLegRebalancePoint, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "algorithm_key": self.algorithm_key,
            "rebalances": [rebalance.to_dict() for rebalance in self.rebalances],
            "metadata": dict(self.metadata),
        }
