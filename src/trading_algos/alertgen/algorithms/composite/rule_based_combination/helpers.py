from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from trading_algos.alertgen.contracts.outputs import NormalizedChildOutput


VALID_COMBINATION_SIGNALS = frozenset({"buy", "sell", "neutral"})


@dataclass(frozen=True)
class AlignedCompositeInputRow:
    timestamp: str
    child_outputs: tuple[NormalizedChildOutput, ...]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class CompositeWarmupState:
    is_ready: bool
    reason_code: str
    diagnostics: dict[str, Any]


def normalize_child_signal_label(signal_label: str) -> str:
    normalized = str(signal_label).strip().lower()
    if normalized not in VALID_COMBINATION_SIGNALS:
        raise ValueError(
            "composite_helper: invalid_signal_label; "
            f"signal_label={signal_label} allowed=buy,sell,neutral"
        )
    return normalized


def normalize_child_direction(direction: int | None, signal_label: str) -> int:
    if direction is None:
        return signal_label_to_direction(signal_label)
    normalized = int(direction)
    if normalized not in {-1, 0, 1}:
        raise ValueError(
            f"composite_helper: invalid_direction; direction={direction} allowed=-1,0,1"
        )
    return normalized


def signal_label_to_direction(signal_label: str) -> int:
    normalized = normalize_child_signal_label(signal_label)
    if normalized == "buy":
        return 1
    if normalized == "sell":
        return -1
    return 0


def direction_to_signal_label(direction: int) -> str:
    if direction > 0:
        return "buy"
    if direction < 0:
        return "sell"
    return "neutral"


def clamp_confidence(value: float | int | None) -> float:
    if value is None:
        return 0.0
    normalized = float(value)
    if normalized < 0.0:
        return 0.0
    if normalized > 1.0:
        return 1.0
    return normalized


def clamp_score(value: float | int | None) -> float:
    if value is None:
        return 0.0
    normalized = float(value)
    if normalized < -1.0:
        return -1.0
    if normalized > 1.0:
        return 1.0
    return normalized


def normalize_child_output(raw_child_output: dict[str, Any]) -> NormalizedChildOutput:
    signal_label = normalize_child_signal_label(
        str(raw_child_output.get("signal_label", "neutral"))
    )
    normalized = NormalizedChildOutput(
        child_key=str(raw_child_output.get("child_key", "child")),
        output_kind="composite_child",
        signal_label=signal_label,
        score=clamp_score(raw_child_output.get("score")),
        confidence=clamp_confidence(raw_child_output.get("confidence")),
        regime_label=(
            str(raw_child_output["regime_label"])
            if raw_child_output.get("regime_label") is not None
            else None
        ),
        direction=normalize_child_direction(
            raw_child_output.get("direction"), signal_label
        ),
        diagnostics=dict(raw_child_output.get("diagnostics", {})),
        reason_codes=tuple(
            str(item) for item in raw_child_output.get("reason_codes", ())
        ),
        event_markers=tuple(
            str(item) for item in raw_child_output.get("event_markers", ())
        ),
    )
    return normalized


def align_child_outputs(
    raw_rows: list[dict[str, Any]],
) -> tuple[AlignedCompositeInputRow, ...]:
    aligned_rows: list[AlignedCompositeInputRow] = []
    for index, row in enumerate(raw_rows):
        timestamp = str(row.get("ts", row.get("timestamp", index)))
        raw_child_outputs = row.get("child_outputs")
        if not isinstance(raw_child_outputs, list):
            raise ValueError(
                "composite_helper: invalid_child_outputs; "
                f"timestamp={timestamp} expected=list"
            )
        child_outputs = tuple(
            normalize_child_output(item) for item in raw_child_outputs
        )
        aligned_rows.append(
            AlignedCompositeInputRow(
                timestamp=timestamp,
                child_outputs=child_outputs,
                metadata={
                    key: value
                    for key, value in row.items()
                    if key not in {"ts", "timestamp", "child_outputs"}
                },
            )
        )
    return tuple(aligned_rows)


def build_child_contribution_rows(
    child_outputs: tuple[NormalizedChildOutput, ...],
) -> list[dict[str, Any]]:
    return [
        {
            "child_key": child.child_key,
            "signal_label": child.signal_label,
            "direction": child.direction,
            "score": child.score,
            "confidence": child.confidence,
            "regime_label": child.regime_label,
            "reason_codes": list(child.reason_codes),
        }
        for child in child_outputs
    ]


def evaluate_child_row_warmup(
    row: AlignedCompositeInputRow,
    *,
    required_child_count: int | None = None,
) -> CompositeWarmupState:
    actual_child_count = len(row.child_outputs)
    expected_child_count = (
        actual_child_count
        if required_child_count is None
        else int(required_child_count)
    )
    if actual_child_count <= 0:
        return CompositeWarmupState(
            is_ready=False,
            reason_code="warmup_pending_no_child_outputs",
            diagnostics={
                "expected_child_count": expected_child_count,
                "actual_child_count": actual_child_count,
                "missing_child_count": max(
                    expected_child_count - actual_child_count, 0
                ),
            },
        )
    if actual_child_count < expected_child_count:
        return CompositeWarmupState(
            is_ready=False,
            reason_code="warmup_pending_incomplete_child_set",
            diagnostics={
                "expected_child_count": expected_child_count,
                "actual_child_count": actual_child_count,
                "missing_child_count": expected_child_count - actual_child_count,
            },
        )
    return CompositeWarmupState(
        is_ready=True,
        reason_code="ready",
        diagnostics={
            "expected_child_count": expected_child_count,
            "actual_child_count": actual_child_count,
            "missing_child_count": 0,
        },
    )
