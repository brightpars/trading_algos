Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `mean_reversion_wave_3`.

Rows in scope:
- algorithm:32 — Intraday VWAP Reversion
- algorithm:33 — Opening Gap Fade
- algorithm:35 — Ornstein-Uhlenbeck Reversion

Relevant fixtures:
- fixture.mean_reversion_one_overshoot_v1

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


