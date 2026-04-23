# Algorithm Library Coder Prompts — Scenario 1 (27-Prompt Compressed Plan)

## Before using these prompts

These prompts assume the repository already contains the starter-pack and planning documents.

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

- This is the **compressed** execution mode: one prompt per batch.

- Give the prompts to the LLM coder **one at a time**, in the listed order.

- This mode is efficient but riskier. If a prompt proves too large, split it and move to the realistic plan instead.

- After each prompt, review the coder output before sending the next one.


## Prompt 01 — `trend_wave_1`

### Batch scope

- Simple Moving Average Crossover
- Exponential Moving Average Crossover
- Triple Moving Average Crossover
- Price vs Moving Average
- Moving Average Ribbon Trend

### Copy-paste prompt

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
Implement this batch end-to-end in one pass as far as honestly possible.

Requirements:
- Use the exact `target_module`, `target_catalog`, capability fields, fixture ids, and performance-budget ids declared in the manifest rows for this batch.
- Reuse shared helpers whenever possible; do not duplicate logic without reason.
- Keep outputs normalized and compatible with composition/reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and reporting payloads for this batch.
- Update manifest statuses only when criteria are truly met.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.

Recommended fixtures to wire or validate in this prompt:
- fixture.trend_monotonic_cross_v1
- fixture.trend_whipsaw_guard_v1



Expected deliverables before you stop:
1. batch rows implemented or honestly left blocked with explicit reasons
2. registry/catalog updated
3. tests added or updated
4. tracker regenerated
5. short summary of:
   - files changed
   - tests run
   - statuses advanced
   - unresolved blockers
```

## Prompt 02 — `composite_contract_wave_1`

### Batch scope

- Hard Boolean Gating (AND / OR / Majority)
- Weighted Linear Score Blend

### Copy-paste prompt

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
Implement this batch end-to-end in one pass as far as honestly possible.

Requirements:
- Use the exact `target_module`, `target_catalog`, capability fields, fixture ids, and performance-budget ids declared in the manifest rows for this batch.
- Reuse shared helpers whenever possible; do not duplicate logic without reason.
- Keep outputs normalized and compatible with composition/reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and reporting payloads for this batch.
- Update manifest statuses only when criteria are truly met.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.

Recommended fixtures to wire or validate in this prompt:
- fixture.composite_boolean_truth_table_v1
- fixture.composite_weighted_blend_v1



Expected deliverables before you stop:
1. batch rows implemented or honestly left blocked with explicit reasons
2. registry/catalog updated
3. tests added or updated
4. tracker regenerated
5. short summary of:
   - files changed
   - tests run
   - statuses advanced
   - unresolved blockers
```

## Prompt 03 — `momentum_wave_1`

### Batch scope

- Rate of Change Momentum
- Accelerating Momentum
- RSI Momentum Continuation
- Stochastic Momentum
- CCI Momentum

### Copy-paste prompt

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
Implement this batch end-to-end in one pass as far as honestly possible.

Requirements:
- Use the exact `target_module`, `target_catalog`, capability fields, fixture ids, and performance-budget ids declared in the manifest rows for this batch.
- Reuse shared helpers whenever possible; do not duplicate logic without reason.
- Keep outputs normalized and compatible with composition/reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and reporting payloads for this batch.
- Update manifest statuses only when criteria are truly met.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.

Recommended fixtures to wire or validate in this prompt:
- fixture.momentum_sustained_up_v1



Expected deliverables before you stop:
1. batch rows implemented or honestly left blocked with explicit reasons
2. registry/catalog updated
3. tests added or updated
4. tracker regenerated
5. short summary of:
   - files changed
   - tests run
   - statuses advanced
   - unresolved blockers
