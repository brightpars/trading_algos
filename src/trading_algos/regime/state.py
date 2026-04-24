from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


def clamp_probability(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def normalize_probability_map(values: Mapping[str, float]) -> dict[str, float]:
    normalized = {
        str(key): clamp_probability(float(value)) for key, value in values.items()
    }
    total = sum(normalized.values())
    if total <= 0.0:
        return {}
    return {key: value / total for key, value in normalized.items()}


@dataclass(frozen=True)
class RegimeState:
    label: str
    confidence: float
    probabilities: dict[str, float] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not str(self.label).strip():
            raise ValueError("regime_state: label is required")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("regime_state: confidence must be within [0.0, 1.0]")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def smooth_regime_probabilities(
    previous: Mapping[str, float] | None,
    current: Mapping[str, float],
    *,
    smoothing: float,
) -> dict[str, float]:
    smoothing_value = clamp_probability(smoothing)
    current_normalized = normalize_probability_map(current)
    previous_normalized = normalize_probability_map(previous or {})
    labels = sorted(set(previous_normalized).union(current_normalized))
    blended = {
        label: (
            previous_normalized.get(label, 0.0) * smoothing_value
            + current_normalized.get(label, 0.0) * (1.0 - smoothing_value)
        )
        for label in labels
    }
    return normalize_probability_map(blended)


def apply_regime_hysteresis(
    previous_label: str | None,
    probability_map: Mapping[str, float],
    *,
    switch_threshold: float,
) -> str:
    normalized = normalize_probability_map(probability_map)
    if not normalized:
        return previous_label or "unknown"
    ordered = sorted(normalized.items(), key=lambda item: (-item[1], item[0]))
    winning_label, winning_probability = ordered[0]
    if previous_label is None or previous_label not in normalized:
        return winning_label
    if previous_label == winning_label:
        return previous_label
    if winning_probability >= clamp_probability(switch_threshold):
        return winning_label
    return previous_label


def build_regime_state(
    probability_map: Mapping[str, float],
    *,
    previous_label: str | None = None,
    smoothing: float = 0.0,
    switch_threshold: float = 0.5,
    diagnostics: Mapping[str, Any] | None = None,
) -> RegimeState:
    smoothed = smooth_regime_probabilities(None, probability_map, smoothing=smoothing)
    label = apply_regime_hysteresis(
        previous_label,
        smoothed,
        switch_threshold=switch_threshold,
    )
    confidence = smoothed.get(label, 0.0)
    return RegimeState(
        label=label,
        confidence=confidence,
        probabilities=smoothed,
        diagnostics=dict(diagnostics or {}),
    )
