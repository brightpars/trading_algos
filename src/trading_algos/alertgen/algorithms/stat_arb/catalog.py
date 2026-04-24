from trading_algos.algorithmspec import AlertAlgorithmSpec, register_algorithm
from trading_algos.alertgen.algorithms.stat_arb.basket_statistical_arbitrage import (
    build_basket_statistical_arbitrage_algorithm,
)
from trading_algos.alertgen.algorithms.stat_arb.funding_basis_arbitrage import (
    build_funding_basis_arbitrage_algorithm,
)
from trading_algos.alertgen.algorithms.stat_arb.pairs_trading_cointegration import (
    build_pairs_trading_cointegration_algorithm,
)
from trading_algos.alertgen.algorithms.stat_arb.pairs_trading_distance_method import (
    build_pairs_trading_distance_method_algorithm,
)
from trading_algos.alertgen.core.validation import (
    require_funding_basis_arb_param,
    require_stat_arb_basket_param,
    require_stat_arb_pair_param,
)


def _pair_param_schema() -> tuple[dict[str, object], ...]:
    return (
        {
            "key": "rows",
            "label": "Rows",
            "type": "object_list",
            "required": True,
            "description": "Pair price rows with ts, symbol, and close.",
        },
        {
            "key": "base_symbol",
            "label": "Base symbol",
            "type": "string",
            "required": True,
            "description": "Primary leg symbol.",
        },
        {
            "key": "quote_symbol",
            "label": "Quote symbol",
            "type": "string",
            "required": True,
            "description": "Hedge leg symbol.",
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
            "key": "minimum_history",
            "label": "Minimum history",
            "type": "integer",
            "required": False,
            "minimum": 1,
            "description": "Minimum aligned observations before the strategy becomes actionable.",
        },
    )


def _basket_param_schema() -> tuple[dict[str, object], ...]:
    return (
        {
            "key": "rows",
            "label": "Rows",
            "type": "object_list",
            "required": True,
            "description": "Basket price rows with ts, symbol, and close.",
        },
        {
            "key": "base_symbol",
            "label": "Base symbol",
            "type": "string",
            "required": True,
            "description": "Asset traded against the basket.",
        },
        {
            "key": "basket_symbols",
            "label": "Basket symbols",
            "type": "string_list",
            "required": True,
            "description": "Basket members used as the hedge leg.",
        },
        {
            "key": "basket_weights",
            "label": "Basket weights",
            "type": "number_list",
            "required": False,
            "description": "Optional explicit basket weights.",
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
            "key": "minimum_history",
            "label": "Minimum history",
            "type": "integer",
            "required": False,
            "minimum": 1,
            "description": "Minimum aligned observations before the strategy becomes actionable.",
        },
    )


def _funding_param_schema() -> tuple[dict[str, object], ...]:
    return (
        *_pair_param_schema(),
        {
            "key": "basis_field",
            "label": "Basis field",
            "type": "string",
            "required": False,
            "description": "Extra field containing basis values on the quote leg.",
        },
        {
            "key": "funding_field",
            "label": "Funding field",
            "type": "string",
            "required": False,
            "description": "Extra field containing funding rate values on the quote leg.",
        },
        {
            "key": "carry_threshold",
            "label": "Carry threshold",
            "type": "number",
            "required": False,
            "minimum": 0.0,
            "description": "Minimum absolute carry distortion required before entry.",
        },
    )


