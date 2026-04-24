from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from trading_algos.events.calendar import (
    EventCalendar,
    EventRecord,
    parse_event_timestamp,
)


@dataclass(frozen=True)
class EventWindowDefinition:
    pre_event_days: int = 0
    post_event_days: int = 0


@dataclass(frozen=True)
class EventWindowState:
    active: bool
    phase: str
    event: EventRecord | None
    anchor_timestamp: str | None
    days_from_event: int | None


def _days_between(left: datetime, right: datetime) -> int:
    return (left.date() - right.date()).days


def resolve_event_window_state(
    *,
    calendar: EventCalendar,
    symbol: str,
    row_timestamp: str,
    window: EventWindowDefinition,
) -> EventWindowState:
    row_dt = parse_event_timestamp(row_timestamp)

    current_event = calendar.latest_public_event(symbol, row_dt)
    if current_event is not None:
        if row_dt >= current_event.event_dt:
            days_after_event = _days_between(row_dt, current_event.event_dt)
            if 0 <= days_after_event <= window.post_event_days:
                return EventWindowState(
                    active=True,
                    phase="post_event",
                    event=current_event,
                    anchor_timestamp=current_event.public_timestamp,
                    days_from_event=days_after_event,
                )
        else:
            days_since_public = _days_between(row_dt, current_event.public_dt)
            if 0 <= days_since_public <= window.pre_event_days:
                return EventWindowState(
                    active=True,
                    phase="pre_event",
                    event=current_event,
                    anchor_timestamp=current_event.public_timestamp,
                    days_from_event=-_days_between(current_event.event_dt, row_dt),
                )

    next_event = calendar.next_public_event(symbol, row_dt)
    if next_event is not None and row_dt >= next_event.public_dt:
        days_since_public = _days_between(row_dt, next_event.public_dt)
        if 0 <= days_since_public <= window.pre_event_days:
            return EventWindowState(
                active=True,
                phase="pre_event",
                event=next_event,
                anchor_timestamp=next_event.public_timestamp,
                days_from_event=-_days_between(next_event.event_dt, row_dt),
            )

    return EventWindowState(
        active=False,
        phase="inactive",
        event=None,
        anchor_timestamp=None,
        days_from_event=None,
    )


def build_event_metadata(
    *,
    state: EventWindowState,
    event_value: float | None,
    event_value_label: str,
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata = {
        "event_window_active": state.active,
        "event_window_phase": state.phase,
        "event_anchor_timestamp": state.anchor_timestamp,
        "event_days_from_anchor": state.days_from_event,
        "event_type": state.event.event_type if state.event is not None else None,
        "event_source": state.event.source if state.event is not None else None,
        event_value_label: event_value,
    }
    if extra_metadata:
        metadata.update(extra_metadata)
    return metadata
