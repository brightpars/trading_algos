# Algorithm Library Coder Prompts — Scenario 2 (Realistic 60-Prompt Plan)

## Before using these prompts

### Required files to copy into the repo first

- Unpack `algorithm_library_starter_pack_v1.zip` into the repository root so these paths exist:

  - `manifests/algorithm_library_manifest.yaml`

  - `manifests/algorithm_framework_blockers.yaml`

  - `manifests/algorithm_test_fixtures.yaml`

  - `manifests/algorithm_performance_budgets.yaml`

  - `docs/algorithm_library_implementation_tracker_initial.md`

  - `docs/algorithm_library_implementation_tracker_template.md`

  - `scripts/build_algorithm_library_tracker.py`

- Also copy these planning/reference docs into the repo:

  - `docs/algorithm_library_requirements_v4.md`

  - `docs/algorithm_library_systematic_implementation_plan_v2.md`


### How to use this document

- This is the **realistic** execution mode.

- It uses:

  - 4 setup prompts

  - 27 implementation prompts

  - 27 hardening prompts

  - 2 final audit/consolidation prompts

- Give the prompts to the LLM coder **one at a time**, in the listed order.

- Do not skip the hardening prompts; that is where fixture coverage, tracker correctness, and honest status promotion are enforced.


## Prompt 01 — Repository bootstrap from starter pack

```text
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md

Goal:
Bootstrap the repository from the starter pack and make sure the manifest-first workflow is wired into the codebase.

Tasks:
- Verify or create these paths in the repo:
  - manifests/algorithm_library_manifest.yaml
  - manifests/algorithm_framework_blockers.yaml
  - manifests/algorithm_test_fixtures.yaml
  - manifests/algorithm_performance_budgets.yaml
  - docs/algorithm_library_implementation_tracker_initial.md
  - docs/algorithm_library_implementation_tracker_template.md
  - scripts/build_algorithm_library_tracker.py
- If the files already exist, compare them against the provided starter-pack versions and update them carefully instead of duplicating them.
- Make sure the tracker builder script can run in this repo layout.
- Do not implement algorithm batches yet.
- Return a summary of:
  - files created or updated
  - any repo-path mismatches you had to fix
  - whether the tracker script runs successfully
```

## Prompt 02 — Manifest, blocker, fixture, and budget consistency checks

```text
Read these files first:
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml
- docs/algorithm_library_systematic_implementation_plan_v2.md

Goal:
Add consistency checks so the manifest ecosystem can be trusted before algorithm implementation starts.

Tasks:
- Add or update tests that validate:
  - manifest rows load correctly
  - no duplicate catalog_ref values exist
  - all blocker keys referenced by rows exist in the blocker registry
  - all fixture ids referenced by rows exist in the fixture registry
  - all performance_budget_id values referenced by rows exist
- Keep the tests lightweight and deterministic.
- Do not implement any algorithm batch yet.
- Regenerate the tracker once the consistency checks pass.
- Return:
  - test files added
  - validation rules implemented
  - any inconsistencies found and fixed
```

## Prompt 03 — Fixture harness and performance-budget harness

```text
Read these files first:
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml
- docs/algorithm_library_systematic_implementation_plan_v2.md

Goal:
Create the reusable test harnesses that later batches will rely on.

Tasks:
- Add a reusable fixture-loading helper that can read the fixture registry and locate the declared datasets or placeholders.
- Add a reusable performance-smoke harness that can associate a strategy or method with its performance budget id.
- The first version can be minimal, but it must be repository-native and testable.
- Add tests proving that:
  - fixture registry rows can be loaded
  - performance budget rows can be loaded
  - missing fixture ids or budget ids fail clearly
- Do not implement algorithm batches yet.
- Return:
  - helper modules added
  - tests added
  - any assumptions that still need later refinement
```

## Prompt 04 — Shared Tier-1 primitives and normalized child-output contract

```text
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml

Goal:
Build the shared primitives and normalized output contracts that the early Tier-1 batches depend on.

Tasks:
- Implement or refine shared helpers for:
  - moving averages
  - crossover detection
  - rolling highs/lows or channels
  - ATR / realized volatility
  - z-score helpers
  - ROC and basic momentum helpers
  - RSI, stochastic, CCI, MACD helpers
  - basic regression helpers if needed
- Create or refine a normalized child-output contract that later composite methods can consume.
- Add tests for the helpers and output contract.
- Regenerate the tracker after changes.
- Do not start family batches yet.
- Return:
  - shared helper modules added
  - output-contract modules added
  - tests added
  - any primitive still missing for early Tier-1 work
```

## Prompt 05 — Implement `trend_wave_1`

### Batch scope

- Simple Moving Average Crossover
- Exponential Moving Average Crossover
- Triple Moving Average Crossover
- Price vs Moving Average
- Moving Average Ribbon Trend

```text
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

Goal:
Implement the batch code, registry wiring, fixtures, and minimum viable tests.

Requirements:
- Follow the manifest row metadata for exact target modules, catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas and diagnostics for every implemented row.
- Wire the relevant fixtures and add minimum viable batch tests.
- Regenerate the tracker after making changes.
- Do not harden unrelated batches.
- Do not move rows to `complete` unless all criteria are already satisfied.

Fixtures to use or update:
- fixture.trend_monotonic_cross_v1
- fixture.trend_whipsaw_guard_v1


When finished, report:
- changed files
- rows implemented
- blockers resolved or still open
- tests added/run
- tracker impact
```

## Prompt 06 — Harden `trend_wave_1`

### Batch scope

- Simple Moving Average Crossover
- Exponential Moving Average Crossover
- Triple Moving Average Crossover
- Price vs Moving Average
- Moving Average Ribbon Trend

```text
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

Goal:
Harden this batch. Close test, fixture, reporting, and manifest-status gaps without starting new batches.

Tasks:
- Review the batch implementation for correctness, output normalization, and reuse of shared helpers.
- Strengthen fixture coverage and expected-behavior checks for the rows in this batch.
- Add or improve tests for registration, parameter validation, short history or warmup handling, behavior, and performance-smoke coverage as appropriate.
- Check diagnostics and report payload fields so the dashboard can explain the strategy outputs.
- Promote manifest statuses only if evidence supports the promotion.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Leave a concise batch summary in your final response.

Fixtures to verify:
- fixture.trend_monotonic_cross_v1
- fixture.trend_whipsaw_guard_v1


Do not:
- start unrelated batches
- silently change batch ownership
- mark rows `production_ready` without evidence
- hide blockers that still exist

Return:
- changed files
- tests added or strengthened
- statuses advanced
- unresolved issues
```

## Prompt 07 — Implement `composite_contract_wave_1`

### Batch scope

- Hard Boolean Gating (AND / OR / Majority)
- Weighted Linear Score Blend

```text
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

Goal:
Implement the batch code, registry wiring, fixtures, and minimum viable tests.

Requirements:
- Follow the manifest row metadata for exact target modules, catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas and diagnostics for every implemented row.
- Wire the relevant fixtures and add minimum viable batch tests.
- Regenerate the tracker after making changes.
- Do not harden unrelated batches.
- Do not move rows to `complete` unless all criteria are already satisfied.

Fixtures to use or update:
- fixture.composite_boolean_truth_table_v1
- fixture.composite_weighted_blend_v1


When finished, report:
- changed files
- rows implemented
- blockers resolved or still open
- tests added/run
- tracker impact
```

## Prompt 08 — Harden `composite_contract_wave_1`

### Batch scope

- Hard Boolean Gating (AND / OR / Majority)
- Weighted Linear Score Blend

```text
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

Goal:
Harden this batch. Close test, fixture, reporting, and manifest-status gaps without starting new batches.

Tasks:
- Review the batch implementation for correctness, output normalization, and reuse of shared helpers.
- Strengthen fixture coverage and expected-behavior checks for the rows in this batch.
- Add or improve tests for registration, parameter validation, short history or warmup handling, behavior, and performance-smoke coverage as appropriate.
- Check diagnostics and report payload fields so the dashboard can explain the strategy outputs.
- Promote manifest statuses only if evidence supports the promotion.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Leave a concise batch summary in your final response.

Fixtures to verify:
- fixture.composite_boolean_truth_table_v1
- fixture.composite_weighted_blend_v1


Do not:
- start unrelated batches
- silently change batch ownership
- mark rows `production_ready` without evidence
- hide blockers that still exist

Return:
- changed files
- tests added or strengthened
- statuses advanced
- unresolved issues
```

