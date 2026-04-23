Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `volatility_wave_2`.

Rows in scope:
- algorithm:55 — Delta-Neutral Volatility Trading
- algorithm:56 — Gamma Scalping
- algorithm:57 — Volatility Risk Premium Capture
- algorithm:58 — Dispersion Trading
- algorithm:59 — Skew Trading
- algorithm:60 — Term Structure Trading
- algorithm:61 — Straddle Breakout Timing

Relevant blockers:
- blocker.options_chain_v1
- blocker.greeks_v1

Relevant fixtures:
- fixture.options_iv_rv_gap_v1

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


