from __future__ import annotations

from trading_algos.algorithmspec.models import AlgorithmSpec


_ALGORITHM_SPECS_BY_KEY: dict[str, AlgorithmSpec] = {}


def register_algorithm(spec: AlgorithmSpec) -> AlgorithmSpec:
    existing_by_key = _ALGORITHM_SPECS_BY_KEY.get(spec.key)
    if existing_by_key is not None:
        raise ValueError(f"algorithm key {spec.key} is already registered")
    _ALGORITHM_SPECS_BY_KEY[spec.key] = spec
    return spec


def list_algorithm_specs() -> list[AlgorithmSpec]:
    return list(_ALGORITHM_SPECS_BY_KEY.values())


def get_algorithm_spec_by_key(alg_key: str) -> AlgorithmSpec:
    normalized_key = str(alg_key).strip()
    try:
        return _ALGORITHM_SPECS_BY_KEY[normalized_key]
    except KeyError as exc:
        raise ValueError(f"sensor_config alg_key={alg_key} is unsupported") from exc
