## PROMPT: bootstrap repository from starter pack
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md

Tasks:
- Verify or create these paths in the repo:
  - manifests/algorithm_library_manifest.yaml
  - manifests/algorithm_framework_blockers.yaml
  - manifests/algorithm_test_fixtures.yaml
  - manifests/algorithm_performance_budgets.yaml
  - docs/algorithm_library_implementation_tracker_initial.md
  - docs/algorithm_library_implementation_tracker_template.md
  - scripts/build_algorithm_library_tracker.py
- If the files already exist, compare them against the starter-pack versions and update them carefully instead of duplicating them.
- Make sure the tracker builder script can run in this repo layout.
- Do not implement algorithm batches yet.
- Run relevant tests.
- Stop when done.

## PROMPT: add manifest and registry consistency checks
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

## PROMPT: create fixture harness and performance-budget harness
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

## PROMPT: build shared tier-1 primitives and normalized child-output contract
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml

Tasks:
- Implement or refine shared helpers for moving averages, crossover detection, rolling highs/lows or channels, ATR or realized volatility, z-score helpers, ROC and momentum helpers, RSI, stochastic, CCI, MACD, and basic regression helpers as needed.
- Create or refine a normalized child-output contract that later composite methods can consume.
- Add tests for the helpers and output contract.
- Regenerate the tracker after changes.
- Do not start family batches yet.
- Run relevant tests.
- Stop when done.

## PROMPT: implement trend_wave_1
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `trend_wave_1`.

Rows in scope:
- algorithm:1 — Simple Moving Average Crossover
- algorithm:2 — Exponential Moving Average Crossover
- algorithm:3 — Triple Moving Average Crossover
- algorithm:4 — Price vs Moving Average
- algorithm:5 — Moving Average Ribbon Trend

Relevant fixtures:
- fixture.trend_monotonic_cross_v1
- fixture.trend_whipsaw_guard_v1

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

## PROMPT: harden trend_wave_1
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on the already-implemented batch `trend_wave_1`.

Rows in scope:
- algorithm:1 — Simple Moving Average Crossover
- algorithm:2 — Exponential Moving Average Crossover
- algorithm:3 — Triple Moving Average Crossover
- algorithm:4 — Price vs Moving Average
- algorithm:5 — Moving Average Ribbon Trend

Fixtures to verify:
- fixture.trend_monotonic_cross_v1
- fixture.trend_whipsaw_guard_v1

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

## PROMPT: implement composite_contract_wave_1
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `composite_contract_wave_1`.

Rows in scope:
- combination:1 — Hard Boolean Gating (AND / OR / Majority)
- combination:2 — Weighted Linear Score Blend

Relevant fixtures:
- fixture.composite_boolean_truth_table_v1
- fixture.composite_weighted_blend_v1

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

## PROMPT: harden composite_contract_wave_1
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on the already-implemented batch `composite_contract_wave_1`.

Rows in scope:
- combination:1 — Hard Boolean Gating (AND / OR / Majority)
- combination:2 — Weighted Linear Score Blend

Fixtures to verify:
- fixture.composite_boolean_truth_table_v1
- fixture.composite_weighted_blend_v1

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

## PROMPT: implement momentum_wave_1
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

## PROMPT: harden momentum_wave_1
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on the already-implemented batch `momentum_wave_1`.

Rows in scope:
- algorithm:15 — Rate of Change Momentum
- algorithm:20 — Accelerating Momentum
- algorithm:21 — RSI Momentum Continuation
- algorithm:22 — Stochastic Momentum
- algorithm:23 — CCI Momentum

Fixtures to verify:
- fixture.momentum_sustained_up_v1

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

## PROMPT: implement mean_reversion_wave_1
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `mean_reversion_wave_1`.

Rows in scope:
- algorithm:26 — Z-Score Mean Reversion
- algorithm:27 — Bollinger Bands Reversion
- algorithm:28 — RSI Reversion
- algorithm:29 — Stochastic Reversion
- algorithm:30 — CCI Reversion

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

## PROMPT: harden mean_reversion_wave_1
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on the already-implemented batch `mean_reversion_wave_1`.

