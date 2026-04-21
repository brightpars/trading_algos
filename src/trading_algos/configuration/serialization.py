from __future__ import annotations

from typing import Any
from typing import cast

from trading_algos.configuration.models import (
    AlgorithmConfiguration,
    AlgorithmNode,
    BaseNode,
    CompatibilityMetadata,
    CompositeNode,
    PipelineNode,
)


def _node_from_dict(payload: dict[str, Any]) -> BaseNode:
    node_type = payload.get("node_type")
    common = {
        "node_id": str(payload.get("node_id", "")),
        "node_type": cast(Any, str(node_type)),
        "name": str(payload.get("name", "")),
        "description": str(payload.get("description", "")),
    }
    if node_type == "algorithm":
        return AlgorithmNode(
            **common,
            alg_key=str(payload.get("alg_key", "")),
            alg_param=dict(payload.get("alg_param") or {}),
            buy_enabled=bool(payload.get("buy_enabled", True)),
            sell_enabled=bool(payload.get("sell_enabled", True)),
            runtime_editable_param_keys=tuple(
                str(item) for item in (payload.get("runtime_editable_param_keys") or [])
            ),
        )
    if node_type in {"and", "or"}:
        return CompositeNode(
            **common,
            children=tuple(str(item) for item in (payload.get("children") or [])),
        )
    if node_type == "pipeline":
        return PipelineNode(
            **common,
            children=tuple(str(item) for item in (payload.get("children") or [])),
            stage_policy=dict(payload.get("stage_policy") or {}),
        )
    return BaseNode(**common)


def configuration_from_dict(payload: dict[str, Any]) -> AlgorithmConfiguration:
    compatibility_payload = payload.get("compatibility_metadata") or {}
    return AlgorithmConfiguration(
        config_key=str(payload.get("config_key", "")),
        version=str(payload.get("version", "")),
        name=str(payload.get("name", "")),
        description=str(payload.get("description", "")),
        tags=tuple(str(item) for item in (payload.get("tags") or [])),
        notes=str(payload.get("notes", "")),
        status=str(payload.get("status", "draft")),
        root_node_id=str(payload.get("root_node_id", "")),
        nodes=tuple(_node_from_dict(node) for node in (payload.get("nodes") or [])),
        runtime_overrides=dict(payload.get("runtime_overrides") or {}),
        algorithm_package_constraints=dict(
            payload.get("algorithm_package_constraints") or {}
        ),
        compatibility_metadata=CompatibilityMetadata(
            expected_package_name=str(
                compatibility_payload.get("expected_package_name", "trading_algos")
            ),
            expected_package_version=(
                str(compatibility_payload["expected_package_version"])
                if compatibility_payload.get("expected_package_version") is not None
                else None
            ),
            minimum_supported_version=(
                str(compatibility_payload["minimum_supported_version"])
                if compatibility_payload.get("minimum_supported_version") is not None
                else None
            ),
            maximum_supported_version=(
                str(compatibility_payload["maximum_supported_version"])
                if compatibility_payload.get("maximum_supported_version") is not None
                else None
            ),
            algorithm_refs=tuple(
                str(item)
                for item in (compatibility_payload.get("algorithm_refs") or [])
            ),
            compatibility_state=cast(
                Any, str(compatibility_payload.get("compatibility_state", "compatible"))
            ),
            compatibility_messages=tuple(
                str(item)
                for item in (compatibility_payload.get("compatibility_messages") or [])
            ),
        ),
        created_by=str(payload.get("created_by", "")),
        created_at=(
            str(payload["created_at"])
            if payload.get("created_at") is not None
            else None
        ),
        updated_at=(
            str(payload["updated_at"])
            if payload.get("updated_at") is not None
            else None
        ),
    )


def configuration_to_dict(configuration: AlgorithmConfiguration) -> dict[str, object]:
    return configuration.to_dict()
