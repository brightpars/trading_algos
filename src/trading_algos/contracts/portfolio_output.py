from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class RankedAsset:
    symbol: str
    rank: int
    score: float
    weight: float = 0.0
    selected: bool = False
    side: str = "neutral"

    def __post_init__(self) -> None:
        if self.rank <= 0:
            raise ValueError("rank must be >= 1")
        if self.side not in {"long", "short", "defensive", "neutral"}:
            raise ValueError("side must be one of long, short, defensive, neutral")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PortfolioRebalancePoint:
    timestamp: str
    ranking: tuple[RankedAsset, ...]
    selected_symbols: tuple[str, ...]
    weights: dict[str, float]
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        gross_exposure = sum(abs(weight) for weight in self.weights.values())
        if gross_exposure > 1.000001:
            raise ValueError("weights gross exposure must be <= 1.0")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["ranking"] = [asset.to_dict() for asset in self.ranking]
        return payload


@dataclass(frozen=True)
class PortfolioWeightOutput:
    algorithm_key: str
    rebalances: tuple[PortfolioRebalancePoint, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "algorithm_key": self.algorithm_key,
            "rebalances": [rebalance.to_dict() for rebalance in self.rebalances],
            "metadata": dict(self.metadata),
        }
