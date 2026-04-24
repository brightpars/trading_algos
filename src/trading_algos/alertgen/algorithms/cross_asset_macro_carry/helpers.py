from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, Mapping, Sequence

from trading_algos.alertgen.contracts.outputs import (
    AlertAlgorithmOutput,
    AlertSeriesPoint,
    NormalizedChildOutput,
)
from trading_algos.contracts.multi_leg_output import (
    MultiLegOutput,
    MultiLegPosition,
    MultiLegRebalancePoint,
)
from trading_algos.contracts.portfolio_output import (
    PortfolioRebalancePoint,
    PortfolioWeightOutput,
    RankedAsset,
)
from trading_algos.data.panel_dataset import MultiAssetPanel, PanelRow
from trading_algos.data.universe_membership import universe_membership_for_rebalance
from trading_algos.rebalance.calendar import select_rebalance_timestamps
from trading_algos.rebalance.runner import build_rebalance_result


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, value))


def _metric_from_fields(row: PanelRow, field_names: Sequence[str]) -> float | None:
    extras = row.extras or {}
    values = [_coerce_float(extras.get(field_name)) for field_name in field_names]
    numeric_values = [value for value in values if value is not None]
    if not numeric_values:
        return None
    return sum(numeric_values) / len(numeric_values)


def _calendar_features(timestamp: str) -> dict[str, object]:
    parsed = date.fromisoformat(str(timestamp)[:10])
    day_of_month = parsed.day
    weekday = parsed.weekday()
    return {
        "month": parsed.month,
        "day_of_month": day_of_month,
        "weekday": weekday,
        "is_month_start": day_of_month <= 3,
        "is_month_end": day_of_month >= 27,
        "is_turn_of_month": day_of_month <= 3 or day_of_month >= 27,
        "is_monday": weekday == 0,
        "is_friday": weekday == 4,
    }


@dataclass(frozen=True)
class CrossAssetRow:
    timestamp: str
    ranking: tuple[RankedAsset, ...]
    selected_symbols: tuple[str, ...]
    weights: dict[str, float]
    diagnostics: dict[str, object]


@dataclass(frozen=True)
class MultiLegRow:
    timestamp: str
    spread_value: float
    legs: tuple[MultiLegPosition, ...]
    diagnostics: dict[str, object]


ScoreFunction = Callable[[str, PanelRow], float | None]
SpreadFunction = Callable[[str, PanelRow], tuple[float, dict[str, object]] | None]


def rank_scores(
    scores: Mapping[str, float],
    *,
    top_n: int,
    bottom_n: int = 0,
    long_only: bool = True,
) -> tuple[tuple[RankedAsset, ...], tuple[str, ...], dict[str, float]]:
    ordered = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    long_symbols = [symbol for symbol, _score in ordered[:top_n] if top_n > 0]
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
    ranking = tuple(
        RankedAsset(
            symbol=symbol,
            rank=rank,
            score=score,
            weight=weights.get(symbol, 0.0),
            selected=symbol in selected_set,
            side=(
                "long"
                if symbol in long_symbols
                else "short"
                if symbol in short_symbols
                else "neutral"
            ),
        )
        for rank, (symbol, score) in enumerate(ordered, start=1)
    )
    return ranking, selected_symbols, weights


