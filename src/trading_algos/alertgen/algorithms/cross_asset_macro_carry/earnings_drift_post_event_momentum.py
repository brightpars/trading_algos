from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from trading_algos.alertgen.algorithms.cross_asset_macro_carry.base import (
    CrossAssetRankingAlertAlgorithm,
)
from trading_algos.alertgen.algorithms.cross_asset_macro_carry.helpers import (
    evaluate_cross_asset_ranking,
)
from trading_algos.data.panel_dataset import MultiAssetPanel, PanelRow


def _build_event_lookup(
    event_rows: list[dict[str, object]],
) -> dict[str, list[dict[str, object]]]:
    event_lookup: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in event_rows:
        event_lookup[str(row["symbol"])].append(dict(row))
    for symbol in event_lookup:
        event_lookup[symbol].sort(key=lambda item: str(item["event_timestamp"]))
    return event_lookup


def _parse_timestamp(value: str, *, end_of_day: bool = False) -> datetime:
    normalized = value.strip().replace("T", " ")
    if len(normalized) == 10:
        normalized = f"{normalized} {'23:59:59' if end_of_day else '00:00:00'}"
    return datetime.fromisoformat(normalized)


class EarningsDriftPostEventMomentumAlertAlgorithm(CrossAssetRankingAlertAlgorithm):
    catalog_ref = "algorithm:85"


def build_earnings_drift_post_event_momentum_algorithm(
    *,
    algorithm_key: str,
    symbol: str,
    alg_param: dict[str, Any],
) -> EarningsDriftPostEventMomentumAlertAlgorithm:
    panel = MultiAssetPanel.from_rows(list(alg_param["rows"]))
    event_lookup = _build_event_lookup(list(alg_param["event_rows"]))
    surprise_field = str(alg_param["surprise_field"])
    post_event_window_days = int(alg_param["post_event_window_days"])

    def _score(symbol_key: str, row: PanelRow) -> float | None:
        symbol_events = event_lookup.get(symbol_key, [])
        row_ts = _parse_timestamp(row.timestamp, end_of_day=True)
        eligible_events = [
            event
            for event in symbol_events
            if _parse_timestamp(str(event["event_timestamp"])) <= row_ts
        ]
        if not eligible_events:
            return None
        latest_event = eligible_events[-1]
        event_ts = _parse_timestamp(str(latest_event["event_timestamp"]))
        if row_ts < event_ts:
            return None
        if (row_ts.date() - event_ts.date()).days > post_event_window_days:
            return None
        surprise_value = latest_event.get(surprise_field)
        if isinstance(surprise_value, bool):
            return float(surprise_value)
        if isinstance(surprise_value, int | float | str):
            try:
                return float(surprise_value)
            except ValueError:
                return None
        return None

    rows = evaluate_cross_asset_ranking(
        panel,
        score_function=_score,
        rebalance_frequency=str(alg_param["rebalance_frequency"]),
        top_n=int(alg_param["top_n"]),
        bottom_n=int(alg_param.get("bottom_n", 0)),
        long_only=bool(alg_param["long_only"]),
        minimum_universe_size=int(alg_param["minimum_universe_size"]),
        score_label="event_drift_score",
    )
    return EarningsDriftPostEventMomentumAlertAlgorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        alg_name="earnings_drift_post_event_momentum",
        family="cross_asset_macro_carry",
        subcategory="earnings",
        rows=rows,
    )
