Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on the already-implemented batch `relative_value_wave_2`.

Rows in scope:
- algorithm:41 — Kalman Filter Pairs Trading
- algorithm:42 — Index Arbitrage
- algorithm:43 — ETF-NAV Arbitrage
- algorithm:44 — ADR Dual-Listing Arbitrage
- algorithm:45 — Convertible Arbitrage
- algorithm:46 — Merger Arbitrage
- algorithm:47 — Futures Cash-and-Carry Arbitrage
- algorithm:48 — Reverse Cash-and-Carry Arbitrage
- algorithm:49 — Triangular Arbitrage (FX/Crypto)
- algorithm:50 — Latency / Exchange Arbitrage
- algorithm:115 — Fixed-Income Arbitrage
- algorithm:116 — Swap Spread Arbitrage

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