def evaluate_cross_asset_ranking(
    panel: MultiAssetPanel,
    *,
    score_function: ScoreFunction,
    rebalance_frequency: str,
    top_n: int,
    bottom_n: int = 0,
    long_only: bool = True,
    minimum_universe_size: int = 2,
    score_label: str,
) -> tuple[CrossAssetRow, ...]:
    schedule = select_rebalance_timestamps(
        panel.timestamps(), frequency=rebalance_frequency
    )
    rows: list[CrossAssetRow] = []
    rebalance_points: list[PortfolioRebalancePoint] = []
    for timestamp in schedule:
        universe = universe_membership_for_rebalance(
            panel, rebalance_timestamp=timestamp
        )
        latest_rows = panel.latest_row_by_symbol_on(timestamp, universe)
        raw_scores: dict[str, float] = {}
        missing_symbols: list[str] = []
        for symbol in universe:
            latest_row = latest_rows.get(symbol)
            if latest_row is None:
                missing_symbols.append(symbol)
                continue
            score = score_function(symbol, latest_row)
            if score is None:
                missing_symbols.append(symbol)
                continue
            raw_scores[symbol] = score
        ranking: tuple[RankedAsset, ...] = ()
        selected_symbols: tuple[str, ...] = ()
        weights: dict[str, float] = {}
        selection_reason = "selection_ready"
        selection_strength = 0.0
        if len(raw_scores) < minimum_universe_size:
            selection_reason = "warmup_pending"
        else:
            ranking, selected_symbols, weights = rank_scores(
                raw_scores, top_n=top_n, bottom_n=bottom_n, long_only=long_only
            )
            if ranking:
                score_values = [asset.score for asset in ranking]
                min_score = min(score_values)
                max_score = max(score_values)
                top_score = ranking[0].score
                if max_score > min_score:
                    selection_strength = _clamp_unit(
                        (top_score - min_score) / (max_score - min_score)
                    )
                elif selected_symbols:
                    selection_strength = 1.0
            if not selected_symbols:
                selection_reason = "no_selection"
        diagnostics = {
            "rebalance_frequency": rebalance_frequency,
            "eligible_universe_size": len(universe),
            "scored_universe_size": len(raw_scores),
            "warmup_pending_symbols": tuple(sorted(missing_symbols)),
            "warmup_ready": len(raw_scores) >= minimum_universe_size,
            "selection_reason": selection_reason,
            "selection_strength": selection_strength,
            "selected_count": len(selected_symbols),
            "gross_exposure": sum(abs(weight) for weight in weights.values()),
            "net_exposure": sum(weights.values()),
            "long_count": sum(1 for weight in weights.values() if weight > 0.0),
            "short_count": sum(1 for weight in weights.values() if weight < 0.0),
            "score_label": score_label,
            "raw_scores": raw_scores,
            "top_ranked_symbol": ranking[0].symbol if ranking else None,
            "top_ranked_score": ranking[0].score if ranking else None,
        }
        row = CrossAssetRow(
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


def evaluate_multi_leg_strategy(
    panel: MultiAssetPanel,
    *,
    spread_function: SpreadFunction,
    rebalance_frequency: str,
) -> tuple[MultiLegRow, ...]:
    schedule = select_rebalance_timestamps(
        panel.timestamps(), frequency=rebalance_frequency
    )
    rows: list[MultiLegRow] = []
    for timestamp in schedule:
        latest_rows = panel.latest_row_by_symbol_on(timestamp)
        best_symbol = ""
        best_spread: float | None = None
        best_diagnostics: dict[str, object] = {}
        for symbol, latest_row in latest_rows.items():
            evaluation = spread_function(symbol, latest_row)
            if evaluation is None:
                continue
            spread_value, diagnostics = evaluation
            if best_spread is None or abs(spread_value) > abs(best_spread):
                best_symbol = symbol
                best_spread = spread_value
                best_diagnostics = diagnostics
        if best_spread is None:
            row = MultiLegRow(
                timestamp=timestamp,
                spread_value=0.0,
                legs=(),
                diagnostics={
                    "selection_reason": "warmup_pending",
                    "warmup_ready": False,
                },
            )
            rows.append(row)
            continue
        legs = (
            MultiLegPosition(
                symbol=f"{best_symbol}:front",
                side="long" if best_spread >= 0.0 else "short",
                weight=0.5,
            ),
            MultiLegPosition(
                symbol=f"{best_symbol}:back",
                side="short" if best_spread >= 0.0 else "long",
                weight=-0.5,
            ),
        )
        rows.append(
            MultiLegRow(
                timestamp=timestamp,
                spread_value=best_spread,
                legs=legs,
                diagnostics={
                    "selection_reason": "selection_ready",
                    "warmup_ready": True,
                    "selected_symbol": best_symbol,
                    **best_diagnostics,
                },
            )
        )
    return tuple(rows)


def build_cross_asset_portfolio_output(
    algorithm_key: str,
    rows: Sequence[CrossAssetRow],
    *,
    family: str,
    subcategory: str,
    catalog_ref: str,
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


def build_multi_leg_output(
    algorithm_key: str,
    rows: Sequence[MultiLegRow],
    *,
    family: str,
    subcategory: str,
    catalog_ref: str,
) -> MultiLegOutput:
    return MultiLegOutput(
        algorithm_key=algorithm_key,
        rebalances=tuple(
            MultiLegRebalancePoint(
                timestamp=row.timestamp,
                spread_value=row.spread_value,
                legs=row.legs,
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


def build_rebalance_output(
    *,
    algorithm_key: str,
    family: str,
    subcategory: str,
    catalog_ref: str,
    rows: Sequence[CrossAssetRow],
) -> AlertAlgorithmOutput:
    points: list[AlertSeriesPoint] = []
    derived_series: dict[str, list[Any]] = {
        "selected_symbols": [],
        "weights": [],
        "ranking": [],
        "top_symbol": [],
        "top_score": [],
        "warmup_ready": [],
        "selection_strength": [],
    }
    child_outputs: tuple[NormalizedChildOutput, ...] = ()
    for row in rows:
        reason_code = str(row.diagnostics.get("selection_reason", "no_selection"))
        raw_confidence = row.diagnostics.get("selection_strength", 0.0)
        confidence = _coerce_float(raw_confidence) or 0.0
        points.append(
            AlertSeriesPoint(
                timestamp=row.timestamp,
                signal_label="buy" if row.selected_symbols else "neutral",
                score=confidence,
                confidence=confidence if row.selected_symbols else 0.0,
                reason_codes=(reason_code,),
            )
        )
        top_asset = row.ranking[0] if row.ranking else None
        derived_series["selected_symbols"].append(list(row.selected_symbols))
        derived_series["weights"].append(dict(row.weights))
        derived_series["ranking"].append([asset.to_dict() for asset in row.ranking])
        derived_series["top_symbol"].append(top_asset.symbol if top_asset else None)
        derived_series["top_score"].append(top_asset.score if top_asset else None)
        derived_series["warmup_ready"].append(
            bool(row.diagnostics.get("warmup_ready", False))
        )
        derived_series["selection_strength"].append(confidence)
    if rows:
        latest = rows[-1]
        reason_code = str(latest.diagnostics.get("selection_reason", "no_selection"))
        raw_confidence = latest.diagnostics.get("selection_strength", 0.0)
        confidence = _coerce_float(raw_confidence) or 0.0
        child_outputs = (
            NormalizedChildOutput(
                child_key=algorithm_key,
                output_kind="diagnostics",
                signal_label="buy" if latest.selected_symbols else "neutral",
                score=confidence,
                confidence=confidence if latest.selected_symbols else 0.0,
                regime_label="selected" if latest.selected_symbols else "neutral",
                direction=1 if latest.selected_symbols else 0,
                diagnostics={
                    "family": family,
                    "subcategory": subcategory,
                    "catalog_ref": catalog_ref,
                    "reporting_mode": "rebalance_report",
                    **latest.diagnostics,
                },
                reason_codes=(reason_code,),
            ),
        )
    return AlertAlgorithmOutput(
        algorithm_key=algorithm_key,
        points=tuple(points),
        derived_series=derived_series,
        summary_metrics={
            "rebalance_count": len(rows),
            "selection_count": sum(1 for row in rows if row.selected_symbols),
        },
        metadata={
            "family": family,
            "subcategory": subcategory,
            "catalog_ref": catalog_ref,
            "supports_composition": True,
            "output_contract_version": "1.0",
            "reporting_mode": "rebalance_report",
            "warmup_period": 1,
        },
        child_outputs=child_outputs,
    )


def build_multi_leg_rebalance_output(
    *,
    algorithm_key: str,
    family: str,
    subcategory: str,
    catalog_ref: str,
    rows: Sequence[MultiLegRow],
) -> AlertAlgorithmOutput:
    points: list[AlertSeriesPoint] = []
    derived_series: dict[str, list[Any]] = {
        "spread_value": [],
        "legs": [],
        "selected_symbol": [],
        "warmup_ready": [],
    }
    child_outputs: tuple[NormalizedChildOutput, ...] = ()
    for row in rows:
        reason_code = str(row.diagnostics.get("selection_reason", "warmup_pending"))
        points.append(
            AlertSeriesPoint(
                timestamp=row.timestamp,
                signal_label="buy" if row.legs else "neutral",
                score=abs(row.spread_value),
                confidence=1.0 if row.legs else 0.0,
                reason_codes=(reason_code,),
            )
        )
        derived_series["spread_value"].append(row.spread_value)
        derived_series["legs"].append([leg.to_dict() for leg in row.legs])
        derived_series["selected_symbol"].append(row.diagnostics.get("selected_symbol"))
        derived_series["warmup_ready"].append(
            bool(row.diagnostics.get("warmup_ready", False))
        )
    if rows:
        latest = rows[-1]
        reason_code = str(latest.diagnostics.get("selection_reason", "warmup_pending"))
        child_outputs = (
            NormalizedChildOutput(
                child_key=algorithm_key,
                output_kind="diagnostics",
                signal_label="buy" if latest.legs else "neutral",
                score=abs(latest.spread_value),
                confidence=1.0 if latest.legs else 0.0,
                regime_label="spread_active" if latest.legs else "neutral",
                direction=1 if latest.spread_value >= 0.0 and latest.legs else 0,
                diagnostics={
                    "family": family,
                    "subcategory": subcategory,
                    "catalog_ref": catalog_ref,
                    "reporting_mode": "rebalance_report",
                    **latest.diagnostics,
                },
                reason_codes=(reason_code,),
            ),
        )
    return AlertAlgorithmOutput(
        algorithm_key=algorithm_key,
        points=tuple(points),
        derived_series=derived_series,
        summary_metrics={"rebalance_count": len(rows)},
        metadata={
            "family": family,
            "subcategory": subcategory,
            "catalog_ref": catalog_ref,
            "supports_composition": True,
            "output_contract_version": "1.0",
            "reporting_mode": "rebalance_report",
            "warmup_period": 1,
        },
        child_outputs=child_outputs,
    )
