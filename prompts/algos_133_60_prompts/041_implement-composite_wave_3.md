Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `composite_wave_3`.

Rows in scope:
- combination:4 — Constrained Multi-Factor Optimization
- combination:7 — Regime Switching / HMM Gating

Relevant blockers:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1
- blocker.regime_state_support_v1

Relevant fixtures:
- fixture.composite_risk_budget_v1
- fixture.composite_regime_switch_v1

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


