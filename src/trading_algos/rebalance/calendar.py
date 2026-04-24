from __future__ import annotations

from typing import Iterable


def select_rebalance_timestamps(
    timestamps: Iterable[str], *, frequency: str = "monthly"
) -> tuple[str, ...]:
    normalized = sorted({str(timestamp)[:10] for timestamp in timestamps})
    if frequency == "all":
        return tuple(normalized)
    selected: list[str] = []
    last_bucket: str | None = None
    for timestamp in normalized:
        if frequency == "weekly":
            bucket = timestamp[:8]
        else:
            bucket = timestamp[:7]
        if bucket != last_bucket:
            selected.append(timestamp)
            last_bucket = bucket
    return tuple(selected)
