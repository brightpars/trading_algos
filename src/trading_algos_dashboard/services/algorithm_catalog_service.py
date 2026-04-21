from __future__ import annotations

from typing import Any

from trading_algos.alertgen import (
    get_alert_algorithm_spec_by_key,
    list_alert_algorithm_specs,
)


def list_algorithm_catalog() -> list[dict[str, Any]]:
    return [_spec_to_dict(spec) for spec in list_alert_algorithm_specs()]


def get_algorithm_catalog_entry(alg_key: str) -> dict[str, Any]:
    return _spec_to_dict(get_alert_algorithm_spec_by_key(alg_key))


def _spec_to_dict(spec: Any) -> dict[str, Any]:
    return {
        "key": spec.key,
        "name": spec.name,
        "description": spec.description,
        "param_schema": list(spec.param_schema),
        "category": spec.category,
        "tags": list(spec.tags),
        "default_param": spec.default_param,
        "warmup_period": spec.warmup_period,
        "supports_buy": spec.supports_buy,
        "supports_sell": spec.supports_sell,
        "version": spec.version,
    }
