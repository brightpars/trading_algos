from __future__ import annotations

import json
from collections.abc import Mapping
from json import JSONDecodeError
from typing import Any


class BacktraceDashboardService:
    def __init__(self, *, backtrace_client_service: Any) -> None:
        self._backtrace_client_service = backtrace_client_service

    def default_form_data(self) -> dict[str, str]:
        return {
            "input_mode": "inline_candles",
            "algorithm_key": "",
            "symbol": "",
            "algorithm_params_json": "{}",
            "candles_json": "[]",
            "data_source_kind": "market_data_service",
            "start_at": "",
            "end_at": "",
            "metadata_json": "{}",
        }

    def build_form_data(
        self,
        *,
        saved_form_data: Mapping[str, str] | None = None,
        form_data: Mapping[str, str] | None = None,
    ) -> dict[str, str]:
        payload = self.default_form_data()
        if saved_form_data is not None:
            payload.update(
                {str(key): str(value) for key, value in saved_form_data.items()}
            )
        if form_data is not None:
            payload.update({str(key): str(value) for key, value in form_data.items()})
        return payload

    def submit_run(self, form_data: Mapping[str, str]) -> dict[str, Any]:
        payload = self._build_request_payload(form_data)
        return self._backtrace_client_service.submit_run(payload)

    def list_runs(self, *, limit: int = 20) -> dict[str, object]:
        return self._backtrace_client_service.list_runs(limit=limit)

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        return self._backtrace_client_service.get_run(run_id)

    def _build_request_payload(self, form_data: Mapping[str, str]) -> dict[str, Any]:
        input_mode = str(form_data.get("input_mode", "inline_candles")).strip()
        algorithm_key = str(form_data.get("algorithm_key", "")).strip()
        symbol = str(form_data.get("symbol", "")).strip()
        algorithm_params = self._parse_json_object(
            form_data.get("algorithm_params_json", "{}"),
            field_label="Params JSON",
        )
        metadata = self._parse_json_object(
            form_data.get("metadata_json", "{}"),
            field_label="Metadata JSON",
        )
        payload = {
            "algorithm_key": algorithm_key,
            "symbol": symbol,
            "algorithm_params": algorithm_params,
            "metadata": metadata,
        }
        if input_mode == "inline_candles":
            payload["candles"] = self._parse_json_array(
                form_data.get("candles_json", "[]"),
                field_label="Candles JSON",
            )
            return payload
        if input_mode == "data_source":
            data_source_kind = str(
                form_data.get("data_source_kind", "market_data_service")
            ).strip()
            payload["data_source"] = {"kind": data_source_kind}
            payload["start_at"] = str(form_data.get("start_at", "")).strip()
            payload["end_at"] = str(form_data.get("end_at", "")).strip()
            return payload
        raise ValueError("Input mode must be inline_candles or data_source.")

    @staticmethod
    def _parse_json_object(raw_value: object, *, field_label: str) -> dict[str, Any]:
        parsed = BacktraceDashboardService._parse_json_value(
            raw_value,
            field_label=field_label,
        )
        if not isinstance(parsed, dict):
            raise ValueError(f"{field_label} must decode to a JSON object.")
        return dict(parsed)

    @staticmethod
    def _parse_json_array(raw_value: object, *, field_label: str) -> list[Any]:
        parsed = BacktraceDashboardService._parse_json_value(
            raw_value,
            field_label=field_label,
        )
        if not isinstance(parsed, list):
            raise ValueError(f"{field_label} must decode to a JSON array.")
        return list(parsed)

    @staticmethod
    def _parse_json_value(raw_value: object, *, field_label: str) -> object:
        try:
            return json.loads(str(raw_value or "").strip())
        except JSONDecodeError as exc:
            raise ValueError(f"{field_label} must be valid JSON.") from exc
