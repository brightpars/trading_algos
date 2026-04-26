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


def _commodity_roll_yield(
    row: PanelRow, *, front_leg_field: str, back_leg_field: str
) -> tuple[float, dict[str, object]] | None:
    extras = row.extras or {}
    near_contract = _coerce_float(extras.get(front_leg_field))
    far_contract = _coerce_float(extras.get(back_leg_field))
    if near_contract is None or far_contract is None:
        return None
    spread_value = near_contract - far_contract
    return spread_value, {
        "front_leg_field": front_leg_field,
        "back_leg_field": back_leg_field,
        "near_contract": near_contract,
        "far_contract": far_contract,
        "roll_yield": spread_value,
    }


class CommodityTermStructureRollYieldAlertAlgorithm(CrossAssetMultiLegAlertAlgorithm):
    catalog_ref = "algorithm:81"


def build_commodity_term_structure_roll_yield_algorithm(
    *,
    algorithm_key: str,
    symbol: str,
    alg_param: dict[str, Any],
) -> CommodityTermStructureRollYieldAlertAlgorithm:
    panel = MultiAssetPanel.from_rows(list(alg_param["rows"]))
    front_leg_field = str(alg_param["front_leg_field"])
    back_leg_field = str(alg_param["back_leg_field"])
    rows = evaluate_multi_leg_strategy(
        panel,
        spread_function=lambda _symbol, row: _commodity_roll_yield(
            row,
            front_leg_field=front_leg_field,
            back_leg_field=back_leg_field,
        ),
        rebalance_frequency=str(alg_param["rebalance_frequency"]),
    )
    return CommodityTermStructureRollYieldAlertAlgorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        alg_name="commodity_term_structure_roll_yield",
        family="cross_asset_macro_carry",
        subcategory="commodity",
        rows=rows,
    )
