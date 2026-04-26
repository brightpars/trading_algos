from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from trading_algos.contracts.portfolio_output import PortfolioRebalancePoint


@dataclass(frozen=True)
class RebalanceResult:
    points: tuple[PortfolioRebalancePoint, ...]
    diagnostics: dict[str, Any]


def build_rebalance_result(
    points: list[PortfolioRebalancePoint], *, schedule: tuple[str, ...]
) -> RebalanceResult:
    return RebalanceResult(
        points=tuple(points),
        diagnostics={
            "rebalance_count": len(points),
            "schedule": list(schedule),
        },
    )
