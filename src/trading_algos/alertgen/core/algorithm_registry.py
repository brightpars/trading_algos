from __future__ import annotations

from trading_algos.algorithmspec.models import AlertAlgorithmSpec
from trading_algos.algorithmspec.registry import (
    get_algorithm_spec_by_key,
    list_algorithm_specs,
    register_algorithm,
)


def register_alert_algorithm(spec: AlertAlgorithmSpec) -> AlertAlgorithmSpec:
    return register_algorithm(spec)


def list_alert_algorithm_specs() -> list[AlertAlgorithmSpec]:
    return list_algorithm_specs()


def get_alert_algorithm_spec_by_key(alg_key: str) -> AlertAlgorithmSpec:
    return get_algorithm_spec_by_key(alg_key)