Rows in scope:
- algorithm:26 — Z-Score Mean Reversion
- algorithm:27 — Bollinger Bands Reversion
- algorithm:28 — RSI Reversion
- algorithm:29 — Stochastic Reversion
- algorithm:30 — CCI Reversion

Fixtures to verify:
- fixture.mean_reversion_one_overshoot_v1

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

## PROMPT: implement trend_wave_2
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `trend_wave_2`.

Rows in scope:
- algorithm:6 — Breakout (Donchian Channel)
- algorithm:7 — Channel Breakout with Confirmation
- algorithm:8 — ADX Trend Filter
- algorithm:9 — Parabolic SAR Trend Following
- algorithm:10 — SuperTrend

Relevant fixtures:
- fixture.trend_monotonic_cross_v1
- fixture.trend_whipsaw_guard_v1

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

## PROMPT: harden trend_wave_2
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on the already-implemented batch `trend_wave_2`.

Rows in scope:
- algorithm:6 — Breakout (Donchian Channel)
- algorithm:7 — Channel Breakout with Confirmation
- algorithm:8 — ADX Trend Filter
- algorithm:9 — Parabolic SAR Trend Following
- algorithm:10 — SuperTrend

Fixtures to verify:
- fixture.trend_monotonic_cross_v1
- fixture.trend_whipsaw_guard_v1

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

## PROMPT: implement trend_wave_3
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `trend_wave_3`.

Rows in scope:
- algorithm:11 — Ichimoku Trend Strategy
- algorithm:12 — MACD Trend Strategy
- algorithm:13 — Linear Regression Trend
- algorithm:14 — Time-Series Momentum

Relevant fixtures:
- fixture.trend_monotonic_cross_v1
- fixture.trend_whipsaw_guard_v1

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

## PROMPT: harden trend_wave_3
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on the already-implemented batch `trend_wave_3`.

Rows in scope:
- algorithm:11 — Ichimoku Trend Strategy
- algorithm:12 — MACD Trend Strategy
- algorithm:13 — Linear Regression Trend
- algorithm:14 — Time-Series Momentum

Fixtures to verify:
- fixture.trend_monotonic_cross_v1
- fixture.trend_whipsaw_guard_v1

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

## PROMPT: implement momentum_wave_2
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `momentum_wave_2`.

Rows in scope:
- algorithm:24 — KST (Know Sure Thing)
- algorithm:25 — Volume-Confirmed Momentum

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

## PROMPT: harden momentum_wave_2
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on the already-implemented batch `momentum_wave_2`.

Rows in scope:
- algorithm:24 — KST (Know Sure Thing)
- algorithm:25 — Volume-Confirmed Momentum

Fixtures to verify:
- fixture.momentum_sustained_up_v1

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

## PROMPT: implement mean_reversion_wave_2
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `mean_reversion_wave_2`.

Rows in scope:
- algorithm:31 — Williams %R Reversion
- algorithm:34 — Range Reversion
- algorithm:36 — Long-Horizon Reversal
- algorithm:37 — Volatility-Adjusted Reversion

Relevant fixtures:
- fixture.mean_reversion_one_overshoot_v1
- fixture.mean_reversion_range_oscillation_v1

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

## PROMPT: harden mean_reversion_wave_2
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on the already-implemented batch `mean_reversion_wave_2`.

Rows in scope:
- algorithm:31 — Williams %R Reversion
- algorithm:34 — Range Reversion
- algorithm:36 — Long-Horizon Reversal
- algorithm:37 — Volatility-Adjusted Reversion

Fixtures to verify:
- fixture.mean_reversion_one_overshoot_v1
- fixture.mean_reversion_range_oscillation_v1

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

## PROMPT: implement volatility_wave_1
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `volatility_wave_1`.

Rows in scope:
- algorithm:52 — Volatility Breakout
- algorithm:53 — ATR Channel Breakout
- algorithm:54 — Volatility Mean Reversion

Relevant fixtures:
- fixture.volatility_compression_release_v1

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

## PROMPT: harden volatility_wave_1
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on the already-implemented batch `volatility_wave_1`.

