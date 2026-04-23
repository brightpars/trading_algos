# Algorithm Library Systematic Implementation Plan — Version 2

## What changed in Version 2

This version keeps the core structure of the original plan, but adds the main improvements identified during review:

1. **The machine-readable manifest becomes the single source of truth** for counts, source-document version, catalog references, and completion totals.
2. **Framework blockers become first-class tracked artifacts**, not just a status value hidden inside algorithm rows.
3. **Golden fixtures and expected-behavior snapshots** become mandatory parts of the testing strategy.
4. **Performance and scalability budgets** become explicit acceptance criteria, not an afterthought.
5. **A small composite-method wave moves earlier** so the child-output contract is validated before too many families are implemented.
6. **Readiness is split into two axes**: delivery status and operational readiness (`research_ready` vs `production_ready`).
7. **A capabilities matrix is added to the manifest**, so every row clearly declares what kind of data, timing model, scope, and output model it needs.

---

## Purpose

This document defines a **systematic, trackable, automatable, and delivery-safe strategy** for implementing the full algorithm library.

It is intended to answer these practical questions:

1. In what order should the algorithms and combination methods be implemented?
2. How should the work be batched so implementation remains manageable?
3. How do we keep the codebase state visible at all times?
4. How do we automate progress tracking so the library does not become a manual spreadsheet exercise?
5. How do we know when a family, phase, blocker, or individual algorithm is actually done?
6. How do we keep the library implementation aligned with evolving requirements documents without tracker drift?
7. How do we distinguish a strategy that is merely coded from a strategy that is truly ready for research or production use?

This plan should be used together with the current requirement, authoring, reporting, and readiness documents in the repository. However, the authoritative totals and source references must come from the manifest metadata, not from prose in this file.

---

## Executive summary

The library should **not** be implemented as a flat list.

Instead, it should be implemented as a **multi-phase product program** with:

- explicit readiness tiers
- family-by-family delivery
- reusable primitives
- small repeatable batches
- machine-readable manifests
- first-class blocker tracking
- generated progress dashboards
- fixture-based behavior validation
- CI-visible completion checks
- performance budgets
- separate research-readiness and production-readiness states

The recommended implementation order is:

1. **Manifest, blocker registry, fixture registry, and tracker automation**
2. **Shared Tier-1 OHLCV primitives**
3. **First trend batch**
4. **Early composite contract-validation batch**
5. **First momentum and mean-reversion batches**
6. **Remaining Tier-1 families**
7. **Cross-sectional, ranking, and rebalance-driven families**
8. **Event-driven families**
9. **Spread / multi-leg / relative-value families**
10. **Advanced execution, options, microstructure, and RL families only after framework expansion**

---

## Core delivery principles

### 1. Treat the library as a product program, not as a loose backlog

Every algorithm and every combination method must have:

- a manifest row
- a family
- a tier
- a target module
- known dependencies
- a test surface
- a readiness state
- an operational-readiness target
- a fixture mapping
- a performance budget id

No row should be considered truly planned until it exists in the manifest.

### 2. The manifest is the single source of truth

Counts, source-document version, row identifiers, family totals, and catalog references must **not** be manually maintained in multiple prose files.

The source of truth should be:

- one top-level manifest metadata section
- one row per algorithm
- one row per combination method
- one blocker registry
- one fixture registry
- one generated markdown dashboard

This means:

- totals shown in dashboards are generated
- percentages are generated
- "missing rows" are discovered automatically
- source-doc version is read from manifest metadata
- drift between docs and code is a CI failure, not a manual cleanup task

### 3. Implement by family and shared primitive, not by random algorithm order

Many strategies are minor variants of the same internal machinery.

The fast path is:

1. build reusable primitives
2. build family scaffolding
3. implement several algorithms that reuse the same internals
4. validate the family through fixture-backed tests

This reduces duplicated code and keeps behavior consistent.

### 4. Separate framework readiness from algorithm readiness

Some rows are blocked because the algorithm is difficult.

Others are blocked because the repository cannot yet support:

- the required input domain
- the required timing model
- the required output contract
- the required simulation environment

Examples:

- microstructure strategies need order-book inputs
- execution algorithms need child-order and execution-plan outputs
- options strategies need option-chain, term-structure, and greek-aware inputs
- cross-sectional strategies need aligned panels and rebalance logic
- event-driven strategies need event calendars and timestamp-valid windows
- relative-value strategies need multi-leg diagnostics and hedge-ratio helpers

Framework readiness must be tracked explicitly.

### 5. Framework blockers are first-class tracked work items

A blocker should not be just a string inside an algorithm row.

It should have:

