# Algorithm Library Remaining Readiness Requirements

## Purpose

This document defines the **remaining repository requirements** that must be implemented before the repo can be considered fully ready for the **entire enriched algorithm library** described in `docs/algorithm_library_requirements_enriched.md`.

The repo is already partially prepared for a first implementation wave of single-asset OHLCV-based signal algorithms. However, the enriched library covers many additional algorithm families that require infrastructure beyond the current alert-style architecture.

This document exists to answer one practical question:

> What still has to be built before this repository is truly ready to implement the whole enriched algorithm set in a clean, scalable, and consistent way?

It should be read together with:

- `docs/algorithm_library_requirements_enriched.md`
- `docs/algorithm_reporting_and_evaluation_requirements.md`
- `docs/algorithm_authoring_guide.md`

---

## Current Readiness Summary

## What the repo is already reasonably ready for

The current repo foundation is now in a decent state for:

- registry-driven algorithm discovery
- family-based algorithm organization
- basic normalized signal output
- single-asset OHLCV batch-series algorithms
- initial dashboard catalog integration
- first-wave trend, momentum, mean-reversion, and simple composite algorithms

This means the repo is already close to ready for:

- trend-following strategies based on OHLCV bars
- momentum oscillators and continuation strategies on a single asset
- single-asset mean-reversion strategies
- some pattern/price-action strategies
- some basic volatility breakout strategies

## What the repo is not fully ready for

The enriched library also includes families that the current architecture does **not yet support well**:

- multi-asset and universe strategies
- statistical arbitrage spread engines
- options and volatility-surface strategies
- microstructure / HFT / market-making strategies
- execution algorithms
- event/fundamental/ML-driven strategies
- fully standardized reporting and layered evaluation

So the repo is **Phase-1 ready**, but not yet **whole-library ready**.

---

## Readiness Goal

The repo will be considered fully ready for the whole enriched algorithm set only when it supports:

1. single-asset OHLCV algorithms
2. multi-asset and universe algorithms
3. spread/ranking/regime/execution output styles
4. options and order-book input domains
5. rich, standardized reporting and evaluation
6. dashboard rendering for diverse algorithm families
7. scalable testing and authoring workflows across all families

---

## Remaining Capability Gaps

## Gap 1: Shared indicators and statistics layer is still too thin

### Problem

The enriched library contains many algorithms that reuse the same primitives:

- moving averages
- RSI, stochastic, CCI, KST
- ATR, realized volatility, bands, channels
- regression, z-scores, spreads, hedge ratios
- ranking and normalization
- session-aware transforms

Today, some reusable pieces exist, but there is not yet a clear, first-class shared package architecture for indicators/statistics/transforms that is broad enough for the whole library.

### Why this matters

Without this layer, each new algorithm risks re-implementing the same calculations differently, which creates:

- inconsistent behavior
- inconsistent charts
- duplicated bugs
- slower implementation velocity

### Required implementation

Add explicit shared packages such as:

- `src/trading_algos/indicators/`
- `src/trading_algos/statistics/`
- `src/trading_algos/transforms/`

### Required contents

At minimum, these packages should support:

- moving averages (SMA, EMA, ribbon helpers)
- oscillators (RSI, stochastic, CCI, MACD, KST)
- volatility estimators (ATR, realized volatility)
- bands/channels (Donchian, Bollinger, ATR channel)
- rolling regression helpers
- z-score and normalization helpers
- spread and hedge ratio helpers
- session alignment and reset helpers
- return transforms and multi-horizon return helpers

### Families blocked until complete

- trend
- momentum
- mean reversion
- volatility breakout
- stat-arb
- pattern/price-action
- cross-asset and factor families

---

## Gap 2: Multi-asset input models do not exist yet

### Problem

The current runtime and contracts are still oriented mostly around:

- one symbol
- one candle stream
- one algorithm producing signal-like output

The enriched library includes many strategies that require:

- multiple aligned symbols
- spreads or baskets
- universe ranking
- benchmark/reference assets
- panel-like data structures

### Why this matters

These algorithms cannot be cleanly implemented using only a single list of candle dicts. They need explicit multi-asset input contracts.

### Required implementation

Add input/data-contract packages such as:

- `src/trading_algos/inputs/ohlcv.py`
- `src/trading_algos/inputs/panel.py`
- `src/trading_algos/inputs/pairs.py`
- `src/trading_algos/inputs/events.py`
- `src/trading_algos/inputs/options.py`
- `src/trading_algos/inputs/order_book.py`

