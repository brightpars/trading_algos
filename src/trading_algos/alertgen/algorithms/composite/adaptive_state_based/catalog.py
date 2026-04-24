from __future__ import annotations

from trading_algos.algorithmspec import AlertAlgorithmSpec, register_algorithm
from trading_algos.alertgen.algorithms.composite.adaptive_state_based.regime_switching_hmm_gating import (
    build_regime_switching_hmm_gating_algorithm,
)
from trading_algos.alertgen.core.validation import (
    require_regime_switching_hmm_gating_param,
)


def register_adaptive_state_based_alert_algorithms() -> None:
    register_algorithm(
        AlertAlgorithmSpec(
            key="regime_switching_hmm_gating",
            name="Regime Switching / HMM Gating",
            catalog_ref="combination:7",
            builder=lambda **kwargs: build_regime_switching_hmm_gating_algorithm(
                algorithm_key="regime_switching_hmm_gating",
                **kwargs,
            ),
            default_param={
                "rows": [],
                "regime_field": "regime_probabilities",
                "regime_map": {},
                "default_signal": "neutral",
                "smoothing": 0.25,
                "switch_threshold": 0.55,
                "expected_child_count": 1,
            },
            param_normalizer=require_regime_switching_hmm_gating_param,
            description="Apply smoothed regime probabilities to activate only the child strategies mapped to the current regime.",
            param_schema=(
                {
                    "key": "rows",
                    "label": "Aligned regime rows",
                    "type": "array",
                    "required": True,
                    "description": "Timestamped rows containing regime probabilities and aligned child outputs.",
                },
                {
                    "key": "regime_field",
                    "label": "Regime field",
                    "type": "string",
                    "required": True,
                    "description": "Field containing the per-regime probability map.",
                },
                {
                    "key": "regime_map",
                    "label": "Regime map",
                    "type": "object",
                    "required": True,
                    "description": "Mapping from regime label to active child keys.",
                },
                {
                    "key": "default_signal",
                    "label": "Default signal",
                    "type": "string",
                    "required": False,
                    "enum": ["buy", "sell", "neutral"],
                    "description": "Fallback signal when warmup is incomplete or no mapped child is active.",
                },
                {
                    "key": "smoothing",
                    "label": "Smoothing",
                    "type": "number",
                    "required": True,
                    "description": "Exponential smoothing weight applied to regime probabilities.",
                },
                {
                    "key": "switch_threshold",
                    "label": "Switch threshold",
                    "type": "number",
                    "required": True,
                    "description": "Minimum winning probability required to switch away from the previous regime.",
                },
                {
                    "key": "expected_child_count",
                    "label": "Expected child count",
                    "type": "integer",
                    "required": False,
                    "minimum": 1,
                    "description": "Minimum aligned child count required before the gate is considered ready.",
                },
            ),
            tags=("composite", "adaptive_state_based", "regime_gate"),
            category="composite",
            family="adaptive_state_based",
            subcategory="regime",
            warmup_period=1,
            input_domains=("multi_asset_panel",),
            output_modes=("signal", "diagnostics", "regime"),
            composition_roles=("regime_gate", "ensemble_member"),
        )
    )
