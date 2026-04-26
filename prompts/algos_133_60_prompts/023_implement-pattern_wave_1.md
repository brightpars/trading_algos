Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `pattern_wave_1`.

Rows in scope:
- algorithm:70 — Support and Resistance Bounce
- algorithm:71 — Breakout Retest
- algorithm:72 — Pivot Point Strategy
- algorithm:73 — Opening Range Breakout
- algorithm:74 — Inside Bar Breakout

Relevant fixtures:
- fixture.pattern_support_rejection_v1
- fixture.pattern_opening_range_breakout_v1

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


