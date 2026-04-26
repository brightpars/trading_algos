from trading_algos.algorithmspec import AlertAlgorithmSpec, register_algorithm
from trading_algos.alertgen.algorithms.stat_arb.basket_statistical_arbitrage import (
    build_basket_statistical_arbitrage_algorithm,
)
from trading_algos.alertgen.algorithms.stat_arb.kalman_filter_pairs_trading import (
    build_kalman_filter_pairs_trading_algorithm,
)
from trading_algos.alertgen.algorithms.stat_arb.index_arbitrage import (
    build_index_arbitrage_algorithm,
)
from trading_algos.alertgen.algorithms.stat_arb.etf_nav_arbitrage import (
    build_etf_nav_arbitrage_algorithm,
)
from trading_algos.alertgen.algorithms.stat_arb.adr_dual_listing_arbitrage import (
    build_adr_dual_listing_arbitrage_algorithm,
)
from trading_algos.alertgen.algorithms.stat_arb.convertible_arbitrage import (
    build_convertible_arbitrage_algorithm,
)
from trading_algos.alertgen.algorithms.stat_arb.merger_arbitrage import (
    build_merger_arbitrage_algorithm,
)
from trading_algos.alertgen.algorithms.stat_arb.futures_cash_and_carry_arbitrage import (
    build_futures_cash_and_carry_arbitrage_algorithm,
)
from trading_algos.alertgen.algorithms.stat_arb.reverse_cash_and_carry_arbitrage import (
    build_reverse_cash_and_carry_arbitrage_algorithm,
)
from trading_algos.alertgen.algorithms.stat_arb.triangular_arbitrage_fx_crypto import (
    build_triangular_arbitrage_fx_crypto_algorithm,
)
from trading_algos.alertgen.algorithms.stat_arb.latency_exchange_arbitrage import (
    build_latency_exchange_arbitrage_algorithm,
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
    require_curve_relative_value_param,
    require_funding_basis_arb_param,
    require_kalman_pair_param,
    require_stat_arb_basket_param,
    require_stat_arb_pair_param,
    require_triangular_arb_param,
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


def _kalman_pair_param_schema() -> tuple[dict[str, object], ...]:
    return (
        *_pair_param_schema(),
        {
            "key": "process_variance",
            "label": "Process variance",
            "type": "number",
            "required": False,
            "minimum": 0.0,
            "description": "Kalman state-transition variance controlling hedge-ratio adaptability.",
        },
        {
            "key": "observation_variance",
            "label": "Observation variance",
            "type": "number",
            "required": False,
            "minimum": 0.0,
            "description": "Kalman observation noise variance used to smooth price observations.",
        },
    )


def _curve_param_schema() -> tuple[dict[str, object], ...]:
    return (
        *_pair_param_schema(),
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
    )


def _triangular_param_schema() -> tuple[dict[str, object], ...]:
    return (
        {
            "key": "rows",
            "label": "Rows",
            "type": "object_list",
            "required": True,
            "description": "Triangular pricing rows with ts, symbol, and close.",
        },
        {
            "key": "base_symbol",
            "label": "Base pair symbol",
            "type": "string",
            "required": True,
            "description": "First leg used in the synthetic cross construction.",
        },
        {
            "key": "cross_symbol",
            "label": "Cross pair symbol",
            "type": "string",
            "required": True,
            "description": "Second leg used in the synthetic cross construction.",
        },
        {
            "key": "implied_symbol",
            "label": "Implied pair symbol",
            "type": "string",
            "required": True,
            "description": "Observed market pair compared against the synthetic rate.",
        },
        {
            "key": "lookback_window",
            "label": "Lookback window",
            "type": "integer",
            "required": True,
            "minimum": 2,
            "description": "Rolling window used to estimate synthetic-rate divergence.",
        },
        {
            "key": "entry_zscore",
            "label": "Entry z-score",
            "type": "number",
            "required": True,
            "minimum": 0.0,
            "description": "Absolute z-score required to open the triangle.",
        },
        {
            "key": "exit_zscore",
            "label": "Exit z-score",
            "type": "number",
            "required": True,
            "minimum": 0.0,
            "description": "Absolute z-score threshold used to close the triangle.",
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


def register_stat_arb_alert_algorithms() -> None:
    specs = [
        AlertAlgorithmSpec(
            key="kalman_filter_pairs_trading",
            name="Kalman Filter Pairs Trading",
            catalog_ref="algorithm:41",
            builder=lambda **kwargs: build_kalman_filter_pairs_trading_algorithm(
                algorithm_key="kalman_filter_pairs_trading", **kwargs
            ),
            default_param={
                "rows": [],
                "base_symbol": "AAA",
                "quote_symbol": "BBB",
                "lookback_window": 3,
                "entry_zscore": 1.0,
                "exit_zscore": 0.25,
                "rebalance_frequency": "all",
                "minimum_history": 3,
                "process_variance": 0.0001,
                "observation_variance": 1.0,
            },
            param_normalizer=require_kalman_pair_param,
            description="Trade pair spread deviations with a Kalman-filtered dynamic hedge ratio.",
            param_schema=_kalman_pair_param_schema(),
            tags=("stat_arb", "pairs", "kalman", "multi_leg"),
            category="stat_arb",
            family="stat_arb",
            subcategory="kalman",
            warmup_period=3,
            input_domains=("pair_prices",),
            asset_scope="pair",
            output_modes=("multi_leg_signal", "hedge_ratio", "diagnostics"),
        ),
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
            key="index_arbitrage",
            name="Index Arbitrage",
            catalog_ref="algorithm:42",
            builder=lambda **kwargs: build_index_arbitrage_algorithm(
                algorithm_key="index_arbitrage", **kwargs
            ),
            default_param={
                "rows": [],
                "base_symbol": "INDEX",
                "basket_symbols": ["FUT", "ETF"],
                "basket_weights": [0.5, 0.5],
                "lookback_window": 3,
                "entry_zscore": 1.0,
                "exit_zscore": 0.25,
                "rebalance_frequency": "all",
                "minimum_history": 3,
            },
            param_normalizer=require_stat_arb_basket_param,
            description="Trade mispricing between an index anchor and related tradeable basket proxies.",
            param_schema=_basket_param_schema(),
            tags=("stat_arb", "index", "basket", "multi_leg"),
            category="stat_arb",
            family="stat_arb",
            subcategory="index",
            warmup_period=3,
            input_domains=("multi_leg_market_data",),
            asset_scope="multi_leg",
            output_modes=("multi_leg_signal", "hedge_ratio", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="etf_nav_arbitrage",
            name="ETF-NAV Arbitrage",
            catalog_ref="algorithm:43",
            builder=lambda **kwargs: build_etf_nav_arbitrage_algorithm(
                algorithm_key="etf_nav_arbitrage", **kwargs
            ),
            default_param={
                "rows": [],
                "base_symbol": "ETF",
                "basket_symbols": ["NAV_PROXY", "HEDGE"],
                "basket_weights": [0.7, 0.3],
                "lookback_window": 3,
                "entry_zscore": 1.0,
                "exit_zscore": 0.25,
                "rebalance_frequency": "all",
                "minimum_history": 3,
            },
            param_normalizer=require_stat_arb_basket_param,
            description="Trade ETF premium/discount versus an indicative NAV proxy basket.",
            param_schema=_basket_param_schema(),
            tags=("stat_arb", "etf", "basket", "multi_leg"),
            category="stat_arb",
            family="stat_arb",
            subcategory="etf",
            warmup_period=3,
            input_domains=("multi_leg_market_data",),
            asset_scope="multi_leg",
            output_modes=("multi_leg_signal", "hedge_ratio", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="adr_dual_listing_arbitrage",
            name="ADR Dual-Listing Arbitrage",
            catalog_ref="algorithm:44",
            builder=lambda **kwargs: build_adr_dual_listing_arbitrage_algorithm(
                algorithm_key="adr_dual_listing_arbitrage", **kwargs
            ),
            default_param={
                "rows": [],
                "base_symbol": "ADR",
                "quote_symbol": "LOCAL",
                "lookback_window": 3,
                "entry_zscore": 1.0,
                "exit_zscore": 0.25,
                "rebalance_frequency": "all",
                "hedge_ratio_method": "ratio",
                "carry_field": "fx_carry",
                "carry_weight": 1.0,
                "minimum_history": 3,
            },
            param_normalizer=require_curve_relative_value_param,
            description="Trade ADR versus local-line dislocations with optional FX carry adjustment.",
            param_schema=_curve_param_schema(),
            tags=("stat_arb", "adr", "pair", "multi_leg"),
            category="stat_arb",
            family="stat_arb",
            subcategory="adr",
            warmup_period=3,
            input_domains=("multi_leg_market_data",),
            asset_scope="multi_leg",
            output_modes=("multi_leg_signal", "hedge_ratio", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="convertible_arbitrage",
            name="Convertible Arbitrage",
            catalog_ref="algorithm:45",
            builder=lambda **kwargs: build_convertible_arbitrage_algorithm(
                algorithm_key="convertible_arbitrage", **kwargs
            ),
            default_param={
                "rows": [],
                "base_symbol": "CONVERTIBLE",
                "quote_symbol": "EQUITY",
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
            description="Trade convertible price dislocations relative to hedge equity and carry context.",
            param_schema=_curve_param_schema(),
            tags=("stat_arb", "convertible", "pair", "multi_leg"),
            category="stat_arb",
            family="stat_arb",
            subcategory="convertible",
            warmup_period=3,
            input_domains=("multi_leg_market_data",),
            asset_scope="multi_leg",
            output_modes=("multi_leg_signal", "hedge_ratio", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="merger_arbitrage",
            name="Merger Arbitrage",
            catalog_ref="algorithm:46",
            builder=lambda **kwargs: build_merger_arbitrage_algorithm(
                algorithm_key="merger_arbitrage", **kwargs
            ),
            default_param={
                "rows": [],
                "base_symbol": "TARGET",
                "quote_symbol": "ACQUIRER",
                "lookback_window": 3,
                "entry_zscore": 1.0,
                "exit_zscore": 0.25,
                "rebalance_frequency": "all",
                "hedge_ratio_method": "ratio",
                "carry_field": "deal_spread",
                "carry_weight": 1.0,
                "minimum_history": 3,
            },
            param_normalizer=require_curve_relative_value_param,
            description="Trade target-acquirer deal spread distortions with paired legs.",
            param_schema=_curve_param_schema(),
            tags=("stat_arb", "merger", "pair", "multi_leg"),
            category="stat_arb",
            family="stat_arb",
            subcategory="merger",
            warmup_period=3,
            input_domains=("multi_leg_market_data",),
            asset_scope="multi_leg",
            output_modes=("multi_leg_signal", "hedge_ratio", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="futures_cash_and_carry_arbitrage",
            name="Futures Cash-and-Carry Arbitrage",
            catalog_ref="algorithm:47",
            builder=lambda **kwargs: build_futures_cash_and_carry_arbitrage_algorithm(
                algorithm_key="futures_cash_and_carry_arbitrage", **kwargs
            ),
            default_param={
                "rows": [],
                "base_symbol": "SPOT",
                "quote_symbol": "FUTURE",
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
            description="Trade positive futures basis versus fair-value carry-adjusted spot.",
            param_schema=_curve_param_schema(),
            tags=("stat_arb", "futures", "carry", "multi_leg"),
            category="stat_arb",
            family="stat_arb",
            subcategory="futures",
            warmup_period=3,
            input_domains=("multi_leg_market_data",),
            asset_scope="multi_leg",
            output_modes=("multi_leg_signal", "hedge_ratio", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="reverse_cash_and_carry_arbitrage",
            name="Reverse Cash-and-Carry Arbitrage",
            catalog_ref="algorithm:48",
            builder=lambda **kwargs: build_reverse_cash_and_carry_arbitrage_algorithm(
                algorithm_key="reverse_cash_and_carry_arbitrage", **kwargs
            ),
            default_param={
                "rows": [],
                "base_symbol": "SPOT",
                "quote_symbol": "FUTURE",
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
            description="Trade negative futures basis versus fair-value carry-adjusted spot.",
            param_schema=_curve_param_schema(),
            tags=("stat_arb", "reverse", "carry", "multi_leg"),
            category="stat_arb",
            family="stat_arb",
            subcategory="reverse",
            warmup_period=3,
            input_domains=("multi_leg_market_data",),
            asset_scope="multi_leg",
            output_modes=("multi_leg_signal", "hedge_ratio", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="triangular_arbitrage_fx_crypto",
            name="Triangular Arbitrage (FX/Crypto)",
            catalog_ref="algorithm:49",
            builder=lambda **kwargs: build_triangular_arbitrage_fx_crypto_algorithm(
                algorithm_key="triangular_arbitrage_fx_crypto", **kwargs
            ),
            default_param={
                "rows": [],
                "base_symbol": "EURUSD",
                "cross_symbol": "USDJPY",
                "implied_symbol": "EURJPY",
                "lookback_window": 3,
                "entry_zscore": 1.0,
                "exit_zscore": 0.25,
                "rebalance_frequency": "all",
                "minimum_history": 3,
            },
            param_normalizer=require_triangular_arb_param,
            description="Trade synthetic cross-rate dislocations across a three-leg FX or crypto triangle.",
            param_schema=_triangular_param_schema(),
            tags=("stat_arb", "triangular", "fx", "multi_leg"),
            category="stat_arb",
            family="stat_arb",
            subcategory="triangular",
            warmup_period=3,
            input_domains=("multi_leg_market_data",),
            asset_scope="multi_leg",
            output_modes=("multi_leg_signal", "hedge_ratio", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="latency_exchange_arbitrage",
            name="Latency / Exchange Arbitrage",
            catalog_ref="algorithm:50",
            builder=lambda **kwargs: build_latency_exchange_arbitrage_algorithm(
                algorithm_key="latency_exchange_arbitrage", **kwargs
            ),
            default_param={
                "rows": [],
                "base_symbol": "VENUE_A",
                "quote_symbol": "VENUE_B",
                "lookback_window": 3,
                "entry_zscore": 1.0,
                "exit_zscore": 0.25,
                "rebalance_frequency": "all",
                "hedge_ratio_method": "ratio",
                "minimum_history": 3,
            },
            param_normalizer=require_stat_arb_pair_param,
            description="Trade transient cross-venue price dislocations as a two-leg latency arbitrage spread.",
            param_schema=_pair_param_schema(),
            tags=("stat_arb", "latency", "pair", "multi_leg"),
            category="stat_arb",
            family="stat_arb",
            subcategory="latency",
            warmup_period=3,
            input_domains=("multi_leg_market_data",),
            asset_scope="multi_leg",
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
