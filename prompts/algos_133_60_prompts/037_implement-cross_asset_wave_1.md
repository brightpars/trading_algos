Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `cross_asset_wave_1`.

Rows in scope:
- algorithm:78 — Carry Trade (FX/Rates)
- algorithm:79 — Yield Curve Steepener/Flattener
- algorithm:80 — Curve Roll-Down Strategy
- algorithm:81 — Commodity Term Structure / Roll Yield
- algorithm:82 — Risk-On / Risk-Off Regime
- algorithm:83 — Intermarket Confirmation
- algorithm:84 — Seasonality / Calendar Effects
- algorithm:85 — Earnings Drift / Post-Event Momentum

Relevant blockers:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.spread_leg_output_v1
- blocker.multi_leg_reporting_v1
- blocker.event_calendar_v1
- blocker.event_window_execution_v1
- blocker.event_reporting_v1

Relevant fixtures:
- fixture.cross_asset_carry_ranking_v1
- fixture.risk_on_off_regime_v1
- fixture.event_earnings_after_close_v1

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


