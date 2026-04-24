from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ExecutionChildOrder:
    timestamp: str
    action: str
    quantity: float
    order_type: str = "limit"
    limit_price: float | None = None
    diagnostics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionPlanPoint:
    timestamp: str
    target_cumulative_quantity: float
    achieved_cumulative_quantity: float
    benchmark_price: float | None = None
    diagnostics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionPlanOutput:
    algorithm_key: str
    plan_points: tuple[ExecutionPlanPoint, ...]
    child_orders: tuple[ExecutionChildOrder, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
