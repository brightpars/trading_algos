from trading_algos.algorithmspec import AlertAlgorithmSpec, register_algorithm
from trading_algos.alertgen.algorithms.factor_risk_premia.dividend_yield_strategy import (
    build_dividend_yield_strategy,
)
from trading_algos.alertgen.algorithms.factor_risk_premia.earnings_quality_strategy import (
    build_earnings_quality_strategy,
)
from trading_algos.alertgen.algorithms.factor_risk_premia.growth_factor_strategy import (
    build_growth_factor_strategy,
)
from trading_algos.alertgen.algorithms.factor_risk_premia.liquidity_factor_strategy import (
    build_liquidity_factor_strategy,
)
from trading_algos.alertgen.algorithms.factor_risk_premia.low_leverage_balance_sheet_strength import (
    build_low_leverage_balance_sheet_strength,
)
from trading_algos.alertgen.algorithms.factor_risk_premia.low_beta_betting_against_beta import (
    build_low_beta_betting_against_beta,
)
from trading_algos.alertgen.algorithms.factor_risk_premia.low_volatility_strategy import (
    build_low_volatility_strategy,
)
from trading_algos.alertgen.algorithms.factor_risk_premia.mid_cap_tilt_strategy import (
    build_mid_cap_tilt_strategy,
)
from trading_algos.alertgen.algorithms.factor_risk_premia.minimum_variance_strategy import (
    build_minimum_variance_strategy,
)
from trading_algos.alertgen.algorithms.factor_risk_premia.profitability_factor_strategy import (
    build_profitability_factor_strategy,
)
from trading_algos.alertgen.algorithms.factor_risk_premia.size_small_cap_strategy import (
    build_size_small_cap_strategy,
)
from trading_algos.alertgen.core.validation import require_factor_portfolio_param


def _factor_portfolio_param_schema(
    field_description: str,
    *,
    include_target_value: bool = False,
    include_weighting_mode: bool = False,
) -> tuple[dict[str, object], ...]:
    schema: list[dict[str, object]] = [
        {
            "key": "rows",
            "label": "Rows",
            "type": "object_list",
            "required": True,
            "description": "Panel rows containing ts, symbol, close, and factor fields.",
        },
        {
            "key": "field_names",
            "label": "Field names",
            "type": "string_list",
            "required": True,
            "description": field_description,
        },
        {
            "key": "rebalance_frequency",
            "label": "Rebalance frequency",
            "type": "string",
            "required": True,
            "enum": ["monthly", "weekly", "all"],
            "description": "Schedule used to sample rebalance dates.",
        },
        {
            "key": "top_n",
            "label": "Top N",
            "type": "integer",
            "required": True,
            "minimum": 1,
            "description": "Number of strongest ranked assets to allocate to.",
        },
        {
            "key": "bottom_n",
            "label": "Bottom N",
            "type": "integer",
            "required": False,
            "minimum": 0,
            "description": "Optional number of weakest assets to short when long_only is false.",
        },
        {
            "key": "long_only",
            "label": "Long only",
            "type": "boolean",
            "required": True,
            "description": "Whether the portfolio allocates only to long positions.",
        },
        {
            "key": "minimum_universe_size",
            "label": "Minimum universe size",
            "type": "integer",
            "required": True,
            "minimum": 1,
            "description": "Minimum number of scored assets required before the rebalance is actionable.",
        },
    ]
    if include_target_value:
        schema.append(
            {
                "key": "target_value",
                "label": "Target value",
                "type": "number",
                "required": False,
                "description": "Preferred center value used to rank names by proximity instead of pure high/low sorting.",
            }
        )
    if include_weighting_mode:
        schema.append(
            {
                "key": "weighting_mode",
                "label": "Weighting mode",
                "type": "string",
                "required": False,
                "enum": ["equal_weight", "inverse_metric"],
                "description": "Method used to convert selected names into portfolio weights.",
            }
        )
    return tuple(schema)