### Minimum Phase-2 input models

Before full-library readiness, the repo must support at least:

- single-asset OHLCV series
- aligned multi-asset OHLCV panels
- pair/spread inputs
- benchmark/reference series binding
- universe membership binding

### Families blocked until complete

- cross-sectional momentum
- relative strength momentum
- dual momentum
- residual momentum
- pairs trading
- basket stat-arb
- intermarket confirmation
- carry and cross-asset strategies
- multi-factor ranking strategies

---

## Gap 3: Output contracts are still too signal-centric

### Problem

The current normalized output direction is good for alert algorithms, but the full enriched library requires more than `buy` / `sell` / `neutral`.

The library needs to support outputs such as:

- score
- confidence
- regime label
- ranking
- spread state
- leg instructions
- execution plan
- quote/action recommendations

### Why this matters

Many advanced families cannot be squeezed into a simple candle-level alert format without creating awkward, misleading abstractions.

### Required implementation

Expand the output contract to support multiple output types explicitly, for example:

- `signal_output`
- `score_output`
- `ranking_output`
- `spread_output`
- `execution_plan_output`
- `diagnostic_output`

### Required design rule

All outputs should still fit into a common envelope so reporting and persistence remain consistent.

### Families blocked until complete

- universe ranking algorithms
- stat-arb leg-construction algorithms
- execution algorithms
- market-making and queue-position strategies
- options structure-building strategies

---

## Gap 4: Configuration and runtime binding are too narrow

### Problem

The configuration graph model is a strong base, but it still assumes a relatively simple algorithm node shape built around:

- `alg_key`
- `alg_param`
- buy/sell enable flags

The enriched library requires nodes that can bind to:

- multiple data sources
- multiple assets
- benchmarks
- pair definitions
- reference indicators
- event calendars
- execution parameters

### Required implementation

Extend configuration node models to support:

- input binding keys
- reference inputs
- asset group definitions
- benchmark bindings
- output mode selection
- role selection (`signal`, `filter`, `regime`, `ranking`, `execution`)

### Required executor changes

The runtime executor must be able to:

- resolve bound inputs per node
- validate input-domain compatibility
- pass the right input contract into the algorithm
- support non-signal node outputs

### Families blocked until complete

- pairs and basket strategies
- dual momentum and benchmark-relative strategies
- intermarket strategies
- macro/carry/factor strategies
- execution algorithms
- event/fundamental strategies

---

## Gap 5: Reporting and evaluation are not implemented yet at the required level

### Problem

A detailed requirements document now exists for reporting and evaluation, but the implementation is not yet complete.

The enriched library requires:

- standard report schema
- standard charts
- tables and narrative analysis blocks
- layered evaluation
- backtest/trade evaluation
- family-specific diagnostics

### Why this matters

Without this, the repo may technically run algorithms, but experiment results will remain:

- inconsistent
- hard to compare
- too weak for a large algorithm library

### Required implementation

Implement the requirements in:

- `docs/algorithm_reporting_and_evaluation_requirements.md`

This includes:

- report models
- evaluation models
- chart and table schemas
- report builders
- evaluator pipeline
- dashboard rendering integration

### Families blocked until complete

- effectively all families if the goal is high-quality implementation at scale

This is the most important horizontal readiness gap.

---

## Gap 6: Multi-asset evaluation and ranking evaluation do not exist

### Problem

Single-asset signal-quality metrics are not enough for:

- ranking strategies
- spread strategies
- portfolio rotation strategies
- carry and cross-asset models

### Required implementation

Add evaluation modules for:

- ranking quality
- long-short spread quality
- portfolio return attribution
- rebalance-based strategies
- benchmark-relative performance

### Families blocked until complete

- cross-sectional momentum
- dual momentum
- residual momentum
- factor strategies
- carry and macro strategies
- statistical arbitrage families

---

## Gap 7: Options input, analytics, and reporting layers are missing

### Problem

The enriched library includes many volatility/options strategies that need:

- option chain data
- greeks
- term structure
- skew/surface analytics
- delta-neutral or structure-building outputs

None of these are currently implemented as first-class repo contracts.

### Required implementation

Add options-specific capabilities such as:

- option chain input model
- greek exposure model
- implied vs realized volatility model
- term structure model
- skew/surface analytics helpers
- option structure output or signal-expression contract

### Reporting requirements

Options reports must support:

- IV/RV charts
- skew charts
- term structure charts
- greek diagnostics
- long-vol/short-vol summary blocks