- a blocker key
- a description
- status
- owner
- affected families
- affected rows
- exit criteria
- unlock conditions
- related framework modules
- target tests

This makes it possible to manage the program honestly.

### 6. Preserve explainability and normalized outputs

Every strategy should expose:

- machine-readable parameter schema
- raw intermediate metrics
- normalized final output
- reporting metadata
- enough diagnostics for the dashboard
- enough child-output structure for composition

Even when internal math differs, outputs should remain composable.

### 7. Use small, repeatable implementation batches

Recommended batch sizes:

- **5 to 10 single-series algorithms**
- **3 to 6 cross-sectional / event-driven / multi-asset algorithms**
- **1 framework expansion plus 2 to 4 dependent algorithms**
- **1 composite-method wave that validates the child-output contract**

### 8. Distinguish delivery completion from operational readiness

An algorithm can be:

- coded
- registered
- tested
- documented

and still only be **research-ready**, not **production-ready**.

This is especially true for:

- microstructure
- execution
- options surface
- institutional relative value
- RL controllers
- any strategy with heavy simulation assumptions

The tracker must model that difference directly.

---

## Readiness tiers

### Tier 1 — Implementable now with the current OHLCV-centric architecture

These are the best early targets because they fit the current repository shape with limited extension.

Typical families:

- trend following
- single-asset momentum
- single-asset mean reversion
- simple volatility breakout / normalization
- many pattern / price-action algorithms
- basic composite methods that consume normalized child outputs

Typical characteristics:

- single symbol
- OHLCV input
- bar-by-bar processing
- signal / score / regime output
- modest warmup handling

### Tier 2 — Implementable after moderate framework expansion

These need new infrastructure, but are still realistic without architectural reinvention.

Typical families:

- cross-sectional momentum and relative strength
- dual momentum and residual momentum
- factor and risk-premia strategies
- rebalance-driven portfolio selection
- event-driven strategies
- rank aggregation and optimization-based combination methods
- some spread / stat-arb families

Typical new requirements:

- aligned multi-asset panels
- rebalance calendar
- ranking outputs
- portfolio-weight outputs
- event calendar inputs
- multi-leg diagnostics

### Tier 3 — Requires substantial new framework or data model

These should remain visible, but explicitly framework-blocked, until infrastructure exists.

Typical families:

- options / greeks / volatility-surface strategies
- execution algorithms
- microstructure / HFT / market making
- advanced institutional stat-arb and fixed-income relative value
- RL control layers

Typical new requirements:

- option chains and surfaces
- order book and own-order state
- execution-plan outputs and fill simulation
- high-frequency timestamp precision
- action-space and reward-model support

---

## Two-axis readiness model

The tracker should model two separate dimensions.

### A. Delivery status

Use one of these values per row:

- `not_started`
- `blocked_framework`
- `ready_to_implement`
- `in_progress`
- `implemented`
- `tested`
- `documented`
- `complete`

Recommended meaning:

- `implemented` = code exists and registers
- `tested` = mapped tests exist and pass
- `documented` = reporting/spec/docs exist
- `complete` = all required deliverables and acceptance checks pass

### B. Operational readiness

Use one of these values per row:

- `not_applicable`
- `prototype_only`
- `research_ready`
- `production_candidate`
- `production_ready`

Recommended meaning:

| State | Meaning |
|---|---|
| `prototype_only` | Code exists mainly to prove concept or wire interfaces. |
| `research_ready` | Good enough for backtesting, evaluation, and dashboard exploration. |
| `production_candidate` | Implementation is stable enough for broader validation but still has known operational gaps. |
| `production_ready` | Inputs, outputs, diagnostics, performance, and safeguards are adequate for production use in the intended environment. |

This axis matters most for advanced families.

---

## Canonical blocker model

Each framework blocker should be tracked explicitly.

### Recommended blocker statuses

- `planned`
- `in_progress`
- `done`

### Suggested blocker categories

- input-domain blocker
- output-contract blocker
- data-model blocker
- execution-model blocker
- simulation blocker
- reporting blocker
- performance blocker

### Example blocker keys

- `blocker.multi_asset_panel_v1`
- `blocker.rebalance_engine_v1`
- `blocker.event_calendar_v1`
- `blocker.spread_leg_output_v1`
- `blocker.options_chain_v1`
- `blocker.greeks_v1`
- `blocker.execution_plan_output_v1`
- `blocker.order_book_input_v1`
- `blocker.fill_simulation_v1`
- `blocker.rl_environment_v1`

---

## Machine-readable tracking system

The tracking system should be repository-native and automation-first.

### Tracking artifacts

1. `manifests/algorithm_library_manifest.yaml`
   - authoritative row-level manifest
2. `manifests/algorithm_framework_blockers.yaml`
   - blocker registry
3. `manifests/algorithm_test_fixtures.yaml`
   - fixture registry
4. `manifests/algorithm_performance_budgets.yaml`
   - performance budgets
5. `docs/algorithm_library_implementation_tracker.md`
   - generated human-readable dashboard
6. `scripts/build_algorithm_library_tracker.py`
   - renders dashboard from manifest + registry state
7. `scripts/build_algorithm_capability_matrix.py`
   - optional derived capability summary
8. `tests/test_algorithm_manifest_consistency.py`
   - checks manifest integrity
9. `tests/test_algorithm_registry_consistency.py`
   - checks manifest vs registry
10. `tests/test_algorithm_fixture_mapping_consistency.py`
   - checks fixture coverage claims

### Why this structure is recommended

- YAML is easy to diff and review
- generated markdown is easy for humans to inspect
- blocker registry prevents vague hidden blockers
- fixture registry makes behavior expectations explicit
- performance budgets prevent "works on my machine" drift
- consistency tests prevent the tracker from lying

---

## Manifest-first source-of-truth policy

The manifest should own these values:

- current source requirements document path
- source requirements document version
- expected totals
- expected family totals
- expected method totals
- catalog-ref namespace
- supported capability taxonomy

### Top-level manifest metadata

Example:

```yaml
manifest_version: 2
source_catalog:
  requirements_doc_path: docs/algorithm_library_requirements_v4.md
  requirements_doc_version: 4
  combination_doc_path: docs/algorithm_library_requirements_v4.md
  source_catalog_generated_at: 2026-04-23
expected_totals:
  algorithms: 121
  combination_methods: 12
expected_family_totals:
  trend: 14
  momentum: 11
  mean_reversion: 12
  composite: 12
# ...
capability_taxonomy_version: 1
```

Important rule:

- prose files may describe the system
- generated dashboards may summarize the system
- only the manifest metadata is allowed to define authoritative totals

---

## Capabilities matrix

Every row should declare what type of strategy it is from an engineering perspective.

### Minimum capability fields per row

- `timeframe_support`
- `asset_scope`
- `position_style`
- `data_frequency_needed`
- `required_input_domains`
- `required_output_modes`
- `supports_composition`
- `reporting_mode`
- `warmup_profile`
- `session_awareness`
- `event_awareness`
- `simulation_needs`

### Recommended value examples

| Field | Example values |
|---|---|
| `timeframe_support` | `intraday`, `daily`, `rebalance_driven`, `mixed` |
| `asset_scope` | `single_asset`, `multi_asset`, `universe`, `portfolio`, `pair`, `basket` |
| `position_style` | `long_only`, `long_short`, `paired_legs`, `allocation`, `execution_child_orders` |
| `data_frequency_needed` | `bar`, `intraday_bar`, `tick`, `order_book`, `event_calendar`, `fundamentals_pti`, `options_surface` |
| `supports_composition` | `true`, `false`, `child_only`, `score_only` |
| `reporting_mode` | `bar_series`, `rebalance_report`, `event_window`, `multi_leg`, `execution_trace` |

This matrix is useful both for planning and for UI/catalog exposure later.

---

## Recommended manifest row schema

Example algorithm row:

```yaml
- catalog_ref: "algorithm:1"
  source_doc_ref: "requirements_v4:algorithm:1"
  kind: algorithm
  name: "Simple Moving Average Crossover"
  family: trend
  subcategory: moving_average
  tier: tier1

  delivery_status: ready_to_implement
  operational_readiness: prototype_only

  framework_blockers: []
  framework_dependencies: []
  code_dependencies:
    - indicators.moving_averages
    - transforms.crossover_detection

  target_module: src/trading_algos/alertgen/algorithms/trend/sma_crossover.py
  target_catalog: src/trading_algos/alertgen/algorithms/trend/catalog.py

  required_input_domains:
    - single_asset_ohlcv
  required_output_modes:
    - signal
    - score
    - diagnostics

  timeframe_support:
    - daily
    - intraday
  asset_scope: single_asset
  position_style: long_only
  data_frequency_needed:
    - bar
  supports_composition: true
  reporting_mode: bar_series
  warmup_profile: rolling_window
  session_awareness: false
  event_awareness: false
  simulation_needs: none

  fixture_ids:
    - fixture.trend_monotonic_cross_v1
    - fixture.trend_whipsaw_guard_v1

  performance_budget_id: perf.single_asset_bar_v1

  required_tests:
    - registry
    - param_validation
    - short_history
    - signal_behavior
    - fixture_behavior
    - performance_smoke

  batch: trend_wave_1
  notes: "Implement with event/state emit mode and min spread filter."
```

Example combination-method row:

```yaml
- catalog_ref: "combination:1"
  source_doc_ref: "requirements_v4:combination:1"
  kind: combination_method
  name: "Hard Boolean Gating (AND / OR / Majority)"
  family: composite
  tier: tier1

  delivery_status: ready_to_implement
  operational_readiness: research_ready

  framework_blockers: []
  framework_dependencies: []

  target_module: src/trading_algos/alertgen/algorithms/composite/boolean_gating.py

  required_input_domains:
    - aligned_child_outputs
  required_output_modes:
    - signal
    - diagnostics

  timeframe_support:
    - daily
    - intraday
  asset_scope: single_asset
  position_style: long_only
  data_frequency_needed:
    - child_output_stream
  supports_composition: true
  reporting_mode: composite_trace
  warmup_profile: child_dependent
  session_awareness: child_dependent
  event_awareness: child_dependent
  simulation_needs: none

  fixture_ids:
    - fixture.composite_boolean_truth_table_v1

  performance_budget_id: perf.composite_signal_v1

  required_tests:
    - alignment
    - voting_logic
    - serialization
    - fixture_behavior

  batch: composite_contract_wave_1
```

---

## Blocker registry schema

Example:

```yaml
- blocker_key: blocker.multi_asset_panel_v1
  description: "Repository support for aligned multi-symbol panels with rebalance-date slicing."
  category: input-domain blocker
  status: planned
  owner: null
  affected_families:
    - momentum
    - factor
    - cross_asset
    - portfolio
  affected_rows:
    - algorithm:17
    - algorithm:18
    - algorithm:19
  target_modules:
    - src/trading_algos/data/panel_dataset.py
    - src/trading_algos/rebalance/calendar.py
  exit_criteria:
    - "Panel loader supports aligned universe slices"
    - "Rebalance-date iteration exists"
    - "Tests cover missing symbols and unequal history"
```

---

## Golden fixtures and expected-behavior snapshots

The plan should require **deterministic fixture datasets** and **expected behavior checks**.

This is the easiest way to make strategy tests meaningful instead of shallow.

### Why fixtures are needed

Without fixtures, many tests collapse to:

- imports work
- registry works
- some output exists

That is not enough.

A good fixture test tells you:

- what input shape the strategy expects
- what a known scenario looks like
- which signal transition should happen
- which internal metric should cross or flip
- what output should be emitted

### Fixture categories to define

1. **Trend fixtures**
   - monotonic uptrend
   - monotonic downtrend
   - single clean crossover
   - whipsaw / false-break scenario

2. **Mean-reversion fixtures**
   - one clear overshoot and re-entry
   - prolonged trend where reversion should be suppressed
   - range-bound oscillation

3. **Momentum fixtures**
   - sustained continuation
   - weakening momentum
   - cross-sectional ranking with deterministic winners

4. **Event-driven fixtures**
   - event timestamp before market open
   - event timestamp after market close
   - overlapping events

5. **Spread / stat-arb fixtures**
   - stable pair then temporary divergence
   - drifted hedge ratio scenario
   - stale-leg alignment failure

6. **Execution / advanced fixtures**
   - partial-fill progression
   - volume-curve deviation
   - queue and order-state transitions

### Recommended fixture schema

```yaml
- fixture_id: fixture.trend_monotonic_cross_v1
  domain: single_asset_ohlcv
  purpose: "Clean SMA crossover"
  inputs:
    dataset_path: tests/fixtures/trend/monotonic_cross.csv
  expected_behaviors:
    - "Fast SMA crosses slow SMA exactly once"
    - "Buy event emitted on first positive crossover"
    - "No sell event after crossover in the fixture horizon"
```

### Required rule

A row cannot be marked `tested` unless it has at least one mapped fixture or an explicit justification for why a fixture is not applicable.

---

## Performance and scalability budgets

Performance should be tracked as a real acceptance criterion.

### Why this matters

A strategy can be logically correct and still be unusable because it is:

- too slow
- too memory-heavy
- too expensive to recompute
- too slow to evaluate across a universe
- too slow to compose in the dashboard

### Minimum budget types

1. **Single-series bar strategies**
2. **Cross-sectional rebalance strategies**
3. **Event-driven strategies**
4. **Multi-leg strategies**
5. **Composite / child-output strategies**
6. **Execution / microstructure strategies**

### Example budget schema

```yaml
- performance_budget_id: perf.single_asset_bar_v1
  description: "Single-asset OHLCV strategy budget"
  acceptance:
    - "Processes 1 million bars within target runtime on CI reference environment"
    - "Peak memory remains below configured threshold"
    - "No per-bar object explosion"
```

### Required rule

