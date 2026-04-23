Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on the already-implemented batch `pattern_wave_2`.

Rows in scope:
- algorithm:75 — Gap-and-Go
- algorithm:76 — Trendline Break Strategy
- algorithm:77 — Volatility Squeeze Breakout

Fixtures to verify:
- fixture.pattern_support_rejection_v1

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


