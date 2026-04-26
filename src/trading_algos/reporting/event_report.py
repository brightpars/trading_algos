from __future__ import annotations

from typing import Any


def build_event_report_payload(
    *, algorithm_key: str, output_data: dict[str, Any]
) -> dict[str, Any]:
    metadata = output_data.get("metadata", {})
    summary_metrics = output_data.get("summary_metrics", {})
    child_outputs = output_data.get("child_outputs", [])
    latest_child = child_outputs[0] if child_outputs else None
    return {
        "algorithm_key": algorithm_key,
        "report_type": "event_window",
        "metadata": metadata,
        "summary_metrics": summary_metrics,
        "latest_child_output": latest_child,
        "data": output_data,
    }