def register_stat_arb_alert_algorithms() -> None:
    specs = [
        AlertAlgorithmSpec(
            key="pairs_trading_distance_method",
            name="Pairs Trading (Distance Method)",
            catalog_ref="algorithm:38",
            builder=lambda **kwargs: build_pairs_trading_distance_method_algorithm(
                algorithm_key="pairs_trading_distance_method", **kwargs
            ),
            default_param={
                "rows": [],
                "base_symbol": "AAA",
                "quote_symbol": "BBB",
                "lookback_window": 3,
                "entry_zscore": 1.0,
                "exit_zscore": 0.25,
                "rebalance_frequency": "all",
                "hedge_ratio_method": "ratio",
                "minimum_history": 3,
            },
            param_normalizer=require_stat_arb_pair_param,
            description="Trade pair spread deviations using a distance-style z-score trigger.",
            param_schema=_pair_param_schema(),
            tags=("stat_arb", "pairs", "distance", "multi_leg"),
            category="stat_arb",
            family="stat_arb",
            subcategory="pairs",
            warmup_period=3,
            input_domains=("pair_prices",),
            asset_scope="pair",
            output_modes=("multi_leg_signal", "hedge_ratio", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="pairs_trading_cointegration",
            name="Pairs Trading (Cointegration)",
            catalog_ref="algorithm:39",
            builder=lambda **kwargs: build_pairs_trading_cointegration_algorithm(
                algorithm_key="pairs_trading_cointegration", **kwargs
            ),
            default_param={
                "rows": [],
                "base_symbol": "AAA",
                "quote_symbol": "BBB",
                "lookback_window": 3,
                "entry_zscore": 1.0,
                "exit_zscore": 0.25,
                "rebalance_frequency": "all",
                "hedge_ratio_method": "ols",
                "minimum_history": 3,
            },
            param_normalizer=require_stat_arb_pair_param,
            description="Trade pair spread deviations using an OLS hedge-ratio proxy for cointegration.",
            param_schema=_pair_param_schema(),
            tags=("stat_arb", "pairs", "cointegration", "multi_leg"),
            category="stat_arb",
            family="stat_arb",
            subcategory="pairs",
            warmup_period=3,
            input_domains=("pair_prices",),
            asset_scope="pair",
            output_modes=("multi_leg_signal", "hedge_ratio", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="basket_statistical_arbitrage",
            name="Basket Statistical Arbitrage",
            catalog_ref="algorithm:40",
            builder=lambda **kwargs: build_basket_statistical_arbitrage_algorithm(
                algorithm_key="basket_statistical_arbitrage", **kwargs
            ),
            default_param={
                "rows": [],
                "base_symbol": "AAA",
                "basket_symbols": ["BBB", "CCC"],
                "basket_weights": [0.5, 0.5],
                "lookback_window": 3,
                "entry_zscore": 1.0,
                "exit_zscore": 0.25,
                "rebalance_frequency": "all",
                "minimum_history": 3,
            },
            param_normalizer=require_stat_arb_basket_param,
            description="Trade one asset against a related basket when the basket spread becomes extreme.",
            param_schema=_basket_param_schema(),
            tags=("stat_arb", "basket", "multi_leg"),
            category="stat_arb",
            family="stat_arb",
            subcategory="basket",
            warmup_period=3,
            input_domains=("basket_prices",),
            asset_scope="basket",
            output_modes=("multi_leg_signal", "hedge_ratio", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="funding_basis_arbitrage",
            name="Funding/Basis Arbitrage",
            catalog_ref="algorithm:51",
            builder=lambda **kwargs: build_funding_basis_arbitrage_algorithm(
                algorithm_key="funding_basis_arbitrage", **kwargs
            ),
            default_param={
                "rows": [],
                "base_symbol": "SPOT",
                "quote_symbol": "PERP",
                "lookback_window": 3,
                "entry_zscore": 1.0,
                "exit_zscore": 0.25,
                "rebalance_frequency": "all",
                "hedge_ratio_method": "ratio",
                "minimum_history": 3,
                "basis_field": "basis",
                "funding_field": "funding_rate",
                "carry_threshold": 0.0,
            },
            param_normalizer=require_funding_basis_arb_param,
            description="Trade spot-versus-derivative carry dislocations using basis and funding diagnostics.",
            param_schema=_funding_param_schema(),
            tags=("stat_arb", "funding", "basis", "multi_leg"),
            category="stat_arb",
            family="stat_arb",
            subcategory="funding",
            warmup_period=3,
            input_domains=("multi_leg_market_data",),
            asset_scope="multi_leg",
            output_modes=("multi_leg_signal", "hedge_ratio", "diagnostics"),
        ),
    ]
    for spec in specs:
        register_algorithm(spec)