## Prompt 09 — Implement `momentum_wave_1`

### Batch scope

- Rate of Change Momentum
- Accelerating Momentum
- RSI Momentum Continuation
- Stochastic Momentum
- CCI Momentum

```text
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

Goal:
Implement the batch code, registry wiring, fixtures, and minimum viable tests.

Requirements:
- Follow the manifest row metadata for exact target modules, catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas and diagnostics for every implemented row.
- Wire the relevant fixtures and add minimum viable batch tests.
- Regenerate the tracker after making changes.
- Do not harden unrelated batches.
- Do not move rows to `complete` unless all criteria are already satisfied.

Fixtures to use or update:
- fixture.momentum_sustained_up_v1


When finished, report:
- changed files
- rows implemented
- blockers resolved or still open
- tests added/run
- tracker impact
```

## Prompt 10 — Harden `momentum_wave_1`

### Batch scope

- Rate of Change Momentum
- Accelerating Momentum
- RSI Momentum Continuation
- Stochastic Momentum
- CCI Momentum

```text
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

Goal:
Harden this batch. Close test, fixture, reporting, and manifest-status gaps without starting new batches.

Tasks:
- Review the batch implementation for correctness, output normalization, and reuse of shared helpers.
- Strengthen fixture coverage and expected-behavior checks for the rows in this batch.
- Add or improve tests for registration, parameter validation, short history or warmup handling, behavior, and performance-smoke coverage as appropriate.
- Check diagnostics and report payload fields so the dashboard can explain the strategy outputs.
- Promote manifest statuses only if evidence supports the promotion.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Leave a concise batch summary in your final response.

Fixtures to verify:
- fixture.momentum_sustained_up_v1


Do not:
- start unrelated batches
- silently change batch ownership
- mark rows `production_ready` without evidence
- hide blockers that still exist

Return:
- changed files
- tests added or strengthened
- statuses advanced
- unresolved issues
```

## Prompt 11 — Implement `mean_reversion_wave_1`

### Batch scope

- Z-Score Mean Reversion
- Bollinger Bands Reversion
- RSI Reversion
- Stochastic Reversion
- CCI Reversion

```text
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

Goal:
Implement the batch code, registry wiring, fixtures, and minimum viable tests.

Requirements:
- Follow the manifest row metadata for exact target modules, catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas and diagnostics for every implemented row.
- Wire the relevant fixtures and add minimum viable batch tests.
- Regenerate the tracker after making changes.
- Do not harden unrelated batches.
- Do not move rows to `complete` unless all criteria are already satisfied.

Fixtures to use or update:
- fixture.mean_reversion_one_overshoot_v1


When finished, report:
- changed files
- rows implemented
- blockers resolved or still open
- tests added/run
- tracker impact
```

## Prompt 12 — Harden `mean_reversion_wave_1`

### Batch scope

- Z-Score Mean Reversion
- Bollinger Bands Reversion
- RSI Reversion
- Stochastic Reversion
- CCI Reversion

```text
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

Goal:
Harden this batch. Close test, fixture, reporting, and manifest-status gaps without starting new batches.

Tasks:
- Review the batch implementation for correctness, output normalization, and reuse of shared helpers.
- Strengthen fixture coverage and expected-behavior checks for the rows in this batch.
- Add or improve tests for registration, parameter validation, short history or warmup handling, behavior, and performance-smoke coverage as appropriate.
- Check diagnostics and report payload fields so the dashboard can explain the strategy outputs.
- Promote manifest statuses only if evidence supports the promotion.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Leave a concise batch summary in your final response.

Fixtures to verify:
- fixture.mean_reversion_one_overshoot_v1


Do not:
- start unrelated batches
- silently change batch ownership
- mark rows `production_ready` without evidence
- hide blockers that still exist

Return:
- changed files
- tests added or strengthened
- statuses advanced
- unresolved issues
```

## Prompt 13 — Implement `trend_wave_2`

### Batch scope

- Breakout (Donchian Channel)
- Channel Breakout with Confirmation
- ADX Trend Filter
- Parabolic SAR Trend Following
- SuperTrend

```text
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

Goal:
Implement the batch code, registry wiring, fixtures, and minimum viable tests.

Requirements:
- Follow the manifest row metadata for exact target modules, catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas and diagnostics for every implemented row.
- Wire the relevant fixtures and add minimum viable batch tests.
- Regenerate the tracker after making changes.
- Do not harden unrelated batches.
- Do not move rows to `complete` unless all criteria are already satisfied.

Fixtures to use or update:
- fixture.trend_monotonic_cross_v1
- fixture.trend_whipsaw_guard_v1


When finished, report:
- changed files
- rows implemented
- blockers resolved or still open
- tests added/run
- tracker impact
```

## Prompt 14 — Harden `trend_wave_2`

### Batch scope

- Breakout (Donchian Channel)
- Channel Breakout with Confirmation
- ADX Trend Filter
- Parabolic SAR Trend Following
- SuperTrend

```text
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

Goal:
Harden this batch. Close test, fixture, reporting, and manifest-status gaps without starting new batches.

Tasks:
- Review the batch implementation for correctness, output normalization, and reuse of shared helpers.
- Strengthen fixture coverage and expected-behavior checks for the rows in this batch.
- Add or improve tests for registration, parameter validation, short history or warmup handling, behavior, and performance-smoke coverage as appropriate.
- Check diagnostics and report payload fields so the dashboard can explain the strategy outputs.
- Promote manifest statuses only if evidence supports the promotion.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Leave a concise batch summary in your final response.

Fixtures to verify:
- fixture.trend_monotonic_cross_v1
- fixture.trend_whipsaw_guard_v1


Do not:
- start unrelated batches
- silently change batch ownership
- mark rows `production_ready` without evidence
- hide blockers that still exist

Return:
- changed files
- tests added or strengthened
- statuses advanced
- unresolved issues
```

## Prompt 15 — Implement `trend_wave_3`

### Batch scope

- Ichimoku Trend Strategy
- MACD Trend Strategy
- Linear Regression Trend
- Time-Series Momentum

```text
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

Goal:
Implement the batch code, registry wiring, fixtures, and minimum viable tests.

Requirements:
- Follow the manifest row metadata for exact target modules, catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas and diagnostics for every implemented row.
- Wire the relevant fixtures and add minimum viable batch tests.
- Regenerate the tracker after making changes.
- Do not harden unrelated batches.
- Do not move rows to `complete` unless all criteria are already satisfied.

Fixtures to use or update:
- fixture.trend_monotonic_cross_v1
- fixture.trend_whipsaw_guard_v1


When finished, report:
- changed files
- rows implemented
- blockers resolved or still open
- tests added/run
- tracker impact
```

## Prompt 16 — Harden `trend_wave_3`

### Batch scope

- Ichimoku Trend Strategy
- MACD Trend Strategy
- Linear Regression Trend
- Time-Series Momentum

```text
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

Goal:
Harden this batch. Close test, fixture, reporting, and manifest-status gaps without starting new batches.

Tasks:
- Review the batch implementation for correctness, output normalization, and reuse of shared helpers.
- Strengthen fixture coverage and expected-behavior checks for the rows in this batch.
- Add or improve tests for registration, parameter validation, short history or warmup handling, behavior, and performance-smoke coverage as appropriate.
- Check diagnostics and report payload fields so the dashboard can explain the strategy outputs.
- Promote manifest statuses only if evidence supports the promotion.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Leave a concise batch summary in your final response.

Fixtures to verify:
- fixture.trend_monotonic_cross_v1
- fixture.trend_whipsaw_guard_v1


Do not:
- start unrelated batches
- silently change batch ownership
- mark rows `production_ready` without evidence
- hide blockers that still exist

Return:
- changed files
- tests added or strengthened
- statuses advanced
- unresolved issues
```

## Prompt 17 — Implement `momentum_wave_2`

### Batch scope

- KST (Know Sure Thing)
- Volume-Confirmed Momentum

