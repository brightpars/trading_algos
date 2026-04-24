from trading_algos.algorithmspec import AlertAlgorithmSpec, register_algorithm
from trading_algos.alertgen.algorithms.fixed_income_relative_value.fixed_income_arbitrage import (
    build_fixed_income_arbitrage_algorithm,
)
from trading_algos.alertgen.algorithms.fixed_income_relative_value.swap_spread_arbitrage import (
    build_swap_spread_arbitrage_algorithm,
)
from trading_algos.alertgen.core.validation import require_curve_relative_value_param


def _curve_param_schema() -> tuple[dict[str, object], ...]:
    return (
        {
            "key": "rows",
            "label": "Rows",
            "type": "object_list",
            "required": True,
            "description": "Curve or related market rows with ts, symbol, close, and optional carry fields.",
        },
        {
            "key": "base_symbol",
            "label": "Base symbol",
            "type": "string",
            "required": True,
            "description": "Primary asset or leg symbol.",
        },
        {
            "key": "quote_symbol",
            "label": "Quote symbol",
            "type": "string",
            "required": True,
            "description": "Hedge asset or comparison leg symbol.",
        },
        {
            "key": "lookback_window",
            "label": "Lookback window",
            "type": "integer",
            "required": True,
            "minimum": 2,
            "description": "Rolling window used to estimate spread state.",
        },
        {
            "key": "entry_zscore",
            "label": "Entry z-score",
            "type": "number",
            "required": True,
            "minimum": 0.0,
            "description": "Absolute z-score required to open the spread.",
        },
        {
            "key": "exit_zscore",
            "label": "Exit z-score",
            "type": "number",
            "required": True,
            "minimum": 0.0,
            "description": "Absolute z-score threshold used to close the spread.",
        },
        {
            "key": "rebalance_frequency",
            "label": "Rebalance frequency",
            "type": "string",
            "required": True,
            "enum": ["monthly", "weekly", "all"],
            "description": "Schedule used to sample evaluation timestamps.",
        },
        {
            "key": "hedge_ratio_method",
            "label": "Hedge ratio method",
            "type": "string",
            "required": False,
            "enum": ["ratio", "ols"],
            "description": "Method used to estimate hedge ratio.",
        },
        {
            "key": "carry_field",
            "label": "Carry field",
            "type": "string",
            "required": False,
            "description": "Optional extra field used to carry-adjust the spread.",
        },
        {
            "key": "carry_weight",
            "label": "Carry weight",
            "type": "number",
            "required": False,
            "minimum": 0.0,
            "description": "Weight applied to carry differential before spread scoring.",
        },
        {
            "key": "minimum_history",
            "label": "Minimum history",
            "type": "integer",
            "required": False,
            "minimum": 1,
            "description": "Minimum aligned observations before the strategy becomes actionable.",
        },
    )


def register_fixed_income_relative_value_alert_algorithms() -> None:
    specs = [
        AlertAlgorithmSpec(
            key="fixed_income_arbitrage",
            name="Fixed-Income Arbitrage",
            catalog_ref="algorithm:115",
            builder=lambda **kwargs: build_fixed_income_arbitrage_algorithm(
                algorithm_key="fixed_income_arbitrage", **kwargs
            ),
            default_param={
                "rows": [],
                "base_symbol": "BOND_A",
                "quote_symbol": "BOND_B",
                "lookback_window": 3,
                "entry_zscore": 1.0,
                "exit_zscore": 0.25,
                "rebalance_frequency": "all",
                "hedge_ratio_method": "ratio",
                "carry_field": "carry",
                "carry_weight": 1.0,
                "minimum_history": 3,
            },
            param_normalizer=require_curve_relative_value_param,
            description="Trade related fixed-income instruments when yield/spread distortions become extreme.",
            param_schema=_curve_param_schema(),
            tags=("fixed_income_relative_value", "multi_leg", "curve"),
            category="fixed_income_relative_value",
            family="fixed_income_relative_value",
            subcategory="fixed",
            warmup_period=3,
            input_domains=("multi_leg_curve_data", "multi_leg_market_data"),
            asset_scope="multi_leg",
            output_modes=("multi_leg_signal", "hedge_ratio", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="swap_spread_arbitrage",
            name="Swap Spread Arbitrage",
            catalog_ref="algorithm:116",
            builder=lambda **kwargs: build_swap_spread_arbitrage_algorithm(
                algorithm_key="swap_spread_arbitrage", **kwargs
            ),
            default_param={
                "rows": [],
                "base_symbol": "SWAP_10Y",
                "quote_symbol": "GOVT_10Y",
                "lookback_window": 3,
                "entry_zscore": 1.0,
                "exit_zscore": 0.25,
                "rebalance_frequency": "all",
                "hedge_ratio_method": "ratio",
                "carry_field": "carry",
                "carry_weight": 1.0,
                "minimum_history": 3,
            },
            param_normalizer=require_curve_relative_value_param,
            description="Trade swap spreads versus comparable sovereign curves when spread dislocations widen.",
            param_schema=_curve_param_schema(),
            tags=("fixed_income_relative_value", "multi_leg", "swap"),
            category="fixed_income_relative_value",
            family="fixed_income_relative_value",
            subcategory="swap",
            warmup_period=3,
            input_domains=("multi_leg_curve_data", "multi_leg_market_data"),
            asset_scope="multi_leg",
            output_modes=("multi_leg_signal", "hedge_ratio", "diagnostics"),
        ),
    ]
    for spec in specs:
        register_algorithm(spec)