Rows in scope:
- algorithm:52 — Volatility Breakout
- algorithm:53 — ATR Channel Breakout
- algorithm:54 — Volatility Mean Reversion

Fixtures to verify:
- fixture.volatility_compression_release_v1

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

## PROMPT: implement pattern_wave_1
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

## PROMPT: harden pattern_wave_1
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on the already-implemented batch `pattern_wave_1`.

Rows in scope:
- algorithm:70 — Support and Resistance Bounce
- algorithm:71 — Breakout Retest
- algorithm:72 — Pivot Point Strategy
- algorithm:73 — Opening Range Breakout
- algorithm:74 — Inside Bar Breakout

Fixtures to verify:
- fixture.pattern_support_rejection_v1
- fixture.pattern_opening_range_breakout_v1

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

## PROMPT: implement pattern_wave_2
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `pattern_wave_2`.

Rows in scope:
- algorithm:75 — Gap-and-Go
- algorithm:76 — Trendline Break Strategy
- algorithm:77 — Volatility Squeeze Breakout

Relevant fixtures:
- fixture.pattern_support_rejection_v1

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

## PROMPT: harden pattern_wave_2
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

## PROMPT: implement mean_reversion_wave_3
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

## PROMPT: harden mean_reversion_wave_3
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on the already-implemented batch `mean_reversion_wave_3`.

Rows in scope:
- algorithm:32 — Intraday VWAP Reversion
- algorithm:33 — Opening Gap Fade
- algorithm:35 — Ornstein-Uhlenbeck Reversion

Fixtures to verify:
- fixture.mean_reversion_one_overshoot_v1

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

## PROMPT: implement momentum_wave_3
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `momentum_wave_3`.

Rows in scope:
- algorithm:16 — Cross-Sectional Momentum
- algorithm:17 — Relative Strength Momentum
- algorithm:18 — Dual Momentum
- algorithm:19 — Residual Momentum

Relevant blockers:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

Relevant fixtures:
- fixture.momentum_cross_sectional_ranking_v1

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

## PROMPT: harden momentum_wave_3
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on the already-implemented batch `momentum_wave_3`.

Rows in scope:
- algorithm:16 — Cross-Sectional Momentum
- algorithm:17 — Relative Strength Momentum
- algorithm:18 — Dual Momentum
- algorithm:19 — Residual Momentum

Fixtures to verify:
- fixture.momentum_cross_sectional_ranking_v1

Check blocker state carefully:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

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

## PROMPT: implement factor_wave_1
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `factor_wave_1`.

Rows in scope:
- algorithm:100 — Low Volatility Strategy
- algorithm:103 — Low Beta / Betting-Against-Beta
- algorithm:107 — Dividend Yield Strategy
- algorithm:108 — Growth Factor Strategy
- algorithm:109 — Liquidity Factor Strategy

Relevant blockers:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

Relevant fixtures:
- fixture.factor_monthly_rebalance_v1

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

## PROMPT: harden factor_wave_1
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on the already-implemented batch `factor_wave_1`.

Rows in scope:
- algorithm:100 — Low Volatility Strategy
- algorithm:103 — Low Beta / Betting-Against-Beta
- algorithm:107 — Dividend Yield Strategy
- algorithm:108 — Growth Factor Strategy
- algorithm:109 — Liquidity Factor Strategy

Fixtures to verify:
- fixture.factor_monthly_rebalance_v1

Check blocker state carefully:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

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

## PROMPT: implement factor_wave_2
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `factor_wave_2`.

Rows in scope:
- algorithm:86 — Value Strategy
- algorithm:87 — Quality Strategy
- algorithm:101 — Minimum Variance Strategy
- algorithm:105 — Size / Small-Cap Strategy
- algorithm:106 — Mid-Cap Tilt Strategy
- algorithm:110 — Profitability Factor Strategy
- algorithm:111 — Earnings Quality Strategy
- algorithm:113 — Low Leverage / Balance-Sheet Strength

Relevant blockers:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

Relevant fixtures:
- fixture.factor_monthly_rebalance_v1

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