```

## Prompt 04 — `mean_reversion_wave_1`

### Batch scope

- Z-Score Mean Reversion
- Bollinger Bands Reversion
- RSI Reversion
- Stochastic Reversion
- CCI Reversion

### Copy-paste prompt

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
Implement this batch end-to-end in one pass as far as honestly possible.

Requirements:
- Use the exact `target_module`, `target_catalog`, capability fields, fixture ids, and performance-budget ids declared in the manifest rows for this batch.
- Reuse shared helpers whenever possible; do not duplicate logic without reason.
- Keep outputs normalized and compatible with composition/reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and reporting payloads for this batch.
- Update manifest statuses only when criteria are truly met.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.

Recommended fixtures to wire or validate in this prompt:
- fixture.mean_reversion_one_overshoot_v1



Expected deliverables before you stop:
1. batch rows implemented or honestly left blocked with explicit reasons
2. registry/catalog updated
3. tests added or updated
4. tracker regenerated
5. short summary of:
   - files changed
   - tests run
   - statuses advanced
   - unresolved blockers
```

## Prompt 05 — `trend_wave_2`

### Batch scope

- Breakout (Donchian Channel)
- Channel Breakout with Confirmation
- ADX Trend Filter
- Parabolic SAR Trend Following
- SuperTrend

### Copy-paste prompt

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
Implement this batch end-to-end in one pass as far as honestly possible.

Requirements:
- Use the exact `target_module`, `target_catalog`, capability fields, fixture ids, and performance-budget ids declared in the manifest rows for this batch.
- Reuse shared helpers whenever possible; do not duplicate logic without reason.
- Keep outputs normalized and compatible with composition/reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and reporting payloads for this batch.
- Update manifest statuses only when criteria are truly met.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.

Recommended fixtures to wire or validate in this prompt:
- fixture.trend_monotonic_cross_v1
- fixture.trend_whipsaw_guard_v1



Expected deliverables before you stop:
1. batch rows implemented or honestly left blocked with explicit reasons
2. registry/catalog updated
3. tests added or updated
4. tracker regenerated
5. short summary of:
   - files changed
   - tests run
   - statuses advanced
   - unresolved blockers
```

## Prompt 06 — `trend_wave_3`

### Batch scope

- Ichimoku Trend Strategy
- MACD Trend Strategy
- Linear Regression Trend
- Time-Series Momentum

### Copy-paste prompt

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
Implement this batch end-to-end in one pass as far as honestly possible.

Requirements:
- Use the exact `target_module`, `target_catalog`, capability fields, fixture ids, and performance-budget ids declared in the manifest rows for this batch.
- Reuse shared helpers whenever possible; do not duplicate logic without reason.
- Keep outputs normalized and compatible with composition/reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and reporting payloads for this batch.
- Update manifest statuses only when criteria are truly met.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.

Recommended fixtures to wire or validate in this prompt:
- fixture.trend_monotonic_cross_v1
- fixture.trend_whipsaw_guard_v1



Expected deliverables before you stop:
1. batch rows implemented or honestly left blocked with explicit reasons
2. registry/catalog updated
3. tests added or updated
4. tracker regenerated
5. short summary of:
   - files changed
   - tests run
   - statuses advanced
   - unresolved blockers
```

## Prompt 07 — `momentum_wave_2`

### Batch scope

- KST (Know Sure Thing)
- Volume-Confirmed Momentum

### Copy-paste prompt

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
Implement this batch end-to-end in one pass as far as honestly possible.

Requirements:
- Use the exact `target_module`, `target_catalog`, capability fields, fixture ids, and performance-budget ids declared in the manifest rows for this batch.
- Reuse shared helpers whenever possible; do not duplicate logic without reason.
- Keep outputs normalized and compatible with composition/reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and reporting payloads for this batch.
- Update manifest statuses only when criteria are truly met.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.

Recommended fixtures to wire or validate in this prompt:
- fixture.momentum_sustained_up_v1



Expected deliverables before you stop:
1. batch rows implemented or honestly left blocked with explicit reasons
2. registry/catalog updated
3. tests added or updated
4. tracker regenerated
5. short summary of:
   - files changed
   - tests run
   - statuses advanced
   - unresolved blockers
