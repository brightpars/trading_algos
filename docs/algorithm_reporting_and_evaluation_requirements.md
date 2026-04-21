# Algorithm Reporting and Evaluation Requirements

## Purpose

This document defines the reporting and evaluation requirements for the trading algorithm library and experiment system.

The goal is to ensure that:

- every algorithm produces reports in a consistent structure
- every experiment can render rich charts and useful analysis
- results are comparable across algorithms and configurations
- reporting logic is separated from algorithm logic
- evaluation supports both current alert-style algorithms and future advanced algorithm families

This document is intended to be the implementation reference before bulk algorithm development begins.

---

## Scope

This requirements set applies to:

- single-algorithm experiments
- configuration/composite experiments
- dashboard experiment detail pages
- persisted experiment results and reports
- alert-style signal algorithms
- future ranking, stat-arb, execution, options, and ML algorithms

This document covers:

- common report payload structure
- required and optional chart types
- evaluation layers and common metrics
- persisted result schema expectations
- dashboard rendering expectations
- rollout phases for implementation

This document does **not** define the detailed math of individual algorithms. It defines how outputs, reports, and evaluation should work once algorithms exist.

---

## Design Principles

### 1. Separate algorithm execution from reporting

Algorithms should expose normalized output and reportable derived data.

Algorithms should **not** be responsible for inventing their own report layout. A shared reporting pipeline should build the final report from standardized inputs.

### 2. Use one common report contract

Every experiment result must conform to the same top-level report structure, even if some sections are empty or optional.

This enables:

- consistent dashboard pages
- easier comparisons
- simpler persistence
- simpler testing

### 3. Require a standard baseline chart set

Every signal algorithm should produce the same required baseline charts. Algorithms may add extra charts, but they must not skip the common baseline unless the chart is genuinely inapplicable.

### 4. Use layered evaluation

There is no single metric system that fits all algorithm families.

Evaluation must be organized into layers:

- signal quality
- trading/backtest performance
- robustness
- family-specific diagnostics

### 5. Preserve comparability while allowing specialization

All algorithms must produce a common summary layer, while advanced families may add specialized metrics and diagnostics.

### 6. Reports must be useful both visually and analytically

Reports must include:

- charts
- summary metrics
- tables
- generated analysis text

Charts alone are not enough.

### 7. Result persistence must be report-aware

Stored experiment results must contain structured report content, not only raw rows and ad hoc metrics.

---

## High-Level Target Architecture

The reporting and evaluation stack should be split into clear layers.

### Algorithm layer

Responsible for:

- normalized output points
- derived indicator series
- event markers
- algorithm-specific diagnostics data

Not responsible for:

- final report page composition
- dashboard-specific rendering structure
- persistence format decisions

### Evaluation layer

Responsible for:

- evaluating algorithm outputs against common frameworks
- computing summary metrics
- computing trade metrics
- computing robustness metrics

### Reporting layer

Responsible for:

- building standardized charts
- assembling report sections
- generating summary tables
- generating narrative analysis blocks

### Persistence layer

Responsible for:

- storing report-ready result objects
- versioning report schema
- ensuring compatibility for dashboard rendering

### Dashboard layer

Responsible for:

- rendering report sections consistently
- rendering standard summary cards and charts
- rendering algorithm-specific optional sections

---

## Common Report Contract

Every experiment result should eventually produce a standardized report object.

## Top-level structure

Suggested top-level report object:

```json
{
  "report_version": "1.0",
  "experiment_summary": {},
  "algorithm_summary": {},
  "evaluation_summary": {},
  "charts": [],
  "tables": [],
  "analysis_blocks": [],
  "artifacts": {},
  "diagnostics": {}
}
```

## Required top-level fields

### `report_version`

Required.

Purpose:

- identify the report schema version
- support future format evolution

### `experiment_summary`

Required.

Must include:

- experiment id
- experiment type
- created/started/finished timestamps
- symbol or input scope
- data source metadata
- candle count or input row count
- repository revision if available
- report generation timestamp

### `algorithm_summary`

Required.

Must include:

- algorithm key
- algorithm name
- family
- subcategory
- algorithm version
- parameter values used
- runtime kind
- asset scope
- input domains
- output modes
- warmup period

For configuration/composite runs, this section must also include:

- configuration key/name/version
- root node id
- child algorithm references

### `evaluation_summary`

Required.

Must include:

- which evaluators were applied
- headline metrics
- metric groups
- notes about unavailable metrics

### `charts`

Required, even if empty in early phases.

Must contain a list of standardized chart objects.

### `tables`

Required, even if empty in early phases.

Must contain structured tables for metrics, parameters, and summaries.

### `analysis_blocks`

Required, even if empty in early phases.

