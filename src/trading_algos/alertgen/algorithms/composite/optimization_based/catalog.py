from __future__ import annotations

from trading_algos.algorithmspec import AlertAlgorithmSpec, register_algorithm
from trading_algos.alertgen.algorithms.composite.optimization_based.constrained_multi_factor_optimization import (
    build_constrained_multi_factor_optimization_algorithm,
)
from trading_algos.alertgen.core.validation import (
    require_constrained_multi_factor_optimization_param,
)


def register_optimization_based_alert_algorithms() -> None:
    register_algorithm(
        AlertAlgorithmSpec(
            key="constrained_multi_factor_optimization",
            name="Constrained Multi-Factor Optimization",
            catalog_ref="combination:4",
            builder=lambda **kwargs: (
                build_constrained_multi_factor_optimization_algorithm(
                    algorithm_key="constrained_multi_factor_optimization",
                    **kwargs,
                )
            ),
            default_param={
                "rows": [],
                "rebalance_frequency": "monthly",
                "target_gross_exposure": 1.0,
                "min_history": 3,
                "max_weight": 0.6,
            },
            param_normalizer=require_constrained_multi_factor_optimization_param,
            description="Allocate across sleeves by maximizing simple return-to-risk scores while respecting a gross-exposure and per-sleeve cap.",
            param_schema=(
                {
                    "key": "rows",
                    "label": "Strategy return rows",
                    "type": "array",
                    "required": True,
                    "description": "Timestamped rows containing sleeve return streams.",
                },
                {
                    "key": "rebalance_frequency",
                    "label": "Rebalance frequency",
                    "type": "string",
                    "required": True,
                    "enum": ["monthly", "weekly", "all"],
                    "description": "Declared rebalance cadence for optimization updates.",
                },
                {
                    "key": "target_gross_exposure",
                    "label": "Target gross exposure",
                    "type": "number",
                    "required": True,
                    "description": "Maximum gross exposure after normalization.",
                },
                {
                    "key": "min_history",
                    "label": "Minimum history",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Minimum return observations required per sleeve.",
                },
                {
                    "key": "max_weight",
                    "label": "Max sleeve weight",
                    "type": "number",
                    "required": True,
                    "description": "Per-sleeve cap before final normalization.",
                },
            ),
            tags=("composite", "optimization_based", "allocation"),
            category="composite",
            family="optimization_based",
            subcategory="constrained",
            warmup_period=3,
            input_domains=("multi_asset_panel",),
            asset_scope="portfolio",
            output_modes=("weights", "diagnostics"),
            composition_roles=("ensemble_member",),
        )
    )
