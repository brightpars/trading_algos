## PROMPT: trend_wave_1
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
- Implement this batch as far as honestly possible.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Reuse shared helpers and avoid duplicated logic.
- Keep outputs normalized and compatible with composition and reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and report payloads for this batch.
- Update manifest statuses only when the evidence supports it.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.
- Run relevant tests.
- Stop when done.

## PROMPT: composite_contract_wave_1
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
- Implement this batch as far as honestly possible.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Reuse shared helpers and avoid duplicated logic.
- Keep outputs normalized and compatible with composition and reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and report payloads for this batch.
- Update manifest statuses only when the evidence supports it.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.
- Run relevant tests.
- Stop when done.

## PROMPT: momentum_wave_1
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
- Implement this batch as far as honestly possible.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Reuse shared helpers and avoid duplicated logic.
- Keep outputs normalized and compatible with composition and reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and report payloads for this batch.
- Update manifest statuses only when the evidence supports it.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.
- Run relevant tests.
- Stop when done.

## PROMPT: mean_reversion_wave_1
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
- Implement this batch as far as honestly possible.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Reuse shared helpers and avoid duplicated logic.
- Keep outputs normalized and compatible with composition and reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and report payloads for this batch.
- Update manifest statuses only when the evidence supports it.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.
- Run relevant tests.
- Stop when done.

## PROMPT: trend_wave_2
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
- Implement this batch as far as honestly possible.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Reuse shared helpers and avoid duplicated logic.
- Keep outputs normalized and compatible with composition and reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and report payloads for this batch.
- Update manifest statuses only when the evidence supports it.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.
- Run relevant tests.
- Stop when done.

## PROMPT: trend_wave_3
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
- Implement this batch as far as honestly possible.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Reuse shared helpers and avoid duplicated logic.
- Keep outputs normalized and compatible with composition and reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and report payloads for this batch.
- Update manifest statuses only when the evidence supports it.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.
- Run relevant tests.
- Stop when done.

## PROMPT: momentum_wave_2
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
- Implement this batch as far as honestly possible.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Reuse shared helpers and avoid duplicated logic.
- Keep outputs normalized and compatible with composition and reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and report payloads for this batch.
- Update manifest statuses only when the evidence supports it.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.
- Run relevant tests.
- Stop when done.

## PROMPT: mean_reversion_wave_2
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
- Implement this batch as far as honestly possible.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Reuse shared helpers and avoid duplicated logic.
- Keep outputs normalized and compatible with composition and reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and report payloads for this batch.
- Update manifest statuses only when the evidence supports it.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.
- Run relevant tests.
- Stop when done.

## PROMPT: volatility_wave_1
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
- Implement this batch as far as honestly possible.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Reuse shared helpers and avoid duplicated logic.
- Keep outputs normalized and compatible with composition and reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and report payloads for this batch.
- Update manifest statuses only when the evidence supports it.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.
- Run relevant tests.
- Stop when done.

## PROMPT: pattern_wave_1
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
- Implement this batch as far as honestly possible.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Reuse shared helpers and avoid duplicated logic.
- Keep outputs normalized and compatible with composition and reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and report payloads for this batch.
- Update manifest statuses only when the evidence supports it.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.
- Run relevant tests.
- Stop when done.

## PROMPT: pattern_wave_2
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
- Implement this batch as far as honestly possible.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Reuse shared helpers and avoid duplicated logic.
- Keep outputs normalized and compatible with composition and reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and report payloads for this batch.
- Update manifest statuses only when the evidence supports it.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.
- Run relevant tests.
- Stop when done.

## PROMPT: mean_reversion_wave_3
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
- Implement this batch as far as honestly possible.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Reuse shared helpers and avoid duplicated logic.
- Keep outputs normalized and compatible with composition and reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and report payloads for this batch.
- Update manifest statuses only when the evidence supports it.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.
- Run relevant tests.
- Stop when done.

## PROMPT: momentum_wave_3
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

