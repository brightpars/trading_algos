Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `event_wave_1`.

Rows in scope:
- algorithm:117 — Post-Earnings Announcement Drift (PEAD)
- algorithm:118 — Pre-Earnings Announcement Drift
- algorithm:119 — Earnings Announcement Premium
- algorithm:120 — Index Rebalancing Effect Strategy
- algorithm:121 — ETF Rebalancing Anticipation / Front-Run Strategy

Relevant blockers:
- blocker.event_calendar_v1
- blocker.event_window_execution_v1
- blocker.event_reporting_v1

Relevant fixtures:
- fixture.event_earnings_after_close_v1
- fixture.event_index_rebalance_window_v1

Tasks:
- Implement the batch code, registry wiring, diagnostics, and minimum viable tests.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas for every implemented row.
- If a blocker is still real, implement only the smallest reusable framework slice needed for this batch.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not harden unrelated batches.
- Run relevant tests.
- Stop when done.