## PROMPT: harden factor_wave_2
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on the already-implemented batch `factor_wave_2`.

Rows in scope:
- algorithm:86 — Value Strategy
- algorithm:87 — Quality Strategy
- algorithm:101 — Minimum Variance Strategy
- algorithm:105 — Size / Small-Cap Strategy
- algorithm:106 — Mid-Cap Tilt Strategy
- algorithm:110 — Profitability Factor Strategy
- algorithm:111 — Earnings Quality Strategy
- algorithm:113 — Low Leverage / Balance-Sheet Strength

Fixtures to verify:
- fixture.factor_monthly_rebalance_v1

Check blocker state carefully:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

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

## PROMPT: implement factor_wave_3
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `factor_wave_3`.

Rows in scope:
- algorithm:88 — Multi-Factor Composite
- algorithm:102 — Residual Volatility Strategy
- algorithm:104 — Defensive Equity Strategy
- algorithm:112 — Investment Quality Strategy
- algorithm:114 — Earnings Stability / Low Earnings Variability

Relevant blockers:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

Relevant fixtures:
- fixture.factor_monthly_rebalance_v1

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

## PROMPT: harden factor_wave_3
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on the already-implemented batch `factor_wave_3`.

Rows in scope:
- algorithm:88 — Multi-Factor Composite
- algorithm:102 — Residual Volatility Strategy
- algorithm:104 — Defensive Equity Strategy
- algorithm:112 — Investment Quality Strategy
- algorithm:114 — Earnings Stability / Low Earnings Variability

Fixtures to verify:
- fixture.factor_monthly_rebalance_v1

Check blocker state carefully:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

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

## PROMPT: implement cross_asset_wave_1
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `cross_asset_wave_1`.

Rows in scope:
- algorithm:78 — Carry Trade (FX/Rates)
- algorithm:79 — Yield Curve Steepener/Flattener
- algorithm:80 — Curve Roll-Down Strategy
- algorithm:81 — Commodity Term Structure / Roll Yield
- algorithm:82 — Risk-On / Risk-Off Regime
- algorithm:83 — Intermarket Confirmation
- algorithm:84 — Seasonality / Calendar Effects
- algorithm:85 — Earnings Drift / Post-Event Momentum

Relevant blockers:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.spread_leg_output_v1
- blocker.multi_leg_reporting_v1
- blocker.event_calendar_v1
- blocker.event_window_execution_v1
- blocker.event_reporting_v1

Relevant fixtures:
- fixture.cross_asset_carry_ranking_v1
- fixture.risk_on_off_regime_v1
- fixture.event_earnings_after_close_v1

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

## PROMPT: harden cross_asset_wave_1
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on the already-implemented batch `cross_asset_wave_1`.

Rows in scope:
- algorithm:78 — Carry Trade (FX/Rates)
- algorithm:79 — Yield Curve Steepener/Flattener
- algorithm:80 — Curve Roll-Down Strategy
- algorithm:81 — Commodity Term Structure / Roll Yield
- algorithm:82 — Risk-On / Risk-Off Regime
- algorithm:83 — Intermarket Confirmation
- algorithm:84 — Seasonality / Calendar Effects
- algorithm:85 — Earnings Drift / Post-Event Momentum

Fixtures to verify:
- fixture.cross_asset_carry_ranking_v1
- fixture.risk_on_off_regime_v1
- fixture.event_earnings_after_close_v1

Check blocker state carefully:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.spread_leg_output_v1
- blocker.multi_leg_reporting_v1
- blocker.event_calendar_v1
- blocker.event_window_execution_v1
- blocker.event_reporting_v1

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

## PROMPT: implement composite_wave_2
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `composite_wave_2`.

Rows in scope:
- combination:3 — Rank Aggregation
- combination:5 — Risk Budgeting / Risk Parity
- combination:6 — Volatility Targeting Overlay

Relevant blockers:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

Relevant fixtures:
- fixture.composite_rank_aggregation_v1
- fixture.composite_risk_budget_v1

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

## PROMPT: harden composite_wave_2
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on the already-implemented batch `composite_wave_2`.