```

## Prompt 08 — `mean_reversion_wave_2`

### Batch scope

- Williams %R Reversion
- Range Reversion
- Long-Horizon Reversal
- Volatility-Adjusted Reversion

### Copy-paste prompt

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
Implement this batch end-to-end in one pass as far as honestly possible.

Requirements:
- Use the exact `target_module`, `target_catalog`, capability fields, fixture ids, and performance-budget ids declared in the manifest rows for this batch.
- Reuse shared helpers whenever possible; do not duplicate logic without reason.
- Keep outputs normalized and compatible with composition/reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and reporting payloads for this batch.
- Update manifest statuses only when criteria are truly met.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.

Recommended fixtures to wire or validate in this prompt:
- fixture.mean_reversion_one_overshoot_v1
- fixture.mean_reversion_range_oscillation_v1



Expected deliverables before you stop:
1. batch rows implemented or honestly left blocked with explicit reasons
2. registry/catalog updated
3. tests added or updated
4. tracker regenerated
5. short summary of:
   - files changed
   - tests run
   - statuses advanced
   - unresolved blockers
```

## Prompt 09 — `volatility_wave_1`

### Batch scope

- Volatility Breakout
- ATR Channel Breakout
- Volatility Mean Reversion

### Copy-paste prompt

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
Implement this batch end-to-end in one pass as far as honestly possible.

Requirements:
- Use the exact `target_module`, `target_catalog`, capability fields, fixture ids, and performance-budget ids declared in the manifest rows for this batch.
- Reuse shared helpers whenever possible; do not duplicate logic without reason.
- Keep outputs normalized and compatible with composition/reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and reporting payloads for this batch.
- Update manifest statuses only when criteria are truly met.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.

Recommended fixtures to wire or validate in this prompt:
- fixture.volatility_compression_release_v1



Expected deliverables before you stop:
1. batch rows implemented or honestly left blocked with explicit reasons
2. registry/catalog updated
3. tests added or updated
4. tracker regenerated
5. short summary of:
   - files changed
   - tests run
   - statuses advanced
   - unresolved blockers
```

## Prompt 10 — `pattern_wave_1`

### Batch scope

- Support and Resistance Bounce
- Breakout Retest
- Pivot Point Strategy
- Opening Range Breakout
- Inside Bar Breakout

### Copy-paste prompt

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
Implement this batch end-to-end in one pass as far as honestly possible.

Requirements:
- Use the exact `target_module`, `target_catalog`, capability fields, fixture ids, and performance-budget ids declared in the manifest rows for this batch.
- Reuse shared helpers whenever possible; do not duplicate logic without reason.
- Keep outputs normalized and compatible with composition/reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and reporting payloads for this batch.
- Update manifest statuses only when criteria are truly met.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.

Recommended fixtures to wire or validate in this prompt:
- fixture.pattern_support_rejection_v1
- fixture.pattern_opening_range_breakout_v1



Expected deliverables before you stop:
1. batch rows implemented or honestly left blocked with explicit reasons
2. registry/catalog updated
3. tests added or updated
4. tracker regenerated
5. short summary of:
   - files changed
   - tests run
   - statuses advanced
   - unresolved blockers
```

## Prompt 11 — `pattern_wave_2`

### Batch scope

- Gap-and-Go
- Trendline Break Strategy
- Volatility Squeeze Breakout

### Copy-paste prompt

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
Implement this batch end-to-end in one pass as far as honestly possible.

Requirements:
- Use the exact `target_module`, `target_catalog`, capability fields, fixture ids, and performance-budget ids declared in the manifest rows for this batch.
- Reuse shared helpers whenever possible; do not duplicate logic without reason.
- Keep outputs normalized and compatible with composition/reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and reporting payloads for this batch.
- Update manifest statuses only when criteria are truly met.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.

Recommended fixtures to wire or validate in this prompt:
- fixture.pattern_support_rejection_v1



