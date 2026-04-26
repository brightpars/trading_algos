from trading_algos.algorithmspec import AlertAlgorithmSpec, register_algorithm
from trading_algos.alertgen.algorithms.composite.aggregate import agreegate_algs
from trading_algos.alertgen.algorithms.composite.adaptive_state_based.catalog import (
    register_adaptive_state_based_alert_algorithms,
)
from trading_algos.alertgen.algorithms.composite.optimization_based.catalog import (
    register_optimization_based_alert_algorithms,
)
from trading_algos.alertgen.algorithms.composite.machine_learning_ensemble.catalog import (
    register_machine_learning_ensemble_alert_algorithms,
)
from trading_algos.alertgen.algorithms.composite.reinforcement_learning.catalog import (
    register_reinforcement_learning_alert_algorithms,
)
from trading_algos.alertgen.algorithms.composite.risk_overlay.catalog import (
    register_risk_overlay_alert_algorithms,
)
from trading_algos.alertgen.algorithms.composite.rule_based_combination.catalog import (
    register_rule_based_combination_alert_algorithms,
)
from trading_algos.alertgen.algorithms.trend.boundary_breakout import (
    LowAnchoredBoundaryBreakoutAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.trend.channel_breakout import (
    CloseHighChannelBreakoutAlertAlgorithm,
)
from trading_algos.alertgen.core.validation import (
    require_buy_sell_window_param,
    require_window_param,
)


def _build_aggregate_boundary_and_channel(
    symbol, report_base_path, alg_param, **_kwargs
):
    return agreegate_algs(
        symbol,
        report_base_path=report_base_path,
        buy_algs_obj_list=[
            LowAnchoredBoundaryBreakoutAlertAlgorithm(
                symbol, report_base_path=report_base_path
            )
        ],
        sell_algs_obj_list=[
            CloseHighChannelBreakoutAlertAlgorithm(
                symbol,
                report_base_path=report_base_path,
                wlen=alg_param["window"],
            ),
            LowAnchoredBoundaryBreakoutAlertAlgorithm(
                symbol, report_base_path=report_base_path
            ),
        ],
    )


def _build_aggregate_channel_dual_window(
    symbol, report_base_path, alg_param, **_kwargs
):
    return agreegate_algs(
        symbol,
        report_base_path=report_base_path,
        buy_algs_obj_list=[
            CloseHighChannelBreakoutAlertAlgorithm(
                symbol,
                report_base_path=report_base_path,
                wlen=alg_param["buy_window"],
            )
        ],
        sell_algs_obj_list=[
            CloseHighChannelBreakoutAlertAlgorithm(
                symbol,
                report_base_path=report_base_path,
                wlen=alg_param["sell_window"],
            )
        ],
    )


def register_composite_alert_algorithms() -> None:
    register_rule_based_combination_alert_algorithms()
    register_risk_overlay_alert_algorithms()
    register_optimization_based_alert_algorithms()
    register_adaptive_state_based_alert_algorithms()
    register_machine_learning_ensemble_alert_algorithms()
    register_reinforcement_learning_alert_algorithms()
    specs = [
        AlertAlgorithmSpec(
            key="aggregate_boundary_and_channel",
            name="Aggregate Boundary and Channel",
            catalog_ref="algorithm:93",
            builder=_build_aggregate_boundary_and_channel,
            default_param={"window": 30},
            param_normalizer=require_window_param,
            description="Aggregate strategy combining low-anchored boundary and close/high channel breakouts.",
            param_schema=(
                {
                    "key": "window",
                    "label": "Window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Window used by the channel-breakout portion of the aggregate strategy.",
                },
            ),
            tags=("aggregate", "ensemble"),
            category="aggregate",
            family="composite",
            subcategory="ensemble",
            warmup_period=30,
            composition_roles=("ensemble_member",),
        ),
        AlertAlgorithmSpec(
            key="aggregate_channel_dual_window",
            name="Aggregate Channel Dual Window",
            catalog_ref="algorithm:93",
            builder=_build_aggregate_channel_dual_window,
            default_param={"buy_window": 20, "sell_window": 30},
            param_normalizer=require_buy_sell_window_param,
            description="Aggregate strategy with separate buy/sell lookback windows.",
            param_schema=(
                {
                    "key": "buy_window",
                    "label": "Buy window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Window used for the buy-side breakout calculation.",
                },
                {
                    "key": "sell_window",
                    "label": "Sell window",
                    "type": "integer",
                    "required": True,
                    "minimum": 1,
                    "description": "Window used for the sell-side breakout calculation.",
                },
            ),
            tags=("aggregate", "ensemble"),
            category="aggregate",
            family="composite",
            subcategory="ensemble",
            warmup_period=30,
            composition_roles=("ensemble_member",),
        ),
    ]
    for spec in specs:
        register_algorithm(spec)