Rows in scope:
- combination:3 — Rank Aggregation
- combination:5 — Risk Budgeting / Risk Parity
- combination:6 — Volatility Targeting Overlay

Fixtures to verify:
- fixture.composite_rank_aggregation_v1
- fixture.composite_risk_budget_v1

Check blocker state carefully:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

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

## PROMPT: implement composite_wave_3
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `composite_wave_3`.

Rows in scope:
- combination:4 — Constrained Multi-Factor Optimization
- combination:7 — Regime Switching / HMM Gating

Relevant blockers:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1
- blocker.regime_state_support_v1

Relevant fixtures:
- fixture.composite_risk_budget_v1
- fixture.composite_regime_switch_v1

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

## PROMPT: harden composite_wave_3
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on the already-implemented batch `composite_wave_3`.

Rows in scope:
- combination:4 — Constrained Multi-Factor Optimization
- combination:7 — Regime Switching / HMM Gating

Fixtures to verify:
- fixture.composite_risk_budget_v1
- fixture.composite_regime_switch_v1

Check blocker state carefully:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1
- blocker.regime_state_support_v1

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

## PROMPT: implement advanced_model_wave_1
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `advanced_model_wave_1`.

Rows in scope:
- algorithm:89 — Sentiment Strategy
- algorithm:90 — Machine Learning Classifier
- algorithm:91 — Machine Learning Regressor
- algorithm:92 — Regime-Switching Strategy
- algorithm:93 — Ensemble / Voting Strategy

Relevant blockers:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

Relevant fixtures:
- fixture.factor_monthly_rebalance_v1

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

## PROMPT: harden advanced_model_wave_1
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on the already-implemented batch `advanced_model_wave_1`.

Rows in scope:
- algorithm:89 — Sentiment Strategy
- algorithm:90 — Machine Learning Classifier
- algorithm:91 — Machine Learning Regressor
- algorithm:92 — Regime-Switching Strategy
- algorithm:93 — Ensemble / Voting Strategy

Fixtures to verify:
- fixture.factor_monthly_rebalance_v1

Check blocker state carefully:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

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

## PROMPT: implement event_wave_1
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `event_wave_1`.

Rows in scope:
- algorithm:117 — Post-Earnings Announcement Drift (PEAD)
- algorithm:118 — Pre-Earnings Announcement Drift
- algorithm:119 — Earnings Announcement Premium
- algorithm:120 — Index Rebalancing Effect Strategy
- algorithm:121 — ETF Rebalancing Anticipation / Front-Run Strategy

Relevant blockers:
- blocker.event_calendar_v1
- blocker.event_window_execution_v1
- blocker.event_reporting_v1

Relevant fixtures:
- fixture.event_earnings_after_close_v1
- fixture.event_index_rebalance_window_v1

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

## PROMPT: harden event_wave_1
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on the already-implemented batch `event_wave_1`.

Rows in scope:
- algorithm:117 — Post-Earnings Announcement Drift (PEAD)
- algorithm:118 — Pre-Earnings Announcement Drift
- algorithm:119 — Earnings Announcement Premium
- algorithm:120 — Index Rebalancing Effect Strategy
- algorithm:121 — ETF Rebalancing Anticipation / Front-Run Strategy

Fixtures to verify:
- fixture.event_earnings_after_close_v1
- fixture.event_index_rebalance_window_v1

Check blocker state carefully:
- blocker.event_calendar_v1
- blocker.event_window_execution_v1
- blocker.event_reporting_v1

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

## PROMPT: implement stat_arb_wave_1
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `stat_arb_wave_1`.

Rows in scope:
- algorithm:38 — Pairs Trading (Distance Method)
- algorithm:39 — Pairs Trading (Cointegration)
- algorithm:40 — Basket Statistical Arbitrage
- algorithm:51 — Funding/Basis Arbitrage

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

## PROMPT: harden stat_arb_wave_1
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on the already-implemented batch `stat_arb_wave_1`.

