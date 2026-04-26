from __future__ import annotations

from trading_algos.algorithmspec import AlertAlgorithmSpec, register_algorithm
from trading_algos.alertgen.algorithms.composite.reinforcement_learning.hierarchical_controller_meta_policy import (
    build_hierarchical_controller_meta_policy_algorithm,
)
from trading_algos.alertgen.algorithms.composite.reinforcement_learning.rl_allocation_controller import (
    build_rl_allocation_controller_algorithm,
)
from trading_algos.alertgen.core.validation import (
    require_hierarchical_controller_meta_policy_param,
    require_rl_allocation_controller_param,
)


def _rl_param_schema() -> tuple[dict[str, object], ...]:
    return (
        {
            "key": "rows",
            "label": "RL environment rows",
            "type": "array",
            "required": True,
            "description": "Timestamped RL environment rows containing state vectors, action scores, reward values, and optional candidate weights.",
        },
        {
            "key": "min_history",
            "label": "Minimum history",
            "type": "integer",
            "required": True,
            "minimum": 1,
            "description": "Minimum environment rows required before the controller emits live allocations.",
        },
        {
            "key": "gross_exposure_limit",
            "label": "Gross exposure limit",
            "type": "number",
            "required": True,
            "description": "Maximum gross exposure allowed after action weights are normalized.",
        },
        {
            "key": "action_weight_templates",
            "label": "Action weight templates",
            "type": "object",
            "required": False,
            "description": "Fallback allocation templates keyed by resolved action name when the environment row omits candidate weights.",
        },
        {
            "key": "action_aliases",
            "label": "Action aliases",
            "type": "object",
            "required": False,
            "description": "Optional mapping from raw environment action names to normalized controller action names.",
        },
        {
            "key": "action_overrides",
            "label": "Action overrides",
            "type": "object",
            "required": False,
            "description": "Optional static action-score overrides applied before the controller selects the best action.",
        },
    )


def register_reinforcement_learning_alert_algorithms() -> None:
    specs = [
        AlertAlgorithmSpec(
            key="rl_allocation_controller",
            name="RL Allocation Controller",
            catalog_ref="combination:11",
            builder=lambda **kwargs: build_rl_allocation_controller_algorithm(
                algorithm_key="rl_allocation_controller", **kwargs
            ),
            default_param={
                "rows": [],
                "min_history": 1,
                "gross_exposure_limit": 1.0,
                "action_weight_templates": {},
                "action_aliases": {},
                "action_overrides": {},
            },
            param_normalizer=require_rl_allocation_controller_param,
            description="Choose an allocation action from an offline RL environment row stream and convert the selected action into normalized portfolio weights.",
            param_schema=_rl_param_schema(),
            tags=("composite", "reinforcement_learning", "allocation"),
            category="composite",
            family="reinforcement_learning",
            subcategory="rl",
            warmup_period=1,
            input_domains=("rl_environment",),
            asset_scope="portfolio",
            output_modes=("weights", "diagnostics"),
            composition_roles=("ensemble_member",),
            runtime_kind="execution",
        ),
        AlertAlgorithmSpec(
            key="hierarchical_controller_meta_policy",
            name="Hierarchical Controller / Meta-Policy",
            catalog_ref="combination:12",
            builder=lambda **kwargs: (
                build_hierarchical_controller_meta_policy_algorithm(
                    algorithm_key="hierarchical_controller_meta_policy", **kwargs
                )
            ),
            default_param={
                "rows": [],
                "min_history": 1,
                "gross_exposure_limit": 1.0,
                "action_weight_templates": {},
                "action_aliases": {},
                "action_overrides": {},
            },
            param_normalizer=require_hierarchical_controller_meta_policy_param,
            description="Use environment metadata to gate the admissible actions before selecting the best lower-level allocation action.",
            param_schema=_rl_param_schema(),
            tags=("composite", "reinforcement_learning", "hierarchical"),
            category="composite",
            family="reinforcement_learning",
            subcategory="hierarchical",
            warmup_period=1,
            input_domains=("rl_environment",),
            asset_scope="portfolio",
            output_modes=("weights", "diagnostics"),
            composition_roles=("ensemble_member",),
            runtime_kind="execution",
        ),
    ]
    for spec in specs:
        register_algorithm(spec)
