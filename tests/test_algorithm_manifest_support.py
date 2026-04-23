from __future__ import annotations

from pathlib import Path

import pytest

from trading_algos.algorithmspec import (
    RegistryLookupError,
    get_fixture_record,
    get_performance_budget_record,
    get_performance_smoke_case,
)


def test_fixture_record_loads_declared_dataset_path() -> None:
    fixture = get_fixture_record("fixture.trend_monotonic_cross_v1")

    assert fixture.fixture_id == "fixture.trend_monotonic_cross_v1"
    assert fixture.domain == "single_asset_ohlcv"
    assert fixture.has_dataset is True
    assert fixture.is_placeholder is False
    assert fixture.dataset_path == Path(
        "/home/mohammad/development/trading_algos/tests/fixtures/trend/monotonic_cross.csv"
    )
    assert fixture.placeholder is None
    assert (
        "Buy event occurs on the first positive crossover" in fixture.expected_behaviors
    )


def test_missing_fixture_id_fails_clearly() -> None:
    with pytest.raises(RegistryLookupError, match=r"fixture_id=fixture\.missing_v1"):
        get_fixture_record("fixture.missing_v1")


def test_performance_budget_record_loads_acceptance_rows() -> None:
    budget = get_performance_budget_record("perf.single_asset_bar_v1")

    assert budget.performance_budget_id == "perf.single_asset_bar_v1"
    assert budget.description == "Budget for single-asset OHLCV bar-by-bar strategies."
    assert len(budget.acceptance) == 3
    assert (
        budget.acceptance[0]
        == "Processes 1,000,000 bars within the target CI runtime budget"
    )


def test_missing_performance_budget_id_fails_clearly() -> None:
    with pytest.raises(
        RegistryLookupError,
        match=r"performance_budget_id=perf\.missing_v1",
    ):
        get_performance_budget_record("perf.missing_v1")


def test_performance_smoke_case_loads_algorithm_budget_mapping() -> None:
    smoke_case = get_performance_smoke_case("algorithm:1")

    assert smoke_case.catalog_ref == "algorithm:1"
    assert smoke_case.kind == "algorithm"
    assert smoke_case.name == "Simple Moving Average Crossover"
    assert smoke_case.performance_budget_id == "perf.single_asset_bar_v1"
    assert (
        smoke_case.performance_budget.performance_budget_id
        == "perf.single_asset_bar_v1"
    )
    assert smoke_case.fixture_ids == (
        "fixture.trend_monotonic_cross_v1",
        "fixture.trend_whipsaw_guard_v1",
    )


def test_performance_smoke_case_loads_combination_method_budget_mapping() -> None:
    smoke_case = get_performance_smoke_case("combination:1")

    assert smoke_case.catalog_ref == "combination:1"
    assert smoke_case.kind == "combination_method"
    assert smoke_case.name == "Hard Boolean Gating (AND / OR / Majority)"
    assert smoke_case.performance_budget_id == "perf.composite_signal_v1"
    assert smoke_case.fixture_ids == ("fixture.composite_boolean_truth_table_v1",)


def test_missing_catalog_ref_fails_clearly_for_performance_smoke_case() -> None:
    with pytest.raises(RegistryLookupError, match=r"catalog_ref=combination:missing"):
        get_performance_smoke_case("combination:missing")
