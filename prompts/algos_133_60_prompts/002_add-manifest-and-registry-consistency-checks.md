Read these files first:
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml
- docs/algorithm_library_systematic_implementation_plan_v2.md

Tasks:
- Add or update tests that validate manifest integrity, duplicate catalog_ref detection, blocker key validity, fixture id validity, and performance_budget_id validity.
- Keep the tests lightweight and deterministic.
- Do not implement algorithm batches yet.
- Regenerate the tracker once the consistency checks pass.
- Run relevant tests.
- Stop when done.