Expected deliverables before you stop:
1. batch rows implemented or honestly left blocked with explicit reasons
2. registry/catalog updated
3. tests added or updated
4. tracker regenerated
5. short summary of:
   - files changed
   - tests run
   - statuses advanced
   - unresolved blockers
```

## Prompt 12 — `mean_reversion_wave_3`

### Batch scope

- Intraday VWAP Reversion
- Opening Gap Fade
- Ornstein-Uhlenbeck Reversion

### Copy-paste prompt

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
Implement this batch end-to-end in one pass as far as honestly possible.

Requirements:
- Use the exact `target_module`, `target_catalog`, capability fields, fixture ids, and performance-budget ids declared in the manifest rows for this batch.
- Reuse shared helpers whenever possible; do not duplicate logic without reason.
- Keep outputs normalized and compatible with composition/reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and reporting payloads for this batch.
- Update manifest statuses only when criteria are truly met.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.

Recommended fixtures to wire or validate in this prompt:
- fixture.mean_reversion_one_overshoot_v1



Expected deliverables before you stop:
1. batch rows implemented or honestly left blocked with explicit reasons
2. registry/catalog updated
3. tests added or updated
4. tracker regenerated
5. short summary of:
   - files changed
   - tests run
   - statuses advanced
   - unresolved blockers
```

## Prompt 13 — `momentum_wave_3`

### Batch scope

- Cross-Sectional Momentum
- Relative Strength Momentum
- Dual Momentum
- Residual Momentum

### Copy-paste prompt

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
Implement this batch end-to-end in one pass as far as honestly possible.

Requirements:
- Use the exact `target_module`, `target_catalog`, capability fields, fixture ids, and performance-budget ids declared in the manifest rows for this batch.
- Reuse shared helpers whenever possible; do not duplicate logic without reason.
- Keep outputs normalized and compatible with composition/reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and reporting payloads for this batch.
- Update manifest statuses only when criteria are truly met.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.

Recommended fixtures to wire or validate in this prompt:
- fixture.momentum_cross_sectional_ranking_v1

Blockers or prerequisite framework slices that may need work inside this same prompt:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1


Expected deliverables before you stop:
1. batch rows implemented or honestly left blocked with explicit reasons
2. registry/catalog updated
3. tests added or updated
4. tracker regenerated
5. short summary of:
   - files changed
   - tests run
   - statuses advanced
   - unresolved blockers
```

## Prompt 14 — `factor_wave_1`

### Batch scope

- Low Volatility Strategy
- Low Beta / Betting-Against-Beta
- Dividend Yield Strategy
- Growth Factor Strategy
- Liquidity Factor Strategy

### Copy-paste prompt

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
Implement this batch end-to-end in one pass as far as honestly possible.

Requirements:
- Use the exact `target_module`, `target_catalog`, capability fields, fixture ids, and performance-budget ids declared in the manifest rows for this batch.
- Reuse shared helpers whenever possible; do not duplicate logic without reason.
- Keep outputs normalized and compatible with composition/reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and reporting payloads for this batch.
- Update manifest statuses only when criteria are truly met.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.

Recommended fixtures to wire or validate in this prompt:
- fixture.factor_monthly_rebalance_v1

Blockers or prerequisite framework slices that may need work inside this same prompt:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1


Expected deliverables before you stop:
1. batch rows implemented or honestly left blocked with explicit reasons
2. registry/catalog updated
3. tests added or updated
4. tracker regenerated
5. short summary of:
   - files changed
   - tests run
   - statuses advanced
   - unresolved blockers
```

## Prompt 15 — `factor_wave_2`

### Batch scope

- Value Strategy
- Quality Strategy
- Minimum Variance Strategy
- Size / Small-Cap Strategy
- Mid-Cap Tilt Strategy
- Profitability Factor Strategy
- Earnings Quality Strategy
- Low Leverage / Balance-Sheet Strength

