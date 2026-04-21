from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class AlertSeriesPoint:
    timestamp: str
    signal_label: str
    score: float | None = None
    confidence: float | None = None
    reason_codes: tuple[str, ...] = ()
    event_markers: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AlertAlgorithmOutput:
    algorithm_key: str
    points: tuple[AlertSeriesPoint, ...]
    derived_series: dict[str, list[Any]] = field(default_factory=dict)
    summary_metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["points"] = [point.to_dict() for point in self.points]
        return payload
