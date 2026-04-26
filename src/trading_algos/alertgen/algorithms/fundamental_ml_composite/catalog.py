from trading_algos.algorithmspec import AlertAlgorithmSpec, register_algorithm
from trading_algos.alertgen.algorithms.fundamental_ml_composite.ensemble_voting_strategy import (
    build_ensemble_voting_strategy,
)
from trading_algos.alertgen.algorithms.fundamental_ml_composite.machine_learning_classifier import (
    build_machine_learning_classifier,
)
from trading_algos.alertgen.algorithms.fundamental_ml_composite.machine_learning_regressor import (
    build_machine_learning_regressor,
)
from trading_algos.alertgen.algorithms.fundamental_ml_composite.quality_strategy import (
    build_quality_strategy,
)
from trading_algos.alertgen.algorithms.fundamental_ml_composite.regime_switching_strategy import (
    build_regime_switching_strategy,
)
from trading_algos.alertgen.algorithms.fundamental_ml_composite.sentiment_strategy import (
    build_sentiment_strategy,
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


def _advanced_model_param_schema(
    field_description: str,
    *,
    threshold_key: str,
    threshold_label: str,
    threshold_description: str,
    include_field_weights: bool = True,
) -> tuple[dict[str, object], ...]:
    schema = list(
        _portfolio_param_schema(
            field_description,
            include_field_weights=include_field_weights,
            include_lower_is_better_fields=False,
        )
    )
    schema.append(
        {
            "key": threshold_key,
            "label": threshold_label,
            "type": "number",
            "required": False,
            "description": threshold_description,
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
        AlertAlgorithmSpec(
            key="sentiment_strategy",
            name="Sentiment Strategy",
            catalog_ref="algorithm:89",
            builder=build_sentiment_strategy,
            default_param={
                "rows": [],
                "field_names": ["sentiment_score", "sentiment_momentum"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
                "field_weights": [0.7, 0.3],
            },
            param_normalizer=require_factor_portfolio_param,
            description="Rank assets by aggregated sentiment features and allocate toward the strongest sentiment names.",
            param_schema=_advanced_model_param_schema(
                "Sentiment feature fields used to compute the rebalance score.",
                threshold_key="sentiment_threshold",
                threshold_label="Sentiment threshold",
                threshold_description="Optional sentiment gate retained in diagnostics for downstream decisioning.",
            ),
            tags=("fundamental", "sentiment", "rebalance", "ml"),
            category="fundamental_ml_composite",
            family="fundamental_ml_composite",
            subcategory="sentiment",
            warmup_period=1,
            input_domains=("fundamentals_pti", "multi_asset_panel"),
            asset_scope="portfolio",
            output_modes=("ranking", "selection", "weights", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="machine_learning_classifier",
            name="Machine Learning Classifier",
            catalog_ref="algorithm:90",
            builder=build_machine_learning_classifier,
            default_param={
                "rows": [],
                "field_names": ["model_probability", "feature_strength"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
                "field_weights": [0.8, 0.2],
                "classification_threshold": 0.5,
            },
            param_normalizer=require_factor_portfolio_param,
            description="Convert model probability features into rebalance-ready ranking, selection, and diagnostics.",
            param_schema=_advanced_model_param_schema(
                "Classifier-derived feature fields used to compute the probability score.",
                threshold_key="classification_threshold",
                threshold_label="Classification threshold",
                threshold_description="Probability threshold used to label the top-ranked model output.",
            ),
            tags=("fundamental", "machine_learning", "classifier", "rebalance"),
            category="fundamental_ml_composite",
            family="fundamental_ml_composite",
            subcategory="machine",
            warmup_period=1,
            input_domains=("feature_matrix", "label_stream"),
            asset_scope="single_asset",
            output_modes=("score", "signal", "model_diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="machine_learning_regressor",
            name="Machine Learning Regressor",
            catalog_ref="algorithm:91",
            builder=build_machine_learning_regressor,
            default_param={
                "rows": [],
                "field_names": ["predicted_return", "return_conviction"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
                "field_weights": [0.75, 0.25],
                "return_threshold": 0.0,
            },
            param_normalizer=require_factor_portfolio_param,
            description="Rank assets on regression-style return forecasts and emit threshold-aware diagnostics.",
            param_schema=_advanced_model_param_schema(
                "Regressor-derived feature fields used to compute the forecast score.",
                threshold_key="return_threshold",
                threshold_label="Return threshold",
                threshold_description="Optional return threshold used to classify the top-ranked forecast direction.",
            ),
            tags=("fundamental", "machine_learning", "regression", "rebalance"),
            category="fundamental_ml_composite",
            family="fundamental_ml_composite",
            subcategory="machine",
            warmup_period=1,
            input_domains=("feature_matrix", "label_stream"),
            asset_scope="single_asset",
            output_modes=("score", "signal", "model_diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="regime_switching_strategy",
            name="Regime-Switching Strategy",
            catalog_ref="algorithm:92",
            builder=build_regime_switching_strategy,
            default_param={
                "rows": [],
                "field_names": ["regime_probability", "macro_regime_score"],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
                "field_weights": [0.6, 0.4],
                "regime_threshold": 0.0,
            },
            param_normalizer=require_factor_portfolio_param,
            description="Estimate regime state from model features and expose regime-aware rebalance diagnostics.",
            param_schema=_advanced_model_param_schema(
                "Regime feature fields used to score assets or sleeves on each rebalance date.",
                threshold_key="regime_threshold",
                threshold_label="Regime threshold",
                threshold_description="Score threshold used to label the dominant regime in diagnostics.",
            ),
            tags=("fundamental", "machine_learning", "regime", "rebalance"),
            category="fundamental_ml_composite",
            family="fundamental_ml_composite",
            subcategory="regime",
            warmup_period=1,
            input_domains=("feature_matrix", "label_stream"),
            asset_scope="portfolio",
            output_modes=("regime", "signal", "diagnostics"),
        ),
        AlertAlgorithmSpec(
            key="ensemble_voting_strategy",
            name="Ensemble / Voting Strategy",
            catalog_ref="algorithm:93",
            builder=build_ensemble_voting_strategy,
            default_param={
                "rows": [],
                "field_names": [
                    "vote_probability",
                    "agreement_score",
                    "member_confidence",
                ],
                "rebalance_frequency": "monthly",
                "top_n": 2,
                "bottom_n": 0,
                "long_only": True,
                "minimum_universe_size": 2,
                "field_weights": [0.5, 0.3, 0.2],
                "vote_threshold": 0.5,
            },
            param_normalizer=require_factor_portfolio_param,
            description="Combine multiple model-style features into one voting score with reusable portfolio output wiring.",
            param_schema=_advanced_model_param_schema(
                "Ensemble member feature fields used to compute the aggregate vote score.",
                threshold_key="vote_threshold",
                threshold_label="Vote threshold",
                threshold_description="Minimum normalized vote strength treated as an accepted ensemble outcome.",
            ),
            tags=("fundamental", "machine_learning", "ensemble", "rebalance"),
            category="fundamental_ml_composite",
            family="fundamental_ml_composite",
            subcategory="ensemble",
            warmup_period=1,
            input_domains=("feature_matrix", "label_stream"),
            asset_scope="portfolio",
            output_modes=("signal", "child_contributions", "diagnostics"),
        ),
    ]
    for spec in specs:
        register_algorithm(spec)