```text
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

Goal:
Implement the batch code, registry wiring, fixtures, and minimum viable tests.

Requirements:
- Follow the manifest row metadata for exact target modules, catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas and diagnostics for every implemented row.
- Wire the relevant fixtures and add minimum viable batch tests.
- Regenerate the tracker after making changes.
- Do not harden unrelated batches.
- Do not move rows to `complete` unless all criteria are already satisfied.

Fixtures to use or update:
- fixture.momentum_sustained_up_v1


When finished, report:
- changed files
- rows implemented
- blockers resolved or still open
- tests added/run
- tracker impact
```

## Prompt 18 — Harden `momentum_wave_2`

### Batch scope

- KST (Know Sure Thing)
- Volume-Confirmed Momentum

```text
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

Goal:
Harden this batch. Close test, fixture, reporting, and manifest-status gaps without starting new batches.

Tasks:
- Review the batch implementation for correctness, output normalization, and reuse of shared helpers.
- Strengthen fixture coverage and expected-behavior checks for the rows in this batch.
- Add or improve tests for registration, parameter validation, short history or warmup handling, behavior, and performance-smoke coverage as appropriate.
- Check diagnostics and report payload fields so the dashboard can explain the strategy outputs.
- Promote manifest statuses only if evidence supports the promotion.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Leave a concise batch summary in your final response.

Fixtures to verify:
- fixture.momentum_sustained_up_v1


Do not:
- start unrelated batches
- silently change batch ownership
- mark rows `production_ready` without evidence
- hide blockers that still exist

Return:
- changed files
- tests added or strengthened
- statuses advanced
- unresolved issues
```

## Prompt 19 — Implement `mean_reversion_wave_2`

### Batch scope

- Williams %R Reversion
- Range Reversion
- Long-Horizon Reversal
- Volatility-Adjusted Reversion

```text
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

Goal:
Implement the batch code, registry wiring, fixtures, and minimum viable tests.

Requirements:
- Follow the manifest row metadata for exact target modules, catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas and diagnostics for every implemented row.
- Wire the relevant fixtures and add minimum viable batch tests.
- Regenerate the tracker after making changes.
- Do not harden unrelated batches.
- Do not move rows to `complete` unless all criteria are already satisfied.

Fixtures to use or update:
- fixture.mean_reversion_one_overshoot_v1
- fixture.mean_reversion_range_oscillation_v1


When finished, report:
- changed files
- rows implemented
- blockers resolved or still open
- tests added/run
- tracker impact
```

## Prompt 20 — Harden `mean_reversion_wave_2`

### Batch scope

- Williams %R Reversion
- Range Reversion
- Long-Horizon Reversal
- Volatility-Adjusted Reversion

```text
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

Goal:
Harden this batch. Close test, fixture, reporting, and manifest-status gaps without starting new batches.

Tasks:
- Review the batch implementation for correctness, output normalization, and reuse of shared helpers.
- Strengthen fixture coverage and expected-behavior checks for the rows in this batch.
- Add or improve tests for registration, parameter validation, short history or warmup handling, behavior, and performance-smoke coverage as appropriate.
- Check diagnostics and report payload fields so the dashboard can explain the strategy outputs.
- Promote manifest statuses only if evidence supports the promotion.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Leave a concise batch summary in your final response.

Fixtures to verify:
- fixture.mean_reversion_one_overshoot_v1
- fixture.mean_reversion_range_oscillation_v1


Do not:
- start unrelated batches
- silently change batch ownership
- mark rows `production_ready` without evidence
- hide blockers that still exist

Return:
- changed files
- tests added or strengthened
- statuses advanced
- unresolved issues
```

## Prompt 21 — Implement `volatility_wave_1`

### Batch scope

- Volatility Breakout
- ATR Channel Breakout
- Volatility Mean Reversion

```text
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

Goal:
Implement the batch code, registry wiring, fixtures, and minimum viable tests.

Requirements:
- Follow the manifest row metadata for exact target modules, catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas and diagnostics for every implemented row.
- Wire the relevant fixtures and add minimum viable batch tests.
- Regenerate the tracker after making changes.
- Do not harden unrelated batches.
- Do not move rows to `complete` unless all criteria are already satisfied.

Fixtures to use or update:
- fixture.volatility_compression_release_v1


When finished, report:
- changed files
- rows implemented
- blockers resolved or still open
- tests added/run
- tracker impact
```

## Prompt 22 — Harden `volatility_wave_1`

### Batch scope

- Volatility Breakout
- ATR Channel Breakout
- Volatility Mean Reversion

```text
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

Goal:
Harden this batch. Close test, fixture, reporting, and manifest-status gaps without starting new batches.

Tasks:
- Review the batch implementation for correctness, output normalization, and reuse of shared helpers.
- Strengthen fixture coverage and expected-behavior checks for the rows in this batch.
- Add or improve tests for registration, parameter validation, short history or warmup handling, behavior, and performance-smoke coverage as appropriate.
- Check diagnostics and report payload fields so the dashboard can explain the strategy outputs.
- Promote manifest statuses only if evidence supports the promotion.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Leave a concise batch summary in your final response.

Fixtures to verify:
- fixture.volatility_compression_release_v1


Do not:
- start unrelated batches
- silently change batch ownership
- mark rows `production_ready` without evidence
- hide blockers that still exist

Return:
- changed files
- tests added or strengthened
- statuses advanced
- unresolved issues
```

## Prompt 23 — Implement `pattern_wave_1`

### Batch scope

- Support and Resistance Bounce
- Breakout Retest
- Pivot Point Strategy
- Opening Range Breakout
- Inside Bar Breakout

```text
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

Goal:
Implement the batch code, registry wiring, fixtures, and minimum viable tests.

Requirements:
- Follow the manifest row metadata for exact target modules, catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas and diagnostics for every implemented row.
- Wire the relevant fixtures and add minimum viable batch tests.
- Regenerate the tracker after making changes.
- Do not harden unrelated batches.
- Do not move rows to `complete` unless all criteria are already satisfied.

Fixtures to use or update:
- fixture.pattern_support_rejection_v1
- fixture.pattern_opening_range_breakout_v1


When finished, report:
- changed files
- rows implemented
- blockers resolved or still open
- tests added/run
- tracker impact
```

## Prompt 24 — Harden `pattern_wave_1`

### Batch scope

- Support and Resistance Bounce
- Breakout Retest
- Pivot Point Strategy
- Opening Range Breakout
- Inside Bar Breakout

```text
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

Goal:
Harden this batch. Close test, fixture, reporting, and manifest-status gaps without starting new batches.

Tasks:
- Review the batch implementation for correctness, output normalization, and reuse of shared helpers.
- Strengthen fixture coverage and expected-behavior checks for the rows in this batch.
- Add or improve tests for registration, parameter validation, short history or warmup handling, behavior, and performance-smoke coverage as appropriate.
- Check diagnostics and report payload fields so the dashboard can explain the strategy outputs.
- Promote manifest statuses only if evidence supports the promotion.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Leave a concise batch summary in your final response.

Fixtures to verify:
- fixture.pattern_support_rejection_v1
- fixture.pattern_opening_range_breakout_v1


Do not:
- start unrelated batches
- silently change batch ownership
- mark rows `production_ready` without evidence
- hide blockers that still exist

Return:
- changed files
- tests added or strengthened
- statuses advanced
- unresolved issues
```

## Prompt 25 — Implement `pattern_wave_2`

### Batch scope

- Gap-and-Go
- Trendline Break Strategy
- Volatility Squeeze Breakout

```text
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

Goal:
Implement the batch code, registry wiring, fixtures, and minimum viable tests.

Requirements:
- Follow the manifest row metadata for exact target modules, catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas and diagnostics for every implemented row.
- Wire the relevant fixtures and add minimum viable batch tests.
- Regenerate the tracker after making changes.
- Do not harden unrelated batches.
- Do not move rows to `complete` unless all criteria are already satisfied.

Fixtures to use or update:
- fixture.pattern_support_rejection_v1


When finished, report:
- changed files
- rows implemented
- blockers resolved or still open
- tests added/run
- tracker impact
```

## Prompt 26 — Harden `pattern_wave_2`

### Batch scope

- Gap-and-Go
- Trendline Break Strategy
- Volatility Squeeze Breakout

