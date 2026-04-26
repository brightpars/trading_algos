from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from trading_algos_dashboard.services.backtrace_models import (
    BacktraceCandle,
    BacktraceRequest,
    BacktraceResult,
    BacktraceResultDict,
    RequiredCandleField,
)


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

    def run_backtrace(self, request: dict[str, Any]) -> BacktraceResultDict:
        started_at = self._utc_now()
        run_id = self._new_run_id()
        request_id = request.get("request_id") if isinstance(request, dict) else None
        try:
            normalized_request = self._normalize_request(request)
        except ValueError as exc:
            finished_at = self._utc_now()
            return BacktraceResult(
                status="failed",
                run_id=run_id,
                request_id=self._safe_optional_string(request_id),
                algorithm_key=self._normalize_string_field_if_present(
                    request, "algorithm_key"
                ),
                symbol=self._normalize_string_field_if_present(request, "symbol"),
                input_summary=self._failed_input_summary(request),
                result_payload={},
                error=str(exc),
                started_at=started_at,
                finished_at=finished_at,
            ).to_transport_dict()

        finished_at = self._utc_now()
        result_payload = self._build_placeholder_result_payload(normalized_request)
        return BacktraceResult(
            status="completed",
            run_id=run_id,
            request_id=normalized_request.request_id,
            algorithm_key=normalized_request.algorithm_key,
            symbol=normalized_request.symbol,
            input_summary=self._build_input_summary(normalized_request),
            result_payload=result_payload,
            error=None,
            started_at=started_at,
            finished_at=finished_at,
        ).to_transport_dict()

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

    def _build_placeholder_result_payload(
        self, request: BacktraceRequest
    ) -> dict[str, Any]:
        return {
            "execution_mode": "local_stub",
            "buy_enabled": request.buy,
            "sell_enabled": request.sell,
            "candles_processed": len(request.candles),
            "signals": [],
            "artifacts": {},
            "summary": {
                "message": "Backtrace execution is not wired yet",
                "algorithm_params": dict(request.algorithm_params),
                "metadata": dict(request.metadata),
            },
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