Must contain short narrative sections summarizing performance and behavior.

### `artifacts`

Optional but strongly recommended.

May include:

- normalized output points
- trade list
- raw derived series
- event markers
- exportable machine-readable payloads

### `diagnostics`

Optional.

May include:

- evaluator warnings
- warmup notes
- unsupported metric notes
- missing-data notes
- algorithm-specific diagnostics payloads

---

## Standard Chart Contract

Each chart entry should use a common structure.

Suggested chart shape:

```json
{
  "chart_id": "price_signals",
  "title": "Price and Signals",
  "category": "overview",
  "chart_type": "timeseries",
  "required": true,
  "series": [],
  "x_axis": {"label": "Time"},
  "y_axis": {"label": "Price"},
  "description": "Shows price with buy/sell markers.",
  "tags": ["baseline", "signals"]
}
```

## Required chart fields

- `chart_id`
- `title`
- `category`
- `chart_type`
- `series`
- `description`

## Supported initial chart categories

- `overview`
- `signals`
- `indicators`
- `evaluation`
- `performance`
- `diagnostics`
- `comparison`

## Supported initial chart types

- `timeseries`
- `scatter`
- `histogram`
- `bar`
- `heatmap`
- `table_visual`

---

## Required Charts for Signal Algorithms

Every alert-style signal algorithm must support the following baseline charts.

### 1. Price and signal overview

Required.

Must show:

- price series
- buy markers
- sell markers
- optional neutral markers if useful

Purpose:

- first-look understanding of algorithm behavior

### 2. Core indicator chart(s)

Required.

Must show the primary algorithm-specific derived series, for example:

- moving averages
- channels
- RSI values
- Bollinger bands
- MACD and signal line

Purpose:

- explain why signals happened

### 3. Confidence or score chart

Required if the algorithm produces confidence or score.

Must show:

- confidence series
- optional thresholds

Purpose:

- understand signal strength and uncertainty

### 4. Ground-truth / regime comparison chart

Required when classification-based evaluation is used.

Must show:

- predicted signal or trend labels
- comparison target such as ground-truth trend or regime label

Purpose:

- visualize agreement and disagreement

### 5. Equity curve chart

Required once basic backtest/trade evaluation exists.

Must show:

- cumulative strategy return under shared trade assumptions
- optional benchmark line if available

Purpose:

- judge whether correct-looking signals actually perform

### 6. Drawdown chart

Required once backtest evaluation exists.

Must show:

- rolling drawdown or cumulative drawdown

Purpose:

- visualize risk and bad periods

---

## Optional Charts

Algorithms may add optional charts when useful.

Examples:

- trade return histogram
- rolling win rate
- per-trade pnl scatter
- rolling precision
- parameter sensitivity heatmap
- regime segmentation chart
- signal frequency over time
- spread/z-score charts for stat-arb
- benchmark slippage chart for execution algorithms

Optional charts must still conform to the common chart contract.

---

## Standard Tables and Summary Blocks

Reports must include structured tables, not only charts.

## Required tables

### 1. Parameter table

Must include:

- parameter name
- value used
- default value if useful
- description if available

### 2. Algorithm metadata table

Must include:

- algorithm key
- family
- version
- asset scope
- runtime kind
- warmup period

### 3. Signal summary table

Must include where applicable:

- total buy signals
- total sell signals
- neutral count
- signal density
- average confidence

### 4. Evaluation metrics table

Must include the common evaluation results grouped by layer.

### 5. Trade summary table

Must include once trade evaluation exists:

- trade count
- win rate
- average trade return
- average holding period if available
- cumulative return
- max drawdown

## Summary cards

Dashboard reports should also expose headline values suitable for summary cards.

Examples:

- total signals
- buy precision
- sell precision
- cumulative return
- max drawdown
- win rate
- profit factor

---

## Narrative Analysis Requirements

Every report should include machine-generated narrative analysis blocks.

These should be concise, structured, and deterministic from metrics where possible.

## Required analysis blocks

### 1. Overall behavior summary

Should summarize:

- whether the strategy was active or sparse
- whether it behaved more like trend following or reversal
- whether it concentrated signals in specific periods

### 2. Performance summary

Should summarize:

- whether performance was strong, weak, or mixed
- whether returns were smooth or unstable
- whether drawdown was acceptable or severe

### 3. Signal quality summary

Should summarize:

- precision behavior
- false reversal behavior
- overtrading or undertrading signs

### 4. Risk summary

Should summarize:

- drawdown behavior
- concentration risk
- dependency on few trades or few periods if detectable

### 5. Limitations / caveats

Should note:

- missing metrics
- too few trades
- insufficient history
- unsupported evaluator for this family

---

