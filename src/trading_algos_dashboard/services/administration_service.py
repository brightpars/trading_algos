from __future__ import annotations

from trading_algos_dashboard.repositories.experiment_repository import (
    ExperimentRepository,
)
from trading_algos_dashboard.repositories.result_repository import ResultRepository


class AdministrationService:
    def __init__(
        self,
        *,
        experiment_repository: ExperimentRepository,
        result_repository: ResultRepository,
    ):
        self.experiment_repository = experiment_repository
        self.result_repository = result_repository

    def get_database_content_summary(self) -> list[dict[str, object]]:
        return [
            {
                "key": "experiments",
                "label": "Experiments",
                "description": "Delete all stored experiment runs and their related results.",
                "record_count": self.experiment_repository.count_experiments(),
                "action_endpoint": "administration.clear_experiments",
                "action_label": "Delete experiments",
            },
            {
                "key": "results",
                "label": "Results",
                "description": "Delete all stored report/result documents without deleting experiments.",
                "record_count": self.result_repository.count_results(),
                "action_endpoint": "administration.clear_results",
                "action_label": "Delete results",
            },
        ]

    def clear_experiments(self) -> dict[str, int]:
        deleted_results = self.result_repository.delete_all_results()
        deleted_experiments = self.experiment_repository.delete_all_experiments()
        return {
            "deleted_experiments": deleted_experiments,
            "deleted_results": deleted_results,
        }

    def clear_results(self) -> int:
        return self.result_repository.delete_all_results()
