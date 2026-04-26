Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `relative_value_wave_2`.

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

Relevant blockers:
- blocker.spread_leg_output_v1
- blocker.hedge_ratio_helpers_v1
- blocker.multi_leg_reporting_v1

Relevant fixtures:
- fixture.statarb_pair_divergence_reversion_v1
- fixture.relative_value_curve_spread_v1

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


