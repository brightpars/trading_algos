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


def _curve_spread(
    row: PanelRow, *, front_leg_field: str, back_leg_field: str
) -> tuple[float, dict[str, object]] | None:
    extras = row.extras or {}
    front_rate = _coerce_float(extras.get(front_leg_field))
    back_rate = _coerce_float(extras.get(back_leg_field))
    if front_rate is None or back_rate is None:
        return None
    spread_value = back_rate - front_rate
    return spread_value, {
        "front_leg_field": front_leg_field,
        "back_leg_field": back_leg_field,
        "front_rate": front_rate,
        "back_rate": back_rate,
        "curve_spread": spread_value,
    }


class YieldCurveSteepenerFlattenerAlertAlgorithm(CrossAssetMultiLegAlertAlgorithm):
    catalog_ref = "algorithm:79"


def build_yield_curve_steepener_flattener_algorithm(
    *,
    algorithm_key: str,
    symbol: str,
    alg_param: dict[str, Any],
) -> YieldCurveSteepenerFlattenerAlertAlgorithm:
    panel = MultiAssetPanel.from_rows(list(alg_param["rows"]))
    front_leg_field = str(alg_param["front_leg_field"])
    back_leg_field = str(alg_param["back_leg_field"])
    rows = evaluate_multi_leg_strategy(
        panel,
        spread_function=lambda _symbol, row: _curve_spread(
            row,
            front_leg_field=front_leg_field,
            back_leg_field=back_leg_field,
        ),
        rebalance_frequency=str(alg_param["rebalance_frequency"]),
    )
    return YieldCurveSteepenerFlattenerAlertAlgorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        alg_name="yield_curve_steepener_flattener",
        family="cross_asset_macro_carry",
        subcategory="yield",
        rows=rows,
    )
