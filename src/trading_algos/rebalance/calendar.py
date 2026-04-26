from __future__ import annotations

from datetime import date
from typing import Iterable


def _parse_rebalance_date(timestamp: str) -> date:
    return date.fromisoformat(str(timestamp)[:10])


def select_rebalance_timestamps(
    timestamps: Iterable[str], *, frequency: str = "monthly"
) -> tuple[str, ...]:
    normalized = sorted({str(timestamp)[:10] for timestamp in timestamps})
    if frequency == "all":
        return tuple(normalized)
    selected: list[str] = []
    bucket: tuple[int, int] | tuple[int, int, int]
    last_bucket: tuple[int, int] | tuple[int, int, int] | None = None
    for timestamp in normalized:
        parsed_timestamp = _parse_rebalance_date(timestamp)
        if frequency == "weekly":
            iso_year, iso_week, _iso_weekday = parsed_timestamp.isocalendar()
            bucket = (iso_year, iso_week)
        else:
            bucket = (parsed_timestamp.year, parsed_timestamp.month, 1)
        if bucket != last_bucket:
            selected.append(timestamp)
            last_bucket = bucket
    return tuple(selected)
