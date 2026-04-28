from __future__ import annotations

from typing import Any


def validate_decmaker_engine_payload(
    payload: Any, label: str = "Decision maker engine config"
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a dict/JSON object")

    normalized = dict(payload)
    _validate_required_keys(
        normalized,
        [
            "type",
            "interval_secs",
            "confidence_threshold_buy",
            "confidence_threshold_sell",
            "max_percent_higher_price_buy",
            "max_percent_lower_price_sell",
        ],
        label,
    )

    normalized["type"] = _require_non_empty_string(normalized["type"], f"{label} type")
    if normalized["type"] != "dec1":
        raise ValueError(f"{label} type must be dec1")
    normalized["interval_secs"] = _require_positive_int_like(
        normalized["interval_secs"], f"{label} interval_secs"
    )
    for field_name in [
        "confidence_threshold_buy",
        "confidence_threshold_sell",
        "max_percent_higher_price_buy",
        "max_percent_lower_price_sell",
    ]:
        normalized[field_name] = _require_float_like(
            normalized[field_name], f"{label} field '{field_name}'"
        )
    return normalized


def _validate_required_keys(
    payload: dict[str, Any], required_keys: list[str], label: str
) -> None:
    missing_keys = [key for key in required_keys if key not in payload]
    if missing_keys:
        raise ValueError(f"{label} is missing required keys: {', '.join(missing_keys)}")


def _require_non_empty_string(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string")
    normalized = value.strip()
    if normalized == "":
        raise ValueError(f"{label} is required")
    return normalized


def _require_positive_int_like(value: Any, label: str) -> int:
    try:
        parsed = int(value)
    except Exception as exc:
        raise ValueError(f"{label} must be an integer: {exc}") from exc
    if parsed <= 0:
        raise ValueError(f"{label} must be > 0")
    return parsed


def _require_float_like(value: Any, label: str) -> float:
    try:
        return float(value)
    except Exception as exc:
        raise ValueError(f"{label} must be numeric: {exc}") from exc
