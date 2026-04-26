Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `factor_wave_2`.

Rows in scope:
- algorithm:86 — Value Strategy
- algorithm:87 — Quality Strategy
- algorithm:101 — Minimum Variance Strategy
- algorithm:105 — Size / Small-Cap Strategy
- algorithm:106 — Mid-Cap Tilt Strategy
- algorithm:110 — Profitability Factor Strategy
- algorithm:111 — Earnings Quality Strategy
- algorithm:113 — Low Leverage / Balance-Sheet Strength

Relevant blockers:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

Relevant fixtures:
- fixture.factor_monthly_rebalance_v1

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


