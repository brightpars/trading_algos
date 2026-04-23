from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]


PROJECT_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_REGISTRY_PATH = PROJECT_ROOT / "manifests" / "algorithm_test_fixtures.yaml"
PERFORMANCE_BUDGET_REGISTRY_PATH = (
    PROJECT_ROOT / "manifests" / "algorithm_performance_budgets.yaml"
)
ALGORITHM_MANIFEST_PATH = PROJECT_ROOT / "manifests" / "algorithm_library_manifest.yaml"


class RegistryLookupError(ValueError):
    """Raised when a requested registry entry cannot be found."""


@dataclass(frozen=True)
class FixtureRecord:
    fixture_id: str
    domain: str
    purpose: str
    dataset_path: Path | None
    placeholder: str | None
    expected_behaviors: tuple[str, ...]
    raw: dict[str, Any]

    @property
    def has_dataset(self) -> bool:
        return self.dataset_path is not None

    @property
    def is_placeholder(self) -> bool:
        return self.placeholder is not None or self.dataset_path is None


@dataclass(frozen=True)
class PerformanceBudgetRecord:
    performance_budget_id: str
    description: str
    acceptance: tuple[str, ...]
    raw: dict[str, Any]


@dataclass(frozen=True)
class PerformanceSmokeCase:
    catalog_ref: str
    kind: str
    name: str
    performance_budget_id: str
    performance_budget: PerformanceBudgetRecord
    fixture_ids: tuple[str, ...]
    raw: dict[str, Any]


def _load_yaml_document(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"manifest_support: invalid_yaml_document; path={path}")
    return loaded


@lru_cache(maxsize=1)
def _fixture_rows_by_id() -> dict[str, dict[str, Any]]:
    document = _load_yaml_document(FIXTURE_REGISTRY_PATH)
    rows = document.get("fixtures", [])
    if not isinstance(rows, list):
        raise ValueError(
            "manifest_support: invalid_fixture_registry; expected_key=fixtures"
        )
    return {str(row["fixture_id"]): row for row in rows}


@lru_cache(maxsize=1)
def _performance_budget_rows_by_id() -> dict[str, dict[str, Any]]:
    document = _load_yaml_document(PERFORMANCE_BUDGET_REGISTRY_PATH)
    rows = document.get("performance_budgets", [])
    if not isinstance(rows, list):
        raise ValueError(
            "manifest_support: invalid_performance_budget_registry; expected_key=performance_budgets"
        )
    return {str(row["performance_budget_id"]): row for row in rows}


@lru_cache(maxsize=1)
def _manifest_rows_by_catalog_ref() -> dict[str, dict[str, Any]]:
    document = _load_yaml_document(ALGORITHM_MANIFEST_PATH)
    rows = document.get("rows", [])
    if not isinstance(rows, list):
        raise ValueError(
            "manifest_support: invalid_algorithm_manifest; expected_key=rows"
        )
    return {str(row["catalog_ref"]): row for row in rows}


def get_fixture_record(fixture_id: str) -> FixtureRecord:
    normalized_fixture_id = fixture_id.strip()
    try:
        row = _fixture_rows_by_id()[normalized_fixture_id]
    except KeyError as exc:
        raise RegistryLookupError(
            "fixture_registry: fixture_id_not_found; "
            f"fixture_id={fixture_id} registry_path={FIXTURE_REGISTRY_PATH}"
        ) from exc

    inputs = row.get("inputs")
    if not isinstance(inputs, dict):
        inputs = {}
    dataset_path_value = inputs.get("dataset_path")
    placeholder_value = inputs.get("placeholder")
    dataset_path = (
        PROJECT_ROOT / str(dataset_path_value)
        if isinstance(dataset_path_value, str) and dataset_path_value.strip()
        else None
    )
    placeholder = str(placeholder_value) if isinstance(placeholder_value, str) else None
    expected_behaviors = row.get("expected_behaviors")
    if not isinstance(expected_behaviors, list):
        expected_behaviors = []

    return FixtureRecord(
        fixture_id=str(row["fixture_id"]),
        domain=str(row["domain"]),
        purpose=str(row["purpose"]),
        dataset_path=dataset_path,
        placeholder=placeholder,
        expected_behaviors=tuple(str(item) for item in expected_behaviors),
        raw=row,
    )


def get_performance_budget_record(
    performance_budget_id: str,
) -> PerformanceBudgetRecord:
    normalized_budget_id = performance_budget_id.strip()
    try:
        row = _performance_budget_rows_by_id()[normalized_budget_id]
    except KeyError as exc:
        raise RegistryLookupError(
            "performance_budget_registry: performance_budget_id_not_found; "
            f"performance_budget_id={performance_budget_id} "
            f"registry_path={PERFORMANCE_BUDGET_REGISTRY_PATH}"
        ) from exc

    acceptance = row.get("acceptance")
    if not isinstance(acceptance, list):
        acceptance = []

    return PerformanceBudgetRecord(
        performance_budget_id=str(row["performance_budget_id"]),
        description=str(row["description"]),
        acceptance=tuple(str(item) for item in acceptance),
        raw=row,
    )


def get_performance_smoke_case(catalog_ref: str) -> PerformanceSmokeCase:
    normalized_catalog_ref = catalog_ref.strip()
    try:
        row = _manifest_rows_by_catalog_ref()[normalized_catalog_ref]
    except KeyError as exc:
        raise RegistryLookupError(
            "algorithm_manifest: catalog_ref_not_found; "
            f"catalog_ref={catalog_ref} manifest_path={ALGORITHM_MANIFEST_PATH}"
        ) from exc

    performance_budget = get_performance_budget_record(
        str(row["performance_budget_id"])
    )
    fixture_ids = row.get("fixture_ids")
    if not isinstance(fixture_ids, list):
        fixture_ids = []

    return PerformanceSmokeCase(
        catalog_ref=str(row["catalog_ref"]),
        kind=str(row["kind"]),
        name=str(row["name"]),
        performance_budget_id=str(row["performance_budget_id"]),
        performance_budget=performance_budget,
        fixture_ids=tuple(str(item) for item in fixture_ids),
        raw=row,
    )