A row should not be marked `production_ready` unless the relevant performance budget passes.

For advanced rows, performance validation can be the difference between `research_ready` and `production_ready`.

---

## Automated tracking workflow

The tracker should be maintained automatically by combining:

1. the manifest
2. the blocker registry
3. the fixture registry
4. the strategy registry discovered from code
5. optional test mappings
6. optional benchmark/performance results

### Desired automation behavior

The tracker generator should be able to:

1. read the manifest metadata
2. inspect registered strategy specs and combination specs
3. inspect blocker registry
4. inspect fixture coverage
5. detect which rows are implemented in code
6. summarize by family, tier, phase, blocker, capability, and readiness state
7. generate a markdown dashboard with:
   - totals
   - percentages
   - family summaries
   - blocker summaries
   - next-ready batches
   - missing fixtures
   - rows stuck in research-only state
   - production-ready counts
   - capability coverage

---

## Required automated progress views

The generated dashboard should include at least these sections.

### 1. Overall progress summary

- algorithms complete / total
- methods complete / total
- counts by delivery status
- counts by operational readiness
- counts by tier

### 2. Family summary table

Columns:

- family
- total rows
- ready to implement
- in progress
- complete
- blocked
- research ready
- production ready
- percent complete
- current active batch

### 3. Framework blockers table

Columns:

- blocker key
- description
- status
- affected families
- affected row count
- exit criteria summary

### 4. Capabilities summary

Columns:

- capability type
- number of rows requiring it
- rows already supported
- rows currently blocked

### 5. Current batch view

Columns:

- batch key
- phase
- rows included
- status
- prerequisites
- remaining tasks

### 6. Fixture coverage view

Columns:

- family
- rows with fixture mapping
- rows missing fixtures
- rows with failing expected behavior

### 7. Performance readiness view

Columns:

- budget id
- rows using budget
- rows passing
- rows failing
- rows unmeasured

### 8. Drift detection view

Examples:

- manifest rows with no registered code
- registered strategies with no manifest row
- rows marked tested but missing fixture mappings
- rows marked production ready but missing performance evidence
- source document version mismatch between tracker and manifest metadata

---

## CI checks to add

### Manifest and registry integrity

1. every implemented strategy in code has a manifest row
2. every manifest row marked `implemented` is actually registered
3. no duplicate `catalog_ref`
4. source metadata exists and is internally consistent
5. family totals in the generated dashboard match manifest metadata

### Test and fixture integrity

6. every row marked `tested` has at least one mapped fixture or explicit waiver
7. every row marked `tested` has mapped test coverage
8. fixture ids referenced by rows actually exist
9. fixture expected-behavior sections are not empty

### Readiness integrity

10. no row marked `production_ready` without performance evidence
11. no Tier-3 row silently marked complete while blocker keys remain unresolved
12. advanced rows can be `complete + research_ready` while still not `production_ready`, but that state must be explicit

---

## Definitions of done

### Algorithm-level done

An individual algorithm is only fully complete when all of the following are true:

1. implementation module exists
2. family catalog registers it
3. spec metadata is complete
4. parameter schema exists
5. normalized output contract is supported
6. intermediate metrics are included for reporting
7. at least one golden fixture is mapped and passes
8. tests cover registration, validation, short history, and behavior
9. manifest row has correct dependency and capability metadata
10. performance budget is assigned
11. delivery status reaches `complete`

### Research-ready done

A row is `research_ready` when:

1. implementation is complete
2. behavior fixtures pass
3. output diagnostics are sufficient for backtesting and dashboard inspection
4. known framework limitations are documented
5. no major correctness blockers remain for the intended research environment

### Production-ready done

A row is `production_ready` only when:

1. all research-ready criteria are true
2. input domain is operationally supported in the target environment
3. performance budget passes
4. reporting is stable enough for monitoring/debugging
5. safeguards and failure modes are defined
6. no unresolved blocker prevents intended production usage

### Family-level done

A family is complete when:

1. all family rows are `complete` or explicitly `blocked_framework`
2. shared primitives are consolidated
3. family catalog is coherent
4. family fixtures and tests pass
5. performance budget coverage exists for the family
6. dashboard exposure is verified

### Phase-level done

A phase is complete when:

1. all included batches are complete or explicitly blocked
2. all phase blocker dependencies are resolved
3. generated tracker reports the expected state
4. CI checks pass
5. fixture and performance summaries are in the expected state

---

## Recommended implementation phases

## Phase 0 — Tracking, metadata, and automation foundation

### Goal

Make progress visible, machine-readable, and auditable before large-scale implementation starts.

### Deliverables

- manifest format
- blocker registry
- fixture registry
- performance budget registry
- generated markdown tracker
- consistency tests
- batch naming convention
- status model
- operational-readiness model
- capabilities taxonomy

### Exit criteria

- every strategy row represented in manifest
- every row assigned family, tier, and blocker state
- every row assigned capability metadata
- tracker can be regenerated automatically
- blocker registry exists and validates
- fixture registry exists, even if initially sparse

---

## Phase 1 — Shared primitives and capability baselines for Tier-1 OHLCV work

### Goal

Build reusable infrastructure that accelerates the earliest families.

### Shared capabilities

- moving averages
- crossover detection helpers
- rolling highs/lows and channels
- ATR and realized volatility
- z-score helpers
- ROC and momentum helpers
- RSI, stochastic, CCI, MACD
- Bollinger and Donchian helpers
- basic regression helpers
- session reset helpers where needed
- normalized signal and diagnostics output contract

### Exit criteria

- helpers exist and are reused by multiple strategies
- no repeated indicator logic without reason
- normalized child-output contract exists
- fixture harness exists for simple OHLCV strategies

---

## Phase 2 — Trend family wave

### Goal

Deliver the first visible family using the new shared primitives.

### Suggested batches

#### Batch `trend_wave_1`

- Simple Moving Average Crossover
- Exponential Moving Average Crossover
- Triple Moving Average Crossover
- Price vs Moving Average
- Moving Average Ribbon Trend

#### Batch `trend_wave_2`

- Breakout (Donchian Channel)
- Channel Breakout with Confirmation
- ADX Trend Filter
- Parabolic SAR Trend Following
- SuperTrend

#### Batch `trend_wave_3`

- Ichimoku Trend Strategy
- MACD Trend Strategy
- Linear Regression Trend
- Time-Series Momentum

### Exit criteria

- trend strategies use shared primitives
- trend fixtures exist and pass
- tracker shows trend family progress automatically
- runtime and memory stay within the single-series bar budget

---

## Phase 3 — Early composite contract-validation wave

### Goal

Validate the child-output contract **early**, before too many families are implemented independently.

### Why this phase moves earlier in Version 2

If composite support is left too late, each family may drift into a slightly different output shape.

A small early composite phase forces the team to standardize:

- signal labels
- score semantics
- alignment assumptions
- diagnostic payload shape
- child contribution reporting

### Suggested batch

#### Batch `composite_contract_wave_1`

- Hard Boolean Gating (AND / OR / Majority)
- Weighted Linear Score Blend

### Exit criteria

- child-output schema is stable
- at least one trend strategy can be composed with another
- composite fixtures exist and pass
- generated reports show child contributions clearly

---

## Phase 4 — Momentum family wave

### Suggested batches

#### Batch `momentum_wave_1`

- Rate of Change Momentum
- Accelerating Momentum
- RSI Momentum Continuation
- Stochastic Momentum
- CCI Momentum

#### Batch `momentum_wave_2`

- KST
- Volume-Confirmed Momentum

#### Batch `momentum_wave_3`

- Cross-Sectional Momentum
- Relative Strength Momentum
- Dual Momentum
- Residual Momentum

### Notes

- the first two batches are early-wave friendly
- `momentum_wave_3` should wait until multi-asset panel and rebalance support exist

### Exit criteria

- single-series momentum rows complete
- multi-asset momentum rows either complete or explicitly blocked
- fixture coverage exists for both continuation and false-continuation cases

---

## Phase 5 — Mean reversion family wave

### Suggested batches

#### Batch `mean_reversion_wave_1`

- Z-Score Mean Reversion
- Bollinger Bands Reversion
- RSI Reversion
- Stochastic Reversion
- CCI Reversion

#### Batch `mean_reversion_wave_2`

- Williams %R Reversion
- Range Reversion
- Volatility-Adjusted Reversion
- Long-Horizon Reversal

#### Batch `mean_reversion_wave_3`

- Intraday VWAP Reversion
- Opening Gap Fade
- Ornstein-Uhlenbeck Reversion

### Notes

- OU reversion should reuse shared statistical-model helpers
- session-aware variants should wait for session-reset support

### Exit criteria

- mean-reversion fixtures include both oscillating and trending scenarios
- trend-suppression or filter behavior is tested where relevant
- runtime remains within expected budget

---

## Phase 6 — Volatility and pattern families

### Volatility batches

#### Batch `volatility_wave_1`

- Volatility Breakout
- ATR Channel Breakout
- Volatility Mean Reversion

#### Batch `volatility_wave_2`

- Straddle Breakout Timing

### Pattern / price-action batches

#### Batch `pattern_wave_1`

- Support and Resistance Bounce
- Breakout Retest
- Pivot Point Strategy
- Opening Range Breakout
- Inside Bar Breakout