```text
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

Goal:
Harden this batch. Close test, fixture, reporting, and manifest-status gaps without starting new batches.

Tasks:
- Review the batch implementation for correctness, output normalization, and reuse of shared helpers.
- Strengthen fixture coverage and expected-behavior checks for the rows in this batch.
- Add or improve tests for registration, parameter validation, short history or warmup handling, behavior, and performance-smoke coverage as appropriate.
- Check diagnostics and report payload fields so the dashboard can explain the strategy outputs.
- Promote manifest statuses only if evidence supports the promotion.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Leave a concise batch summary in your final response.

Fixtures to verify:
- fixture.pattern_support_rejection_v1


Do not:
- start unrelated batches
- silently change batch ownership
- mark rows `production_ready` without evidence
- hide blockers that still exist

Return:
- changed files
- tests added or strengthened
- statuses advanced
- unresolved issues
```

## Prompt 27 — Implement `mean_reversion_wave_3`

### Batch scope

- Intraday VWAP Reversion
- Opening Gap Fade
- Ornstein-Uhlenbeck Reversion

```text
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

Goal:
Implement the batch code, registry wiring, fixtures, and minimum viable tests.

Requirements:
- Follow the manifest row metadata for exact target modules, catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas and diagnostics for every implemented row.
- Wire the relevant fixtures and add minimum viable batch tests.
- Regenerate the tracker after making changes.
- Do not harden unrelated batches.
- Do not move rows to `complete` unless all criteria are already satisfied.

Fixtures to use or update:
- fixture.mean_reversion_one_overshoot_v1


When finished, report:
- changed files
- rows implemented
- blockers resolved or still open
- tests added/run
- tracker impact
```

## Prompt 28 — Harden `mean_reversion_wave_3`

### Batch scope

- Intraday VWAP Reversion
- Opening Gap Fade
- Ornstein-Uhlenbeck Reversion

```text
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

Goal:
Harden this batch. Close test, fixture, reporting, and manifest-status gaps without starting new batches.

Tasks:
- Review the batch implementation for correctness, output normalization, and reuse of shared helpers.
- Strengthen fixture coverage and expected-behavior checks for the rows in this batch.
- Add or improve tests for registration, parameter validation, short history or warmup handling, behavior, and performance-smoke coverage as appropriate.
- Check diagnostics and report payload fields so the dashboard can explain the strategy outputs.
- Promote manifest statuses only if evidence supports the promotion.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Leave a concise batch summary in your final response.

Fixtures to verify:
- fixture.mean_reversion_one_overshoot_v1


Do not:
- start unrelated batches
- silently change batch ownership
- mark rows `production_ready` without evidence
- hide blockers that still exist

Return:
- changed files
- tests added or strengthened
- statuses advanced
- unresolved issues
```

## Prompt 29 — Implement `momentum_wave_3`

### Batch scope

- Cross-Sectional Momentum
- Relative Strength Momentum
- Dual Momentum
- Residual Momentum

```text
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

Goal:
Implement the batch code, registry wiring, fixtures, and minimum viable tests.

Requirements:
- Follow the manifest row metadata for exact target modules, catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas and diagnostics for every implemented row.
- Wire the relevant fixtures and add minimum viable batch tests.
- Regenerate the tracker after making changes.
- Do not harden unrelated batches.
- Do not move rows to `complete` unless all criteria are already satisfied.

Fixtures to use or update:
- fixture.momentum_cross_sectional_ranking_v1

Blockers relevant to this batch:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

Before implementing rows, check whether each blocker already exists in a sufficient form.
If not, implement the smallest reusable slice needed to unlock this batch without overbuilding unrelated framework.

When finished, report:
- changed files
- rows implemented
- blockers resolved or still open
- tests added/run
- tracker impact
```

## Prompt 30 — Harden `momentum_wave_3`

### Batch scope

- Cross-Sectional Momentum
- Relative Strength Momentum
- Dual Momentum
- Residual Momentum

```text
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

Goal:
Harden this batch. Close test, fixture, reporting, and manifest-status gaps without starting new batches.

Tasks:
- Review the batch implementation for correctness, output normalization, and reuse of shared helpers.
- Strengthen fixture coverage and expected-behavior checks for the rows in this batch.
- Add or improve tests for registration, parameter validation, short history or warmup handling, behavior, and performance-smoke coverage as appropriate.
- Check diagnostics and report payload fields so the dashboard can explain the strategy outputs.
- Promote manifest statuses only if evidence supports the promotion.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Leave a concise batch summary in your final response.

Fixtures to verify:
- fixture.momentum_cross_sectional_ranking_v1

Check blocker state carefully:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

If a blocker is only partially resolved, keep the affected rows in an honest state.
Do not promote rows past what the evidence supports.

Do not:
- start unrelated batches
- silently change batch ownership
- mark rows `production_ready` without evidence
- hide blockers that still exist

Return:
- changed files
- tests added or strengthened
- statuses advanced
- unresolved issues
```

## Prompt 31 — Implement `factor_wave_1`

### Batch scope

- Low Volatility Strategy
- Low Beta / Betting-Against-Beta
- Dividend Yield Strategy
- Growth Factor Strategy
- Liquidity Factor Strategy

```text
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

Goal:
Implement the batch code, registry wiring, fixtures, and minimum viable tests.

Requirements:
- Follow the manifest row metadata for exact target modules, catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas and diagnostics for every implemented row.
- Wire the relevant fixtures and add minimum viable batch tests.
- Regenerate the tracker after making changes.
- Do not harden unrelated batches.
- Do not move rows to `complete` unless all criteria are already satisfied.

Fixtures to use or update:
- fixture.factor_monthly_rebalance_v1

Blockers relevant to this batch:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

Before implementing rows, check whether each blocker already exists in a sufficient form.
If not, implement the smallest reusable slice needed to unlock this batch without overbuilding unrelated framework.

When finished, report:
- changed files
- rows implemented
- blockers resolved or still open
- tests added/run
- tracker impact
```

## Prompt 32 — Harden `factor_wave_1`

### Batch scope

- Low Volatility Strategy
- Low Beta / Betting-Against-Beta
- Dividend Yield Strategy
- Growth Factor Strategy
- Liquidity Factor Strategy

```text
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

Goal:
Harden this batch. Close test, fixture, reporting, and manifest-status gaps without starting new batches.

Tasks:
- Review the batch implementation for correctness, output normalization, and reuse of shared helpers.
- Strengthen fixture coverage and expected-behavior checks for the rows in this batch.
- Add or improve tests for registration, parameter validation, short history or warmup handling, behavior, and performance-smoke coverage as appropriate.
- Check diagnostics and report payload fields so the dashboard can explain the strategy outputs.
- Promote manifest statuses only if evidence supports the promotion.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Leave a concise batch summary in your final response.

Fixtures to verify:
- fixture.factor_monthly_rebalance_v1

Check blocker state carefully:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

If a blocker is only partially resolved, keep the affected rows in an honest state.
Do not promote rows past what the evidence supports.

Do not:
- start unrelated batches
- silently change batch ownership
- mark rows `production_ready` without evidence
- hide blockers that still exist

Return:
- changed files
- tests added or strengthened
- statuses advanced
- unresolved issues
```

## Prompt 33 — Implement `factor_wave_2`

### Batch scope

- Value Strategy
- Quality Strategy
- Minimum Variance Strategy
- Size / Small-Cap Strategy
- Mid-Cap Tilt Strategy
- Profitability Factor Strategy
- Earnings Quality Strategy
- Low Leverage / Balance-Sheet Strength

```text
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

Goal:
Implement the batch code, registry wiring, fixtures, and minimum viable tests.

Requirements:
- Follow the manifest row metadata for exact target modules, catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas and diagnostics for every implemented row.
- Wire the relevant fixtures and add minimum viable batch tests.
- Regenerate the tracker after making changes.
- Do not harden unrelated batches.
- Do not move rows to `complete` unless all criteria are already satisfied.

Fixtures to use or update:
- fixture.factor_monthly_rebalance_v1

Blockers relevant to this batch:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

Before implementing rows, check whether each blocker already exists in a sufficient form.
If not, implement the smallest reusable slice needed to unlock this batch without overbuilding unrelated framework.

When finished, report:
- changed files
- rows implemented
- blockers resolved or still open
- tests added/run
- tracker impact
```

## Prompt 34 — Harden `factor_wave_2`

### Batch scope

