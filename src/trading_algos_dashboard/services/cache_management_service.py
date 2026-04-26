from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from trading_algos_dashboard.services.chart_service import (
    normalize_interactive_payloads,
)
from trading_algos_dashboard.services.data_source_service import (
    MarketDataSourceService,
)
from trading_algos_dashboard.services.market_data_cache import CachedMarketData
from trading_algos_dashboard.services.market_data_cache import LayeredMarketDataCache


@dataclass(frozen=True)
class CacheEntryView:
    symbol: str
    start: datetime
    end: datetime
    candle_count: int
    in_memory: bool
    in_shared: bool
    memory_stored_at: datetime | None
    shared_stored_at: datetime | None
    shared_ttl_hours: int | None
    shared_expires_at: datetime | None
    chart_payload: dict[str, Any] | None


class CacheManagementService:
    def __init__(
        self,
        *,
        market_data_cache: LayeredMarketDataCache,
        data_source_service: MarketDataSourceService,
    ) -> None:
        self.market_data_cache = market_data_cache
        self.data_source_service = data_source_service

    def list_entries(self) -> list[CacheEntryView]:
        memory_entries = {
            self._entry_key(entry): entry
            for entry in self.market_data_cache.list_memory_entries()
        }
        shared_entries = {
            self._entry_key(entry): entry
            for entry in self.market_data_cache.list_shared_entries()
        }
        combined_keys = sorted(
            {*memory_entries.keys(), *shared_entries.keys()},
            key=lambda item: (item[0], item[1], item[2]),
        )
        ttl_hours = None
        if self.market_data_cache.shared_cache is not None:
            ttl_hours = self.market_data_cache.shared_cache.ttl_hours
        entries: list[CacheEntryView] = []
        for key in combined_keys:
            memory_entry = memory_entries.get(key)
            shared_entry = shared_entries.get(key)
            reference_entry = memory_entry or shared_entry
            if reference_entry is None:
                continue
            shared_expires_at = None
            if shared_entry is not None and ttl_hours is not None:
                shared_expires_at = shared_entry.stored_at + timedelta(hours=ttl_hours)
            entries.append(
                CacheEntryView(
                    symbol=reference_entry.key.symbol,
                    start=reference_entry.key.start,
                    end=reference_entry.key.end,
                    candle_count=reference_entry.candle_count,
                    in_memory=memory_entry is not None,
                    in_shared=shared_entry is not None,
                    memory_stored_at=(
                        memory_entry.stored_at if memory_entry is not None else None
                    ),
                    shared_stored_at=(
                        shared_entry.stored_at if shared_entry is not None else None
                    ),
                    shared_ttl_hours=ttl_hours if shared_entry is not None else None,
                    shared_expires_at=shared_expires_at,
                    chart_payload=self._build_chart_payload(reference_entry),
                )
            )
        return entries

    def fill_entry(
        self, *, symbol: str, start: datetime, end: datetime
    ) -> CacheEntryView:
        result = self.data_source_service.fetch_candles(
            symbol=symbol,
            start=start,
            end=end,
        )
        for entry in self.list_entries():
            if (
                entry.symbol == result.symbol
                and entry.start == result.start
                and entry.end == result.end
            ):
                return entry
        raise ValueError("Cache entry was filled but could not be loaded")

    def delete_entry(
        self, *, symbol: str, start: datetime, end: datetime
    ) -> dict[str, bool]:
        return self.market_data_cache.delete(symbol=symbol, start=start, end=end)

    @staticmethod
    def parse_datetime_local(value: str) -> datetime:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is not None:
            return parsed.astimezone(timezone.utc)
        return parsed

    @staticmethod
    def _entry_key(entry: CachedMarketData) -> tuple[str, datetime, datetime]:
        return (entry.key.symbol, entry.key.start, entry.key.end)

    def _build_chart_payload(self, entry: CachedMarketData) -> dict[str, Any] | None:
        if not entry.candles:
            return None
        x_values: list[str] = []
        close_values: list[float] = []
        for candle in entry.candles:
            ts_value = candle.get("ts")
            close_value = candle.get("Close")
            if ts_value is None or close_value is None:
                continue
            x_values.append(str(ts_value))
            try:
                close_values.append(float(close_value))
            except (TypeError, ValueError):
                x_values.pop()
        if not x_values:
            return None
        payloads = normalize_interactive_payloads(
            [
                (
                    {
                        "data": [
                            {
                                "x": x_values,
                                "y": close_values,
                                "type": "scatter",
                                "mode": "lines",
                                "name": entry.key.symbol,
                            }
                        ],
                        "layout": {
                            "title": f"{entry.key.symbol} cached candles",
                            "margin": {"t": 40, "r": 20, "b": 40, "l": 50},
                            "height": 320,
                        },
                        "config": {"responsive": True, "displayModeBar": False},
                    },
                    "close price chart",
                )
            ]
        )
        return payloads[0]["payload"] if payloads else None
