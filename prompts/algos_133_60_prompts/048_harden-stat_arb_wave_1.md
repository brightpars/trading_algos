Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on the already-implemented batch `stat_arb_wave_1`.

Rows in scope:
- algorithm:38 — Pairs Trading (Distance Method)
- algorithm:39 — Pairs Trading (Cointegration)
- algorithm:40 — Basket Statistical Arbitrage
- algorithm:51 — Funding/Basis Arbitrage

Fixtures to verify:
- fixture.statarb_pair_divergence_reversion_v1
- fixture.relative_value_curve_spread_v1

Check blocker state carefully:
- blocker.spread_leg_output_v1
- blocker.hedge_ratio_helpers_v1
- blocker.multi_leg_reporting_v1

Tasks:
- Review the batch implementation for correctness, reuse of shared helpers, and output normalization.
- Strengthen fixture coverage and expected-behavior checks.
- Add or improve tests for registration, parameter validation, short history or warmup handling, behavior, and performance-smoke coverage as appropriate.
- Check diagnostics and report payload fields so the dashboard can explain strategy outputs.
- Promote manifest statuses only if the evidence supports the promotion.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start unrelated batches.
- Do not mark rows `production_ready` without evidence.
- Run relevant tests.
- Stop when done.


