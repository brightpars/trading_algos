from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Protocol
from uuid import uuid4

from trading_algos.alertgen import get_alert_algorithm_spec_by_key
from trading_algos.alertgen.core.validation import normalize_alertgen_sensor_config
from trading_algos_dashboard.services.backtrace_models import (
    BacktraceCandle,
    BacktraceRequest,
    BacktraceResult,
    BacktraceResultDict,
    RequiredCandleField,
)
from trading_algos_dashboard.services.algorithm_runner_service import (
    run_alert_algorithm,
)


class BacktraceSessionStore(Protocol):
    def create_session(self, document: dict[str, Any]) -> dict[str, Any]: ...

    def update_session(self, run_id: str, values: dict[str, Any]) -> None: ...


class EnginesControlRuntimeService:
    _REQUIRED_REQUEST_FIELDS: tuple[str, ...] = (
        "algorithm_key",
        "symbol",
        "candles",
    )
    _REQUIRED_CANDLE_FIELDS: tuple[RequiredCandleField, ...] = (
        "ts",
        "Open",
        "High",
        "Low",
        "Close",
    )

    def __init__(
        self,
        *,
        backtrace_session_repository: BacktraceSessionStore | None = None,
    ) -> None:
        self._backtrace_session_repository = backtrace_session_repository

    def run_backtrace(self, request: dict[str, Any]) -> BacktraceResultDict:
        started_at = self._utc_now()
        run_id = self._new_run_id()
        request_id = request.get("request_id") if isinstance(request, dict) else None
        self._create_run_record(
            run_id=run_id,
            request=request,
            request_id=request_id,
            created_at=started_at,
        )
        try:
            normalized_request = self._normalize_request(request)
            execution_result = self._execute_backtrace(normalized_request)
        except ValueError as exc:
            finished_at = self._utc_now()
            result = BacktraceResult(
                status="failed",
                run_id=run_id,
                request_id=self._safe_optional_string(request_id),
                algorithm_key=self._normalize_string_field_if_present(
                    request, "algorithm_key"
                ),
                symbol=self._normalize_string_field_if_present(request, "symbol"),
                input_summary=self._failed_input_summary(request),
                signal_summary={},
                evaluation_summary={},
                report={},
                chart_payload={},
                execution_steps=[],
                error=str(exc),
                started_at=started_at,
                finished_at=finished_at,
            ).to_transport_dict()
            self._mark_run_failed(result)
            return result
        except Exception as exc:
            finished_at = self._utc_now()
            result = BacktraceResult(
                status="failed",
                run_id=run_id,
                request_id=self._safe_optional_string(request_id),
                algorithm_key=self._normalize_string_field_if_present(
                    request, "algorithm_key"
                ),
                symbol=self._normalize_string_field_if_present(request, "symbol"),
                input_summary=self._failed_input_summary(request),
                signal_summary={},
                evaluation_summary={},
                report={},
                chart_payload={},
                execution_steps=[],
                error=str(exc),
                started_at=started_at,
                finished_at=finished_at,
            ).to_transport_dict()
            self._mark_run_failed(result)
            return result

        finished_at = self._utc_now()
        result = BacktraceResult(
            status="completed",
            run_id=run_id,
            request_id=normalized_request.request_id,
            algorithm_key=normalized_request.algorithm_key,
            symbol=normalized_request.symbol,
            input_summary=self._build_input_summary(normalized_request),
            signal_summary=dict(execution_result["signal_summary"]),
            evaluation_summary=dict(execution_result["evaluation_summary"]),
            report=dict(execution_result["report"]),
            chart_payload=dict(execution_result["chart_payload"]),
            execution_steps=list(execution_result["execution_steps"]),
            error=None,
            started_at=started_at,
            finished_at=finished_at,
        ).to_transport_dict()
        self._mark_run_completed(request=normalized_request, result=result)
        return result

    def _create_run_record(
        self,
        *,
        run_id: str,
        request: Any,
        request_id: Any,
        created_at: str,
    ) -> None:
        if self._backtrace_session_repository is None:
            return
        self._backtrace_session_repository.create_session(
            {
                "run_id": run_id,
                "request_id": self._safe_optional_string(request_id),
                "status": "running",
                "algorithm_key": self._normalize_string_field_if_present(
                    request, "algorithm_key"
                ),
                "symbol": self._normalize_string_field_if_present(request, "symbol"),
                "request": self._normalize_transport_value(request),
                "input_summary": self._failed_input_summary(request),
                "result_summary": {},
                "full_result": None,
                "error": None,
                "created_at": created_at,
                "started_at": created_at,
                "finished_at": None,
            }
        )

    def _mark_run_completed(
        self, *, request: BacktraceRequest, result: BacktraceResultDict
    ) -> None:
        if self._backtrace_session_repository is None:
            return
        self._backtrace_session_repository.update_session(
            result["run_id"],
            {
                "status": "completed",
                "algorithm_key": request.algorithm_key,
                "symbol": request.symbol,
                "request": self._normalize_transport_value(request.to_transport_dict()),
                "input_summary": dict(result["input_summary"]),
                "result_summary": self._build_result_summary(result),
                "full_result": self._normalize_transport_value(result),
                "error": None,
                "finished_at": result["finished_at"],
            },
        )

    def _mark_run_failed(self, result: BacktraceResultDict) -> None:
        if self._backtrace_session_repository is None:
            return
        self._backtrace_session_repository.update_session(
            result["run_id"],
            {
                "status": "failed",
                "algorithm_key": result["algorithm_key"],
                "symbol": result["symbol"],
                "input_summary": dict(result["input_summary"]),
                "result_summary": {},
                "full_result": self._normalize_transport_value(result),
                "error": result["error"],
                "finished_at": result["finished_at"],
            },
        )

    def _build_result_summary(self, result: BacktraceResultDict) -> dict[str, Any]:
        signal_summary = result["signal_summary"]
        return {
            "status": result["status"],
            "total_rows": signal_summary.get("total_rows"),
            "buy_count": signal_summary.get("buy_count"),
            "sell_count": signal_summary.get("sell_count"),
            "execution_step_count": len(result["execution_steps"]),
            "has_report": bool(result["report"]),
            "has_chart_payload": bool(result["chart_payload"]),
        }

    def _execute_backtrace(self, request: BacktraceRequest) -> dict[str, Any]:
        report_base_path = request.report_base_path
        if report_base_path is not None:
            return self._run_alert_algorithm(
                request=request,
                report_base_path=report_base_path,
            )

        with TemporaryDirectory(prefix="engines-control-backtrace-") as temp_dir:
            return self._run_alert_algorithm(
                request=request,
                report_base_path=temp_dir,
            )

    def _run_alert_algorithm(
        self, *, request: BacktraceRequest, report_base_path: str
    ) -> dict[str, Any]:
        algorithm_spec = get_alert_algorithm_spec_by_key(request.algorithm_key)
        sensor_config = normalize_alertgen_sensor_config(
            {
                "symbol": request.symbol,
                "alg_key": request.algorithm_key,
                "alg_param": {
                    **dict(algorithm_spec.default_param),
                    **dict(request.algorithm_params),
                },
                "buy": request.buy,
                "sell": request.sell,
            }
        )
        execution_result = run_alert_algorithm(
            sensor_config=sensor_config,
            report_base_path=report_base_path,
            candles=[dict(candle.to_transport_dict()) for candle in request.candles],
        )
        report = self._normalize_transport_value(execution_result["report"])
        return {
            "signal_summary": self._normalize_transport_value(
                execution_result["signal_summary"]
            ),
            "evaluation_summary": self._normalize_transport_value(
                report.get("evaluation_summary", {})
            ),
            "report": report,
            "chart_payload": self._normalize_transport_value(
                execution_result["chart_payload"]
            ),
            "execution_steps": self._normalize_execution_steps(
                execution_result.get("execution_steps", [])
            ),
        }

    def _normalize_request(self, request: dict[str, Any]) -> BacktraceRequest:
        if not isinstance(request, dict):
            raise ValueError("Backtrace request must be a JSON object")

        self._validate_required_fields(request)
        algorithm_key = self._require_non_empty_string(request, "algorithm_key")
        symbol = self._require_non_empty_string(request, "symbol")
        candles = self._normalize_candles(request["candles"])
        algorithm_params = self._normalize_optional_dict(
            request.get("algorithm_params"),
            field_name="algorithm_params",
        )
        metadata = self._normalize_optional_dict(
            request.get("metadata"),
            field_name="metadata",
        )

        return BacktraceRequest(
            algorithm_key=algorithm_key,
            algorithm_params=algorithm_params,
            symbol=symbol,
            candles=candles,
            buy=self._normalize_optional_bool(
                request.get("buy"), field_name="buy", default=True
            ),
            sell=self._normalize_optional_bool(
                request.get("sell"), field_name="sell", default=True
            ),
            request_id=self._normalize_optional_string(request.get("request_id")),
            report_base_path=self._normalize_optional_string(
                request.get("report_base_path")
            ),
            metadata=metadata,
        )

    def _validate_required_fields(self, request: dict[str, Any]) -> None:
        for field_name in self._REQUIRED_REQUEST_FIELDS:
            if field_name not in request:
                raise ValueError(
                    f"Backtrace request is missing required field: {field_name}"
                )

    def _normalize_candles(self, candles: Any) -> list[BacktraceCandle]:
        if not isinstance(candles, list):
            raise ValueError("Backtrace request field candles must be a list")

        normalized: list[BacktraceCandle] = []
        for index, candle in enumerate(candles):
            if not isinstance(candle, dict):
                raise ValueError(f"Candle #{index} must be a JSON object")
            for field_name in self._REQUIRED_CANDLE_FIELDS:
                if field_name not in candle:
                    raise ValueError(
                        f"Candle #{index} is missing required field: {field_name}"
                    )
            normalized.append(
                BacktraceCandle(
                    ts=candle["ts"],
                    open=candle["Open"],
                    high=candle["High"],
                    low=candle["Low"],
                    close=candle["Close"],
                    volume=candle.get("Volume"),
                )
            )
        return normalized

    def _normalize_optional_dict(
        self, value: Any, *, field_name: str
    ) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValueError(
                f"Backtrace request field {field_name} must be a JSON object"
            )
        return dict(value)

    def _normalize_optional_bool(
        self, value: Any, *, field_name: str, default: bool
    ) -> bool:
        if value is None:
            return default
        if not isinstance(value, bool):
            raise ValueError(f"Backtrace request field {field_name} must be a boolean")
        return value

    def _normalize_optional_string(self, value: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Optional string field must be a string when provided")
        normalized = value.strip()
        return normalized or None

    def _safe_optional_string(self, value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        normalized = value.strip()
        return normalized or None

    def _require_non_empty_string(
        self, request: dict[str, Any], field_name: str
    ) -> str:
        value = request.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"Backtrace request field {field_name} must be a non-empty string"
            )
        return value.strip()

    def _build_input_summary(self, request: BacktraceRequest) -> dict[str, Any]:
        return {
            "candle_count": len(request.candles),
            "buy_enabled": request.buy,
            "sell_enabled": request.sell,
            "has_report_base_path": request.report_base_path is not None,
            "algorithm_param_keys": sorted(request.algorithm_params.keys()),
            "metadata_keys": sorted(request.metadata.keys()),
        }

    def _failed_input_summary(self, request: Any) -> dict[str, Any]:
        if not isinstance(request, dict):
            return {"request_type": type(request).__name__}
        candles = request.get("candles")
        candle_count = len(candles) if isinstance(candles, list) else None
        return {
            "provided_keys": sorted(request.keys()),
            "candle_count": candle_count,
        }

    def _normalize_string_field_if_present(self, request: Any, field_name: str) -> str:
        if not isinstance(request, dict):
            return ""
        value = request.get(field_name)
        if not isinstance(value, str):
            return ""
        return value.strip()

    def _new_run_id(self) -> str:
        return str(uuid4())

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _normalize_execution_steps(self, steps: Any) -> list[dict[str, Any]]:
        if not isinstance(steps, list):
            return []
        normalized_steps: list[dict[str, Any]] = []
        for step in steps:
            if not isinstance(step, dict):
                continue
            normalized_steps.append(self._normalize_transport_value(step))
        return normalized_steps

    def _normalize_transport_value(self, value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, dict):
            return {
                str(key): self._normalize_transport_value(nested_value)
                for key, nested_value in value.items()
            }
        if isinstance(value, list):
            return [self._normalize_transport_value(item) for item in value]
        if isinstance(value, tuple):
            return [self._normalize_transport_value(item) for item in value]
        if isinstance(value, Path):
            return str(value)
        return value
