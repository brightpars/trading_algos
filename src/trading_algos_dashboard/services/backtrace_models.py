from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, NotRequired, TypedDict


RequiredCandleField = Literal["ts", "Open", "High", "Low", "Close"]
ResultStatus = Literal["completed", "failed"]
BatchResultStatus = Literal["completed", "partial_failure", "failed"]
BacktraceInputMode = Literal["inline_candles", "data_source"]


class BacktraceDataSourceDict(TypedDict):
    kind: str


class BacktraceCandleDict(TypedDict):
    ts: Any
    Open: Any
    High: Any
    Low: Any
    Close: Any
    Volume: NotRequired[Any]


class BacktraceRequestDict(TypedDict):
    algorithm_key: str
    algorithm_params: NotRequired[dict[str, Any]]
    symbol: str
    candles: NotRequired[list[BacktraceCandleDict]]
    data_source: NotRequired[BacktraceDataSourceDict]
    start_at: NotRequired[str]
    end_at: NotRequired[str]
    buy: NotRequired[bool]
    sell: NotRequired[bool]
    request_id: NotRequired[str]
    report_base_path: NotRequired[str]
    metadata: NotRequired[dict[str, Any]]


class BacktraceBatchRequestDict(TypedDict):
    items: list[BacktraceRequestDict]


class BacktraceResultDict(TypedDict):
    status: ResultStatus
    run_id: str
    request_id: str | None
    algorithm_key: str
    symbol: str
    input_summary: dict[str, Any]
    signal_summary: dict[str, Any]
    evaluation_summary: dict[str, Any]
    report: dict[str, Any]
    chart_payload: dict[str, Any]
    execution_steps: list[dict[str, Any]]
    error: str | None
    started_at: str
    finished_at: str


class BacktraceBatchResultDict(TypedDict):
    status: BatchResultStatus
    item_count: int
    success_count: int
    failure_count: int
    items: list[BacktraceResultDict]
    started_at: str
    finished_at: str


@dataclass(frozen=True)
class BacktraceCandle:
    ts: Any
    open: Any
    high: Any
    low: Any
    close: Any
    volume: Any | None = None

    def to_transport_dict(self) -> BacktraceCandleDict:
        payload: BacktraceCandleDict = {
            "ts": self.ts,
            "Open": self.open,
            "High": self.high,
            "Low": self.low,
            "Close": self.close,
        }
        if self.volume is not None:
            payload["Volume"] = self.volume
        return payload


@dataclass(frozen=True)
class BacktraceDataSource:
    kind: str

    def to_transport_dict(self) -> BacktraceDataSourceDict:
        return {"kind": self.kind}


@dataclass(frozen=True)
class BacktraceRequest:
    algorithm_key: str
    algorithm_params: dict[str, Any]
    symbol: str
    candles: list[BacktraceCandle]
    input_mode: BacktraceInputMode
    data_source: BacktraceDataSource | None
    start_at: str | None
    end_at: str | None
    buy: bool
    sell: bool
    request_id: str | None
    report_base_path: str | None
    metadata: dict[str, Any]

    def to_transport_dict(self) -> BacktraceRequestDict:
        payload: BacktraceRequestDict = {
            "algorithm_key": self.algorithm_key,
            "algorithm_params": dict(self.algorithm_params),
            "symbol": self.symbol,
            "candles": [candle.to_transport_dict() for candle in self.candles],
            "buy": self.buy,
            "sell": self.sell,
            "metadata": dict(self.metadata),
        }
        if self.data_source is not None:
            payload["data_source"] = self.data_source.to_transport_dict()
        if self.start_at is not None:
            payload["start_at"] = self.start_at
        if self.end_at is not None:
            payload["end_at"] = self.end_at
        if self.request_id is not None:
            payload["request_id"] = self.request_id
        if self.report_base_path is not None:
            payload["report_base_path"] = self.report_base_path
        return payload


@dataclass(frozen=True)
class BacktraceResult:
    status: ResultStatus
    run_id: str
    request_id: str | None
    algorithm_key: str
    symbol: str
    input_summary: dict[str, Any]
    signal_summary: dict[str, Any]
    evaluation_summary: dict[str, Any]
    report: dict[str, Any]
    chart_payload: dict[str, Any]
    execution_steps: list[dict[str, Any]]
    error: str | None
    started_at: str
    finished_at: str

    def to_transport_dict(self) -> BacktraceResultDict:
        return {
            "status": self.status,
            "run_id": self.run_id,
            "request_id": self.request_id,
            "algorithm_key": self.algorithm_key,
            "symbol": self.symbol,
            "input_summary": dict(self.input_summary),
            "signal_summary": dict(self.signal_summary),
            "evaluation_summary": dict(self.evaluation_summary),
            "report": dict(self.report),
            "chart_payload": dict(self.chart_payload),
            "execution_steps": [dict(step) for step in self.execution_steps],
            "error": self.error,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


@dataclass(frozen=True)
class BacktraceBatchResult:
    status: BatchResultStatus
    item_count: int
    success_count: int
    failure_count: int
    items: list[BacktraceResult]
    started_at: str
    finished_at: str

    def to_transport_dict(self) -> BacktraceBatchResultDict:
        return {
            "status": self.status,
            "item_count": self.item_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "items": [item.to_transport_dict() for item in self.items],
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }
