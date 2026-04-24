from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from trading_algos.contracts.portfolio_output import (
    PortfolioRebalancePoint,
    PortfolioWeightOutput,
    RankedAsset,
)
from trading_algos.data.panel_dataset import MultiAssetPanel, PanelRow
from trading_algos.data.universe_membership import universe_membership_for_rebalance
from trading_algos.rebalance.calendar import select_rebalance_timestamps
from trading_algos.rebalance.runner import build_rebalance_result


@dataclass(frozen=True)
class FactorStrategyRow:
    timestamp: str
    ranking: tuple[RankedAsset, ...]
    selected_symbols: tuple[str, ...]
    weights: dict[str, float]
    diagnostics: dict[str, object]


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_metric_value(row: PanelRow, field_names: Sequence[str]) -> float | None:
    extras = row.extras or {}
    values = [_coerce_float(extras.get(field_name)) for field_name in field_names]
    numeric_values = [value for value in values if value is not None]
    if not numeric_values:
        return None
    return sum(numeric_values) / len(numeric_values)


def _rank_factor_scores(
    scores: dict[str, float],
    *,
    top_n: int,
    bottom_n: int,
    long_only: bool,
) -> tuple[tuple[RankedAsset, ...], tuple[str, ...], dict[str, float]]:
    ordered = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    long_symbols = [symbol for symbol, _score in ordered[:top_n]]
    short_symbols = (
        [symbol for symbol, _score in ordered[-bottom_n:]]
        if bottom_n > 0 and not long_only
        else []
    )
    weights: dict[str, float] = {}
    if long_symbols:
        long_weight = 1.0 / len(long_symbols) if long_only else 0.5 / len(long_symbols)
        for symbol in long_symbols:
            weights[symbol] = long_weight
    if short_symbols:
        short_weight = -0.5 / len(short_symbols)
        for symbol in short_symbols:
            weights[symbol] = short_weight

    selected_symbols = tuple([*long_symbols, *short_symbols])
    selected_set = set(selected_symbols)
    ranking: list[RankedAsset] = []
    for rank, (symbol, score) in enumerate(ordered, start=1):
        side = "neutral"
        if symbol in long_symbols:
            side = "long"
        elif symbol in short_symbols:
            side = "short"
        ranking.append(
            RankedAsset(
                symbol=symbol,
                rank=rank,
                score=score,
                weight=weights.get(symbol, 0.0),
                selected=symbol in selected_set,
                side=side,
            )
        )
    return tuple(ranking), selected_symbols, weights


def evaluate_factor_strategy(
    panel: MultiAssetPanel,
    *,
    factor_name: str,
    field_names: Sequence[str],
    higher_is_better: bool,
    rebalance_frequency: str,
    top_n: int,
    bottom_n: int,
    long_only: bool,
    minimum_universe_size: int,
) -> tuple[FactorStrategyRow, ...]:
    schedule = select_rebalance_timestamps(
        panel.timestamps(), frequency=rebalance_frequency
    )
    rows: list[FactorStrategyRow] = []
    rebalance_points: list[PortfolioRebalancePoint] = []
    for timestamp in schedule:
        universe = universe_membership_for_rebalance(
            panel, rebalance_timestamp=timestamp
        )
        latest_rows = panel.latest_row_by_symbol_on(timestamp, universe)
        raw_scores: dict[str, float] = {}
        missing_metric_symbols: list[str] = []
        for symbol in universe:
            latest_row = latest_rows.get(symbol)
            if latest_row is None:
                missing_metric_symbols.append(symbol)
                continue
            metric_value = _extract_metric_value(latest_row, field_names)
            if metric_value is None:
                missing_metric_symbols.append(symbol)
                continue
            raw_scores[symbol] = metric_value

        scored_universe_size = len(raw_scores)
        ranking: tuple[RankedAsset, ...] = ()
        selected_symbols: tuple[str, ...] = ()
        weights: dict[str, float] = {}
        selection_reason = "selection_ready"
        normalized_scores: dict[str, float] = {}
        if scored_universe_size < minimum_universe_size:
            selection_reason = "warmup_pending"
        else:
            normalized_scores = {
                symbol: (score if higher_is_better else -score)
                for symbol, score in raw_scores.items()
            }
            ranking, selected_symbols, weights = _rank_factor_scores(
                normalized_scores,
                top_n=top_n,
                bottom_n=bottom_n,
                long_only=long_only,
            )
            if not selected_symbols:
                selection_reason = "no_selection"

        diagnostics = {
            "factor_name": factor_name,
            "field_names": tuple(field_names),
            "higher_is_better": higher_is_better,
            "rebalance_frequency": rebalance_frequency,
            "eligible_universe_size": len(universe),
            "scored_universe_size": scored_universe_size,
            "missing_metric_symbols": tuple(sorted(missing_metric_symbols)),
            "warmup_pending_symbols": tuple(sorted(missing_metric_symbols)),
            "warmup_ready": scored_universe_size >= minimum_universe_size,
            "selection_reason": selection_reason,
            "selected_count": len(selected_symbols),
            "raw_scores": raw_scores,
            "normalized_scores": normalized_scores,
        }
        strategy_row = FactorStrategyRow(
            timestamp=timestamp,
            ranking=ranking,
            selected_symbols=selected_symbols,
            weights=weights,
            diagnostics=diagnostics,
        )
        rows.append(strategy_row)
        rebalance_points.append(
            PortfolioRebalancePoint(
                timestamp=timestamp,
                ranking=ranking,
                selected_symbols=selected_symbols,
                weights=weights,
                diagnostics=diagnostics,
            )
        )
    _ = build_rebalance_result(rebalance_points, schedule=schedule)
    return tuple(rows)


def build_factor_portfolio_weight_output(
    algorithm_key: str,
    rows: Sequence[FactorStrategyRow],
    *,
    catalog_ref: str,
    subcategory: str,
) -> PortfolioWeightOutput:
    return PortfolioWeightOutput(
        algorithm_key=algorithm_key,
        rebalances=tuple(
            PortfolioRebalancePoint(
                timestamp=row.timestamp,
                ranking=row.ranking,
                selected_symbols=row.selected_symbols,
                weights=row.weights,
                diagnostics=row.diagnostics,
            )
            for row in rows
        ),
        metadata={
            "family": "factor_risk_premia",
            "subcategory": subcategory,
            "catalog_ref": catalog_ref,
            "reporting_mode": "rebalance_report",
            "supports_composition": True,
            "output_contract_version": "1.0",
        },
    )
