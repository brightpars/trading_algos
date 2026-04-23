#!/usr/bin/env python3
from collections import Counter
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

BASE = Path(__file__).resolve().parents[1]
MANIFEST_PATH = BASE / "manifests" / "algorithm_library_manifest.yaml"
BLOCKERS_PATH = BASE / "manifests" / "algorithm_framework_blockers.yaml"
FIXTURES_PATH = BASE / "manifests" / "algorithm_test_fixtures.yaml"
BUDGETS_PATH = BASE / "manifests" / "algorithm_performance_budgets.yaml"
OUT_PATH = BASE / "docs" / "algorithm_library_implementation_tracker.md"


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"Expected mapping at {path}")
    return data


def md_table(headers: list[str], rows: list[dict[str, Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(str(row.get(h, "")).replace("\n", " ") for h in headers)
            + " |"
        )
    return "\n".join(lines)


def main():
    manifest = load_yaml(MANIFEST_PATH)
    blockers = load_yaml(BLOCKERS_PATH)
    fixtures = load_yaml(FIXTURES_PATH)
    budgets = load_yaml(BUDGETS_PATH)

    rows = manifest["rows"]
    status_counts = Counter(r["delivery_status"] for r in rows)
    op_counts = Counter(r["operational_readiness"] for r in rows)
    tier_counts = Counter(r["tier"] for r in rows)
    kind_counts = Counter(r["kind"] for r in rows)

    family_rows = []
    for fam in sorted(set(r["family"] for r in rows)):
        famrows = [r for r in rows if r["family"] == fam]
        c = Counter(r["delivery_status"] for r in famrows)
        family_rows.append(
            {
                "family": fam,
                "kind_mix": "/".join(sorted(set(r["kind"] for r in famrows))),
                "total": len(famrows),
                "ready": c.get("ready_to_implement", 0),
                "blocked": c.get("blocked_framework", 0),
                "in_progress": c.get("in_progress", 0),
                "complete": c.get("complete", 0),
            }
        )

    blocker_rows = []
    for b in blockers["blockers"]:
        blocker_rows.append(
            {
                "blocker_key": b["blocker_key"],
                "status": b["status"],
                "affected_rows": len(b.get("affected_rows", [])),
                "affected_families": ", ".join(b.get("affected_families", [])[:5]),
            }
        )

    ready_batches = Counter(
        r["batch"] for r in rows if r["delivery_status"] == "ready_to_implement"
    )
    batch_rows = [{"batch": b, "ready_rows": n} for b, n in ready_batches.most_common()]

    fixture_rows = [
        {
            "metric": "rows with fixture ids",
            "count": sum(1 for r in rows if r.get("fixture_ids")),
        },
        {
            "metric": "rows without fixture ids",
            "count": sum(1 for r in rows if not r.get("fixture_ids")),
        },
        {"metric": "fixtures in registry", "count": len(fixtures["fixtures"])},
        {"metric": "performance budgets", "count": len(budgets["performance_budgets"])},
    ]

    text = f"""# Algorithm Library Implementation Tracker

## Source metadata

- Requirements document path: `{manifest["source_catalog"]["requirements_doc_path"]}`
- Requirements document version: `{
        manifest["source_catalog"]["requirements_doc_version"]
    }`
- Implementation plan path: `{manifest["source_catalog"]["implementation_plan_path"]}`
- Total algorithm rows: **{manifest["expected_totals"]["algorithms"]}**
- Total combination-method rows: **{
        manifest["expected_totals"]["combination_methods"]
    }**
- Total tracked rows: **{manifest["expected_totals"]["all_rows"]}**

## Overall status summary

{
        md_table(
            ["metric", "count"],
            [
                {"metric": "algorithm rows", "count": kind_counts["algorithm"]},
                {
                    "metric": "combination-method rows",
                    "count": kind_counts["combination_method"],
                },
                {
                    "metric": "ready_to_implement",
                    "count": status_counts["ready_to_implement"],
                },
                {
                    "metric": "blocked_framework",
                    "count": status_counts["blocked_framework"],
                },
                {"metric": "in_progress", "count": status_counts["in_progress"]},
                {"metric": "complete", "count": status_counts["complete"]},
                {"metric": "prototype_only", "count": op_counts["prototype_only"]},
                {"metric": "research_ready", "count": op_counts["research_ready"]},
                {"metric": "production_ready", "count": op_counts["production_ready"]},
                {"metric": "tier1 rows", "count": tier_counts["tier1"]},
                {"metric": "tier2 rows", "count": tier_counts["tier2"]},
                {"metric": "tier3 rows", "count": tier_counts["tier3"]},
            ],
        )
    }

## Family summary

{
        md_table(
            [
                "family",
                "kind_mix",
                "total",
                "ready",
                "blocked",
                "in_progress",
                "complete",
            ],
            family_rows,
        )
    }

## Framework blockers summary

{
        md_table(
            ["blocker_key", "status", "affected_rows", "affected_families"],
            blocker_rows,
        )
    }

## Next-ready batches

{md_table(["batch", "ready_rows"], batch_rows)}

## Fixture coverage

{md_table(["metric", "count"], fixture_rows)}
"""

    OUT_PATH.write_text(text, encoding="utf-8")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
