from __future__ import annotations

from trading_algos.algorithmspec import AlertAlgorithmSpec, register_algorithm
from trading_algos.alertgen.algorithms.composite.risk_overlay.risk_budgeting_risk_parity import (
    build_risk_budgeting_risk_parity_algorithm,
)
from trading_algos.alertgen.algorithms.composite.risk_overlay.volatility_targeting_overlay import (
    build_volatility_targeting_overlay_algorithm,
)
from trading_algos.alertgen.core.validation import (
    require_risk_budgeting_param,
    require_volatility_targeting_overlay_param,
)


def register_risk_overlay_alert_algorithms() -> None:
    specs = [
        AlertAlgorithmSpec(
            key="risk_budgeting_risk_parity",
            name="Risk Budgeting / Risk Parity",
            catalog_ref="combination:5",
            builder=lambda **kwargs: build_risk_budgeting_risk_parity_algorithm(
                algorithm_key="risk_budgeting_risk_parity", **kwargs
            ),
            default_param={
                "rows": [],
                "rebalance_frequency": "monthly",
                "target_gross_exposure": 1.0,
                "min_history": 3,
            },
            param_normalizer=require_risk_budgeting_param,
            description="Allocate across sleeves by inverse realized risk to approximate equal risk contribution.",
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
                    "description": "Declared rebalance cadence for allocation updates.",
                },
                {
                    "key": "target_gross_exposure",
                    "label": "Target gross exposure",
                    "type": "number",
                    "required": True,
                    "description": "Maximum gross exposure after weight normalization.",
                },
                {
                    "key": "min_history",
                    "label": "Minimum history",
                    "type": "integer",
                    "required": True,
                    "minimum": 2,
                    "description": "Minimum return observations required per sleeve.",
                },
            ),
            tags=("composite", "risk_overlay", "risk_parity"),
            category="composite",
            family="risk_overlay",
            subcategory="risk",
            warmup_period=3,
            input_domains=("multi_asset_panel",),
            asset_scope="portfolio",
            output_modes=("weights", "diagnostics"),
            composition_roles=("ensemble_member",),
        ),
        AlertAlgorithmSpec(
            key="volatility_targeting_overlay",
            name="Volatility Targeting Overlay",
            catalog_ref="combination:6",
            builder=lambda **kwargs: build_volatility_targeting_overlay_algorithm(
                algorithm_key="volatility_targeting_overlay", **kwargs
            ),
            default_param={
                "rows": [],
                "target_volatility": 0.10,
                "base_weight": 1.0,
                "min_history": 5,
                "max_leverage": 2.0,
                "min_leverage": 0.0,
            },
            param_normalizer=require_volatility_targeting_overlay_param,
            description="Scale portfolio exposure up or down to keep realized volatility near a target level.",
            param_schema=(
                {
                    "key": "rows",
                    "label": "Return rows",
                    "type": "array",
                    "required": True,
                    "description": "Timestamped rows containing portfolio return history windows.",
                },
                {
                    "key": "target_volatility",
                    "label": "Target volatility",
                    "type": "number",
                    "required": True,
                    "description": "Desired realized volatility level.",
                },
                {
                    "key": "base_weight",
                    "label": "Base weight",
                    "type": "number",
                    "required": True,
                    "description": "Base exposure before volatility scaling.",
                },
                {
                    "key": "min_history",
                    "label": "Minimum history",
                    "type": "integer",
                    "required": True,
                    "minimum": 2,
                    "description": "Minimum return observations required before scaling becomes active.",
                },
                {
                    "key": "max_leverage",
                    "label": "Max leverage",
                    "type": "number",
                    "required": True,
                    "description": "Upper cap on the volatility-targeted leverage multiplier.",
                },
                {
                    "key": "min_leverage",
                    "label": "Min leverage",
                    "type": "number",
                    "required": True,
                    "description": "Lower cap on the volatility-targeted leverage multiplier.",
                },
            ),
            tags=("composite", "risk_overlay", "volatility_targeting"),
            category="composite",
            family="risk_overlay",
            subcategory="volatility",
            warmup_period=5,
            input_domains=("multi_asset_panel",),
            asset_scope="portfolio",
            output_modes=("weights", "diagnostics"),
            composition_roles=("ensemble_member",),
        ),
    ]
    for spec in specs:
        register_algorithm(spec)