- Value Strategy
- Quality Strategy
- Minimum Variance Strategy
- Size / Small-Cap Strategy
- Mid-Cap Tilt Strategy
- Profitability Factor Strategy
- Earnings Quality Strategy
- Low Leverage / Balance-Sheet Strength

```text
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

Goal:
Harden this batch. Close test, fixture, reporting, and manifest-status gaps without starting new batches.

Tasks:
- Review the batch implementation for correctness, output normalization, and reuse of shared helpers.
- Strengthen fixture coverage and expected-behavior checks for the rows in this batch.
- Add or improve tests for registration, parameter validation, short history or warmup handling, behavior, and performance-smoke coverage as appropriate.
- Check diagnostics and report payload fields so the dashboard can explain the strategy outputs.
- Promote manifest statuses only if evidence supports the promotion.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Leave a concise batch summary in your final response.

Fixtures to verify:
- fixture.factor_monthly_rebalance_v1

Check blocker state carefully:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

If a blocker is only partially resolved, keep the affected rows in an honest state.
Do not promote rows past what the evidence supports.

Do not:
- start unrelated batches
- silently change batch ownership
- mark rows `production_ready` without evidence
- hide blockers that still exist

Return:
- changed files
- tests added or strengthened
- statuses advanced
- unresolved issues
```

## Prompt 35 — Implement `factor_wave_3`

### Batch scope

- Multi-Factor Composite
- Residual Volatility Strategy
- Defensive Equity Strategy
- Investment Quality Strategy
- Earnings Stability / Low Earnings Variability

```text
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

Goal:
Implement the batch code, registry wiring, fixtures, and minimum viable tests.

Requirements:
- Follow the manifest row metadata for exact target modules, catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas and diagnostics for every implemented row.
- Wire the relevant fixtures and add minimum viable batch tests.
- Regenerate the tracker after making changes.
- Do not harden unrelated batches.
- Do not move rows to `complete` unless all criteria are already satisfied.

Fixtures to use or update:
- fixture.factor_monthly_rebalance_v1

Blockers relevant to this batch:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

Before implementing rows, check whether each blocker already exists in a sufficient form.
If not, implement the smallest reusable slice needed to unlock this batch without overbuilding unrelated framework.

When finished, report:
- changed files
- rows implemented
- blockers resolved or still open
- tests added/run
- tracker impact
```

## Prompt 36 — Harden `factor_wave_3`

### Batch scope

- Multi-Factor Composite
- Residual Volatility Strategy
- Defensive Equity Strategy
- Investment Quality Strategy
- Earnings Stability / Low Earnings Variability

```text
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

Goal:
Harden this batch. Close test, fixture, reporting, and manifest-status gaps without starting new batches.

Tasks:
- Review the batch implementation for correctness, output normalization, and reuse of shared helpers.
- Strengthen fixture coverage and expected-behavior checks for the rows in this batch.
- Add or improve tests for registration, parameter validation, short history or warmup handling, behavior, and performance-smoke coverage as appropriate.
- Check diagnostics and report payload fields so the dashboard can explain the strategy outputs.
- Promote manifest statuses only if evidence supports the promotion.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Leave a concise batch summary in your final response.

Fixtures to verify:
- fixture.factor_monthly_rebalance_v1

Check blocker state carefully:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

If a blocker is only partially resolved, keep the affected rows in an honest state.
Do not promote rows past what the evidence supports.

Do not:
- start unrelated batches
- silently change batch ownership
- mark rows `production_ready` without evidence
- hide blockers that still exist

Return:
- changed files
- tests added or strengthened
- statuses advanced
- unresolved issues
```

## Prompt 37 — Implement `cross_asset_wave_1`

### Batch scope

- Carry Trade (FX/Rates)
- Yield Curve Steepener/Flattener
- Curve Roll-Down Strategy
- Commodity Term Structure / Roll Yield
- Risk-On / Risk-Off Regime
- Intermarket Confirmation
- Seasonality / Calendar Effects
- Earnings Drift / Post-Event Momentum

```text
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

Goal:
Implement the batch code, registry wiring, fixtures, and minimum viable tests.

Requirements:
- Follow the manifest row metadata for exact target modules, catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas and diagnostics for every implemented row.
- Wire the relevant fixtures and add minimum viable batch tests.
- Regenerate the tracker after making changes.
- Do not harden unrelated batches.
- Do not move rows to `complete` unless all criteria are already satisfied.

Fixtures to use or update:
- fixture.cross_asset_carry_ranking_v1
- fixture.risk_on_off_regime_v1
- fixture.event_earnings_after_close_v1

Blockers relevant to this batch:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.spread_leg_output_v1
- blocker.multi_leg_reporting_v1
- blocker.event_calendar_v1
- blocker.event_window_execution_v1
- blocker.event_reporting_v1

Before implementing rows, check whether each blocker already exists in a sufficient form.
If not, implement the smallest reusable slice needed to unlock this batch without overbuilding unrelated framework.

When finished, report:
- changed files
- rows implemented
- blockers resolved or still open
- tests added/run
- tracker impact
```

## Prompt 38 — Harden `cross_asset_wave_1`

### Batch scope

- Carry Trade (FX/Rates)
- Yield Curve Steepener/Flattener
- Curve Roll-Down Strategy
- Commodity Term Structure / Roll Yield
- Risk-On / Risk-Off Regime
- Intermarket Confirmation
- Seasonality / Calendar Effects
- Earnings Drift / Post-Event Momentum

```text
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

Goal:
Harden this batch. Close test, fixture, reporting, and manifest-status gaps without starting new batches.

Tasks:
- Review the batch implementation for correctness, output normalization, and reuse of shared helpers.
- Strengthen fixture coverage and expected-behavior checks for the rows in this batch.
- Add or improve tests for registration, parameter validation, short history or warmup handling, behavior, and performance-smoke coverage as appropriate.
- Check diagnostics and report payload fields so the dashboard can explain the strategy outputs.
- Promote manifest statuses only if evidence supports the promotion.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Leave a concise batch summary in your final response.

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

If a blocker is only partially resolved, keep the affected rows in an honest state.
Do not promote rows past what the evidence supports.

Do not:
- start unrelated batches
- silently change batch ownership
- mark rows `production_ready` without evidence
- hide blockers that still exist

Return:
- changed files
- tests added or strengthened
- statuses advanced
- unresolved issues
```

## Prompt 39 — Implement `composite_wave_2`

### Batch scope

- Rank Aggregation
- Risk Budgeting / Risk Parity
- Volatility Targeting Overlay

```text
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

Goal:
Implement the batch code, registry wiring, fixtures, and minimum viable tests.

Requirements:
- Follow the manifest row metadata for exact target modules, catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas and diagnostics for every implemented row.
- Wire the relevant fixtures and add minimum viable batch tests.
- Regenerate the tracker after making changes.
- Do not harden unrelated batches.
- Do not move rows to `complete` unless all criteria are already satisfied.

Fixtures to use or update:
- fixture.composite_rank_aggregation_v1
- fixture.composite_risk_budget_v1

Blockers relevant to this batch:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

Before implementing rows, check whether each blocker already exists in a sufficient form.
If not, implement the smallest reusable slice needed to unlock this batch without overbuilding unrelated framework.

When finished, report:
- changed files
- rows implemented
- blockers resolved or still open
- tests added/run
- tracker impact
```

## Prompt 40 — Harden `composite_wave_2`

### Batch scope

- Rank Aggregation
- Risk Budgeting / Risk Parity
- Volatility Targeting Overlay

```text
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

Goal:
Harden this batch. Close test, fixture, reporting, and manifest-status gaps without starting new batches.

Tasks:
- Review the batch implementation for correctness, output normalization, and reuse of shared helpers.
- Strengthen fixture coverage and expected-behavior checks for the rows in this batch.
- Add or improve tests for registration, parameter validation, short history or warmup handling, behavior, and performance-smoke coverage as appropriate.
- Check diagnostics and report payload fields so the dashboard can explain the strategy outputs.
- Promote manifest statuses only if evidence supports the promotion.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Leave a concise batch summary in your final response.

Fixtures to verify:
- fixture.composite_rank_aggregation_v1
- fixture.composite_risk_budget_v1

Check blocker state carefully:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

If a blocker is only partially resolved, keep the affected rows in an honest state.
Do not promote rows past what the evidence supports.

Do not:
- start unrelated batches
- silently change batch ownership
- mark rows `production_ready` without evidence
- hide blockers that still exist

Return:
- changed files
- tests added or strengthened
- statuses advanced
- unresolved issues
```

