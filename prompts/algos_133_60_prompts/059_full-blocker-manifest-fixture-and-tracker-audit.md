Read these files first:
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml
- docs/algorithm_library_systematic_implementation_plan_v2.md

Tasks:
- Audit the manifest, blockers, fixture registry, and tracker for drift or dishonest status claims.
- Check for rows marked implemented but not actually registered.
- Check for rows marked tested without real fixture or test evidence.
- Check for rows marked complete while blocker keys are unresolved.
- Check for rows marked production_ready without sufficient evidence.
- Fix what is safe to fix automatically.
- Regenerate the tracker.
- Run relevant tests.
- Stop when done.


