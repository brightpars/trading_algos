from __future__ import annotations

from typing import Any

from trading_algos.alertgen.algorithms.event_driven.base import (
    EventDrivenAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.event_driven.helpers import (
    evaluate_event_rows,
    extract_expected_buy_flow,
)
from trading_algos.data.panel_dataset import MultiAssetPanel
from trading_algos.events import EventCalendar, EventWindowDefinition


class IndexRebalancingEffectAlertAlgorithm(EventDrivenAlertAlgorithm):
    catalog_ref = "algorithm:120"


def build_index_rebalancing_effect_strategy_algorithm(
    *,
    algorithm_key: str,
    symbol: str,
    alg_param: dict[str, Any],
) -> IndexRebalancingEffectAlertAlgorithm:
    panel = MultiAssetPanel.from_rows(list(alg_param["rows"]))
    panel_rows = tuple(row for row in panel.rows if row.symbol == symbol)
    calendar = EventCalendar.from_rows(list(alg_param["event_rows"]))
    event_value_field = str(alg_param["event_value_field"])
    expected_direction_field = str(
        alg_param.get("expected_direction_field", "expected_direction")
    )
    minimum_score_threshold = float(alg_param.get("minimum_score_threshold", 0.0))
    rows = evaluate_event_rows(
        panel_rows=panel_rows,
        calendar=calendar,
        window=EventWindowDefinition(
            pre_event_days=int(alg_param.get("pre_event_window_days", 0)),
            post_event_days=int(alg_param.get("post_event_window_days", 0)),
        ),
        event_value_label=event_value_field,
        bullish_phase=str(alg_param["bullish_phase"]),
        event_value_function=lambda _row, event_metadata: extract_expected_buy_flow(
            event_metadata,
            event_value_field=event_value_field,
            expected_direction_field=expected_direction_field,
            minimum_score_threshold=minimum_score_threshold,
        ),
    )
    return IndexRebalancingEffectAlertAlgorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        alg_name="index_rebalancing_effect_strategy",
        family="event_driven",
        subcategory="index",
        rows=rows,
    )