## Prompt 41 — Implement `composite_wave_3`

### Batch scope

- Constrained Multi-Factor Optimization
- Regime Switching / HMM Gating

```text
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

Goal:
Implement the batch code, registry wiring, fixtures, and minimum viable tests.

Requirements:
- Follow the manifest row metadata for exact target modules, catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas and diagnostics for every implemented row.
- Wire the relevant fixtures and add minimum viable batch tests.
- Regenerate the tracker after making changes.
- Do not harden unrelated batches.
- Do not move rows to `complete` unless all criteria are already satisfied.

Fixtures to use or update:
- fixture.composite_risk_budget_v1
- fixture.composite_regime_switch_v1

Blockers relevant to this batch:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1
- blocker.regime_state_support_v1

Before implementing rows, check whether each blocker already exists in a sufficient form.
If not, implement the smallest reusable slice needed to unlock this batch without overbuilding unrelated framework.

When finished, report:
- changed files
- rows implemented
- blockers resolved or still open
- tests added/run
- tracker impact
```

## Prompt 42 — Harden `composite_wave_3`

### Batch scope

- Constrained Multi-Factor Optimization
- Regime Switching / HMM Gating

```text
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

Goal:
Harden this batch. Close test, fixture, reporting, and manifest-status gaps without starting new batches.

Tasks:
- Review the batch implementation for correctness, output normalization, and reuse of shared helpers.
- Strengthen fixture coverage and expected-behavior checks for the rows in this batch.
- Add or improve tests for registration, parameter validation, short history or warmup handling, behavior, and performance-smoke coverage as appropriate.
- Check diagnostics and report payload fields so the dashboard can explain the strategy outputs.
- Promote manifest statuses only if evidence supports the promotion.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Leave a concise batch summary in your final response.

Fixtures to verify:
- fixture.composite_risk_budget_v1
- fixture.composite_regime_switch_v1

Check blocker state carefully:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1
- blocker.regime_state_support_v1

If a blocker is only partially resolved, keep the affected rows in an honest state.
Do not promote rows past what the evidence supports.

Do not:
- start unrelated batches
- silently change batch ownership
- mark rows `production_ready` without evidence
- hide blockers that still exist

Return:
- changed files
- tests added or strengthened
- statuses advanced
- unresolved issues
```

## Prompt 43 — Implement `advanced_model_wave_1`

### Batch scope

- Sentiment Strategy
- Machine Learning Classifier
- Machine Learning Regressor
- Regime-Switching Strategy
- Ensemble / Voting Strategy

```text
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

Goal:
Implement the batch code, registry wiring, fixtures, and minimum viable tests.

Requirements:
- Follow the manifest row metadata for exact target modules, catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas and diagnostics for every implemented row.
- Wire the relevant fixtures and add minimum viable batch tests.
- Regenerate the tracker after making changes.
- Do not harden unrelated batches.
- Do not move rows to `complete` unless all criteria are already satisfied.

Fixtures to use or update:
- fixture.factor_monthly_rebalance_v1

Blockers relevant to this batch:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

Before implementing rows, check whether each blocker already exists in a sufficient form.
If not, implement the smallest reusable slice needed to unlock this batch without overbuilding unrelated framework.

When finished, report:
- changed files
- rows implemented
- blockers resolved or still open
- tests added/run
- tracker impact
```

## Prompt 44 — Harden `advanced_model_wave_1`

### Batch scope

- Sentiment Strategy
- Machine Learning Classifier
- Machine Learning Regressor
- Regime-Switching Strategy
- Ensemble / Voting Strategy

```text
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

Goal:
Harden this batch. Close test, fixture, reporting, and manifest-status gaps without starting new batches.

Tasks:
- Review the batch implementation for correctness, output normalization, and reuse of shared helpers.
- Strengthen fixture coverage and expected-behavior checks for the rows in this batch.
- Add or improve tests for registration, parameter validation, short history or warmup handling, behavior, and performance-smoke coverage as appropriate.
- Check diagnostics and report payload fields so the dashboard can explain the strategy outputs.
- Promote manifest statuses only if evidence supports the promotion.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Leave a concise batch summary in your final response.

Fixtures to verify:
- fixture.factor_monthly_rebalance_v1

Check blocker state carefully:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

If a blocker is only partially resolved, keep the affected rows in an honest state.
Do not promote rows past what the evidence supports.

Do not:
- start unrelated batches
- silently change batch ownership
- mark rows `production_ready` without evidence
- hide blockers that still exist

Return:
- changed files
- tests added or strengthened
- statuses advanced
- unresolved issues
```

## Prompt 45 — Implement `event_wave_1`

### Batch scope

- Post-Earnings Announcement Drift (PEAD)
- Pre-Earnings Announcement Drift
- Earnings Announcement Premium
- Index Rebalancing Effect Strategy
- ETF Rebalancing Anticipation / Front-Run Strategy

```text
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

Goal:
Implement the batch code, registry wiring, fixtures, and minimum viable tests.

Requirements:
- Follow the manifest row metadata for exact target modules, catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas and diagnostics for every implemented row.
- Wire the relevant fixtures and add minimum viable batch tests.
- Regenerate the tracker after making changes.
- Do not harden unrelated batches.
- Do not move rows to `complete` unless all criteria are already satisfied.

Fixtures to use or update:
- fixture.event_earnings_after_close_v1
- fixture.event_index_rebalance_window_v1

Blockers relevant to this batch:
- blocker.event_calendar_v1
- blocker.event_window_execution_v1
- blocker.event_reporting_v1

Before implementing rows, check whether each blocker already exists in a sufficient form.
If not, implement the smallest reusable slice needed to unlock this batch without overbuilding unrelated framework.

When finished, report:
- changed files
- rows implemented
- blockers resolved or still open
- tests added/run
- tracker impact
```

## Prompt 46 — Harden `event_wave_1`

### Batch scope

- Post-Earnings Announcement Drift (PEAD)
- Pre-Earnings Announcement Drift
- Earnings Announcement Premium
- Index Rebalancing Effect Strategy
- ETF Rebalancing Anticipation / Front-Run Strategy

```text
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

Goal:
Harden this batch. Close test, fixture, reporting, and manifest-status gaps without starting new batches.

Tasks:
- Review the batch implementation for correctness, output normalization, and reuse of shared helpers.
- Strengthen fixture coverage and expected-behavior checks for the rows in this batch.
- Add or improve tests for registration, parameter validation, short history or warmup handling, behavior, and performance-smoke coverage as appropriate.
- Check diagnostics and report payload fields so the dashboard can explain the strategy outputs.
- Promote manifest statuses only if evidence supports the promotion.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Leave a concise batch summary in your final response.

Fixtures to verify:
- fixture.event_earnings_after_close_v1
- fixture.event_index_rebalance_window_v1

Check blocker state carefully:
- blocker.event_calendar_v1
- blocker.event_window_execution_v1
- blocker.event_reporting_v1

If a blocker is only partially resolved, keep the affected rows in an honest state.
Do not promote rows past what the evidence supports.

Do not:
- start unrelated batches
- silently change batch ownership
- mark rows `production_ready` without evidence
- hide blockers that still exist

Return:
- changed files
- tests added or strengthened
- statuses advanced
- unresolved issues
```

## Prompt 47 — Implement `stat_arb_wave_1`

### Batch scope

- Pairs Trading (Distance Method)
- Pairs Trading (Cointegration)
- Basket Statistical Arbitrage
- Funding/Basis Arbitrage

```text
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

Goal:
Implement the batch code, registry wiring, fixtures, and minimum viable tests.

Requirements:
- Follow the manifest row metadata for exact target modules, catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas and diagnostics for every implemented row.
- Wire the relevant fixtures and add minimum viable batch tests.
- Regenerate the tracker after making changes.
- Do not harden unrelated batches.
- Do not move rows to `complete` unless all criteria are already satisfied.

Fixtures to use or update:
- fixture.statarb_pair_divergence_reversion_v1
- fixture.relative_value_curve_spread_v1

Blockers relevant to this batch:
- blocker.spread_leg_output_v1
- blocker.hedge_ratio_helpers_v1
- blocker.multi_leg_reporting_v1

Before implementing rows, check whether each blocker already exists in a sufficient form.
If not, implement the smallest reusable slice needed to unlock this batch without overbuilding unrelated framework.

When finished, report:
- changed files
- rows implemented
- blockers resolved or still open
- tests added/run
- tracker impact
```