Rows in scope:
- algorithm:38 — Pairs Trading (Distance Method)
- algorithm:39 — Pairs Trading (Cointegration)
- algorithm:40 — Basket Statistical Arbitrage
- algorithm:51 — Funding/Basis Arbitrage

Fixtures to verify:
- fixture.statarb_pair_divergence_reversion_v1
- fixture.relative_value_curve_spread_v1

Check blocker state carefully:
- blocker.spread_leg_output_v1
- blocker.hedge_ratio_helpers_v1
- blocker.multi_leg_reporting_v1

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

## PROMPT: implement relative_value_wave_2
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

## PROMPT: harden relative_value_wave_2
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on the already-implemented batch `relative_value_wave_2`.

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

Fixtures to verify:
- fixture.statarb_pair_divergence_reversion_v1
- fixture.relative_value_curve_spread_v1

Check blocker state carefully:
- blocker.spread_leg_output_v1
- blocker.hedge_ratio_helpers_v1
- blocker.multi_leg_reporting_v1

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

## PROMPT: implement volatility_wave_2
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

## PROMPT: harden volatility_wave_2
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on the already-implemented batch `volatility_wave_2`.

Rows in scope:
- algorithm:55 — Delta-Neutral Volatility Trading
- algorithm:56 — Gamma Scalping
- algorithm:57 — Volatility Risk Premium Capture
- algorithm:58 — Dispersion Trading
- algorithm:59 — Skew Trading
- algorithm:60 — Term Structure Trading
- algorithm:61 — Straddle Breakout Timing

Fixtures to verify:
- fixture.options_iv_rv_gap_v1

Check blocker state carefully:
- blocker.options_chain_v1
- blocker.greeks_v1

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

## PROMPT: implement composite_wave_4
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `composite_wave_4`.

Rows in scope:
- combination:8 — Bagging Ensemble
- combination:9 — Boosting Ensemble
- combination:10 — Stacking / Meta-Learning

Relevant fixtures:
- fixture.composite_ml_ensemble_v1

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

## PROMPT: harden composite_wave_4
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on the already-implemented batch `composite_wave_4`.

Rows in scope:
- combination:8 — Bagging Ensemble
- combination:9 — Boosting Ensemble
- combination:10 — Stacking / Meta-Learning

Fixtures to verify:
- fixture.composite_ml_ensemble_v1

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

## PROMPT: implement composite_wave_5
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on batch `composite_wave_5`.

Rows in scope:
- combination:11 — RL Allocation Controller
- combination:12 — Hierarchical Controller / Meta-Policy

Relevant blockers:
- blocker.rl_environment_v1

Relevant fixtures:
- fixture.composite_rl_policy_stub_v1

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

## PROMPT: harden composite_wave_5
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on the already-implemented batch `composite_wave_5`.

Rows in scope:
- combination:11 — RL Allocation Controller
- combination:12 — Hierarchical Controller / Meta-Policy

Fixtures to verify:
- fixture.composite_rl_policy_stub_v1

Check blocker state carefully:
- blocker.rl_environment_v1

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

## PROMPT: implement advanced_wave_blocked
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

## PROMPT: harden advanced_wave_blocked
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml

Work only on the already-implemented batch `advanced_wave_blocked`.

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

Fixtures to verify:
- fixture.microstructure_top_of_book_imbalance_v1
- fixture.microstructure_queue_state_v1
- fixture.execution_twap_schedule_v1
- fixture.execution_vwap_curve_drift_v1

Check blocker state carefully:
- blocker.order_book_input_v1
- blocker.own_order_state_v1
- blocker.execution_plan_output_v1
- blocker.fill_simulation_v1

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

## PROMPT: full blocker, manifest, fixture, and tracker audit
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

## PROMPT: final repo-wide consolidation and readiness pass
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml

Tasks:
- Refactor obvious duplication across family modules without changing external behavior.
- Improve documentation comments, schema clarity, and registry readability where needed.
- Verify that tracker generation, consistency tests, fixture harnesses, and performance-smoke hooks work together coherently.
- Make a final honest pass over delivery status and operational readiness values.
- Do not start new strategy families or new framework expansions in this prompt.
- Run relevant tests.
- Stop when done.