Relevant blockers or prerequisite framework slices:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

Relevant fixtures:
- fixture.momentum_cross_sectional_ranking_v1

Tasks:
- Implement this batch as far as honestly possible.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Reuse shared helpers and avoid duplicated logic.
- Keep outputs normalized and compatible with composition and reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and report payloads for this batch.
- Update manifest statuses only when the evidence supports it.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.
- Run relevant tests.
- Stop when done.

## PROMPT: factor_wave_1
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

Relevant blockers or prerequisite framework slices:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

Relevant fixtures:
- fixture.factor_monthly_rebalance_v1

Tasks:
- Implement this batch as far as honestly possible.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Reuse shared helpers and avoid duplicated logic.
- Keep outputs normalized and compatible with composition and reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and report payloads for this batch.
- Update manifest statuses only when the evidence supports it.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.
- Run relevant tests.
- Stop when done.

## PROMPT: factor_wave_2
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

Relevant blockers or prerequisite framework slices:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

Relevant fixtures:
- fixture.factor_monthly_rebalance_v1

Tasks:
- Implement this batch as far as honestly possible.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Reuse shared helpers and avoid duplicated logic.
- Keep outputs normalized and compatible with composition and reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and report payloads for this batch.
- Update manifest statuses only when the evidence supports it.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.
- Run relevant tests.
- Stop when done.

## PROMPT: factor_wave_3
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

Relevant blockers or prerequisite framework slices:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

Relevant fixtures:
- fixture.factor_monthly_rebalance_v1

Tasks:
- Implement this batch as far as honestly possible.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Reuse shared helpers and avoid duplicated logic.
- Keep outputs normalized and compatible with composition and reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and report payloads for this batch.
- Update manifest statuses only when the evidence supports it.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.
- Run relevant tests.
- Stop when done.

## PROMPT: cross_asset_wave_1
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

Relevant blockers or prerequisite framework slices:
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
- Implement this batch as far as honestly possible.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Reuse shared helpers and avoid duplicated logic.
- Keep outputs normalized and compatible with composition and reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and report payloads for this batch.
- Update manifest statuses only when the evidence supports it.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.
- Run relevant tests.
- Stop when done.

## PROMPT: composite_wave_2
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

Relevant blockers or prerequisite framework slices:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

Relevant fixtures:
- fixture.composite_rank_aggregation_v1
- fixture.composite_risk_budget_v1

Tasks:
- Implement this batch as far as honestly possible.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Reuse shared helpers and avoid duplicated logic.
- Keep outputs normalized and compatible with composition and reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and report payloads for this batch.
- Update manifest statuses only when the evidence supports it.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.
- Run relevant tests.
- Stop when done.

## PROMPT: composite_wave_3
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

Relevant blockers or prerequisite framework slices:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1
- blocker.regime_state_support_v1

Relevant fixtures:
- fixture.composite_risk_budget_v1
- fixture.composite_regime_switch_v1

Tasks:
- Implement this batch as far as honestly possible.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Reuse shared helpers and avoid duplicated logic.
- Keep outputs normalized and compatible with composition and reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and report payloads for this batch.
- Update manifest statuses only when the evidence supports it.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.
- Run relevant tests.
- Stop when done.

## PROMPT: advanced_model_wave_1
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

Relevant blockers or prerequisite framework slices:
- blocker.multi_asset_panel_v1
- blocker.rebalance_engine_v1
- blocker.portfolio_weight_output_v1

Relevant fixtures:
- fixture.factor_monthly_rebalance_v1

Tasks:
- Implement this batch as far as honestly possible.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Reuse shared helpers and avoid duplicated logic.
- Keep outputs normalized and compatible with composition and reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and report payloads for this batch.
- Update manifest statuses only when the evidence supports it.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.
- Run relevant tests.
- Stop when done.

## PROMPT: event_wave_1
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

Relevant blockers or prerequisite framework slices:
- blocker.event_calendar_v1
- blocker.event_window_execution_v1
- blocker.event_reporting_v1

