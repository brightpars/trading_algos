Read these files first:
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml
- docs/algorithm_library_systematic_implementation_plan_v2.md

Tasks:
- Add a reusable fixture-loading helper that can read the fixture registry and locate declared datasets or placeholders.
- Add a reusable performance-smoke harness that can associate a strategy or method with its performance budget id.
- Add tests proving that fixture and performance budget rows can be loaded and that missing ids fail clearly.
- Do not implement algorithm batches yet.
- Run relevant tests.
- Stop when done.


