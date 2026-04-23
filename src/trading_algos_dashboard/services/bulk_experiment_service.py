from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BulkExperimentSubmissionResult:
    created_experiment_ids: list[str]

    @property
    def created_count(self) -> int:
        return len(self.created_experiment_ids)


class BulkExperimentService:
    def __init__(
        self,
        *,
        experiment_service: Any,
        algorithm_catalog_service: Any,
        max_bulk_experiments: int = 100,
    ) -> None:
        if max_bulk_experiments < 1:
            raise ValueError("max_bulk_experiments must be at least 1")
        self.experiment_service = experiment_service
        self.algorithm_catalog_service = algorithm_catalog_service
        self.max_bulk_experiments = max_bulk_experiments

    def submit_all_algorithms_for_symbol(
        self,
        *,
        symbol: str,
        start_date: str,
        start_time: str,
        end_date: str,
        end_time: str,
        notes: str = "",
    ) -> BulkExperimentSubmissionResult:
        runnable_algorithms = (
            self.algorithm_catalog_service.list_runnable_algorithm_implementations()
        )
        if not runnable_algorithms:
            raise ValueError(
                "No runnable algorithms are available for bulk submission."
            )
        self._ensure_within_batch_limit(len(runnable_algorithms))

        created_experiment_ids = [
            self.experiment_service.create_experiment(
                symbol=symbol,
                start_date=start_date,
                start_time=start_time,
                end_date=end_date,
                end_time=end_time,
                algorithms=[
                    {
                        "alg_key": algorithm["key"],
                        "alg_param": algorithm.get("default_param", {}),
                    }
                ],
                notes=notes,
            )
            for algorithm in runnable_algorithms
        ]
        return BulkExperimentSubmissionResult(
            created_experiment_ids=created_experiment_ids
        )

    def submit_single_algorithm_for_symbols(
        self,
        *,
        alg_key: str,
        symbols_text: str,
        start_date: str,
        start_time: str,
        end_date: str,
        end_time: str,
        notes: str = "",
    ) -> BulkExperimentSubmissionResult:
        normalized_symbols = self._normalize_symbols(symbols_text)
        if not normalized_symbols:
            raise ValueError("At least one symbol is required.")
        self._ensure_within_batch_limit(len(normalized_symbols))

        algorithm = (
            self.algorithm_catalog_service.get_runnable_algorithm_implementation(
                alg_key
            )
        )
        created_experiment_ids = [
            self.experiment_service.create_experiment(
                symbol=symbol,
                start_date=start_date,
                start_time=start_time,
                end_date=end_date,
                end_time=end_time,
                algorithms=[
                    {
                        "alg_key": algorithm["key"],
                        "alg_param": algorithm.get("default_param", {}),
                    }
                ],
                notes=notes,
            )
            for symbol in normalized_symbols
        ]
        return BulkExperimentSubmissionResult(
            created_experiment_ids=created_experiment_ids
        )

    def _normalize_symbols(self, raw_symbols: str) -> list[str]:
        seen_symbols: set[str] = set()
        normalized_symbols: list[str] = []
        for chunk in raw_symbols.replace(",", "\n").splitlines():
            symbol = chunk.strip().upper()
            if not symbol or symbol in seen_symbols:
                continue
            seen_symbols.add(symbol)
            normalized_symbols.append(symbol)
        return normalized_symbols

    def _ensure_within_batch_limit(self, experiment_count: int) -> None:
        if experiment_count > self.max_bulk_experiments:
            raise ValueError(
                "Bulk submission exceeds max batch size of "
                f"{self.max_bulk_experiments} experiments."
            )
