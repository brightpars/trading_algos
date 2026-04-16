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