## Prompt 48 — Harden `stat_arb_wave_1`

### Batch scope

- Pairs Trading (Distance Method)
- Pairs Trading (Cointegration)
- Basket Statistical Arbitrage
- Funding/Basis Arbitrage

```text
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

Goal:
Harden this batch. Close test, fixture, reporting, and manifest-status gaps without starting new batches.

Tasks:
- Review the batch implementation for correctness, output normalization, and reuse of shared helpers.
- Strengthen fixture coverage and expected-behavior checks for the rows in this batch.
- Add or improve tests for registration, parameter validation, short history or warmup handling, behavior, and performance-smoke coverage as appropriate.
- Check diagnostics and report payload fields so the dashboard can explain the strategy outputs.
- Promote manifest statuses only if evidence supports the promotion.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Leave a concise batch summary in your final response.

Fixtures to verify:
- fixture.statarb_pair_divergence_reversion_v1
- fixture.relative_value_curve_spread_v1

Check blocker state carefully:
- blocker.spread_leg_output_v1
- blocker.hedge_ratio_helpers_v1
- blocker.multi_leg_reporting_v1

If a blocker is only partially resolved, keep the affected rows in an honest state.
Do not promote rows past what the evidence supports.

Do not:
- start unrelated batches
- silently change batch ownership
- mark rows `production_ready` without evidence
- hide blockers that still exist

Return:
- changed files
- tests added or strengthened
- statuses advanced
- unresolved issues
```

## Prompt 49 — Implement `relative_value_wave_2`

### Batch scope

- Kalman Filter Pairs Trading
- Index Arbitrage
- ETF-NAV Arbitrage
- ADR Dual-Listing Arbitrage
- Convertible Arbitrage
- Merger Arbitrage
- Futures Cash-and-Carry Arbitrage
- Reverse Cash-and-Carry Arbitrage
- Triangular Arbitrage (FX/Crypto)
- Latency / Exchange Arbitrage
- Fixed-Income Arbitrage
- Swap Spread Arbitrage

```text
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

Goal:
Implement the batch code, registry wiring, fixtures, and minimum viable tests.

Requirements:
- Follow the manifest row metadata for exact target modules, catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas and diagnostics for every implemented row.
- Wire the relevant fixtures and add minimum viable batch tests.
- Regenerate the tracker after making changes.
- Do not harden unrelated batches.
- Do not move rows to `complete` unless all criteria are already satisfied.

Fixtures to use or update:
- fixture.statarb_pair_divergence_reversion_v1
- fixture.relative_value_curve_spread_v1

Blockers relevant to this batch:
- blocker.spread_leg_output_v1
- blocker.hedge_ratio_helpers_v1
- blocker.multi_leg_reporting_v1

Before implementing rows, check whether each blocker already exists in a sufficient form.
If not, implement the smallest reusable slice needed to unlock this batch without overbuilding unrelated framework.

When finished, report:
- changed files
- rows implemented
- blockers resolved or still open
- tests added/run
- tracker impact
```

## Prompt 50 — Harden `relative_value_wave_2`

### Batch scope

- Kalman Filter Pairs Trading
- Index Arbitrage
- ETF-NAV Arbitrage
- ADR Dual-Listing Arbitrage
- Convertible Arbitrage
- Merger Arbitrage
- Futures Cash-and-Carry Arbitrage
- Reverse Cash-and-Carry Arbitrage
- Triangular Arbitrage (FX/Crypto)
- Latency / Exchange Arbitrage
- Fixed-Income Arbitrage
- Swap Spread Arbitrage

```text
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

Goal:
Harden this batch. Close test, fixture, reporting, and manifest-status gaps without starting new batches.

Tasks:
- Review the batch implementation for correctness, output normalization, and reuse of shared helpers.
- Strengthen fixture coverage and expected-behavior checks for the rows in this batch.
- Add or improve tests for registration, parameter validation, short history or warmup handling, behavior, and performance-smoke coverage as appropriate.
- Check diagnostics and report payload fields so the dashboard can explain the strategy outputs.
- Promote manifest statuses only if evidence supports the promotion.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Leave a concise batch summary in your final response.

Fixtures to verify:
- fixture.statarb_pair_divergence_reversion_v1
- fixture.relative_value_curve_spread_v1

Check blocker state carefully:
- blocker.spread_leg_output_v1
- blocker.hedge_ratio_helpers_v1
- blocker.multi_leg_reporting_v1

If a blocker is only partially resolved, keep the affected rows in an honest state.
Do not promote rows past what the evidence supports.

Do not:
- start unrelated batches
- silently change batch ownership
- mark rows `production_ready` without evidence
- hide blockers that still exist

Return:
- changed files
- tests added or strengthened
- statuses advanced
- unresolved issues
```

## Prompt 51 — Implement `volatility_wave_2`

### Batch scope

- Delta-Neutral Volatility Trading
- Gamma Scalping
- Volatility Risk Premium Capture
- Dispersion Trading
- Skew Trading
- Term Structure Trading
- Straddle Breakout Timing

```text
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

Goal:
Implement the batch code, registry wiring, fixtures, and minimum viable tests.

Requirements:
- Follow the manifest row metadata for exact target modules, catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas and diagnostics for every implemented row.
- Wire the relevant fixtures and add minimum viable batch tests.
- Regenerate the tracker after making changes.
- Do not harden unrelated batches.
- Do not move rows to `complete` unless all criteria are already satisfied.

Fixtures to use or update:
- fixture.options_iv_rv_gap_v1

Blockers relevant to this batch:
- blocker.options_chain_v1
- blocker.greeks_v1

Before implementing rows, check whether each blocker already exists in a sufficient form.
If not, implement the smallest reusable slice needed to unlock this batch without overbuilding unrelated framework.

When finished, report:
- changed files
- rows implemented
- blockers resolved or still open
- tests added/run
- tracker impact
```

## Prompt 52 — Harden `volatility_wave_2`

### Batch scope

- Delta-Neutral Volatility Trading
- Gamma Scalping
- Volatility Risk Premium Capture
- Dispersion Trading
- Skew Trading
- Term Structure Trading
- Straddle Breakout Timing

```text
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

Goal:
Harden this batch. Close test, fixture, reporting, and manifest-status gaps without starting new batches.

Tasks:
- Review the batch implementation for correctness, output normalization, and reuse of shared helpers.
- Strengthen fixture coverage and expected-behavior checks for the rows in this batch.
- Add or improve tests for registration, parameter validation, short history or warmup handling, behavior, and performance-smoke coverage as appropriate.
- Check diagnostics and report payload fields so the dashboard can explain the strategy outputs.
- Promote manifest statuses only if evidence supports the promotion.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Leave a concise batch summary in your final response.

Fixtures to verify:
- fixture.options_iv_rv_gap_v1

Check blocker state carefully:
- blocker.options_chain_v1
- blocker.greeks_v1

If a blocker is only partially resolved, keep the affected rows in an honest state.
Do not promote rows past what the evidence supports.

Do not:
- start unrelated batches
- silently change batch ownership
- mark rows `production_ready` without evidence
- hide blockers that still exist

Return:
- changed files
- tests added or strengthened
- statuses advanced
- unresolved issues
```

## Prompt 53 — Implement `composite_wave_4`

### Batch scope

- Bagging Ensemble
- Boosting Ensemble
- Stacking / Meta-Learning

```text
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

Goal:
Implement the batch code, registry wiring, fixtures, and minimum viable tests.

Requirements:
- Follow the manifest row metadata for exact target modules, catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas and diagnostics for every implemented row.
- Wire the relevant fixtures and add minimum viable batch tests.
- Regenerate the tracker after making changes.
- Do not harden unrelated batches.
- Do not move rows to `complete` unless all criteria are already satisfied.

Fixtures to use or update:
- fixture.composite_ml_ensemble_v1


When finished, report:
- changed files
- rows implemented
- blockers resolved or still open
- tests added/run
- tracker impact
```

## Prompt 54 — Harden `composite_wave_4`

### Batch scope

