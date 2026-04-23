Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `advanced_wave_blocked`.

Rows in scope:
- algorithm:62 — Bid-Ask Market Making
- algorithm:63 — Inventory-Skewed Market Making
- algorithm:64 — Order Book Imbalance Strategy
- algorithm:65 — Microprice Strategy
- algorithm:66 — Queue Position Strategy
- algorithm:67 — Liquidity Rebate Capture
- algorithm:68 — Opening Auction Strategy
- algorithm:69 — Closing Auction Strategy
- algorithm:94 — TWAP
- algorithm:95 — VWAP
- algorithm:96 — POV / Participation Rate
- algorithm:97 — Implementation Shortfall / Arrival Price
- algorithm:98 — Iceberg / Hidden Size
- algorithm:99 — Sniper / Opportunistic Execution

Relevant blockers:
- blocker.order_book_input_v1
- blocker.own_order_state_v1
- blocker.execution_plan_output_v1
- blocker.fill_simulation_v1

Relevant fixtures:
- fixture.microstructure_top_of_book_imbalance_v1
- fixture.microstructure_queue_state_v1
- fixture.execution_twap_schedule_v1
- fixture.execution_vwap_curve_drift_v1

Tasks:
- Implement the batch code, registry wiring, diagnostics, and minimum viable tests.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas for every implemented row.
- If a blocker is still real, implement only the smallest reusable framework slice needed for this batch.
- Do not pretend framework-heavy rows are production-ready.
- It is acceptable to leave rows as `blocked_framework` or `prototype_only` after adding justified scaffolding and tests.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not harden unrelated batches.
- Run relevant tests.
- Stop when done.


