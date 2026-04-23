from __future__ import annotations

from typing import Any

from trading_algos_dashboard.services.bulk_experiment_service import (
    BulkExperimentService,
)


class _ExperimentServiceStub:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def create_experiment(self, **kwargs: Any) -> str:
        self.calls.append(dict(kwargs))
        return f"exp_{len(self.calls)}"


class _AlgorithmCatalogServiceStub:
    def __init__(self) -> None:
        self.runnable_algorithms = [
            {
                "key": "boundary_breakout",
                "name": "Boundary Breakout",
                "status": "runnable",
                "default_param": {"window": 5},
            },
            {
                "key": "close_high_channel_breakout",
                "name": "Close High Channel Breakout",
                "status": "runnable",
                "default_param": {"window": 2},
            },
        ]

    def list_runnable_algorithm_implementations(self) -> list[dict[str, Any]]:
        return list(self.runnable_algorithms)

    def get_runnable_algorithm_implementation(self, alg_key: str) -> dict[str, Any]:
        for algorithm in self.runnable_algorithms:
            if algorithm["key"] == alg_key:
                return dict(algorithm)
        raise ValueError(f"Algorithm is not runnable: {alg_key}")


def test_submit_all_algorithms_for_symbol_creates_one_experiment_per_algorithm():
    experiment_service = _ExperimentServiceStub()
    service = BulkExperimentService(
        experiment_service=experiment_service,
        algorithm_catalog_service=_AlgorithmCatalogServiceStub(),
    )

    result = service.submit_all_algorithms_for_symbol(
        symbol="AAPL",
        start_date="2024-01-01",
        start_time="09:30",
        end_date="2024-01-31",
        end_time="16:00",
        notes="bulk notes",
    )

    assert result.created_count == 2
    assert len(experiment_service.calls) == 2
    assert experiment_service.calls[0]["algorithms"] == [
        {"alg_key": "boundary_breakout", "alg_param": {"window": 5}}
    ]
    assert experiment_service.calls[1]["algorithms"] == [
        {"alg_key": "close_high_channel_breakout", "alg_param": {"window": 2}}
    ]


def test_submit_single_algorithm_for_symbols_normalizes_and_deduplicates_symbols():
    experiment_service = _ExperimentServiceStub()
    service = BulkExperimentService(
        experiment_service=experiment_service,
        algorithm_catalog_service=_AlgorithmCatalogServiceStub(),
    )

    result = service.submit_single_algorithm_for_symbols(
        alg_key="boundary_breakout",
        symbols_text="aapl\nMSFT, aapl, nvda",
        start_date="2024-01-01",
        start_time="09:30",
        end_date="2024-01-31",
        end_time="16:00",
        notes="symbols run",
    )

    assert result.created_count == 3
    assert [call["symbol"] for call in experiment_service.calls] == [
        "AAPL",
        "MSFT",
        "NVDA",
    ]


def test_submit_single_algorithm_for_symbols_requires_at_least_one_symbol():
    service = BulkExperimentService(
        experiment_service=_ExperimentServiceStub(),
        algorithm_catalog_service=_AlgorithmCatalogServiceStub(),
    )

    try:
        service.submit_single_algorithm_for_symbols(
            alg_key="boundary_breakout",
            symbols_text="  ,   \n ",
            start_date="2024-01-01",
            start_time="09:30",
            end_date="2024-01-31",
            end_time="16:00",
        )
    except ValueError as exc:
        assert str(exc) == "At least one symbol is required."
    else:
        raise AssertionError("Expected ValueError for empty symbol batch")


def test_submit_all_algorithms_for_symbol_rejects_empty_runnable_catalog():
    experiment_service = _ExperimentServiceStub()
    catalog_service = _AlgorithmCatalogServiceStub()
    catalog_service.runnable_algorithms = []
    service = BulkExperimentService(
        experiment_service=experiment_service,
        algorithm_catalog_service=catalog_service,
    )

    try:
        service.submit_all_algorithms_for_symbol(
            symbol="AAPL",
            start_date="2024-01-01",
            start_time="09:30",
            end_date="2024-01-31",
            end_time="16:00",
        )
    except ValueError as exc:
        assert str(exc) == "No runnable algorithms are available for bulk submission."
    else:
        raise AssertionError("Expected ValueError for empty runnable algorithm list")


def test_bulk_service_enforces_max_batch_size() -> None:
    service = BulkExperimentService(
        experiment_service=_ExperimentServiceStub(),
        algorithm_catalog_service=_AlgorithmCatalogServiceStub(),
        max_bulk_experiments=1,
    )

    try:
        service.submit_all_algorithms_for_symbol(
            symbol="AAPL",
            start_date="2024-01-01",
            start_time="09:30",
            end_date="2024-01-31",
            end_time="16:00",
        )
    except ValueError as exc:
        assert str(exc) == "Bulk submission exceeds max batch size of 1 experiments."
    else:
        raise AssertionError("Expected ValueError for oversized batch")
