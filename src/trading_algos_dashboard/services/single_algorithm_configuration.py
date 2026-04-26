from __future__ import annotations

from typing import Any


def build_single_algorithm_configuration_payload(
    *,
    alg_key: str,
    alg_param: dict[str, Any],
) -> dict[str, Any]:
    sanitized_key = alg_key.strip() or "algorithm"
    config_slug = sanitized_key.replace("_", "-")
    return {
        "config_key": f"single-{config_slug}",
        "version": "1",
        "name": f"Algorithm config: {sanitized_key}",
        "root_node_id": "alg1",
        "nodes": [
            {
                "node_id": "alg1",
                "node_type": "algorithm",
                "alg_key": sanitized_key,
                "alg_param": dict(alg_param),
                "buy_enabled": True,
                "sell_enabled": True,
            }
        ],
        "runtime_overrides": {},
        "compatibility_metadata": {},
    }


def extract_single_algorithm_from_configuration_payload(
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    root_node_id = payload.get("root_node_id")
    nodes = payload.get("nodes")
    if (
        not isinstance(root_node_id, str)
        or not isinstance(nodes, list)
        or len(nodes) != 1
    ):
        return None
    node = nodes[0]
    if not isinstance(node, dict):
        return None
    if node.get("node_id") != root_node_id or node.get("node_type") != "algorithm":
        return None
    alg_key = node.get("alg_key")
    alg_param = node.get("alg_param", {})
    if not isinstance(alg_key, str) or not isinstance(alg_param, dict):
        return None
    return {
        "alg_key": alg_key,
        "alg_param": dict(alg_param),
        "buy": bool(node.get("buy_enabled", True)),
        "sell": bool(node.get("sell_enabled", True)),
    }
