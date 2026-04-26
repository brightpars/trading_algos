from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from trading_algos_dashboard.services.backtrace_models import (
    BacktraceBatchResultDict,
    BacktraceResultDict,
)


class BacktraceRunner(Protocol):
    def run_backtrace(self, request: dict[str, Any]) -> BacktraceResultDict: ...

    def run_backtrace_batch(
        self, request: dict[str, Any]
    ) -> BacktraceBatchResultDict: ...


class BacktraceSessionReader(Protocol):
    def get_run(self, run_id: str) -> dict[str, Any] | None: ...

    def list_recent_runs(self, *, limit: int = 20) -> list[dict[str, Any]]: ...


class BacktraceClientService:
    def __init__(
        self,
        *,
        runtime_service: BacktraceRunner,
        backtrace_session_repository: BacktraceSessionReader,
    ) -> None:
        self._runtime_service = runtime_service
        self._backtrace_session_repository = backtrace_session_repository

    def submit_run(self, payload: Mapping[str, object]) -> dict[str, Any]:
        result = self._runtime_service.run_backtrace(dict(payload))
        if result.get("status") == "failed" and self._is_validation_error(
            result.get("error")
        ):
            raise ValueError(str(result.get("error") or "Invalid backtrace request"))
        persisted = self._backtrace_session_repository.get_run(str(result["run_id"]))
        if persisted is None:
            raise RuntimeError(
                "backtrace_client_service: persisted run missing; run_id="
                f"{result['run_id']}"
            )
        return self._serialize_run_detail(persisted)

    def submit_batch(self, payload: Mapping[str, object]) -> dict[str, Any]:
        result = self._runtime_service.run_backtrace_batch(dict(payload))
        serialized_items: list[dict[str, Any]] = []
        for item in result["items"]:
            persisted = self._backtrace_session_repository.get_run(str(item["run_id"]))
            if persisted is None:
                serialized_items.append(
                    {
                        "run_id": item["run_id"],
                        "request_id": item["request_id"],
                        "status": item["status"],
                        "algorithm_key": item["algorithm_key"],
                        "symbol": item["symbol"],
                        "input_summary": dict(item["input_summary"]),
                        "result_summary": self._build_result_summary(item),
                        "error": item["error"],
                        "metadata": {},
                        "created_at": item["started_at"],
                        "started_at": item["started_at"],
                        "finished_at": item["finished_at"],
                        "request": None,
                        "full_result": dict(item),
                    }
                )
                continue
            serialized_items.append(self._serialize_run_detail(persisted))

        return {
            "status": result["status"],
            "item_count": result["item_count"],
            "success_count": result["success_count"],
            "failure_count": result["failure_count"],
            "items": serialized_items,
            "started_at": result["started_at"],
            "finished_at": result["finished_at"],
        }

    def list_runs(self, *, limit: int = 20) -> dict[str, object]:
        runs = self._backtrace_session_repository.list_recent_runs(limit=limit)
        return {
            "items": [self._serialize_run_summary(run) for run in runs],
            "count": len(runs),
        }

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        payload = self._backtrace_session_repository.get_run(run_id)
        if payload is None:
            return None
        return self._serialize_run_detail(payload)

    @staticmethod
    def _is_validation_error(error: object) -> bool:
        if not isinstance(error, str):
            return False
        return error.startswith(
            (
                "Backtrace request ",
                "Candle #",
                "Optional string field must be a string",
            )
        )

    @staticmethod
    def _serialize_run_summary(run: Mapping[str, Any]) -> dict[str, Any]:
        request = run.get("request")
        metadata: dict[str, Any] = {}
        if isinstance(request, Mapping):
            raw_metadata = request.get("metadata")
            if isinstance(raw_metadata, Mapping):
                metadata = dict(raw_metadata)
        return {
            "run_id": run.get("run_id"),
            "request_id": run.get("request_id"),
            "status": run.get("status"),
            "algorithm_key": run.get("algorithm_key"),
            "symbol": run.get("symbol"),
            "input_summary": dict(run.get("input_summary") or {}),
            "result_summary": dict(run.get("result_summary") or {}),
            "error": run.get("error"),
            "metadata": metadata,
            "created_at": run.get("created_at"),
            "started_at": run.get("started_at"),
            "finished_at": run.get("finished_at"),
        }

    @classmethod
    def _serialize_run_detail(cls, run: Mapping[str, Any]) -> dict[str, Any]:
        payload = cls._serialize_run_summary(run)
        request = run.get("request")
        full_result = run.get("full_result")
        payload["request"] = dict(request) if isinstance(request, Mapping) else None
        payload["full_result"] = (
            dict(full_result) if isinstance(full_result, Mapping) else full_result
        )
        return payload

    @staticmethod
    def _build_result_summary(result: Mapping[str, Any]) -> dict[str, Any]:
        signal_summary = result.get("signal_summary")
        if not isinstance(signal_summary, Mapping):
            signal_summary = {}
        execution_steps = result.get("execution_steps")
        step_count = len(execution_steps) if isinstance(execution_steps, list) else 0
        report = result.get("report")
        chart_payload = result.get("chart_payload")
        return {
            "status": result.get("status"),
            "total_rows": signal_summary.get("total_rows"),
            "buy_count": signal_summary.get("buy_count"),
            "sell_count": signal_summary.get("sell_count"),
            "execution_step_count": step_count,
            "has_report": bool(report),
            "has_chart_payload": bool(chart_payload),
        }
