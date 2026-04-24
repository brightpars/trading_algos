from __future__ import annotations

from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable


def parse_event_timestamp(value: str) -> datetime:
    normalized = value.strip().replace("T", " ")
    if len(normalized) == 10:
        normalized = f"{normalized} 00:00:00"
    return datetime.fromisoformat(normalized)


def normalize_public_timestamp(row: dict[str, Any]) -> datetime:
    explicit_public_timestamp = row.get("public_timestamp")
    if isinstance(explicit_public_timestamp, str) and explicit_public_timestamp.strip():
        return parse_event_timestamp(explicit_public_timestamp)
    return parse_event_timestamp(str(row["event_timestamp"]))


@dataclass(frozen=True)
class EventRecord:
    symbol: str
    event_timestamp: str
    public_timestamp: str
    event_type: str
    source: str
    metadata: dict[str, Any]

    @property
    def event_dt(self) -> datetime:
        return parse_event_timestamp(self.event_timestamp)

    @property
    def public_dt(self) -> datetime:
        return parse_event_timestamp(self.public_timestamp)


class EventCalendar:
    def __init__(self, records_by_symbol: dict[str, tuple[EventRecord, ...]]) -> None:
        self._records_by_symbol = records_by_symbol
        self._public_timestamps_by_symbol = {
            symbol: tuple(record.public_dt for record in records)
            for symbol, records in records_by_symbol.items()
        }

    @classmethod
    def from_rows(cls, rows: Iterable[dict[str, Any]]) -> EventCalendar:
        records_by_symbol: dict[str, list[EventRecord]] = {}
        for raw_row in rows:
            symbol = str(raw_row["symbol"])
            event_timestamp = str(raw_row["event_timestamp"])
            public_dt = normalize_public_timestamp(raw_row)
            record = EventRecord(
                symbol=symbol,
                event_timestamp=event_timestamp,
                public_timestamp=public_dt.isoformat(sep=" "),
                event_type=str(raw_row.get("event_type", "earnings")),
                source=str(raw_row.get("source", "manifest_fixture")),
                metadata=dict(raw_row),
            )
            records_by_symbol.setdefault(symbol, []).append(record)
        normalized = {
            symbol: tuple(sorted(records, key=lambda record: record.public_dt))
            for symbol, records in records_by_symbol.items()
        }
        return cls(normalized)

    def records_for_symbol(self, symbol: str) -> tuple[EventRecord, ...]:
        return self._records_by_symbol.get(symbol, ())

    def latest_public_event(
        self, symbol: str, timestamp: datetime
    ) -> EventRecord | None:
        records = self.records_for_symbol(symbol)
        public_timestamps = self._public_timestamps_by_symbol.get(symbol, ())
        if not records:
            return None
        index = bisect_right(public_timestamps, timestamp) - 1
        if index < 0:
            return None
        return records[index]

    def next_public_event(self, symbol: str, timestamp: datetime) -> EventRecord | None:
        records = self.records_for_symbol(symbol)
        public_timestamps = self._public_timestamps_by_symbol.get(symbol, ())
        if not records:
            return None
        index = bisect_left(public_timestamps, timestamp)
        if index >= len(records):
            return None
        return records[index]

    def events_between(
        self,
        symbol: str,
        *,
        start_timestamp: datetime,
        end_timestamp: datetime,
    ) -> tuple[EventRecord, ...]:
        records = self.records_for_symbol(symbol)
        public_timestamps = self._public_timestamps_by_symbol.get(symbol, ())
        if not records:
            return ()
        start_index = bisect_left(public_timestamps, start_timestamp)
        end_index = bisect_right(public_timestamps, end_timestamp)
        return records[start_index:end_index]