#### Batch `pattern_wave_2`

- Gap-and-Go
- Trendline Break Strategy
- Volatility Squeeze Breakout

### Notes

- pattern definitions must be deterministic and fixture-backed
- options-heavy volatility rows should remain blocked until option support exists

---

## Phase 7 — Cross-sectional, factor, macro, and portfolio families

### Required blockers to resolve before start

- `blocker.multi_asset_panel_v1`
- `blocker.rebalance_engine_v1`
- `blocker.portfolio_weight_output_v1`

### Suggested batches

#### Batch `cross_asset_wave_1`

- Carry Trade
- Risk-On / Risk-Off Regime
- Intermarket Confirmation
- Seasonality / Calendar Effects
- Earnings Drift / Post-Event Momentum

#### Batch `factor_wave_1`

- Low Volatility Strategy
- Low Beta / Betting-Against-Beta
- Dividend Yield Strategy
- Growth Factor Strategy
- Liquidity Factor Strategy

#### Batch `factor_wave_2`

- Value Strategy
- Quality Strategy
- Profitability Factor Strategy
- Earnings Quality Strategy
- Low Leverage / Balance-Sheet Strength

#### Batch `factor_wave_3`

- Multi-Factor Composite
- Defensive Equity Strategy
- Residual Volatility Strategy
- Investment Quality Strategy
- Earnings Stability / Low Earnings Variability

#### Batch `portfolio_wave_1`

- Minimum Variance Strategy
- Size / Small-Cap Strategy
- Mid-Cap Tilt Strategy

### Exit criteria

- rebalance-driven outputs work correctly
- ranking and weight outputs are normalized and reportable
- cross-sectional fixture sets exist
- portfolio and factor families meet their budget class

---

## Phase 8 — Advanced composite and portfolio-combination methods

### Required blockers to resolve before start

- `blocker.multi_asset_panel_v1`
- `blocker.portfolio_weight_output_v1`
- `blocker.regime_state_support_v1` if applicable

### Suggested batches

#### Batch `composite_wave_2`

- Rank Aggregation
- Risk Budgeting / Risk Parity
- Volatility Targeting Overlay

#### Batch `composite_wave_3`

- Regime Switching / HMM Gating
- Constrained Multi-Factor Optimization

#### Batch `composite_wave_4`

- Bagging Ensemble
- Boosting Ensemble
- Stacking / Meta-Learning

#### Batch `composite_wave_5`

- RL Allocation Controller
- Hierarchical Controller / Meta-Policy

### Notes

- RL rows may still remain `blocked_framework` until environment support exists
- optimizer-based methods should be tested with deterministic toy fixtures as well as realistic datasets

---

## Phase 9 — Event-driven families

### Required blockers to resolve before start

- `blocker.event_calendar_v1`
- `blocker.event_window_execution_v1`
- `blocker.event_reporting_v1`

### Suggested batch `event_wave_1`

- Post-Earnings Announcement Drift (PEAD)
- Pre-Earnings Announcement Drift
- Earnings Announcement Premium
- Index Rebalancing Effect Strategy
- ETF Rebalancing Anticipation / Front-Run Strategy

### Exit criteria

- event timestamps are handled correctly
- before-open and after-close cases are covered by fixtures
- event metadata appears in reports
- no lookahead leakage in event-window logic

---

## Phase 10 — Spread and relative-value families

### Required blockers to resolve before start

- `blocker.spread_leg_output_v1`
- `blocker.hedge_ratio_helpers_v1`
- `blocker.multi_leg_reporting_v1`

### Suggested batch `stat_arb_wave_1`

- Pairs Trading (Distance Method)
- Pairs Trading (Cointegration)
- Basket Statistical Arbitrage
- Funding / Basis Arbitrage

### Suggested batch `relative_value_wave_2`

- Yield Curve Steepener / Flattener
- Curve Roll-Down Strategy
- Commodity Term Structure / Roll Yield
- Fixed-Income Arbitrage
- Swap Spread Arbitrage

### Exit criteria

- paired or multi-leg instructions are normalized
- hedge-ratio diagnostics are visible
- spread fixtures exist and pass
- multi-leg reporting contract is stable

---

## Phase 11 — Advanced and framework-heavy families

These rows should remain explicit in the tracker and should **not** be hidden or prematurely claimed as done.

### Families

- options / volatility-surface
- execution algorithms
- microstructure / HFT / market making
- advanced institutional relative-value engines
- RL production controllers

### Required blockers typically include

- `blocker.options_chain_v1`
- `blocker.greeks_v1`
- `blocker.execution_plan_output_v1`
- `blocker.fill_simulation_v1`
- `blocker.order_book_input_v1`
- `blocker.own_order_state_v1`
- `blocker.rl_environment_v1`

