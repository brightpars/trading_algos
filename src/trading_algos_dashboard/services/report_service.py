from __future__ import annotations

from typing import Any

from trading_algos_dashboard.repositories.result_repository import ResultRepository


class ReportService:
    def __init__(self, result_repository: ResultRepository):
        self.result_repository = result_repository

    def list_reports(self) -> list[dict[str, Any]]:
        return [
            result
            for result in self.result_repository.collection.find({}).sort(
                "created_at", -1
            )
        ]

    def list_standardized_reports(self) -> list[dict[str, Any]]:
        return [
            result
            for result in self.list_reports()
            if isinstance(result.get("report"), dict)
        ]

    def summarize_report(self, result: dict[str, Any]) -> dict[str, Any]:
        report = result.get("report")
        if not isinstance(report, dict):
            return {
                "experiment_id": result.get("experiment_id"),
                "name": result.get("alg_name") or result.get("config_name"),
                "report_version": None,
            }
        algorithm_summary = report.get("algorithm_summary") or {}
        evaluation_summary = report.get("evaluation_summary") or {}
        return {
            "experiment_id": result.get("experiment_id"),
            "name": algorithm_summary.get("algorithm_name"),
            "report_version": report.get("report_version"),
            "schema_version": report.get("schema_version"),
            "headline_metrics": evaluation_summary.get("headline_metrics") or {},
        }
