from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Sequence

from trading_algos.alertgen.contracts.outputs import (
    AlertAlgorithmOutput,
    AlertSeriesPoint,
    NormalizedChildOutput,
)
from trading_algos.data.panel_dataset import PanelRow
from trading_algos.events import (
    EventCalendar,
    EventWindowDefinition,
    build_event_metadata,
    resolve_event_window_state,
)


@dataclass(frozen=True)
class EventDrivenRow:
    timestamp: str
    signal_label: str
    score: float
    confidence: float
    diagnostics: dict[str, Any]
    reason_codes: tuple[str, ...]


EventValueFunction = Callable[[PanelRow, dict[str, Any]], float | None]


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, value))


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def extract_positive_event_value(
    event_metadata: dict[str, Any],
    *,
    event_value_field: str,
    minimum_score_threshold: float,
) -> float | None:
    raw_value = event_metadata.get(event_value_field)
    if raw_value is None:
        return None
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        return None
    if value < minimum_score_threshold:
        return None
    return value


def extract_expected_buy_flow(
    event_metadata: dict[str, Any],
    *,
    event_value_field: str,
    expected_direction_field: str,
    minimum_score_threshold: float,
) -> float | None:
    direction = str(event_metadata.get(expected_direction_field, "buy")).lower()
    value = extract_positive_event_value(
        event_metadata,
        event_value_field=event_value_field,
        minimum_score_threshold=minimum_score_threshold,
    )
    if value is None:
        return None
    return value if direction == "buy" else None


def evaluate_event_rows(
    *,
    panel_rows: Sequence[PanelRow],
    calendar: EventCalendar,
    window: EventWindowDefinition,
    event_value_label: str,
    event_value_function: EventValueFunction,
    bullish_phase: str,
) -> tuple[EventDrivenRow, ...]:
    rows: list[EventDrivenRow] = []
    for index, row in enumerate(panel_rows):
        state = resolve_event_window_state(
            calendar=calendar,
            symbol=row.symbol,
            row_timestamp=row.timestamp,
            window=window,
        )
        event_metadata = dict(state.event.metadata) if state.event is not None else {}
        event_value = (
            event_value_function(row, event_metadata)
            if state.event is not None
            else None
        )
        warmup_ready = index >= 1
        active = state.active and event_value is not None and warmup_ready
        score = _clamp_unit(abs(_coerce_float(event_value) or 0.0)) if active else 0.0
        signal_label = "buy" if active and state.phase == bullish_phase else "neutral"
        if not warmup_ready:
            reason_code = "warmup_pending"
        elif state.event is None:
            reason_code = "no_event_available"
        elif not state.active:
            reason_code = "event_window_inactive"
        elif event_value is None:
            reason_code = "event_value_unavailable"
        elif state.phase != bullish_phase:
            reason_code = f"{state.phase}_phase_filtered"
        else:
            reason_code = f"{state.phase}_window_active"
        diagnostics = build_event_metadata(
            state=state,
            event_value=_coerce_float(event_value),
            event_value_label=event_value_label,
            extra_metadata={
                "symbol": row.symbol,
                "close": row.close,
                "warmup_ready": warmup_ready,
                "decision_reason": reason_code,
                "reason_codes": [reason_code],
            },
        )
        rows.append(
            EventDrivenRow(
                timestamp=row.timestamp,
                signal_label=signal_label,
                score=score,
                confidence=score if signal_label == "buy" else 0.0,
                diagnostics=diagnostics,
                reason_codes=(reason_code,),
            )
        )
    return tuple(rows)


def build_event_window_output(
    *,
    algorithm_key: str,
    family: str,
    subcategory: str,
    catalog_ref: str,
    rows: Sequence[EventDrivenRow],
) -> AlertAlgorithmOutput:
    points = tuple(
        AlertSeriesPoint(
            timestamp=row.timestamp,
            signal_label=row.signal_label,
            score=row.score,
            confidence=row.confidence,
            diagnostics=row.diagnostics,
            reason_codes=row.reason_codes,
        )
        for row in rows
    )
    derived_series: dict[str, list[Any]] = {
        "event_window_active": [
            bool(row.diagnostics.get("event_window_active", False)) for row in rows
        ],
        "warmup_ready": [
            bool(row.diagnostics.get("warmup_ready", False)) for row in rows
        ],
        "event_window_phase": [
            row.diagnostics.get("event_window_phase") for row in rows
        ],
        "event_anchor_timestamp": [
            row.diagnostics.get("event_anchor_timestamp") for row in rows
        ],
        "event_days_from_anchor": [
            row.diagnostics.get("event_days_from_anchor") for row in rows
        ],
        "decision_reason": [row.diagnostics.get("decision_reason") for row in rows],
        "reason_codes": [list(row.reason_codes) for row in rows],
    }
    latest = rows[-1] if rows else None
    child_outputs = (
        (
            NormalizedChildOutput(
                child_key=algorithm_key,
                output_kind="diagnostics",
                signal_label=latest.signal_label,
                score=latest.score,
                confidence=latest.confidence,
                regime_label=str(
                    latest.diagnostics.get("event_window_phase", "inactive")
                ),
                direction=1 if latest.signal_label == "buy" else 0,
                diagnostics={
                    "family": family,
                    "subcategory": subcategory,
                    "catalog_ref": catalog_ref,
                    "reporting_mode": "event_window",
                    **latest.diagnostics,
                },
                reason_codes=latest.reason_codes,
            ),
        )
        if latest is not None
        else ()
    )
    return AlertAlgorithmOutput(
        algorithm_key=algorithm_key,
        points=points,
        derived_series=derived_series,
        summary_metrics={
            "event_point_count": len(rows),
            "active_event_count": sum(1 for row in rows if row.signal_label == "buy"),
        },
        metadata={
            "family": family,
            "subcategory": subcategory,
            "catalog_ref": catalog_ref,
            "supports_composition": True,
            "output_contract_version": "1.0",
            "reporting_mode": "event_window",
            "warmup_period": 1,
        },
        child_outputs=child_outputs,
    )
