from __future__ import annotations

from trading_algos.algorithmspec import AlertAlgorithmSpec, register_algorithm
from trading_algos.alertgen.algorithms.composite.rule_based_combination.hard_boolean_gating_and_or_majority import (
    build_hard_boolean_gating_algorithm,
)
from trading_algos.alertgen.algorithms.composite.rule_based_combination.rank_aggregation import (
    build_rank_aggregation_algorithm,
)
from trading_algos.alertgen.algorithms.composite.rule_based_combination.weighted_linear_score_blend import (
    build_weighted_linear_score_blend_algorithm,
)
from trading_algos.alertgen.core.validation import (
    require_hard_boolean_gating_param,
    require_rank_aggregation_param,
    require_weighted_linear_score_blend_param,
)


def register_rule_based_combination_alert_algorithms() -> None:
    specs = [
        AlertAlgorithmSpec(
            key="hard_boolean_gating_and_or_majority",
            name="Hard Boolean Gating (AND / OR / Majority)",
            catalog_ref="combination:1",
            builder=lambda **kwargs: build_hard_boolean_gating_algorithm(
                algorithm_key="hard_boolean_gating_and_or_majority", **kwargs
            ),
            default_param={
                "mode": "and",
                "tie_policy": "neutral",
                "veto_sell_count": 0,
                "rows": [],
            },
            param_normalizer=require_hard_boolean_gating_param,
            description="Combine aligned child outputs with AND, OR, or majority vote semantics.",
            param_schema=(
                {
                    "key": "mode",
                    "label": "Mode",
                    "type": "string",
                    "required": True,
                    "enum": ["and", "or", "majority"],
                    "description": "Boolean aggregation mode applied to aligned child outputs.",
                },
                {
                    "key": "tie_policy",
                    "label": "Tie policy",
                    "type": "string",
                    "required": True,
                    "enum": ["neutral", "buy", "sell"],
                    "description": "How majority ties resolve when buy and sell vote counts are equal.",
                },
                {
                    "key": "veto_sell_count",
                    "label": "Sell veto count",
                    "type": "integer",
                    "required": True,
                    "minimum": 0,
                    "description": "If positive, this many sell votes force a sell decision before the main rule.",
                },
                {
                    "key": "rows",
                    "label": "Aligned child rows",
                    "type": "array",
                    "required": True,
                    "description": "Aligned child-output rows containing timestamped child contribution payloads.",
                },
            ),
            tags=("composite", "rule_based_combination", "boolean"),
            category="composite",
            family="rule_based_combination",
            subcategory="hard",
            warmup_period=1,
            input_domains=("ohlcv",),
            output_modes=("signal", "score"),
            composition_roles=("ensemble_member",),
        ),
        AlertAlgorithmSpec(
            key="rank_aggregation",
            name="Rank Aggregation",
            catalog_ref="combination:3",
            builder=lambda **kwargs: build_rank_aggregation_algorithm(
                algorithm_key="rank_aggregation", **kwargs
            ),
            default_param={
                "rows": [],
                "aggregation_method": "average_rank",
                "rank_field_names": [],
                "score_field_names": [],
                "top_k": 2,
                "minimum_child_count": 1,
            },
            param_normalizer=require_rank_aggregation_param,
            description="Aggregate cross-sectional child ranks or scores into one final ranking and top-k selection.",
            param_schema=(
                {
                    "key": "rows",
                    "label": "Cross-sectional rows",
                    "type": "array",
                    "required": True,
                    "description": "Timestamped rows containing per-asset child ranks or scores.",
                },
                {
                    "key": "aggregation_method",
                    "label": "Aggregation method",
                    "type": "string",
                    "required": True,
                    "enum": ["average_rank", "median_rank"],
                    "description": "How multiple child rank columns are collapsed into one aggregate rank.",
                },
                {
                    "key": "rank_field_names",
                    "label": "Rank fields",
                    "type": "array",
                    "required": True,
                    "description": "Per-asset field names containing child rank values.",
                },
                {
                    "key": "score_field_names",
                    "label": "Score fields",
                    "type": "array",
                    "required": False,
                    "description": "Optional per-asset score fields blended with inverse rank strength.",
                },
                {
                    "key": "top_k",
                    "label": "Top k",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Number of highest-ranked assets selected at each rebalance.",
                },
                {
                    "key": "minimum_child_count",
                    "label": "Minimum child count",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Minimum number of child rank/score inputs required per asset.",
                },
            ),
            tags=("composite", "rule_based_combination", "ranking"),
            category="composite",
            family="rule_based_combination",
            subcategory="rank",
            warmup_period=1,
            input_domains=("multi_asset_panel",),
            asset_scope="portfolio",
            output_modes=("ranking", "selection", "diagnostics"),
            composition_roles=("ensemble_member",),
        ),
        AlertAlgorithmSpec(
            key="weighted_linear_score_blend",
            name="Weighted Linear Score Blend",
            catalog_ref="combination:2",
            builder=lambda **kwargs: build_weighted_linear_score_blend_algorithm(
                algorithm_key="weighted_linear_score_blend", **kwargs
            ),
            default_param={
                "weights": {},
                "buy_threshold": 0.25,
                "sell_threshold": -0.25,
                "rows": [],
            },
            param_normalizer=require_weighted_linear_score_blend_param,
            description="Blend normalized child scores with fixed weights into one composite signal.",
            param_schema=(
                {
                    "key": "weights",
                    "label": "Weights",
                    "type": "object",
                    "required": True,
                    "description": "Mapping from child_key to fixed linear weight.",
                },
                {
                    "key": "buy_threshold",
                    "label": "Buy threshold",
                    "type": "number",
                    "required": True,
                    "description": "Composite score threshold at or above which the output becomes buy.",
                },
                {
                    "key": "sell_threshold",
                    "label": "Sell threshold",
                    "type": "number",
                    "required": True,
                    "description": "Composite score threshold at or below which the output becomes sell.",
                },
                {
                    "key": "rows",
                    "label": "Aligned child rows",
                    "type": "array",
                    "required": True,
                    "description": "Aligned child-output rows containing timestamped child contribution payloads.",
                },
            ),
            tags=("composite", "rule_based_combination", "weighted"),
            category="composite",
            family="rule_based_combination",
            subcategory="weighted",
            warmup_period=1,
            input_domains=("ohlcv",),
            output_modes=("signal", "score"),
            composition_roles=("ensemble_member",),
        ),
    ]
    for spec in specs:
        register_algorithm(spec)