def register_factor_risk_premia_alert_algorithms() -> None:
    specs = [
        AlertAlgorithmSpec(
            key="low_volatility_strategy",
            name="Low Volatility Strategy",
            catalog_ref="algorithm:100",
            builder=build_low_volatility_strategy,
            default_param={
                "rows": [],
                "field_names": ["volatility_20d", "realized_volatility"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
            param_normalizer=require_factor_portfolio_param,
            description="Rank assets by lower realized volatility and build a rebalance-driven portfolio.",
            param_schema=_factor_portfolio_param_schema(
                "Factor fields used to compute the low-volatility score."
            ),
            tags=("factor", "low_volatility", "rebalance"),
            category="factor_risk_premia",
            family="factor_risk_premia",
            subcategory="low",
            warmup_period=1,
            input_domains=("fundamentals_pti", "multi_asset_panel"),
            asset_scope="portfolio",
            output_modes=("ranking", "selection", "weights", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="low_beta_betting_against_beta",
            name="Low Beta / Betting-Against-Beta",
            catalog_ref="algorithm:103",
            builder=build_low_beta_betting_against_beta,
            default_param={
                "rows": [],
                "field_names": ["beta_252d", "market_beta"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
            param_normalizer=require_factor_portfolio_param,
            description="Prefer lower-beta securities and allocate on rebalance dates.",
            param_schema=_factor_portfolio_param_schema(
                "Factor fields used to compute the beta score."
            ),
            tags=("factor", "beta", "rebalance"),
            category="factor_risk_premia",
            family="factor_risk_premia",
            subcategory="low",
            warmup_period=1,
            input_domains=("fundamentals_pti", "multi_asset_panel"),
            asset_scope="portfolio",
            output_modes=("ranking", "selection", "weights", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="dividend_yield_strategy",
            name="Dividend Yield Strategy",
            catalog_ref="algorithm:107",
            builder=build_dividend_yield_strategy,
            default_param={
                "rows": [],
                "field_names": ["dividend_yield", "forward_dividend_yield"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
            param_normalizer=require_factor_portfolio_param,
            description="Rank assets by dividend yield and build an income-oriented factor portfolio.",
            param_schema=_factor_portfolio_param_schema(
                "Factor fields used to compute the dividend-yield score."
            ),
            tags=("factor", "dividend", "rebalance"),
            category="factor_risk_premia",
            family="factor_risk_premia",
            subcategory="dividend",
            warmup_period=1,
            input_domains=("fundamentals_pti", "multi_asset_panel"),
            asset_scope="portfolio",
            output_modes=("ranking", "selection", "weights", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="growth_factor_strategy",
            name="Growth Factor Strategy",
            catalog_ref="algorithm:108",
            builder=build_growth_factor_strategy,
            default_param={
                "rows": [],
                "field_names": ["earnings_growth", "sales_growth"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
            param_normalizer=require_factor_portfolio_param,
            description="Rank assets by growth metrics and allocate to the strongest names on rebalance dates.",
            param_schema=_factor_portfolio_param_schema(
                "Factor fields used to compute the growth score."
            ),
            tags=("factor", "growth", "rebalance"),
            category="factor_risk_premia",
            family="factor_risk_premia",
            subcategory="growth",
            warmup_period=1,
            input_domains=("fundamentals_pti", "multi_asset_panel"),
            asset_scope="portfolio",
            output_modes=("ranking", "selection", "weights", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="liquidity_factor_strategy",
            name="Liquidity Factor Strategy",
            catalog_ref="algorithm:109",
            builder=build_liquidity_factor_strategy,
            default_param={
                "rows": [],
                "field_names": ["liquidity_score", "turnover_ratio"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
            param_normalizer=require_factor_portfolio_param,
            description="Rank assets by liquidity-related metrics and build a tradability-aware factor sleeve.",
            param_schema=_factor_portfolio_param_schema(
                "Factor fields used to compute the liquidity score."
            ),
            tags=("factor", "liquidity", "rebalance"),
            category="factor_risk_premia",
            family="factor_risk_premia",
            subcategory="liquidity",
            warmup_period=1,
            input_domains=("fundamentals_pti", "multi_asset_panel"),
            asset_scope="portfolio",
            output_modes=("ranking", "selection", "weights", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="minimum_variance_strategy",
            name="Minimum Variance Strategy",
            catalog_ref="algorithm:101",
            builder=build_minimum_variance_strategy,
            default_param={
                "rows": [],
                "field_names": ["volatility_20d", "realized_volatility"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
                "weighting_mode": "inverse_metric",
            },
            param_normalizer=require_factor_portfolio_param,
            description="Select lower-risk names and tilt portfolio weights toward the lowest estimated variance members.",
            param_schema=_factor_portfolio_param_schema(
                "Factor fields used to estimate the variance proxy.",
                include_weighting_mode=True,
            ),
            tags=("factor", "minimum_variance", "rebalance"),
            category="factor_risk_premia",
            family="factor_risk_premia",
            subcategory="minimum",
            warmup_period=1,
            input_domains=("fundamentals_pti", "multi_asset_panel"),
            asset_scope="portfolio",
            output_modes=("ranking", "selection", "weights", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="size_small_cap_strategy",
            name="Size / Small-Cap Strategy",
            catalog_ref="algorithm:105",
            builder=build_size_small_cap_strategy,
            default_param={
                "rows": [],
                "field_names": ["market_cap_billions"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
            param_normalizer=require_factor_portfolio_param,
            description="Prefer smaller-cap names using market-cap style inputs.",
            param_schema=_factor_portfolio_param_schema(
                "Factor fields used to compute the size score. Lower values rank better."
            ),
            tags=("factor", "size", "rebalance"),
            category="factor_risk_premia",
            family="factor_risk_premia",
            subcategory="size",
            warmup_period=1,
            input_domains=("fundamentals_pti", "multi_asset_panel"),
            asset_scope="portfolio",
            output_modes=("ranking", "selection", "weights", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="mid_cap_tilt_strategy",
            name="Mid-Cap Tilt Strategy",
            catalog_ref="algorithm:106",
            builder=build_mid_cap_tilt_strategy,
            default_param={
                "rows": [],
                "field_names": ["market_cap_billions"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
                "target_value": 10.0,
            },
            param_normalizer=require_factor_portfolio_param,
            description="Rank assets by closeness to a target mid-cap band.",
            param_schema=_factor_portfolio_param_schema(
                "Factor fields used to compute the market-cap score.",
                include_target_value=True,
            ),
            tags=("factor", "mid_cap", "rebalance"),
            category="factor_risk_premia",
            family="factor_risk_premia",
            subcategory="mid",
            warmup_period=1,
            input_domains=("fundamentals_pti", "multi_asset_panel"),
            asset_scope="portfolio",
            output_modes=("ranking", "selection", "weights", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="profitability_factor_strategy",
            name="Profitability Factor Strategy",
            catalog_ref="algorithm:110",
            builder=build_profitability_factor_strategy,
            default_param={
                "rows": [],
                "field_names": ["return_on_assets", "gross_profitability"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
            param_normalizer=require_factor_portfolio_param,
            description="Rank assets by profitability metrics and allocate to the strongest firms.",
            param_schema=_factor_portfolio_param_schema(
                "Factor fields used to compute the profitability score."
            ),
            tags=("factor", "profitability", "rebalance"),
            category="factor_risk_premia",
            family="factor_risk_premia",
            subcategory="profitability",
            warmup_period=1,
            input_domains=("fundamentals_pti", "multi_asset_panel"),
            asset_scope="portfolio",
            output_modes=("ranking", "selection", "weights", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="earnings_quality_strategy",
            name="Earnings Quality Strategy",
            catalog_ref="algorithm:111",
            builder=build_earnings_quality_strategy,
            default_param={
                "rows": [],
                "field_names": ["cash_earnings_ratio", "earnings_stability"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
            param_normalizer=require_factor_portfolio_param,
            description="Prefer firms with stronger cash support and more stable earnings quality.",
            param_schema=_factor_portfolio_param_schema(
                "Factor fields used to compute the earnings-quality score."
            ),
            tags=("factor", "earnings_quality", "rebalance"),
            category="factor_risk_premia",
            family="factor_risk_premia",
            subcategory="earnings",
            warmup_period=1,
            input_domains=("fundamentals_pti", "multi_asset_panel"),
            asset_scope="portfolio",
            output_modes=("ranking", "selection", "weights", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="low_leverage_balance_sheet_strength",
            name="Low Leverage / Balance-Sheet Strength",
            catalog_ref="algorithm:113",
            builder=build_low_leverage_balance_sheet_strength,
            default_param={
                "rows": [],
                "field_names": ["debt_to_equity", "net_debt_to_ebitda"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
            param_normalizer=require_factor_portfolio_param,
            description="Favor firms with lower leverage and stronger balance-sheet resilience.",
            param_schema=_factor_portfolio_param_schema(
                "Factor fields used to compute the balance-sheet-strength score. Lower values rank better."
            ),
            tags=("factor", "balance_sheet", "rebalance"),
            category="factor_risk_premia",
            family="factor_risk_premia",
            subcategory="low",
            warmup_period=1,
            input_domains=("fundamentals_pti", "multi_asset_panel"),
            asset_scope="portfolio",
            output_modes=("ranking", "selection", "weights", "diagnostics"),
        ),
    ]
    for spec in specs:
        register_algorithm(spec)
