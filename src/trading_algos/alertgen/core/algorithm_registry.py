from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


Normalizer = Callable[[Any, str], Any]
AlgorithmBuilder = Callable[..., Any]


@dataclass(frozen=True)
class AlertAlgorithmSpec:
    key: str
    name: str
    builder: AlgorithmBuilder
    default_param: Any
    param_normalizer: Normalizer
    description: str = ""
    param_schema: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    supports_buy: bool = True
    supports_sell: bool = True
    tags: tuple[str, ...] = field(default_factory=tuple)
    version: str = "1.0"
    category: str = "general"
    warmup_period: int = 1


_ALGORITHM_SPECS_BY_KEY: dict[str, AlertAlgorithmSpec] = {}


def register_alert_algorithm(spec: AlertAlgorithmSpec) -> AlertAlgorithmSpec:
    existing_by_key = _ALGORITHM_SPECS_BY_KEY.get(spec.key)
    if existing_by_key is not None:
        raise ValueError(f"alert algorithm key {spec.key} is already registered")
    _ALGORITHM_SPECS_BY_KEY[spec.key] = spec
    return spec


def list_alert_algorithm_specs() -> list[AlertAlgorithmSpec]:
    return list(_ALGORITHM_SPECS_BY_KEY.values())


def get_alert_algorithm_spec_by_key(alg_key: str) -> AlertAlgorithmSpec:
    normalized_key = str(alg_key).strip()
    try:
        return _ALGORITHM_SPECS_BY_KEY[normalized_key]
    except KeyError as exc:
        raise ValueError(f"sensor_config alg_key={alg_key} is unsupported") from exc