### Copy-paste prompt

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
Implement this batch end-to-end in one pass as far as honestly possible.

Requirements:
- Use the exact `target_module`, `target_catalog`, capability fields, fixture ids, and performance-budget ids declared in the manifest rows for this batch.
- Reuse shared helpers whenever possible; do not duplicate logic without reason.
- Keep outputs normalized and compatible with composition/reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and reporting payloads for this batch.
- Update manifest statuses only when criteria are truly met.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.

Recommended fixtures to wire or validate in this prompt:
- fixture.factor_monthly_rebalance_v1

Blockers or prerequisite framework slices that may need work inside this same prompt:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1


Expected deliverables before you stop:
1. batch rows implemented or honestly left blocked with explicit reasons
2. registry/catalog updated
3. tests added or updated
4. tracker regenerated
5. short summary of:
   - files changed
   - tests run
   - statuses advanced
   - unresolved blockers
```

## Prompt 16 — `factor_wave_3`

### Batch scope

- Multi-Factor Composite
- Residual Volatility Strategy
- Defensive Equity Strategy
- Investment Quality Strategy
- Earnings Stability / Low Earnings Variability

### Copy-paste prompt

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
Implement this batch end-to-end in one pass as far as honestly possible.

Requirements:
- Use the exact `target_module`, `target_catalog`, capability fields, fixture ids, and performance-budget ids declared in the manifest rows for this batch.
- Reuse shared helpers whenever possible; do not duplicate logic without reason.
- Keep outputs normalized and compatible with composition/reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and reporting payloads for this batch.
- Update manifest statuses only when criteria are truly met.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.

Recommended fixtures to wire or validate in this prompt:
- fixture.factor_monthly_rebalance_v1

Blockers or prerequisite framework slices that may need work inside this same prompt:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1


Expected deliverables before you stop:
1. batch rows implemented or honestly left blocked with explicit reasons
2. registry/catalog updated
3. tests added or updated
4. tracker regenerated
5. short summary of:
   - files changed
   - tests run
   - statuses advanced
   - unresolved blockers
```

## Prompt 17 — `cross_asset_wave_1`

### Batch scope

- Carry Trade (FX/Rates)
- Yield Curve Steepener/Flattener
- Curve Roll-Down Strategy
- Commodity Term Structure / Roll Yield
- Risk-On / Risk-Off Regime
- Intermarket Confirmation
- Seasonality / Calendar Effects
- Earnings Drift / Post-Event Momentum

### Copy-paste prompt

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
Implement this batch end-to-end in one pass as far as honestly possible.

Requirements:
- Use the exact `target_module`, `target_catalog`, capability fields, fixture ids, and performance-budget ids declared in the manifest rows for this batch.
- Reuse shared helpers whenever possible; do not duplicate logic without reason.
- Keep outputs normalized and compatible with composition/reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and reporting payloads for this batch.
- Update manifest statuses only when criteria are truly met.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.

Recommended fixtures to wire or validate in this prompt:
- fixture.cross_asset_carry_ranking_v1
- fixture.risk_on_off_regime_v1
- fixture.event_earnings_after_close_v1

Blockers or prerequisite framework slices that may need work inside this same prompt:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.spread_leg_output_v1
- blocker.multi_leg_reporting_v1
- blocker.event_calendar_v1
- blocker.event_window_execution_v1
- blocker.event_reporting_v1


Expected deliverables before you stop:
1. batch rows implemented or honestly left blocked with explicit reasons
2. registry/catalog updated
3. tests added or updated
4. tracker regenerated
5. short summary of:
   - files changed
   - tests run
   - statuses advanced
   - unresolved blockers
