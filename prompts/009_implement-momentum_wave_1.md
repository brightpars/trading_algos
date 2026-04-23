Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `momentum_wave_1`.

Rows in scope:
- algorithm:15 — Rate of Change Momentum
- algorithm:20 — Accelerating Momentum
- algorithm:21 — RSI Momentum Continuation
- algorithm:22 — Stochastic Momentum
- algorithm:23 — CCI Momentum

Relevant fixtures:
- fixture.momentum_sustained_up_v1

Tasks:
- Implement the batch code, registry wiring, diagnostics, and minimum viable tests.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas for every implemented row.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not harden unrelated batches.
- Run relevant tests.
- Stop when done.


