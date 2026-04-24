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


def _extract_weighted_metric_components(
    row: PanelRow,
    *,
    field_names: Sequence[str],
    field_weights: Sequence[float] | None,
    lower_is_better_fields: frozenset[str],
) -> tuple[dict[str, float], dict[str, float], float] | None:
    extras = row.extras or {}
    components: dict[str, float] = {}
    oriented_components: dict[str, float] = {}
    weighted_total = 0.0
    total_weight = 0.0
    resolved_weights = (
        tuple(field_weights)
        if field_weights is not None
        else tuple(1.0 for _field_name in field_names)
    )
    for field_name, field_weight in zip(field_names, resolved_weights, strict=True):
        metric_value = _coerce_float(extras.get(field_name))
        if metric_value is None:
            continue
        components[field_name] = metric_value
        oriented_value = (
            -metric_value if field_name in lower_is_better_fields else metric_value
        )
        oriented_components[field_name] = oriented_value
        weighted_total += oriented_value * field_weight
        total_weight += field_weight
    if not components or total_weight <= 0.0:
        return None
    return components, oriented_components, weighted_total / total_weight


def _rank_factor_scores(
    scores: dict[str, float],
    *,
    raw_scores: dict[str, float],
    top_n: int,
    bottom_n: int,
    long_only: bool,
    weighting_mode: str,
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
        if weighting_mode == "inverse_metric":
            inverse_values = {
                symbol: 1.0 / max(raw_scores.get(symbol, 0.0), 1e-9)
                for symbol in long_symbols
            }
            inverse_total = sum(inverse_values.values())
            long_exposure = 1.0 if long_only else 0.5
            for symbol in long_symbols:
                weights[symbol] = long_exposure * (
                    inverse_values[symbol] / inverse_total
                )
        else:
            long_weight = (
                1.0 / len(long_symbols) if long_only else 0.5 / len(long_symbols)
            )
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


def _clamp_unit_interval(value: float) -> float:
    return max(0.0, min(1.0, value))


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
    target_value: float | None = None,
    weighting_mode: str = "equal_weight",
    field_weights: Sequence[float] | None = None,
    lower_is_better_fields: Sequence[str] = (),
) -> tuple[FactorStrategyRow, ...]:
    schedule = select_rebalance_timestamps(
        panel.timestamps(), frequency=rebalance_frequency
    )
    rows: list[FactorStrategyRow] = []
    rebalance_points: list[PortfolioRebalancePoint] = []
    lower_is_better_field_set = frozenset(lower_is_better_fields)
    for timestamp in schedule:
        universe = universe_membership_for_rebalance(
            panel, rebalance_timestamp=timestamp
        )
        latest_rows = panel.latest_row_by_symbol_on(timestamp, universe)
        raw_scores: dict[str, float] = {}
        component_scores: dict[str, dict[str, float]] = {}
        oriented_component_scores: dict[str, dict[str, float]] = {}
        missing_metric_symbols: list[str] = []
        for symbol in universe:
            latest_row = latest_rows.get(symbol)
            if latest_row is None:
                missing_metric_symbols.append(symbol)
                continue
            weighted_components = _extract_weighted_metric_components(
                latest_row,
                field_names=field_names,
                field_weights=field_weights,
                lower_is_better_fields=lower_is_better_field_set,
            )
            if weighted_components is None:
                missing_metric_symbols.append(symbol)
                continue
            components, oriented_components, metric_value = weighted_components
            raw_scores[symbol] = metric_value
            component_scores[symbol] = components
            oriented_component_scores[symbol] = oriented_components

        scored_universe_size = len(raw_scores)
        ranking: tuple[RankedAsset, ...] = ()
        selected_symbols: tuple[str, ...] = ()
        weights: dict[str, float] = {}
        selection_reason = "selection_ready"
        normalized_scores: dict[str, float] = {}
        selection_strength = 0.0
        top_ranked_symbol: str | None = None
        top_ranked_score: float | None = None
        gross_exposure = 0.0
        net_exposure = 0.0
        long_count = 0
        short_count = 0
        if scored_universe_size < minimum_universe_size:
            selection_reason = "warmup_pending"
        else:
            if target_value is not None:
                normalized_scores = {
                    symbol: -abs(score - target_value)
                    for symbol, score in raw_scores.items()
                }
            else:
                normalized_scores = {
                    symbol: (score if higher_is_better else -score)
                    for symbol, score in raw_scores.items()
                }
            ranking, selected_symbols, weights = _rank_factor_scores(
                normalized_scores,
                raw_scores=raw_scores,
                top_n=top_n,
                bottom_n=bottom_n,
                long_only=long_only,
                weighting_mode=weighting_mode,
            )
            if ranking:
                top_ranked_symbol = ranking[0].symbol
                top_ranked_score = ranking[0].score
                score_values = [asset.score for asset in ranking]
                min_score = min(score_values)
                max_score = max(score_values)
                if max_score > min_score and top_ranked_score is not None:
                    selection_strength = _clamp_unit_interval(
                        (top_ranked_score - min_score) / (max_score - min_score)
                    )
                elif selected_symbols:
                    selection_strength = 1.0
            gross_exposure = sum(abs(weight) for weight in weights.values())
            net_exposure = sum(weights.values())
            long_count = sum(1 for weight in weights.values() if weight > 0.0)
            short_count = sum(1 for weight in weights.values() if weight < 0.0)
            if not selected_symbols:
                selection_reason = "no_selection"

        diagnostics = {
            "factor_name": factor_name,
            "field_names": tuple(field_names),
            "higher_is_better": higher_is_better,
            "target_value": target_value,
            "weighting_mode": weighting_mode,
            "field_weights": tuple(field_weights)
            if field_weights is not None
            else None,
            "lower_is_better_fields": tuple(sorted(lower_is_better_field_set)),
            "rebalance_frequency": rebalance_frequency,
            "eligible_universe_size": len(universe),
            "scored_universe_size": scored_universe_size,
            "missing_metric_symbols": tuple(sorted(missing_metric_symbols)),
            "warmup_pending_symbols": tuple(sorted(missing_metric_symbols)),
            "warmup_ready": scored_universe_size >= minimum_universe_size,
            "selection_reason": selection_reason,
            "selection_strength": selection_strength,
            "selected_count": len(selected_symbols),
            "long_count": long_count,
            "short_count": short_count,
            "gross_exposure": gross_exposure,
            "net_exposure": net_exposure,
            "top_ranked_symbol": top_ranked_symbol,
            "top_ranked_score": top_ranked_score,
            "raw_scores": raw_scores,
            "normalized_scores": normalized_scores,
            "component_scores": component_scores,
            "oriented_component_scores": oriented_component_scores,
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
    family: str,
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
            "family": family,
            "subcategory": subcategory,
            "catalog_ref": catalog_ref,
            "reporting_mode": "rebalance_report",
            "supports_composition": True,
            "output_contract_version": "1.0",
        },
    )
