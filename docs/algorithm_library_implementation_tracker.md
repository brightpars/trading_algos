# Algorithm Library Implementation Tracker

## Source metadata

- Requirements document path: `docs/algorithm_library_requirements_v4.md`
- Requirements document version: `4`
- Implementation plan path: `docs/algorithm_library_systematic_implementation_plan_v2.md`
- Total algorithm rows: **121**
- Total combination-method rows: **12**
- Total tracked rows: **133**

## Overall status summary

| metric | count |
| --- | --- |
| algorithm rows | 121 |
| combination-method rows | 12 |
| ready_to_implement | 4 |
| blocked_framework | 66 |
| in_progress | 0 |
| complete | 63 |
| prototype_only | 70 |
| research_ready | 63 |
| production_ready | 0 |
| tier1 rows | 45 |
| tier2 rows | 53 |
| tier3 rows | 35 |

## Family summary

| family | kind_mix | total | ready | blocked | in_progress | complete |
| --- | --- | --- | --- | --- | --- | --- |
| adaptive_state_based | combination_method | 1 | 0 | 1 | 0 | 0 |
| cross_asset_macro_carry | algorithm | 8 | 0 | 8 | 0 | 0 |
| event_driven | algorithm | 5 | 0 | 5 | 0 | 0 |
| execution | algorithm | 6 | 0 | 6 | 0 | 0 |
| factor_risk_premia | algorithm | 15 | 0 | 4 | 0 | 11 |
| fixed_income_relative_value | algorithm | 2 | 0 | 2 | 0 | 0 |
| fundamental_ml_composite | algorithm | 8 | 0 | 6 | 0 | 2 |
| machine_learning_ensemble | combination_method | 3 | 3 | 0 | 0 | 0 |
| mean_reversion | algorithm | 12 | 0 | 0 | 0 | 12 |
| microstructure_hft | algorithm | 8 | 0 | 8 | 0 | 0 |
| momentum | algorithm | 11 | 0 | 0 | 0 | 11 |
| optimization_based | combination_method | 1 | 0 | 1 | 0 | 0 |
| pattern_price_action | algorithm | 8 | 0 | 0 | 0 | 8 |
| reinforcement_learning | combination_method | 2 | 0 | 2 | 0 | 0 |
| risk_overlay | combination_method | 2 | 1 | 1 | 0 | 0 |
| rule_based_combination | combination_method | 3 | 0 | 1 | 0 | 2 |
| stat_arb | algorithm | 14 | 0 | 14 | 0 | 0 |
| trend | algorithm | 14 | 0 | 0 | 0 | 14 |
| volatility_options | algorithm | 10 | 0 | 7 | 0 | 3 |

## Framework blockers summary

| blocker_key | status | affected_rows | affected_families |
| --- | --- | --- | --- |
| blocker.multi_asset_panel_v1 | planned | 38 | cross_asset_macro_carry, factor_risk_premia, fundamental_ml_composite, momentum, optimization_based |
| blocker.rebalance_engine_v1 | planned | 38 | cross_asset_macro_carry, factor_risk_premia, fundamental_ml_composite, momentum, optimization_based |
| blocker.portfolio_weight_output_v1 | planned | 29 | factor_risk_premia, fundamental_ml_composite, momentum, optimization_based, risk_overlay |
| blocker.event_calendar_v1 | planned | 6 | cross_asset_macro_carry, event_driven |
| blocker.event_window_execution_v1 | planned | 6 | cross_asset_macro_carry, event_driven |
| blocker.event_reporting_v1 | planned | 6 | cross_asset_macro_carry, event_driven |
| blocker.spread_leg_output_v1 | planned | 19 | cross_asset_macro_carry, fixed_income_relative_value, stat_arb |
| blocker.hedge_ratio_helpers_v1 | planned | 16 | fixed_income_relative_value, stat_arb |
| blocker.multi_leg_reporting_v1 | planned | 19 | cross_asset_macro_carry, fixed_income_relative_value, stat_arb |
| blocker.options_chain_v1 | planned | 7 | volatility_options |
| blocker.greeks_v1 | planned | 7 | volatility_options |
| blocker.execution_plan_output_v1 | planned | 6 | execution |
| blocker.fill_simulation_v1 | planned | 6 | execution |
| blocker.order_book_input_v1 | planned | 8 | microstructure_hft |
| blocker.own_order_state_v1 | planned | 8 | microstructure_hft |
| blocker.rl_environment_v1 | planned | 2 | reinforcement_learning |
| blocker.regime_state_support_v1 | planned | 1 | adaptive_state_based |

## Next-ready batches

| batch | ready_rows |
| --- | --- |
| composite_wave_4 | 3 |
| composite_wave_2 | 1 |

## Fixture coverage

| metric | count |
| --- | --- |
| rows with fixture ids | 133 |
| rows without fixture ids | 0 |
| fixtures in registry | 28 |
| performance budgets | 9 |