### Families blocked until complete

- delta-neutral volatility trading
- gamma scalping
- volatility risk premium capture
- dispersion trading
- skew trading
- term structure trading
- straddle breakout timing

---

## Gap 8: Order-book and event-driven runtime support is missing

### Problem

The enriched library includes microstructure and HFT families that cannot be implemented correctly in a bar-only batch-series runtime.

These algorithms need:

- event-driven inputs
- order-book snapshots and updates
- own-order state
- inventory state
- fills and queue-position state

### Required implementation

Add runtime and contract support for:

- top-of-book and level-2 input models
- event-driven processing
- inventory and quote state
- execution action outputs
- fill simulation or live hooks

### Reporting requirements

These strategies require specialized reports for:

- inventory evolution
- quote placement
- queue and fill behavior
- spread capture
- adverse selection diagnostics

### Families blocked until complete

- market making
- inventory-skewed market making
- order-book imbalance
- microprice
- queue position
- rebate capture
- auction strategies

---

## Gap 9: Execution algorithm contracts are missing

### Problem

Execution algorithms are not alpha signal generators in the usual sense. They require different inputs and outputs.

They need:

- parent order definitions
- benchmark definitions
- child-order schedules
- fills/slippage tracking
- execution-quality evaluation

### Required implementation

Add execution-specific contracts such as:

- parent order input model
- execution plan output model
- child-order event stream
- benchmark tracking model
- execution metrics and reports

### Families blocked until complete

- TWAP
- VWAP execution
- POV
- implementation shortfall
- iceberg
- sniper execution

---

## Gap 10: Event, fundamental, and ML data workflows are missing

### Problem

The enriched library includes families that require non-price datasets:

- earnings/event calendars
- merger terms
- valuation/fundamental metrics
- sentiment feeds
- feature matrices and labels for ML

### Required implementation

Add support for:

- event input models
- fundamental input models
- feature matrix contracts
- model artifact references
- offline fit/evaluate/predict workflow definitions

### Families blocked until complete

- merger arbitrage
- earnings drift / post-event momentum
- value strategy
- quality strategy
- multi-factor composite
- sentiment strategies
- ML classifier/regressor
- regime-switching models with richer features

---

## Gap 11: Strategy construction and position-expression layers are incomplete

### Problem

For many advanced strategies, the signal is only part of the problem.

The repo also needs to define how the signal is expressed as:

- long/short pair legs
- basket weights
- option structures
- hedged positions
- order schedules

### Required implementation

Add position-expression layers that can translate algorithm intent into structured outputs.

Examples:

- pair leg instructions
- basket weights
- volatility expression recommendation
- execution schedule recommendation

### Families blocked until complete

- pairs/stat-arb
- options strategies
- execution strategies
- multi-asset ranking strategies

---

## Gap 12: Testing infrastructure is not yet broad enough for the whole library

### Problem

The current test base is adequate for current alert algorithms, but not for the full enriched set.

The repo needs standardized fixtures and contract tests for multiple input domains.

### Required implementation

Expand tests to cover:

- indicator helpers
- statistics helpers
- single-asset OHLCV fixtures
- multi-asset panel fixtures
- pair/spread fixtures
- options fixtures
- order-book fixtures
- execution result fixtures
- evaluator contract tests
- report builder contract tests

### Required test categories

- algorithm registration contract tests
- input-domain validation tests
- report contract tests
- evaluator contract tests
- dashboard serialization tests

### Families blocked until complete

- all advanced families if quality and maintainability matter

---

## Gap-to-Family Mapping

## Families mostly ready now

These are closest to implementable once reporting/evaluation is built:

- trend following
- single-asset momentum
- single-asset mean reversion
- basic volatility breakout
- simple pattern/price-action
- simple composites

## Families blocked mainly by reporting/evaluation plus shared helpers

- all first-wave OHLCV families if you want consistent experiment quality

## Families blocked mainly by multi-asset inputs and ranking outputs

- cross-sectional momentum
- relative strength momentum
- dual momentum
- residual momentum
- pairs trading
- basket stat-arb
- intermarket confirmation
- carry and curve strategies
- multi-factor ranking strategies

## Families blocked mainly by options models

- volatility/options family

## Families blocked mainly by event-driven and order-book runtime

- microstructure / HFT / market making family

## Families blocked mainly by execution contracts

- execution algorithms family

## Families blocked mainly by event/fundamental/ML data workflows

- merger arbitrage
- earnings drift
- value / quality strategies
- sentiment strategies
- ML classifier/regressor
- advanced regime-switching

