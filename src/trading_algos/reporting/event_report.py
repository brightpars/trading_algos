from __future__ import annotations

from typing import Any


def build_event_report_payload(
    *, algorithm_key: str, output_data: dict[str, Any]
) -> dict[str, Any]:
    return {
        "algorithm_key": algorithm_key,
        "report_type": "event_window",
        "data": output_data,
    }