- Bagging Ensemble
- Boosting Ensemble
- Stacking / Meta-Learning

```text
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

Goal:
Harden this batch. Close test, fixture, reporting, and manifest-status gaps without starting new batches.

Tasks:
- Review the batch implementation for correctness, output normalization, and reuse of shared helpers.
- Strengthen fixture coverage and expected-behavior checks for the rows in this batch.
- Add or improve tests for registration, parameter validation, short history or warmup handling, behavior, and performance-smoke coverage as appropriate.
- Check diagnostics and report payload fields so the dashboard can explain the strategy outputs.
- Promote manifest statuses only if evidence supports the promotion.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Leave a concise batch summary in your final response.

Fixtures to verify:
- fixture.composite_ml_ensemble_v1


Do not:
- start unrelated batches
- silently change batch ownership
- mark rows `production_ready` without evidence
- hide blockers that still exist

Return:
- changed files
- tests added or strengthened
- statuses advanced
- unresolved issues
```

## Prompt 55 — Implement `composite_wave_5`

### Batch scope

- RL Allocation Controller
- Hierarchical Controller / Meta-Policy

```text
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

Goal:
Implement the batch code, registry wiring, fixtures, and minimum viable tests.

Requirements:
- Follow the manifest row metadata for exact target modules, catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas and diagnostics for every implemented row.
- Wire the relevant fixtures and add minimum viable batch tests.
- Regenerate the tracker after making changes.
- Do not harden unrelated batches.
- Do not move rows to `complete` unless all criteria are already satisfied.

Fixtures to use or update:
- fixture.composite_rl_policy_stub_v1

Blockers relevant to this batch:
- blocker.rl_environment_v1

Before implementing rows, check whether each blocker already exists in a sufficient form.
If not, implement the smallest reusable slice needed to unlock this batch without overbuilding unrelated framework.

When finished, report:
- changed files
- rows implemented
- blockers resolved or still open
- tests added/run
- tracker impact
```

## Prompt 56 — Harden `composite_wave_5`

### Batch scope

- RL Allocation Controller
- Hierarchical Controller / Meta-Policy

```text
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

Goal:
Harden this batch. Close test, fixture, reporting, and manifest-status gaps without starting new batches.

Tasks:
- Review the batch implementation for correctness, output normalization, and reuse of shared helpers.
- Strengthen fixture coverage and expected-behavior checks for the rows in this batch.
- Add or improve tests for registration, parameter validation, short history or warmup handling, behavior, and performance-smoke coverage as appropriate.
- Check diagnostics and report payload fields so the dashboard can explain the strategy outputs.
- Promote manifest statuses only if evidence supports the promotion.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Leave a concise batch summary in your final response.

Fixtures to verify:
- fixture.composite_rl_policy_stub_v1

Check blocker state carefully:
- blocker.rl_environment_v1

If a blocker is only partially resolved, keep the affected rows in an honest state.
Do not promote rows past what the evidence supports.

Do not:
- start unrelated batches
- silently change batch ownership
- mark rows `production_ready` without evidence
- hide blockers that still exist

Return:
- changed files
- tests added or strengthened
- statuses advanced
- unresolved issues
```

## Prompt 57 — Implement `advanced_wave_blocked`

### Batch scope

- Bid-Ask Market Making
- Inventory-Skewed Market Making
- Order Book Imbalance Strategy
- Microprice Strategy
- Queue Position Strategy
- Liquidity Rebate Capture
- Opening Auction Strategy
- Closing Auction Strategy
- TWAP
- VWAP
- POV / Participation Rate
- Implementation Shortfall / Arrival Price
- Iceberg / Hidden Size
- Sniper / Opportunistic Execution

```text
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

Goal:
Implement only the reusable framework slices, stubs, and contracts that are appropriate for this blocked batch.

Requirements:
- Follow the manifest row metadata for exact target modules, catalogs, capability fields, fixture ids, and performance budget ids.
- Build or extend shared helpers before copying logic into individual rows.
- Keep outputs normalized and composable.
- Add or update parameter schemas and diagnostics for every implemented row.
- Wire the relevant fixtures and add minimum viable batch tests.
- Regenerate the tracker after making changes.
- Do not harden unrelated batches.
- Do not move rows to `complete` unless all criteria are already satisfied.

Fixtures to use or update:
- fixture.microstructure_top_of_book_imbalance_v1
- fixture.microstructure_queue_state_v1
- fixture.execution_twap_schedule_v1
- fixture.execution_vwap_curve_drift_v1

Blockers relevant to this batch:
- blocker.order_book_input_v1
- blocker.own_order_state_v1
- blocker.execution_plan_output_v1
- blocker.fill_simulation_v1

Before implementing rows, check whether each blocker already exists in a sufficient form.
If not, implement the smallest reusable slice needed to unlock this batch without overbuilding unrelated framework.

Special rule:
- Do not pretend market-making, execution, or other framework-heavy rows are production-ready.
- It is acceptable to leave rows as `blocked_framework` or `prototype_only` after adding the correct supporting scaffolding and tests.

When finished, report:
- changed files
- rows implemented
- blockers resolved or still open
- tests added/run
- tracker impact
```

## Prompt 58 — Harden `advanced_wave_blocked`

### Batch scope

- Bid-Ask Market Making
- Inventory-Skewed Market Making
- Order Book Imbalance Strategy
- Microprice Strategy
- Queue Position Strategy
- Liquidity Rebate Capture
- Opening Auction Strategy
- Closing Auction Strategy
- TWAP
- VWAP
- POV / Participation Rate
- Implementation Shortfall / Arrival Price
- Iceberg / Hidden Size
- Sniper / Opportunistic Execution

```text
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

Goal:
Harden this batch. Close test, fixture, reporting, and manifest-status gaps without starting new batches.

Tasks:
- Review the batch implementation for correctness, output normalization, and reuse of shared helpers.
- Strengthen fixture coverage and expected-behavior checks for the rows in this batch.
- Add or improve tests for registration, parameter validation, short history or warmup handling, behavior, and performance-smoke coverage as appropriate.
- Check diagnostics and report payload fields so the dashboard can explain the strategy outputs.
- Promote manifest statuses only if evidence supports the promotion.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Leave a concise batch summary in your final response.

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

If a blocker is only partially resolved, keep the affected rows in an honest state.
Do not promote rows past what the evidence supports.

Do not:
- start unrelated batches
- silently change batch ownership
- mark rows `production_ready` without evidence
- hide blockers that still exist

Return:
- changed files
- tests added or strengthened
- statuses advanced
- unresolved issues
```

## Prompt 59 — Full blocker, manifest, fixture, and tracker audit

```text
Read these files first:
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml
- manifests/algorithm_test_fixtures.yaml
- manifests/algorithm_performance_budgets.yaml
- docs/algorithm_library_systematic_implementation_plan_v2.md

Goal:
Run a full program-level audit after all batch prompts have been executed.

Tasks:
- Audit the manifest, blockers, fixture registry, and tracker for drift or dishonesty.
- Check for:
  - rows marked implemented but not actually registered
  - rows marked tested without real fixture or test evidence
  - rows marked complete while blocker keys are still unresolved
  - rows marked production-ready without sufficient evidence
  - batches whose current state does not match manifest/tracker summaries
- Fix what is safe to fix automatically.
- Regenerate the tracker.
- Return:
  - issues found
  - fixes applied
  - issues still needing human review
```

## Prompt 60 — Final repo-wide consolidation and readiness pass

```text
Read these files first:
- docs/algorithm_library_requirements_v4.md
- docs/algorithm_library_systematic_implementation_plan_v2.md
- manifests/algorithm_library_manifest.yaml
- manifests/algorithm_framework_blockers.yaml

Goal:
Perform the final consolidation pass after all implementation and hardening prompts.

Tasks:
- Refactor obvious duplication across family modules without changing external behavior.
- Improve documentation comments, schema clarity, and registry readability where needed.
- Verify that tracker generation, consistency tests, fixture harnesses, and performance-smoke hooks work together coherently.
- Make a final honest pass over delivery status and operational readiness values.
- Do not start new strategy families or new framework expansions in this prompt; this is a consolidation pass.
- Return:
  - final refactors made
  - documentation or schema improvements
  - readiness promotions or demotions
  - any remaining strategic gaps in the repo
```