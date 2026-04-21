from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import Any
from typing import cast

from trading_algos.alertgen.core.algorithm_registry import (
    get_alert_algorithm_spec_by_key,
)
from trading_algos.configuration.models import (
    AlgorithmConfiguration,
    CompatibilityMetadata,
)


def _installed_package_version() -> str:
    try:
        return version("trading_algos")
    except PackageNotFoundError:
        return "0"


def evaluate_configuration_compatibility(
    configuration: AlgorithmConfiguration,
) -> CompatibilityMetadata:
    from trading_algos.alertgen.core.catalog import register_builtin_alert_algorithms

    register_builtin_alert_algorithms()
    messages: list[str] = []
    state = "compatible"
    installed_version = _installed_package_version()

    if configuration.compatibility_metadata.expected_package_name not in {
        "",
        "trading_algos",
    }:
        messages.append("expected_package_name must be trading_algos")
        state = "incompatible"

    minimum_version = configuration.compatibility_metadata.minimum_supported_version
    maximum_version = configuration.compatibility_metadata.maximum_supported_version
    expected_version = configuration.compatibility_metadata.expected_package_version
    if expected_version and expected_version != installed_version:
        messages.append(
            f"expected package version {expected_version} does not match installed {installed_version}"
        )
        state = "warning"
    if minimum_version and installed_version < minimum_version:
        messages.append(
            f"installed package version {installed_version} is below minimum {minimum_version}"
        )
        state = "incompatible"
    if maximum_version and installed_version > maximum_version:
        messages.append(
            f"installed package version {installed_version} is above maximum {maximum_version}"
        )
        state = "incompatible"

    algorithm_refs: set[str] = set()
    for node in configuration.nodes:
        alg_key = getattr(node, "alg_key", None)
        if not alg_key:
            continue
        algorithm_refs.add(str(alg_key))
        try:
            get_alert_algorithm_spec_by_key(str(alg_key))
        except ValueError:
            messages.append(
                f"algorithm {alg_key} is not available in installed package"
            )
            state = "incompatible"

    return CompatibilityMetadata(
        expected_package_name="trading_algos",
        expected_package_version=expected_version,
        minimum_supported_version=minimum_version,
        maximum_supported_version=maximum_version,
        algorithm_refs=tuple(sorted(algorithm_refs)),
        compatibility_state=cast(Any, state),
        compatibility_messages=tuple(messages),
    )
