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
            {
                "key": "delta_neutral_volatility_trading",
                "name": "Delta Neutral Volatility Trading",
                "status": "runnable",
                "default_param": {
                    "rows": [],
                    "iv_rv_threshold": 0.05,
                    "min_gamma": 0.01,
                    "target_delta_band": 0.1,
                },
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

    assert result.created_count == 3
    assert result.skipped_count == 0
    assert len(experiment_service.calls) == 3
    assert experiment_service.calls[0]["algorithms"] == [
        {"alg_key": "boundary_breakout", "alg_param": {"window": 5}}
    ]
    assert experiment_service.calls[1]["algorithms"] == [
        {"alg_key": "close_high_channel_breakout", "alg_param": {"window": 2}}
    ]
    assert experiment_service.calls[2]["algorithms"] == [
        {
            "alg_key": "delta_neutral_volatility_trading",
            "alg_param": {
                "rows": [],
                "iv_rv_threshold": 0.05,
                "min_gamma": 0.01,
                "target_delta_band": 0.1,
            },
        }
    ]


def test_submit_all_algorithms_for_symbol_skips_non_executable_defaults_when_enabled() -> (
    None
):
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
        skip_non_executable_defaults=True,
    )

    assert result.created_count == 2
    assert result.skipped_count == 1
    assert result.skipped_algorithms == ["delta_neutral_volatility_trading"]
    assert len(experiment_service.calls) == 2


def test_submit_all_algorithms_for_symbol_includes_alg_key_in_validation_error() -> (
    None
):
    class _FailingExperimentServiceStub(_ExperimentServiceStub):
        def create_experiment(self, **kwargs: Any) -> str:
            algorithm = kwargs["algorithms"][0]
            if algorithm["alg_key"] == "delta_neutral_volatility_trading":
                raise ValueError(
                    "Alert generator sensor_config alg_param rows must be a non-empty list"
                )
            return super().create_experiment(**kwargs)

    experiment_service = _FailingExperimentServiceStub()
    service = BulkExperimentService(
        experiment_service=experiment_service,
        algorithm_catalog_service=_AlgorithmCatalogServiceStub(),
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
        assert str(exc) == (
            "Bulk submission failed for alg_key=delta_neutral_volatility_trading: "
            "Alert generator sensor_config alg_param rows must be a non-empty list"
        )
    else:
        raise AssertionError("Expected ValueError with alg_key context")


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
