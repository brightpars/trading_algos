from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


def _normalize_timestamp(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, date):
        return value.isoformat()
    text = str(value)
    return text[:10] if len(text) >= 10 else text


@dataclass(frozen=True)
class PanelRow:
    timestamp: str
    symbol: str
    close: float
    open: float | None = None
    high: float | None = None
    low: float | None = None
    volume: float | None = None
    extras: dict[str, Any] | None = None


class MultiAssetPanel:
    def __init__(self, rows: list[PanelRow]) -> None:
        self.rows = list(rows)

    @classmethod
    def from_rows(cls, raw_rows: list[dict[str, Any]]) -> "MultiAssetPanel":
        rows: list[PanelRow] = []
        for index, row in enumerate(raw_rows):
            if not isinstance(row, dict):
                raise ValueError(f"panel_dataset: row must be dict; index={index}")
            symbol = str(row.get("symbol", "")).strip()
            if symbol == "":
                raise ValueError(f"panel_dataset: symbol is required; index={index}")
            if "Close" not in row and "close" not in row:
                raise ValueError(
                    f"panel_dataset: close is required; index={index} symbol={symbol}"
                )
            close_value = row.get("Close", row.get("close"))
            if close_value is None:
                raise ValueError(
                    f"panel_dataset: close is required; index={index} symbol={symbol}"
                )
            extra_fields = {
                str(key): value
                for key, value in row.items()
                if key
                not in {
                    "ts",
                    "timestamp",
                    "symbol",
                    "Close",
                    "close",
                    "Open",
                    "High",
                    "Low",
                    "Volume",
                }
            }
            rows.append(
                PanelRow(
                    timestamp=_normalize_timestamp(
                        row.get("ts", row.get("timestamp", index))
                    ),
                    symbol=symbol,
                    close=float(close_value),
                    open=(float(row["Open"]) if row.get("Open") is not None else None),
                    high=(float(row["High"]) if row.get("High") is not None else None),
                    low=(float(row["Low"]) if row.get("Low") is not None else None),
                    volume=(
                        float(row["Volume"]) if row.get("Volume") is not None else None
                    ),
                    extras=extra_fields,
                )
            )
        return cls(rows)

    def symbols(self) -> tuple[str, ...]:
        return tuple(sorted({row.symbol for row in self.rows}))

    def timestamps(self) -> tuple[str, ...]:
        return tuple(sorted({row.timestamp for row in self.rows}))

    def closes_by_symbol(self) -> dict[str, list[tuple[str, float]]]:
        grouped: dict[str, list[tuple[str, float]]] = {}
        for row in sorted(self.rows, key=lambda item: (item.symbol, item.timestamp)):
            grouped.setdefault(row.symbol, []).append((row.timestamp, row.close))
        return grouped

    def universe_on(self, rebalance_timestamp: str) -> tuple[str, ...]:
        eligible = {
            row.symbol for row in self.rows if row.timestamp <= rebalance_timestamp
        }
        return tuple(sorted(eligible))

    def rows_for_symbol_until(
        self, symbol: str, *, timestamp: str
    ) -> tuple[PanelRow, ...]:
        return tuple(
            row
            for row in self.rows
            if row.symbol == symbol and row.timestamp <= timestamp
        )

    def latest_row_by_symbol_on(
        self, timestamp: str, universe: tuple[str, ...] | None = None
    ) -> dict[str, PanelRow]:
        allowed = set(universe) if universe is not None else None
        latest: dict[str, PanelRow] = {}
        for row in sorted(self.rows, key=lambda item: (item.timestamp, item.symbol)):
            if row.timestamp > timestamp:
                continue
            if allowed is not None and row.symbol not in allowed:
                continue
            latest[row.symbol] = row
        return latest
