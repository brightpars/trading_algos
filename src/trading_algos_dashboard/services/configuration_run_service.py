from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from trading_algos.configuration.executor import evaluate_configuration_graph


def run_configuration_payload(
    *,
    payload: dict[str, Any],
    symbol: str,
    report_base_path: str,
    candles: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    evaluation = evaluate_configuration_graph(
        configuration=payload,
        symbol=symbol,
        report_base_path=report_base_path,
        candles=candles,
    )
    root_result = evaluation["root_result"]
    decisions = root_result["decisions"]
    latest_decision = (
        decisions[-1]
        if decisions
        else {
            "buy_signal": False,
            "sell_signal": False,
            "no_signal": True,
            "confidence": 0.0,
        }
    )
    trend = "UNKNOWN"
    if latest_decision["sell_signal"]:
        trend = "DOWN"
    elif latest_decision["buy_signal"]:
        trend = "UP"
    return {
        "input_kind": "configuration",
        "config_key": evaluation["configuration"].config_key,
        "config_version": evaluation["configuration"].version,
        "config_name": evaluation["configuration"].name,
        "signal_summary": evaluation["signal_summary"],
        "latest_decision": {
            "trend": trend,
            "confidence": latest_decision["confidence"],
            "buy_signal": latest_decision["buy_signal"],
            "sell_signal": latest_decision["sell_signal"],
            "buy_range_signal": False,
            "sell_range_signal": False,
            "no_signal": latest_decision["no_signal"],
            "annotations": {"config_key": evaluation["configuration"].config_key},
        },
        "node_results": [
            {
                "node_id": item["node_id"],
                "node_type": item["node_type"],
                "node_name": item["node_name"],
                "chart_payload": item.get("chart_payload"),
            }
            for item in evaluation["node_results"]
        ],
        "chart_payload": root_result.get("chart_payload"),
        "eval_dict": {},
    }