## Reportable Algorithm Output Requirements

All algorithms should expose a standard reportable output model to the reporting layer.

## Required output elements

### 1. Normalized output points

Each point should include at minimum:

- timestamp
- output label or state
- optional score
- optional confidence
- optional reason codes
- optional event markers

### 2. Derived series

Algorithms must be able to expose named derived series used for charts.

Examples:

- `close`
- `sma_fast`
- `sma_slow`
- `rsi`
- `upper_band`
- `lower_band`
- `zscore`

### 3. Metadata for reporting

Algorithms must expose enough metadata for report builders to label charts and tables correctly.

### 4. Diagnostics payloads

Algorithms may expose optional diagnostics payloads such as:

- detected events
- state-machine transitions
- filter gate decisions
- child algorithm contributions

---

## Layered Evaluation Framework

Evaluation must be implemented as layered evaluators.

## Layer A: Signal quality evaluation

This layer evaluates signal correctness or classification quality.

Applicable to:

- alert-style algorithms
- regime-label algorithms
- filter/gate algorithms where labels make sense

### Initial metrics

- buy signal count
- sell signal count
- neutral count
- correct buy count
- correct sell count
- absolute wrong count
- correct prediction count
- buy precision
- sell precision
- activity ratio

### Notes

The current slope-based future-trend ground-truth method may remain here as an initial evaluator.

It must be treated as:

- one heuristic evaluator
- not the universal truth framework

## Layer B: Trading and backtest evaluation

This layer evaluates tradability and economic usefulness.

Applicable to:

- most signal algorithms
- configuration/composite strategies

### Initial required metrics

- trade count
- win rate
- loss rate
- average return per trade
- median return per trade
- cumulative return
- max drawdown
- average holding duration if available
- exposure ratio
- turnover estimate if available

### Derived metrics to support soon after

- profit factor
- recovery factor
- return volatility
- Sharpe-like ratio
- downside-volatility ratio

### Important requirement

Backtest assumptions must be shared and explicit.

The framework must define a common baseline assumption set for early implementation, for example:

- entry on next bar open after signal
- exit on opposite signal or neutral rule
- no slippage initially, then optional slippage layer later
- configurable fees/transaction costs later

This is necessary for fair comparison across algorithms.

## Layer C: Robustness evaluation

This layer evaluates stability and sensitivity.

Applicable to:

- all tradable strategies

### Required later-phase metrics

- rolling-window performance
- best/worst subperiod performance
- parameter sensitivity summary
- outlier dependence summary
- performance by volatility regime
- performance by trend/range regime

## Layer D: Specialized-family evaluation

This layer covers advanced families that need custom evaluators.

Examples:

### Ranking / cross-sectional algorithms

- rank correlation
- top-bucket vs bottom-bucket spread
- hit rate by rank bucket

### Statistical arbitrage

- spread convergence success rate
- time-to-mean-reversion
- hedge stability metrics

### Execution algorithms

- VWAP deviation
- implementation shortfall
- fill rate
- slippage versus benchmark

### ML algorithms

- calibration quality
- ROC/AUC where applicable
- precision/recall by threshold
- probability distribution diagnostics

---

## Evaluation Output Contract

Each evaluator should produce structured output with:

- evaluator id
- evaluator version
- metric group name
- metrics dictionary
- notes/warnings
- applicability status

Suggested shape:

```json
{
  "evaluator_id": "signal_quality_v1",
  "applies": true,
  "metric_group": "signal_quality",
  "metrics": {},
  "warnings": []
}
```

This allows multiple evaluators to be composed into one report.

---

## Experiment Result Persistence Requirements

The result repository should eventually store structured report-ready objects.

## Required persisted sections

- experiment metadata
- algorithm/config metadata
- normalized outputs
- evaluator outputs
- report sections
- chart payloads
- summary cards
- narrative analysis blocks
- schema version information

## Persistence principles

### 1. Persist structured data, not just rendered HTML

The dashboard should render from structured payloads.

### 2. Persist enough data for comparisons

Comparison pages should be able to compare:

- metrics
- signal behavior
- equity curves
- drawdowns

### 3. Persist schema version fields

All persisted report/evaluation payloads must be versioned.

---

## Dashboard Rendering Requirements

The dashboard experiment detail and report views should render a consistent layout.

## Required experiment report sections

### 1. Summary area

Must show:

- experiment status
- symbol/input scope
- algorithm/config name
- time range
- headline metrics

### 2. Standard charts area

Must show the required baseline charts in a predictable order.

### 3. Metrics area

Must show:

- evaluation tables
- grouped metrics by layer

### 4. Analysis area

Must show:

- narrative performance notes
- warnings and caveats

### 5. Diagnostics area

