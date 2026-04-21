from __future__ import annotations

from collections.abc import Sequence
from copy import deepcopy
from typing import Any
from typing import cast

from trading_algos.alertgen.core.algorithm_registry import (
    get_alert_algorithm_spec_by_key,
)
from trading_algos.alertgen.contracts.outputs import (
    AlertAlgorithmOutput,
    AlertSeriesPoint,
)
from trading_algos.configuration.models import (
    AlgorithmConfiguration,
    AlgorithmNode,
    BaseNode,
    CompositeNode,
)
from trading_algos.configuration.validation import validate_configuration_payload


def _copy_row(row: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(dict(row))


def _algorithm_result(
    node: AlgorithmNode,
    *,
    symbol: str,
    report_base_path: str,
    candles: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    from trading_algos.alertgen.core.catalog import register_builtin_alert_algorithms

    register_builtin_alert_algorithms()
    spec = get_alert_algorithm_spec_by_key(node.alg_key)
    normalized_alg_param = spec.param_normalizer(
        node.alg_param,
        f"node {node.node_id} alg_param",
    )
    algorithm = spec.builder(
        symbol=symbol,
        report_base_path=report_base_path,
        alg_param=normalized_alg_param,
        sensor_config={
            "symbol": symbol,
            "alg_key": node.alg_key,
            "alg_param": normalized_alg_param,
            "buy": node.buy_enabled,
            "sell": node.sell_enabled,
        },
    )
    algorithm.process_list(list(candles))
    algorithm.evaluate()
    rows = [_copy_row(item) for item in algorithm.data_list]
    decisions = [
        {
            "buy_signal": bool(item.get("buy_SIGNAL")),
            "sell_signal": bool(item.get("sell_SIGNAL")),
            "no_signal": bool(item.get("no_SIGNAL")),
            "confidence": float(item.get("trend_confidence", 0.0) or 0.0),
        }
        for item in rows
    ]
    return {
        "node_id": node.node_id,
        "node_type": node.node_type,
        "node_name": node.name or algorithm.alg_name,
        "alg_key": node.alg_key,
        "alg_param": normalized_alg_param,
        "algorithm": algorithm,
        "rows": rows,
        "decisions": decisions,
        "chart_payload": algorithm._build_default_signal_chart_payload(  # noqa: SLF001
            title=f"{node.name or algorithm.alg_name} signals"
        ),
        "latest_decision": {
            "trend": algorithm.current_decision().trend,
            "confidence": algorithm.current_decision().confidence,
            "buy_signal": algorithm.current_decision().buy_signal,
            "sell_signal": algorithm.current_decision().sell_signal,
            "no_signal": algorithm.current_decision().no_signal,
        },
        "eval_dict": algorithm.eval_dict,
    }


def _composite_result(
    node: CompositeNode,
    child_results: list[dict[str, Any]],
    *,
    candles: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    if node.node_type == "pipeline":
        raise ValueError("pipeline node execution is not implemented yet")

    rows: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    mode_all = node.node_type == "and"
    for index, candle in enumerate(candles):
        child_decisions = [child["decisions"][index] for child in child_results]
        buy_signal = (
            all(item["buy_signal"] for item in child_decisions)
            if mode_all
            else any(item["buy_signal"] for item in child_decisions)
        )
        sell_signal = (
            all(item["sell_signal"] for item in child_decisions)
            if mode_all
            else any(item["sell_signal"] for item in child_decisions)
        )
        no_signal = not buy_signal and not sell_signal
        confidence = (
            min(item["confidence"] for item in child_decisions)
            if mode_all and child_decisions
            else max((item["confidence"] for item in child_decisions), default=0.0)
        )
        row = _copy_row(candle)
        row["buy_SIGNAL"] = buy_signal
        row["sell_SIGNAL"] = sell_signal
        row["no_SIGNAL"] = no_signal
        row["trend_confidence"] = confidence
        row["node_id"] = node.node_id
        rows.append(row)
        decisions.append(
            {
                "buy_signal": buy_signal,
                "sell_signal": sell_signal,
                "no_signal": no_signal,
                "confidence": confidence,
            }
        )
    return {
        "node_id": node.node_id,
        "node_type": node.node_type,
        "node_name": node.name or node.node_type.upper(),
        "rows": rows,
        "decisions": decisions,
        "children": [child["node_id"] for child in child_results],
    }


def build_configuration_normalized_output(
    root_result: dict[str, Any],
) -> AlertAlgorithmOutput:
    rows = root_result["rows"]
    points = []
    for item in rows:
        if item.get("buy_SIGNAL"):
            signal_label = "buy"
        elif item.get("sell_SIGNAL"):
            signal_label = "sell"
        else:
            signal_label = "neutral"
        points.append(
            AlertSeriesPoint(
                timestamp=str(item.get("ts", "")),
                signal_label=signal_label,
                confidence=float(item.get("trend_confidence", 0.0) or 0.0),
            )
        )
    return AlertAlgorithmOutput(
        algorithm_key=str(root_result.get("node_name", "configuration")),
        points=tuple(points),
        derived_series={
            "close": [item.get("Close") for item in rows],
            "buy_signal": [bool(item.get("buy_SIGNAL")) for item in rows],
            "sell_signal": [bool(item.get("sell_SIGNAL")) for item in rows],
            "gt_trend": [item.get("gt_trend") for item in rows],
        },
        summary_metrics=dict(root_result.get("eval_dict") or {}),
        metadata={
            "algorithm_name": root_result.get("node_name", "configuration"),
            "family": "configuration",
            "runtime_kind": "configuration",
        },
    )


def _execute_node(
    node_id: str,
    *,
    nodes_by_id: dict[str, BaseNode],
    cache: dict[str, dict[str, Any]],
    symbol: str,
    report_base_path: str,
    candles: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    if node_id in cache:
        return cache[node_id]
    node = nodes_by_id[node_id]
    if isinstance(node, AlgorithmNode):
        result = _algorithm_result(
            node,
            symbol=symbol,
            report_base_path=report_base_path,
            candles=candles,
        )
    else:
        child_results = [
            _execute_node(
                child_id,
                nodes_by_id=nodes_by_id,
                cache=cache,
                symbol=symbol,
                report_base_path=report_base_path,
                candles=candles,
            )
            for child_id in getattr(node, "children", ())
        ]
        result = _composite_result(
            cast(CompositeNode, node), child_results, candles=candles
        )
    cache[node_id] = result
    return result


def run_configuration_graph(
    *,
    configuration: AlgorithmConfiguration | dict[str, object] | str,
    symbol: str,
    report_base_path: str,
    candles: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    normalized = validate_configuration_payload(configuration)
    nodes_by_id = {node.node_id: node for node in normalized.nodes}
    cache: dict[str, dict[str, Any]] = {}
    root_result = _execute_node(
        normalized.root_node_id,
        nodes_by_id=nodes_by_id,
        cache=cache,
        symbol=symbol,
        report_base_path=report_base_path,
        candles=candles,
    )
    return {
        "configuration": normalized,
        "root_result": root_result,
        "node_results": list(cache.values()),
    }


def evaluate_configuration_graph(
    *,
    configuration: AlgorithmConfiguration | dict[str, object] | str,
    symbol: str,
    report_base_path: str,
    candles: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    execution = run_configuration_graph(
        configuration=configuration,
        symbol=symbol,
        report_base_path=report_base_path,
        candles=candles,
    )
    root_result = execution["root_result"]
    decisions = root_result["decisions"]
    return {
        **execution,
        "signal_summary": {
            "buy_count": sum(1 for item in decisions if item["buy_signal"]),
            "sell_count": sum(1 for item in decisions if item["sell_signal"]),
            "no_signal_count": sum(1 for item in decisions if item["no_signal"]),
            "total_rows": len(decisions),
        },
    }