```

## Prompt 18 — `composite_wave_2`

### Batch scope

- Rank Aggregation
- Risk Budgeting / Risk Parity
- Volatility Targeting Overlay

### Copy-paste prompt

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
Implement this batch end-to-end in one pass as far as honestly possible.

Requirements:
- Use the exact `target_module`, `target_catalog`, capability fields, fixture ids, and performance-budget ids declared in the manifest rows for this batch.
- Reuse shared helpers whenever possible; do not duplicate logic without reason.
- Keep outputs normalized and compatible with composition/reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and reporting payloads for this batch.
- Update manifest statuses only when criteria are truly met.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.

Recommended fixtures to wire or validate in this prompt:
- fixture.composite_rank_aggregation_v1
- fixture.composite_risk_budget_v1

Blockers or prerequisite framework slices that may need work inside this same prompt:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1


Expected deliverables before you stop:
1. batch rows implemented or honestly left blocked with explicit reasons
2. registry/catalog updated
3. tests added or updated
4. tracker regenerated
5. short summary of:
   - files changed
   - tests run
   - statuses advanced
   - unresolved blockers
```

## Prompt 19 — `composite_wave_3`

### Batch scope

- Constrained Multi-Factor Optimization
- Regime Switching / HMM Gating

### Copy-paste prompt

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
Implement this batch end-to-end in one pass as far as honestly possible.

Requirements:
- Use the exact `target_module`, `target_catalog`, capability fields, fixture ids, and performance-budget ids declared in the manifest rows for this batch.
- Reuse shared helpers whenever possible; do not duplicate logic without reason.
- Keep outputs normalized and compatible with composition/reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and reporting payloads for this batch.
- Update manifest statuses only when criteria are truly met.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.

Recommended fixtures to wire or validate in this prompt:
- fixture.composite_risk_budget_v1
- fixture.composite_regime_switch_v1

Blockers or prerequisite framework slices that may need work inside this same prompt:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1
- blocker.regime_state_support_v1


Expected deliverables before you stop:
1. batch rows implemented or honestly left blocked with explicit reasons
2. registry/catalog updated
3. tests added or updated
4. tracker regenerated
5. short summary of:
   - files changed
   - tests run
   - statuses advanced
   - unresolved blockers
```

## Prompt 20 — `advanced_model_wave_1`

### Batch scope

- Sentiment Strategy
- Machine Learning Classifier
- Machine Learning Regressor
- Regime-Switching Strategy
- Ensemble / Voting Strategy

### Copy-paste prompt

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
Implement this batch end-to-end in one pass as far as honestly possible.

Requirements:
- Use the exact `target_module`, `target_catalog`, capability fields, fixture ids, and performance-budget ids declared in the manifest rows for this batch.
- Reuse shared helpers whenever possible; do not duplicate logic without reason.
- Keep outputs normalized and compatible with composition/reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and reporting payloads for this batch.
- Update manifest statuses only when criteria are truly met.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.

Recommended fixtures to wire or validate in this prompt:
- fixture.factor_monthly_rebalance_v1

Blockers or prerequisite framework slices that may need work inside this same prompt:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1


Expected deliverables before you stop:
1. batch rows implemented or honestly left blocked with explicit reasons
2. registry/catalog updated
3. tests added or updated
4. tracker regenerated
5. short summary of:
   - files changed
   - tests run
   - statuses advanced
   - unresolved blockers
```

## Prompt 21 — `event_wave_1`

### Batch scope

- Post-Earnings Announcement Drift (PEAD)
- Pre-Earnings Announcement Drift
- Earnings Announcement Premium
- Index Rebalancing Effect Strategy
- ETF Rebalancing Anticipation / Front-Run Strategy

### Copy-paste prompt

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
Implement this batch end-to-end in one pass as far as honestly possible.

Requirements:
- Use the exact `target_module`, `target_catalog`, capability fields, fixture ids, and performance-budget ids declared in the manifest rows for this batch.
- Reuse shared helpers whenever possible; do not duplicate logic without reason.
- Keep outputs normalized and compatible with composition/reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and reporting payloads for this batch.
- Update manifest statuses only when criteria are truly met.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.

Recommended fixtures to wire or validate in this prompt:
- fixture.event_earnings_after_close_v1
- fixture.event_index_rebalance_window_v1

