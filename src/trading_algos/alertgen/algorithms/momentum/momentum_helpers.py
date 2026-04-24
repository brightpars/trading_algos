from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from trading_algos.contracts.portfolio_output import (
    PortfolioRebalancePoint,
    PortfolioWeightOutput,
    RankedAsset,
)
from trading_algos.data.panel_dataset import MultiAssetPanel
from trading_algos.data.universe_membership import universe_membership_for_rebalance
from trading_algos.rebalance.calendar import select_rebalance_timestamps
from trading_algos.rebalance.runner import build_rebalance_result


def clamp_unit(value: float) -> float:
    if value < -1.0:
        return -1.0
    if value > 1.0:
        return 1.0
    return value


def confirmation_state(previous_count: int, *, condition_met: bool) -> int:
    return previous_count + 1 if condition_met else 0


def simple_average(values: Sequence[float | None], window: int) -> list[float | None]:
    if window <= 0:
        raise ValueError("window must be positive")
    result: list[float | None] = []
    running_values: list[float] = []
    for value in values:
        if value is None:
            running_values.clear()
            result.append(None)
            continue
        running_values.append(value)
        if len(running_values) > window:
            running_values.pop(0)
        if len(running_values) == window:
            result.append(sum(running_values) / window)
        else:
            result.append(None)
    return result


def weighted_sum_components(
    components: list[list[float | None]], *, weights: list[float]
) -> list[float | None]:
    if len(components) != len(weights):
        raise ValueError("components and weights must have equal length")
    if not components:
        return []
    component_length = len(components[0])
    if any(len(component) != component_length for component in components):
        raise ValueError("all components must have equal length")
    result: list[float | None] = []
    for index in range(component_length):
        values = [component[index] for component in components]
        if any(value is None for value in values):
            result.append(None)
            continue
        total = 0.0
        for value, weight in zip(values, weights, strict=True):
            assert value is not None
            total += value * weight
        result.append(total)
    return result


def relative_volume(
    volumes: list[float], *, window: int
) -> tuple[list[float | None], list[float | None]]:
    averages = simple_average(volumes, window)
    rel_volume: list[float | None] = []
    for volume, baseline in zip(volumes, averages, strict=True):
        if baseline is None or baseline == 0.0:
            rel_volume.append(None)
            continue
        rel_volume.append(volume / baseline)
    return averages, rel_volume


@dataclass(frozen=True)
class MomentumSignalState:
    regime: str
    score: float
    bullish: bool
    bearish: bool
    primary_value: float | None
    signal_value: float | None
    threshold_value: float | None
    aligned_count: int
    reason_code: str


@dataclass(frozen=True)
class CrossSectionalMomentumRow:
    timestamp: str
    ranking: tuple[RankedAsset, ...]
    selected_symbols: tuple[str, ...]
    weights: dict[str, float]
    diagnostics: dict[str, object]


def trailing_return(closes: Sequence[float], window: int) -> float | None:
    if window <= 0:
        raise ValueError("window must be positive")
    if len(closes) <= window:
        return None
    start_price = closes[-window - 1]
    end_price = closes[-1]
    if start_price == 0.0:
        return None
    return ((end_price / start_price) - 1.0) * 100.0


def rank_cross_sectional_scores(
    scores: dict[str, float],
    *,
    top_n: int,
    bottom_n: int = 0,
    long_only: bool = True,
    defensive_symbol: str | None = None,
) -> tuple[tuple[RankedAsset, ...], tuple[str, ...], dict[str, float]]:
    ordered = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    ranking: list[RankedAsset] = []
    selected_symbols: list[str] = []
    weights: dict[str, float] = {}
    long_symbols = [symbol for symbol, _score in ordered[:top_n] if top_n > 0]
    short_symbols = (
        [symbol for symbol, _score in ordered[-bottom_n:]]
        if (bottom_n > 0 and not long_only)
        else []
    )
    if long_symbols:
        long_weight = 1.0 / len(long_symbols) if long_only else 0.5 / len(long_symbols)
        for symbol in long_symbols:
            weights[symbol] = long_weight
            selected_symbols.append(symbol)
    if short_symbols:
        short_weight = -0.5 / len(short_symbols)
        for symbol in short_symbols:
            weights[symbol] = short_weight
            selected_symbols.append(symbol)
    if not selected_symbols and defensive_symbol is not None:
        weights[defensive_symbol] = 1.0
        selected_symbols.append(defensive_symbol)
    selected_set = set(selected_symbols)
    for rank, (symbol, score) in enumerate(ordered, start=1):
        if symbol in long_symbols:
            side = "long"
        elif symbol in short_symbols:
            side = "short"
        else:
            side = "neutral"
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
    return tuple(ranking), tuple(selected_symbols), weights


def evaluate_cross_sectional_momentum(
    panel: MultiAssetPanel,
    *,
    lookback_window: int,
    top_n: int,
    bottom_n: int = 0,
    rebalance_frequency: str = "monthly",
    long_only: bool = True,
    score_adjustments: dict[str, float] | None = None,
    absolute_momentum_threshold: float | None = None,
    defensive_symbol: str | None = None,
) -> tuple[CrossSectionalMomentumRow, ...]:
    adjustments = score_adjustments or {}
    close_map = panel.closes_by_symbol()
    schedule = select_rebalance_timestamps(
        panel.timestamps(), frequency=rebalance_frequency
    )
    rows: list[CrossSectionalMomentumRow] = []
    rebalance_points: list[PortfolioRebalancePoint] = []
    for timestamp in schedule:
        eligible_universe = universe_membership_for_rebalance(
            panel, rebalance_timestamp=timestamp
        )
        scores: dict[str, float] = {}
        warmup_symbols: list[str] = []
        absolute_pass_count = 0
        for symbol in eligible_universe:
            history = [
                close for ts, close in close_map.get(symbol, []) if ts <= timestamp
            ]
            score = trailing_return(history, lookback_window)
            if score is None:
                warmup_symbols.append(symbol)
                continue
            adjusted_score = score + float(adjustments.get(symbol, 0.0))
            if (
                absolute_momentum_threshold is not None
                and adjusted_score < absolute_momentum_threshold
            ):
                continue
            absolute_pass_count += 1
            scores[symbol] = adjusted_score
        ranking, selected_symbols, weights = rank_cross_sectional_scores(
            scores,
            top_n=top_n,
            bottom_n=bottom_n,
            long_only=long_only,
            defensive_symbol=defensive_symbol,
        )
        diagnostics = {
            "lookback_window": lookback_window,
            "eligible_universe_size": len(eligible_universe),
            "scored_universe_size": len(scores),
            "warmup_pending_symbols": tuple(sorted(warmup_symbols)),
            "absolute_pass_count": absolute_pass_count,
            "selected_count": len(selected_symbols),
            "rebalance_frequency": rebalance_frequency,
        }
        row = CrossSectionalMomentumRow(
            timestamp=timestamp,
            ranking=ranking,
            selected_symbols=selected_symbols,
            weights=weights,
            diagnostics=diagnostics,
        )
        rows.append(row)
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


def build_portfolio_weight_output(
    algorithm_key: str,
    rows: Sequence[CrossSectionalMomentumRow],
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
            "family": "momentum",
            "subcategory": subcategory,
            "catalog_ref": catalog_ref,
            "reporting_mode": "rebalance_report",
            "supports_composition": True,
            "output_contract_version": "1.0",
        },
    )
