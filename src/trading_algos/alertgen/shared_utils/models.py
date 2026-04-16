from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Candle:
    ts: Any
    open: float
    high: float
    low: float
    close: float
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "Candle":
        return cls(
            ts=data.get("ts"),
            open=float(data["Open"]),
            high=float(data["High"]),
            low=float(data["Low"]),
            close=float(data["Close"]),
            extra={
                key: value
                for key, value in data.items()
                if key not in {"ts", "Open", "High", "Low", "Close"}
            },
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "ts": self.ts,
            "Open": self.open,
            "High": self.high,
            "Low": self.low,
            "Close": self.close,
            **self.extra,
        }


@dataclass(frozen=True)
class AlgorithmDecision:
    trend: str
    confidence: float
    buy_signal: bool
    sell_signal: bool
    buy_range_signal: bool = False
    sell_range_signal: bool = False
    no_signal: bool = False
    annotations: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AlgorithmMetadata:
    alg_name: str
    symbol: str
    date: str
    evaluate_window_len: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "alg_name": self.alg_name,
            "symbol": self.symbol,
            "date": self.date,
            "evaluate_window_len": self.evaluate_window_len,
        }


@dataclass(frozen=True)
class EvaluationSummary:
    metrics: dict[str, int]


@dataclass(frozen=True)
class AnalysisReportData:
    data: list[dict[str, Any]]
    eval_dict: dict[str, Any]
