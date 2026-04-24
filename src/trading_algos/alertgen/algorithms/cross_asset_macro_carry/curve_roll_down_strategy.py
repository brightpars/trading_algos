from __future__ import annotations

from typing import Any

from trading_algos.alertgen.algorithms.cross_asset_macro_carry.base import (
    CrossAssetMultiLegAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.cross_asset_macro_carry.helpers import (
    _coerce_float,
    evaluate_multi_leg_strategy,
)
from trading_algos.data.panel_dataset import MultiAssetPanel, PanelRow


def _roll_down_spread(
    row: PanelRow, *, front_leg_field: str, back_leg_field: str
) -> tuple[float, dict[str, object]] | None:
    extras = row.extras or {}
    front_roll = _coerce_float(extras.get(front_leg_field))
    back_roll = _coerce_float(extras.get(back_leg_field))
    if front_roll is None or back_roll is None:
        return None
    spread_value = front_roll - back_roll
    return spread_value, {
        "front_leg_field": front_leg_field,
        "back_leg_field": back_leg_field,
        "front_roll": front_roll,
        "back_roll": back_roll,
        "roll_down_spread": spread_value,
    }


class CurveRollDownStrategyAlertAlgorithm(CrossAssetMultiLegAlertAlgorithm):
    catalog_ref = "algorithm:80"


def build_curve_roll_down_strategy_algorithm(
    *,
    algorithm_key: str,
    symbol: str,
    alg_param: dict[str, Any],
) -> CurveRollDownStrategyAlertAlgorithm:
    panel = MultiAssetPanel.from_rows(list(alg_param["rows"]))
    front_leg_field = str(alg_param["front_leg_field"])
    back_leg_field = str(alg_param["back_leg_field"])
    rows = evaluate_multi_leg_strategy(
        panel,
        spread_function=lambda _symbol, row: _roll_down_spread(
            row,
            front_leg_field=front_leg_field,
            back_leg_field=back_leg_field,
        ),
        rebalance_frequency=str(alg_param["rebalance_frequency"]),
    )
    return CurveRollDownStrategyAlertAlgorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        alg_name="curve_roll_down_strategy",
        family="cross_asset_macro_carry",
        subcategory="curve",
        rows=rows,
    )
