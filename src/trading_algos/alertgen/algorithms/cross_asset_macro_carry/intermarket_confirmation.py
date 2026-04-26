from __future__ import annotations

from typing import Any

from trading_algos.alertgen.algorithms.cross_asset_macro_carry.base import (
    CrossAssetRankingAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.cross_asset_macro_carry.helpers import (
    _metric_from_fields,
    evaluate_cross_asset_ranking,
)
from trading_algos.data.panel_dataset import MultiAssetPanel


class IntermarketConfirmationAlertAlgorithm(CrossAssetRankingAlertAlgorithm):
    catalog_ref = "algorithm:83"


def build_intermarket_confirmation_algorithm(
    *,
    algorithm_key: str,
    symbol: str,
    alg_param: dict[str, Any],
) -> IntermarketConfirmationAlertAlgorithm:
    panel = MultiAssetPanel.from_rows(list(alg_param["rows"]))
    field_names = tuple(str(field_name) for field_name in alg_param["field_names"])
    rows = evaluate_cross_asset_ranking(
        panel,
        score_function=lambda _symbol, row: _metric_from_fields(row, field_names),
        rebalance_frequency=str(alg_param["rebalance_frequency"]),
        top_n=int(alg_param["top_n"]),
        bottom_n=int(alg_param.get("bottom_n", 0)),
        long_only=bool(alg_param["long_only"]),
        minimum_universe_size=int(alg_param["minimum_universe_size"]),
        score_label="confirmation_score",
    )
    return IntermarketConfirmationAlertAlgorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        alg_name="intermarket_confirmation",
        family="cross_asset_macro_carry",
        subcategory="intermarket",
        rows=rows,
    )