Blockers or prerequisite framework slices that may need work inside this same prompt:
- blocker.event_calendar_v1
- blocker.event_window_execution_v1
- blocker.event_reporting_v1


Expected deliverables before you stop:
1. batch rows implemented or honestly left blocked with explicit reasons
2. registry/catalog updated
3. tests added or updated
4. tracker regenerated
5. short summary of:
   - files changed
   - tests run
   - statuses advanced
   - unresolved blockers
```

## Prompt 22 — `stat_arb_wave_1`

### Batch scope

- Pairs Trading (Distance Method)
- Pairs Trading (Cointegration)
- Basket Statistical Arbitrage
- Funding/Basis Arbitrage

### Copy-paste prompt

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
Implement this batch end-to-end in one pass as far as honestly possible.

Requirements:
- Use the exact `target_module`, `target_catalog`, capability fields, fixture ids, and performance-budget ids declared in the manifest rows for this batch.
- Reuse shared helpers whenever possible; do not duplicate logic without reason.
- Keep outputs normalized and compatible with composition/reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and reporting payloads for this batch.
- Update manifest statuses only when criteria are truly met.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.

Recommended fixtures to wire or validate in this prompt:
- fixture.statarb_pair_divergence_reversion_v1
- fixture.relative_value_curve_spread_v1

Blockers or prerequisite framework slices that may need work inside this same prompt:
- blocker.spread_leg_output_v1
- blocker.hedge_ratio_helpers_v1
- blocker.multi_leg_reporting_v1


Expected deliverables before you stop:
1. batch rows implemented or honestly left blocked with explicit reasons
2. registry/catalog updated
3. tests added or updated
4. tracker regenerated
5. short summary of:
   - files changed
   - tests run
   - statuses advanced
   - unresolved blockers
```

## Prompt 23 — `relative_value_wave_2`

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

### Copy-paste prompt

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
Implement this batch end-to-end in one pass as far as honestly possible.

Requirements:
- Use the exact `target_module`, `target_catalog`, capability fields, fixture ids, and performance-budget ids declared in the manifest rows for this batch.
- Reuse shared helpers whenever possible; do not duplicate logic without reason.
- Keep outputs normalized and compatible with composition/reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and reporting payloads for this batch.
- Update manifest statuses only when criteria are truly met.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.

Recommended fixtures to wire or validate in this prompt:
- fixture.statarb_pair_divergence_reversion_v1
- fixture.relative_value_curve_spread_v1

Blockers or prerequisite framework slices that may need work inside this same prompt:
- blocker.spread_leg_output_v1
- blocker.hedge_ratio_helpers_v1
- blocker.multi_leg_reporting_v1


Expected deliverables before you stop:
1. batch rows implemented or honestly left blocked with explicit reasons
2. registry/catalog updated
3. tests added or updated
4. tracker regenerated
5. short summary of:
   - files changed
   - tests run
   - statuses advanced
   - unresolved blockers
```

## Prompt 24 — `volatility_wave_2`

### Batch scope

- Delta-Neutral Volatility Trading
- Gamma Scalping
- Volatility Risk Premium Capture
- Dispersion Trading
- Skew Trading
- Term Structure Trading
- Straddle Breakout Timing

### Copy-paste prompt

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
Implement this batch end-to-end in one pass as far as honestly possible.

Requirements:
- Use the exact `target_module`, `target_catalog`, capability fields, fixture ids, and performance-budget ids declared in the manifest rows for this batch.
- Reuse shared helpers whenever possible; do not duplicate logic without reason.
- Keep outputs normalized and compatible with composition/reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and reporting payloads for this batch.
- Update manifest statuses only when criteria are truly met.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.

Recommended fixtures to wire or validate in this prompt:
- fixture.options_iv_rv_gap_v1

Blockers or prerequisite framework slices that may need work inside this same prompt:
- blocker.options_chain_v1
- blocker.greeks_v1


Expected deliverables before you stop:
1. batch rows implemented or honestly left blocked with explicit reasons
2. registry/catalog updated
3. tests added or updated
4. tracker regenerated
5. short summary of:
   - files changed
   - tests run
   - statuses advanced
   - unresolved blockers
```