---

## Required Module Additions and Refactors

The following architecture additions are recommended before the repo is fully ready.

## Shared computation modules

- `src/trading_algos/indicators/`
- `src/trading_algos/statistics/`
- `src/trading_algos/transforms/`

## Input contracts

- `src/trading_algos/inputs/ohlcv.py`
- `src/trading_algos/inputs/panel.py`
- `src/trading_algos/inputs/pairs.py`
- `src/trading_algos/inputs/options.py`
- `src/trading_algos/inputs/order_book.py`
- `src/trading_algos/inputs/events.py`
- `src/trading_algos/inputs/fundamentals.py`

## Output contracts

- expanded output models for ranking, spread, execution, and diagnostics

## Reporting and evaluation

- `src/trading_algos/reporting/`
- `src/trading_algos/evaluation/`

## Runtime and execution

- `src/trading_algos/runtime/`
- event-driven support modules
- execution output and tracking modules

## Configuration model extensions

Refactor:

- `src/trading_algos/configuration/models.py`
- `src/trading_algos/configuration/validation.py`
- `src/trading_algos/configuration/executor.py`

## Dashboard integration

Likely future work in:

- `src/trading_algos_dashboard/services/report_service.py`
- `src/trading_algos_dashboard/services/experiment_service.py`
- experiment/report templates and chart JS

---

## Phased Remaining Readiness Plan

## Phase 1: Finish first-wave readiness

Implement before large-scale OHLCV algorithm onboarding:

1. shared indicators/statistics/transforms
2. reporting models and report builder
3. layered evaluation foundation
4. basic backtest/trade evaluation
5. dashboard-ready report rendering

### Outcome

Repo becomes truly ready for:

- trend
- momentum
- mean reversion
- basic volatility breakout
- basic pattern/price-action
- simple composites

## Phase 2: Multi-asset readiness

Implement:

1. panel and pair input models
2. ranking and spread outputs
3. configuration input bindings
4. multi-asset evaluation/reporting support

### Outcome

Repo becomes ready for:

- cross-sectional momentum
- dual momentum
- relative strength rotation
- pairs and basket stat-arb
- intermarket and macro families

## Phase 3: Options and event-data readiness

Implement:

1. options input contracts
2. greek and vol analytics
3. event/fundamental inputs
4. family-specific reporting extensions

### Outcome

Repo becomes ready for:

- volatility/options family
- event-driven/fundamental families

## Phase 4: Execution and market-microstructure readiness

Implement:

1. execution plan contracts
2. parent/child order models
3. order-book/event-driven runtime
4. market-making inventory/fill state
5. execution-specific evaluation and reports

### Outcome

Repo becomes ready for:

- execution algorithms
- microstructure / HFT / market-making families

## Phase 5: ML and advanced family support

Implement:

1. feature matrix and model interfaces
2. ML evaluation/calibration modules
3. advanced family-specific extensions

### Outcome

Repo becomes ready for:

- ML classifier/regressor families
- advanced regime-switching and ensemble workflows

---

## Acceptance Criteria for Full Readiness

The repo should be considered fully ready for the whole enriched algorithm set only when all of the following are true:

1. shared indicator/statistics libraries exist and cover the reusable math needed by the enriched list
2. the runtime supports both single-asset and multi-asset input contracts
3. the configuration system supports richer input binding and non-signal output modes
4. a common reporting system is implemented and used by experiments
5. a layered evaluation framework is implemented and supports both signal and trading metrics
6. multi-asset ranking/spread algorithms can run without awkward single-symbol hacks
7. options strategies can consume option-chain and greek-aware inputs
8. execution algorithms can emit execution-plan-style outputs
9. order-book/event-driven strategies have appropriate runtime and reporting support
10. event/fundamental/ML strategies have appropriate input and evaluation pipelines
11. test coverage exists for all supported input/output families

---

## Final Recommendation

Do **not** treat the repo as fully ready for the whole enriched library yet.

Treat it as:

- **ready soon for the first OHLCV wave** after reporting/evaluation and shared helper work
- **not yet ready for the entire enriched set** until the remaining readiness phases above are implemented

The recommended next implementation order is:

1. reporting/evaluation implementation
2. shared indicators/statistics/transforms
3. multi-asset and ranking/spread support
4. options and event-data support
5. execution and order-book runtime support
6. ML and advanced-family support

Once those phases are complete, the repository will be in a strong position to implement the whole enriched algorithm catalog without repeated architectural rework.