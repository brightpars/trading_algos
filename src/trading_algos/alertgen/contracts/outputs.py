from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


VALID_SIGNAL_LABELS = frozenset({"buy", "sell", "neutral"})
VALID_OUTPUT_KINDS = frozenset({"signal", "score", "diagnostics", "composite_child"})


@dataclass(frozen=True)
class AlertSeriesPoint:
    timestamp: str
    signal_label: str
    score: float | None = None
    confidence: float | None = None
    reason_codes: tuple[str, ...] = ()
    event_markers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.signal_label not in VALID_SIGNAL_LABELS:
            raise ValueError(f"unsupported signal_label: {self.signal_label}")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within [0.0, 1.0]")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NormalizedChildOutput:
    child_key: str
    output_kind: str
    signal_label: str
    score: float | None = None
    confidence: float | None = None
    regime_label: str | None = None
    direction: int | None = None
    diagnostics: dict[str, Any] = field(default_factory=dict)
    reason_codes: tuple[str, ...] = ()
    event_markers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.output_kind not in VALID_OUTPUT_KINDS:
            raise ValueError(f"unsupported output_kind: {self.output_kind}")
        if self.signal_label not in VALID_SIGNAL_LABELS:
            raise ValueError(f"unsupported signal_label: {self.signal_label}")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within [0.0, 1.0]")
        if self.direction is not None and self.direction not in {-1, 0, 1}:
            raise ValueError("direction must be one of -1, 0, 1")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AlertAlgorithmOutput:
    algorithm_key: str
    points: tuple[AlertSeriesPoint, ...]
    derived_series: dict[str, list[Any]] = field(default_factory=dict)
    summary_metrics: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    child_outputs: tuple[NormalizedChildOutput, ...] = ()

    def __post_init__(self) -> None:
        point_count = len(self.points)
        for series_name, series_values in self.derived_series.items():
            if point_count and len(series_values) != point_count:
                raise ValueError(
                    f"derived series length mismatch for {series_name}: "
                    f"expected {point_count}, got {len(series_values)}"
                )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["points"] = [point.to_dict() for point in self.points]
        payload["child_outputs"] = [child.to_dict() for child in self.child_outputs]
        return payload