## Prompt 25 — `composite_wave_4`

### Batch scope

- Bagging Ensemble
- Boosting Ensemble
- Stacking / Meta-Learning

### Copy-paste prompt

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
Implement this batch end-to-end in one pass as far as honestly possible.

Requirements:
- Use the exact `target_module`, `target_catalog`, capability fields, fixture ids, and performance-budget ids declared in the manifest rows for this batch.
- Reuse shared helpers whenever possible; do not duplicate logic without reason.
- Keep outputs normalized and compatible with composition/reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and reporting payloads for this batch.
- Update manifest statuses only when criteria are truly met.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.

Recommended fixtures to wire or validate in this prompt:
- fixture.composite_ml_ensemble_v1



Expected deliverables before you stop:
1. batch rows implemented or honestly left blocked with explicit reasons
2. registry/catalog updated
3. tests added or updated
4. tracker regenerated
5. short summary of:
   - files changed
   - tests run
   - statuses advanced
   - unresolved blockers
```

## Prompt 26 — `composite_wave_5`

### Batch scope

- RL Allocation Controller
- Hierarchical Controller / Meta-Policy

### Copy-paste prompt

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
Implement this batch end-to-end in one pass as far as honestly possible.

Requirements:
- Use the exact `target_module`, `target_catalog`, capability fields, fixture ids, and performance-budget ids declared in the manifest rows for this batch.
- Reuse shared helpers whenever possible; do not duplicate logic without reason.
- Keep outputs normalized and compatible with composition/reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and reporting payloads for this batch.
- Update manifest statuses only when criteria are truly met.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.

Recommended fixtures to wire or validate in this prompt:
- fixture.composite_rl_policy_stub_v1

Blockers or prerequisite framework slices that may need work inside this same prompt:
- blocker.rl_environment_v1


Expected deliverables before you stop:
1. batch rows implemented or honestly left blocked with explicit reasons
2. registry/catalog updated
3. tests added or updated
4. tracker regenerated
5. short summary of:
   - files changed
   - tests run
   - statuses advanced
   - unresolved blockers
```

## Prompt 27 — `advanced_wave_blocked`

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

### Copy-paste prompt

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
Implement this batch end-to-end in one pass as far as honestly possible.

Requirements:
- Use the exact `target_module`, `target_catalog`, capability fields, fixture ids, and performance-budget ids declared in the manifest rows for this batch.
- Reuse shared helpers whenever possible; do not duplicate logic without reason.
- Keep outputs normalized and compatible with composition/reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and reporting payloads for this batch.
- Update manifest statuses only when criteria are truly met.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.

Recommended fixtures to wire or validate in this prompt:
- fixture.microstructure_top_of_book_imbalance_v1
- fixture.microstructure_queue_state_v1
- fixture.execution_twap_schedule_v1
- fixture.execution_vwap_curve_drift_v1

Blockers or prerequisite framework slices that may need work inside this same prompt:
- blocker.order_book_input_v1
- blocker.own_order_state_v1
- blocker.execution_plan_output_v1
- blocker.fill_simulation_v1

Special rule for this batch:
- Do **not** fake-complete these rows if the required framework is still missing.
- Your job here is to implement the narrowest reusable framework slices, stubs, contracts, tests, and manifest/blocker updates that move this batch forward honestly.
- Leave rows as `blocked_framework` or `prototype_only` when that is the correct status.

Expected deliverables before you stop:
1. batch rows implemented or honestly left blocked with explicit reasons
2. registry/catalog updated
3. tests added or updated
4. tracker regenerated
5. short summary of:
   - files changed
   - tests run
   - statuses advanced
   - unresolved blockers
```