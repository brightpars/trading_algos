from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import replace

from trading_algos.alertgen.core.validation import _normalize_alertgen_alg_param
from trading_algos.configuration.compatibility import (
    evaluate_configuration_compatibility,
)
from trading_algos.configuration.models import (
    AlgorithmConfiguration,
    AlgorithmNode,
    BaseNode,
    CompositeNode,
)
from trading_algos.configuration.serialization import configuration_from_dict


def _require_non_empty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or value.strip() == "":
        raise ValueError(f"{label} is required")
    return value.strip()


def _visit_cycle(
    node_id: str,
    children_by_node: dict[str, tuple[str, ...]],
    active: set[str],
    visited: set[str],
) -> None:
    if node_id in active:
        raise ValueError("configuration graph must be acyclic")
    if node_id in visited:
        return
    active.add(node_id)
    for child_id in children_by_node.get(node_id, ()):  # pragma: no branch
        _visit_cycle(child_id, children_by_node, active, visited)
    active.remove(node_id)
    visited.add(node_id)


def validate_configuration_payload(
    payload: AlgorithmConfiguration | Mapping[str, object] | str,
) -> AlgorithmConfiguration:
    if isinstance(payload, str):
        payload = json.loads(payload)
    raw_nodes: list[object] | None = None
    if isinstance(payload, AlgorithmConfiguration):
        configuration = payload
    elif isinstance(payload, Mapping):
        raw_nodes_value = payload.get("nodes")
        raw_nodes = list(raw_nodes_value) if isinstance(raw_nodes_value, list) else []
        configuration = configuration_from_dict(dict(payload))
    else:
        raise ValueError("configuration payload must be a dict/JSON object")

    _require_non_empty_string(configuration.config_key, "config_key")
    _require_non_empty_string(configuration.version, "version")
    _require_non_empty_string(configuration.name, "name")
    _require_non_empty_string(configuration.root_node_id, "root_node_id")
    if len(configuration.nodes) == 0:
        raise ValueError("nodes must be a non-empty list")

    nodes_by_id: dict[str, BaseNode] = {}
    children_by_node: dict[str, tuple[str, ...]] = {}
    for node in configuration.nodes:
        _require_non_empty_string(node.node_id, "node_id")
        if node.node_id in nodes_by_id:
            raise ValueError(f"node_id {node.node_id} must be unique")
        if node.node_type not in {"algorithm", "and", "or", "pipeline"}:
            raise ValueError(f"unsupported node_type {node.node_type}")
        nodes_by_id[node.node_id] = node
        children_by_node[node.node_id] = tuple(getattr(node, "children", ()))

    if configuration.root_node_id not in nodes_by_id:
        raise ValueError("root_node_id must reference an existing node")

    raw_children_by_node_id: dict[str, tuple[object, ...]] = {}
    for raw_node in raw_nodes or []:
        if not isinstance(raw_node, Mapping):
            continue
        raw_node_id = raw_node.get("node_id")
        if not isinstance(raw_node_id, str):
            continue
        raw_children = raw_node.get("children")
        if isinstance(raw_children, list | tuple):
            raw_children_by_node_id[raw_node_id] = tuple(raw_children)

    for node in configuration.nodes:
        if isinstance(node, AlgorithmNode):
            _require_non_empty_string(node.alg_key, f"node {node.node_id} alg_key")
            node_children = raw_children_by_node_id.get(node.node_id, ())
            if node_children:
                raise ValueError("algorithm nodes must not declare children")
            if node.buy_enabled is False and node.sell_enabled is False:
                raise ValueError(
                    f"node {node.node_id} requires at least one of buy_enabled/sell_enabled"
                )
            _normalize_alertgen_alg_param(
                alg_key=node.alg_key,
                raw_alg_param=node.alg_param,
                label=f"node {node.node_id} alg_param",
            )
            invalid_runtime_editable_keys = [
                key
                for key in node.runtime_editable_param_keys
                if key not in node.alg_param
            ]
            if invalid_runtime_editable_keys:
                invalid_keys = ", ".join(sorted(invalid_runtime_editable_keys))
                raise ValueError(
                    "node "
                    f"{node.node_id} runtime_editable_param_keys must be present in alg_param: {invalid_keys}"
                )
        elif isinstance(node, CompositeNode):
            min_children = 2
            if len(node.children) < min_children:
                raise ValueError(
                    f"node {node.node_id} requires at least {min_children} children"
                )
            for child_id in node.children:
                if child_id not in nodes_by_id:
                    raise ValueError(
                        f"node {node.node_id} references missing child node {child_id}"
                    )

    _visit_cycle(configuration.root_node_id, children_by_node, set(), set())
    compatibility = evaluate_configuration_compatibility(configuration)
    if compatibility.compatibility_state == "incompatible":
        raise ValueError("; ".join(compatibility.compatibility_messages))
    return replace(configuration, compatibility_metadata=compatibility)
