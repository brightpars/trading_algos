from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]

BASE_DIR = Path(__file__).resolve().parents[1]
MANIFEST_PATH = BASE_DIR / "manifests" / "algorithm_library_manifest.yaml"
BLOCKERS_PATH = BASE_DIR / "manifests" / "algorithm_framework_blockers.yaml"
FIXTURES_PATH = BASE_DIR / "manifests" / "algorithm_test_fixtures.yaml"
BUDGETS_PATH = BASE_DIR / "manifests" / "algorithm_performance_budgets.yaml"


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _find_duplicate_catalog_refs(rows: list[dict[str, Any]]) -> list[str]:
    counts = Counter(row["catalog_ref"] for row in rows)
    return sorted(catalog_ref for catalog_ref, count in counts.items() if count > 1)


def _manifest_bundle() -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    set[str],
    set[str],
    set[str],
]:
    manifest = _load_yaml(MANIFEST_PATH)
    blockers = _load_yaml(BLOCKERS_PATH)
    fixtures = _load_yaml(FIXTURES_PATH)
    budgets = _load_yaml(BUDGETS_PATH)

    rows = manifest["rows"]
    assert isinstance(rows, list)

    blocker_keys = {blocker["blocker_key"] for blocker in blockers["blockers"]}
    fixture_ids = {fixture["fixture_id"] for fixture in fixtures["fixtures"]}
    budget_ids = {
        budget["performance_budget_id"] for budget in budgets["performance_budgets"]
    }
    return manifest, rows, blocker_keys, fixture_ids, budget_ids


def test_manifest_integrity_matches_declared_counts() -> None:
    manifest, rows, _, _, _ = _manifest_bundle()

    algorithms = [row for row in rows if row["kind"] == "algorithm"]
    combination_methods = [row for row in rows if row["kind"] == "combination_method"]

    assert manifest["manifest_version"] == 1
    assert manifest["capability_taxonomy_version"] == 1
    assert manifest["source_catalog"]["implementation_plan_path"] == (
        "docs/algorithm_library_systematic_implementation_plan.md"
    )
    assert len(algorithms) == manifest["expected_totals"]["algorithms"]
    assert (
        len(combination_methods) == manifest["expected_totals"]["combination_methods"]
    )
    assert len(rows) == manifest["expected_totals"]["all_rows"]

    assert Counter(row["family"] for row in algorithms) == Counter(
        manifest["expected_family_totals"]
    )
    assert Counter(row["family"] for row in combination_methods) == Counter(
        manifest["expected_method_family_totals"]
    )


def test_manifest_catalog_refs_are_unique() -> None:
    _, rows, _, _, _ = _manifest_bundle()

    assert _find_duplicate_catalog_refs(rows) == []


def test_duplicate_catalog_ref_detection_is_explicit() -> None:
    _, rows, _, _, _ = _manifest_bundle()

    duplicated_rows = [*rows, {**rows[0]}]

    assert _find_duplicate_catalog_refs(duplicated_rows) == [rows[0]["catalog_ref"]]


def test_manifest_blocker_keys_exist_in_blocker_registry() -> None:
    _, rows, blocker_keys, _, _ = _manifest_bundle()

    missing_blocker_keys = sorted(
        blocker_key
        for row in rows
        for blocker_key in row.get("framework_blockers", [])
        if blocker_key not in blocker_keys
    )

    assert missing_blocker_keys == []


def test_manifest_fixture_ids_exist_in_fixture_registry() -> None:
    _, rows, _, fixture_ids, _ = _manifest_bundle()

    missing_fixture_ids = sorted(
        fixture_id
        for row in rows
        for fixture_id in row.get("fixture_ids", [])
        if fixture_id not in fixture_ids
    )

    assert missing_fixture_ids == []


def test_manifest_performance_budget_ids_exist_in_budget_registry() -> None:
    _, rows, _, _, budget_ids = _manifest_bundle()

    missing_budget_ids = sorted(
        row["performance_budget_id"]
        for row in rows
        if row["performance_budget_id"] not in budget_ids
    )

    assert missing_budget_ids == []


@pytest.mark.parametrize(
    ("path", "top_level_key"),
    [
        (MANIFEST_PATH, "rows"),
        (BLOCKERS_PATH, "blockers"),
        (FIXTURES_PATH, "fixtures"),
        (BUDGETS_PATH, "performance_budgets"),
    ],
)
def test_manifest_registry_files_load_with_non_empty_collections(
    path: Path, top_level_key: str
) -> None:
    loaded = _load_yaml(path)

    assert top_level_key in loaded
    assert isinstance(loaded[top_level_key], list)
    assert loaded[top_level_key]
