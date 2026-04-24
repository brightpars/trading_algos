from trading_algos.algorithmspec import AlertAlgorithmSpec, register_algorithm
from trading_algos.alertgen.algorithms.fundamental_ml_composite.quality_strategy import (
    build_quality_strategy,
)
from trading_algos.alertgen.algorithms.fundamental_ml_composite.multi_factor_composite import (
    build_multi_factor_composite,
)
from trading_algos.alertgen.algorithms.fundamental_ml_composite.value_strategy import (
    build_value_strategy,
)
from trading_algos.alertgen.core.validation import require_factor_portfolio_param


def _portfolio_param_schema(
    field_description: str,
    *,
    include_field_weights: bool = False,
    include_lower_is_better_fields: bool = False,
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
    if include_field_weights:
        schema.append(
            {
                "key": "field_weights",
                "label": "Field weights",
                "type": "number_list",
                "required": False,
                "description": "Optional positive weights aligned to field_names for weighted multi-factor scoring.",
            }
        )
    if include_lower_is_better_fields:
        schema.append(
            {
                "key": "lower_is_better_fields",
                "label": "Lower-is-better fields",
                "type": "string_list",
                "required": False,
                "description": "Subset of field_names that should be inverted because smaller values are preferred.",
            }
        )
    return tuple(schema)


def register_fundamental_ml_composite_alert_algorithms() -> None:
    specs = [
        AlertAlgorithmSpec(
            key="value_strategy",
            name="Value Strategy",
            catalog_ref="algorithm:86",
            builder=build_value_strategy,
            default_param={
                "rows": [],
                "field_names": ["price_to_book", "price_to_earnings"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
            param_normalizer=require_factor_portfolio_param,
            description="Rank assets by cheaper valuation multiples and allocate to the most attractive names.",
            param_schema=_portfolio_param_schema(
                "Factor fields used to compute the value score."
            ),
            tags=("fundamental", "value", "rebalance"),
            category="fundamental_ml_composite",
            family="fundamental_ml_composite",
            subcategory="value",
            warmup_period=1,
            input_domains=("fundamentals_pti", "multi_asset_panel"),
            asset_scope="portfolio",
            output_modes=("ranking", "selection", "weights", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="quality_strategy",
            name="Quality Strategy",
            catalog_ref="algorithm:87",
            builder=build_quality_strategy,
            default_param={
                "rows": [],
                "field_names": ["return_on_equity", "gross_margin"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
            },
            param_normalizer=require_factor_portfolio_param,
            description="Rank assets by profitability and balance-sheet quality characteristics.",
            param_schema=_portfolio_param_schema(
                "Factor fields used to compute the quality score."
            ),
            tags=("fundamental", "quality", "rebalance"),
            category="fundamental_ml_composite",
            family="fundamental_ml_composite",
            subcategory="quality",
            warmup_period=1,
            input_domains=("fundamentals_pti", "multi_asset_panel"),
            asset_scope="portfolio",
            output_modes=("ranking", "selection", "weights", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="multi_factor_composite",
            name="Multi-Factor Composite",
            catalog_ref="algorithm:88",
            builder=build_multi_factor_composite,
            default_param={
                "rows": [],
                "field_names": [
                    "price_to_book",
                    "price_to_earnings",
                    "return_on_equity",
                    "gross_margin",
                    "volatility_20d",
                    "realized_volatility",
                ],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
                "field_weights": [0.20, 0.15, 0.20, 0.15, 0.15, 0.15],
                "lower_is_better_fields": [
                    "price_to_book",
                    "price_to_earnings",
                    "volatility_20d",
                    "realized_volatility",
                ],
            },
            param_normalizer=require_factor_portfolio_param,
            description="Combine value, quality, and defensive factors into one rebalance-driven composite ranking.",
            param_schema=_portfolio_param_schema(
                "Factor fields used to compute the multi-factor composite score.",
                include_field_weights=True,
                include_lower_is_better_fields=True,
            ),
            tags=("fundamental", "multi_factor", "rebalance"),
            category="fundamental_ml_composite",
            family="fundamental_ml_composite",
            subcategory="multi",
            warmup_period=1,
            input_domains=("fundamentals_pti", "multi_asset_panel"),
            asset_scope="portfolio",
            output_modes=("ranking", "selection", "weights", "diagnostics"),
        ),
    ]
    for spec in specs:
        register_algorithm(spec)
