from __future__ import annotations

from typing import Any

from trading_algos.reporting.models import ReportDocument


def build_persisted_report_payload(
    report: ReportDocument,
    *,
    schema_version: str = "1.0",
) -> dict[str, Any]:
    payload = report.to_dict()
    payload["schema_version"] = schema_version
    payload["report_version"] = report.report_version
    return payload