### Policy

These rows may become:

- `implemented + research_ready`
- or remain `blocked_framework`

But they must not be presented as fully production-ready unless the operational requirements are actually met.

---

## Implementation batch template

Every batch should be described using the same structure.

### Batch definition fields

- batch key
- phase
- family
- rows included
- shared primitives required
- framework blockers required
- target modules
- fixture ids required
- performance budget ids
- tests to add
- completion criteria
- readiness target (`research_ready` or `production_candidate`)

### Example

```yaml
batch: trend_wave_1
phase: phase_2_trend
family: trend
rows:
  - algorithm:1
  - algorithm:2
  - algorithm:3
  - algorithm:4
  - algorithm:5
shared_primitives:
  - indicators.moving_averages
  - transforms.crossover_detection
  - statistics.spread_thresholds
framework_blockers: []
fixture_ids:
  - fixture.trend_monotonic_cross_v1
  - fixture.trend_whipsaw_guard_v1
performance_budget_ids:
  - perf.single_asset_bar_v1
completion_criteria:
  - all rows registered
  - behavior fixtures pass
  - docs/report payload present
  - tracker regenerated
  - performance smoke passes
readiness_target: research_ready
```

---

## Required engineering workflow per batch

For each implementation batch, use this sequence:

1. confirm target batch from manifest
2. confirm unresolved blockers
3. confirm required shared primitives
4. confirm fixture ids and performance budget ids
5. implement shared helpers first
6. implement algorithms or methods
7. register specs in family or composite catalog
8. add tests and fixture checks
9. regenerate tracker
10. run CI checks
11. promote statuses only when criteria are actually met

### Recommended delivery-status promotion path

- `not_started` -> `in_progress`
- `in_progress` -> `implemented`
- `implemented` -> `tested`
- `tested` -> `documented`
- `documented` -> `complete`

### Recommended operational-readiness promotion path

- `prototype_only` -> `research_ready`
- `research_ready` -> `production_candidate`
- `production_candidate` -> `production_ready`

These two paths should not be conflated.

---

## Minimal automation roadmap

### Step A — Create the manifest

Create a machine-readable manifest covering all rows in the current algorithm catalog and all combination-method rows.

### Step B — Create the blocker registry

Create an explicit blocker registry and attach blocker keys to affected rows.

### Step C — Create the fixture registry

Add at least one deterministic fixture for the earliest Tier-1 families and wire the schema into CI.

### Step D — Create the tracker generator

Generate a markdown progress report from:

- manifest
- blocker registry
- fixture registry
- registry state
- optional performance results

### Step E — Add consistency tests

Add tests that fail when:

- tracker metadata drifts from manifest
- manifest claims do not match registry state
- fixture ids are missing
- rows are marked production-ready without required evidence

### Step F — Start implementation from the first practical batch

Begin with:

- `trend_wave_1`
- `composite_contract_wave_1`
- `momentum_wave_1`
- `mean_reversion_wave_1`

This validates the foundation early and keeps the output contract honest.

---

## Recommended first practical ACT-mode sequence

If implementation starts immediately after this plan, the best early order is:

1. create manifest metadata and row inventory
2. create blocker registry
3. create fixture registry
4. create tracker generation script
5. add consistency tests
6. add shared indicator/transforms packages
7. implement `trend_wave_1`
8. implement `composite_contract_wave_1`
9. implement `momentum_wave_1`
10. implement `mean_reversion_wave_1`
11. regenerate tracker after each batch
12. only promote rows to `research_ready` or higher once fixture and reporting criteria pass

This gives quick visible progress while also validating the architecture.

---

## Explicit non-goals for early waves

Early waves should **not** pretend to provide full-library readiness.

They should not claim full support for:

- order-book-driven strategies
- options-surface-driven strategies
- execution plans with realistic fill simulation
- advanced institutional relative-value engines
- RL production controllers

Those should remain visible as planned or blocked until the required framework exists.

---

## Summary

The systematic way to implement the full library is:

1. make the manifest the single source of truth
2. classify all rows by tier, capability, and blocker state
3. track blockers as first-class work items
4. generate the tracker automatically
5. validate strategy behavior with golden fixtures
6. add performance budgets as real acceptance criteria
7. implement family-by-family in small batches
8. move a small composite wave earlier to validate the signal contract
9. separate `complete` from `research_ready` and `production_ready`
10. let CI verify that tracker, manifest, fixtures, tests, and code stay aligned

This turns a very large algorithm-library objective into a controlled delivery program with visible progress, low ambiguity, honest blockers, and much less tracker drift.
