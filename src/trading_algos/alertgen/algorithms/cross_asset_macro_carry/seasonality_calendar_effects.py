from __future__ import annotations

from typing import Any

from trading_algos.alertgen.algorithms.cross_asset_macro_carry.base import (
    CrossAssetRankingAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.cross_asset_macro_carry.helpers import (
    _calendar_features,
    evaluate_cross_asset_ranking,
)
from trading_algos.data.panel_dataset import MultiAssetPanel, PanelRow


def _seasonality_score(row: PanelRow, *, calendar_pattern: str) -> float | None:
    features = _calendar_features(row.timestamp)
    if calendar_pattern == "turn_of_month":
        return 1.0 if bool(features["is_turn_of_month"]) else 0.0
    if calendar_pattern == "month_end":
        return 1.0 if bool(features["is_month_end"]) else 0.0
    if calendar_pattern == "monday":
        return 1.0 if bool(features["is_monday"]) else 0.0
    if calendar_pattern == "friday":
        return 1.0 if bool(features["is_friday"]) else 0.0
    return None


class SeasonalityCalendarEffectsAlertAlgorithm(CrossAssetRankingAlertAlgorithm):
    catalog_ref = "algorithm:84"


def build_seasonality_calendar_effects_algorithm(
    *,
    algorithm_key: str,
    symbol: str,
    alg_param: dict[str, Any],
) -> SeasonalityCalendarEffectsAlertAlgorithm:
    panel = MultiAssetPanel.from_rows(list(alg_param["rows"]))
    calendar_pattern = str(alg_param["calendar_pattern"])
    rows = evaluate_cross_asset_ranking(
        panel,
        score_function=lambda _symbol, row: _seasonality_score(
            row, calendar_pattern=calendar_pattern
        ),
        rebalance_frequency=str(alg_param["rebalance_frequency"]),
        top_n=int(alg_param["top_n"]),
        bottom_n=int(alg_param.get("bottom_n", 0)),
        long_only=bool(alg_param["long_only"]),
        minimum_universe_size=int(alg_param["minimum_universe_size"]),
        score_label="calendar_score",
    )
    return SeasonalityCalendarEffectsAlertAlgorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        alg_name="seasonality_calendar_effects",
        family="cross_asset_macro_carry",
        subcategory="seasonality",
        rows=rows,
    )