Optional but recommended.

Should show:

- evaluator warnings
- algorithm-specific diagnostic sections
- child strategy contributions for composite strategies

## Comparison requirements

The dashboard should later support side-by-side comparison using the same standardized sections.

---

## Family-Specific Reporting Extensions

The standard report schema must support future family-specific additions.

## Trend / momentum / mean reversion

Must support:

- price and signals
- indicator overlays
- trading performance charts

## Composite strategies

Must also support:

- child algorithm contribution breakdown
- child signal agreement/disagreement views

## Statistical arbitrage

Must also support:

- spread chart
- z-score chart
- hedge ratio chart if relevant

## Execution algorithms

Must also support:

- benchmark comparison chart
- execution schedule chart
- slippage and participation diagnostics

## ML algorithms

Must also support:

- probability/score chart
- threshold analysis
- calibration diagnostics

---

## Required Implementation Architecture

The following module structure is recommended.

## Reporting package

Suggested files:

- `src/trading_algos/reporting/__init__.py`
- `src/trading_algos/reporting/models.py`
- `src/trading_algos/reporting/charts.py`
- `src/trading_algos/reporting/tables.py`
- `src/trading_algos/reporting/analysis.py`
- `src/trading_algos/reporting/builders.py`
- `src/trading_algos/reporting/persistence.py`

Responsibilities:

- report models
- chart models
- summary block models
- narrative analysis builders
- report assembly
- persistence helpers

## Evaluation package

Suggested files:

- `src/trading_algos/evaluation/__init__.py`
- `src/trading_algos/evaluation/models.py`
- `src/trading_algos/evaluation/signal_quality.py`
- `src/trading_algos/evaluation/backtest.py`
- `src/trading_algos/evaluation/robustness.py`
- `src/trading_algos/evaluation/family_specific.py`
- `src/trading_algos/evaluation/pipeline.py`

Responsibilities:

- common evaluation contracts
- metric group outputs
- layered evaluator execution

## Dashboard integration targets

Likely touched later:

- `src/trading_algos_dashboard/services/report_service.py`
- `src/trading_algos_dashboard/services/experiment_service.py`
- `src/trading_algos_dashboard/templates/experiments/detail.html`
- `src/trading_algos_dashboard/templates/reports/detail.html`
- chart rendering JS where needed

---

## Readiness Requirements Before Bulk Algorithm Implementation

The following must be implemented before mass algorithm onboarding begins.

### Requirement R1: Standard report schema

Must be implemented first.

Minimum deliverables:

- report models
- chart models
- table models
- summary block models

### Requirement R2: Shared report builder

Must assemble consistent reports from normalized algorithm output.

### Requirement R3: Shared evaluation framework

Must include:

- current signal evaluator as one module
- first-pass backtest evaluator
- grouped metric outputs

### Requirement R4: Shared persistence model for results

Must define what gets stored in the result repository and how it is versioned.

### Requirement R5: Dashboard rendering support

Must support standardized report sections before many algorithms are added.

---

## Rollout Phases

## Phase R1: Reporting foundation

Implement:

- report models
- chart schema
- summary card schema
- baseline report builder

Outcome:

- every algorithm can plug into one report shape

## Phase R2: Evaluation foundation

Implement:

- signal-quality evaluator
- simple trade/backtest evaluator
- grouped evaluation summary output

Outcome:

- reports become comparable in a useful way

## Phase R3: Dashboard integration

Implement:

- experiment detail rendering from report objects
- summary cards
- standard chart sections
- analysis sections

Outcome:

- experiments become readable and consistent in the UI

## Phase R4: Advanced family support

Implement:

- stat-arb extensions
- ranking extensions
- execution extensions
- ML extensions

Outcome:

- advanced families fit without breaking the common model

---

## Acceptance Criteria

This reporting/evaluation readiness effort is considered complete when:

1. every signal algorithm can produce a standard report object
2. experiment detail pages can render a common summary + charts + tables + analysis layout
3. evaluation includes both signal quality and basic trading performance
4. persisted results are versioned and report-aware
5. algorithm-specific extra charts can be added without changing the common dashboard structure
6. at least one trend algorithm, one mean-reversion algorithm, and one composite algorithm can all render through the same reporting pipeline

---

## Final Recommendation

Do **not** begin large-scale algorithm implementation until Phase R1 and Phase R2 are completed.

The repo is now structurally improved for algorithm registration and organization, but reporting and evaluation are still the most important readiness gap.

The next implementation effort should focus on:

1. common report models
2. common evaluation models
3. report/evaluation builders
4. dashboard experiment report rendering

After that, Wave 1 algorithm implementation can proceed with much lower risk of inconsistent results and weak experiment reporting.