Relevant fixtures:
- fixture.event_earnings_after_close_v1
- fixture.event_index_rebalance_window_v1

Tasks:
- Implement this batch as far as honestly possible.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Reuse shared helpers and avoid duplicated logic.
- Keep outputs normalized and compatible with composition and reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and report payloads for this batch.
- Update manifest statuses only when the evidence supports it.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.
- Run relevant tests.
- Stop when done.

## PROMPT: stat_arb_wave_1
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

Relevant blockers or prerequisite framework slices:
- blocker.spread_leg_output_v1
- blocker.hedge_ratio_helpers_v1
- blocker.multi_leg_reporting_v1

Relevant fixtures:
- fixture.statarb_pair_divergence_reversion_v1
- fixture.relative_value_curve_spread_v1

Tasks:
- Implement this batch as far as honestly possible.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Reuse shared helpers and avoid duplicated logic.
- Keep outputs normalized and compatible with composition and reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and report payloads for this batch.
- Update manifest statuses only when the evidence supports it.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.
- Run relevant tests.
- Stop when done.

## PROMPT: relative_value_wave_2
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

Relevant blockers or prerequisite framework slices:
- blocker.spread_leg_output_v1
- blocker.hedge_ratio_helpers_v1
- blocker.multi_leg_reporting_v1

Relevant fixtures:
- fixture.statarb_pair_divergence_reversion_v1
- fixture.relative_value_curve_spread_v1

Tasks:
- Implement this batch as far as honestly possible.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Reuse shared helpers and avoid duplicated logic.
- Keep outputs normalized and compatible with composition and reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and report payloads for this batch.
- Update manifest statuses only when the evidence supports it.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.
- Run relevant tests.
- Stop when done.

## PROMPT: volatility_wave_2
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

Relevant blockers or prerequisite framework slices:
- blocker.options_chain_v1
- blocker.greeks_v1

Relevant fixtures:
- fixture.options_iv_rv_gap_v1

Tasks:
- Implement this batch as far as honestly possible.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Reuse shared helpers and avoid duplicated logic.
- Keep outputs normalized and compatible with composition and reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and report payloads for this batch.
- Update manifest statuses only when the evidence supports it.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.
- Run relevant tests.
- Stop when done.

## PROMPT: composite_wave_4
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
- Implement this batch as far as honestly possible.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Reuse shared helpers and avoid duplicated logic.
- Keep outputs normalized and compatible with composition and reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and report payloads for this batch.
- Update manifest statuses only when the evidence supports it.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.
- Run relevant tests.
- Stop when done.

## PROMPT: composite_wave_5
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

Relevant blockers or prerequisite framework slices:
- blocker.rl_environment_v1

Relevant fixtures:
- fixture.composite_rl_policy_stub_v1

Tasks:
- Implement this batch as far as honestly possible.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Reuse shared helpers and avoid duplicated logic.
- Keep outputs normalized and compatible with composition and reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and report payloads for this batch.
- Update manifest statuses only when the evidence supports it.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.
- Run relevant tests.
- Stop when done.

## PROMPT: advanced_wave_blocked
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

Relevant blockers or prerequisite framework slices:
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
- Implement this batch as far as honestly possible.
- Follow the manifest for target modules, target catalogs, capability fields, fixture ids, and performance budget ids.
- Reuse shared helpers and avoid duplicated logic.
- Keep outputs normalized and compatible with composition and reporting.
- Add or update parameter schemas, registry entries, diagnostics, fixtures, tests, and report payloads for this batch.
- Do not fake-complete framework-heavy rows; add only the reusable framework slices, contracts, stubs, tests, and blocker updates that are justified.
- Leave rows as `blocked_framework` or `prototype_only` when that is the correct state.
- Update manifest statuses only when the evidence supports it.
- Regenerate the tracker with `python scripts/build_algorithm_library_tracker.py`.
- Do not start any other batch.
- Run relevant tests.
- Stop when done.
