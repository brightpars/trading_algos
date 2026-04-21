from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class EvaluationResult:
    evaluator_id: str
    evaluator_version: str
    metric_group: str
    applies: bool
    metrics: dict[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    applicability_status: str = "applicable"
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
