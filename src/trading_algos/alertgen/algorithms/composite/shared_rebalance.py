from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from trading_algos.alertgen.contracts.outputs import (
    AlertAlgorithmOutput,
    AlertSeriesPoint,
    NormalizedChildOutput,
)
from trading_algos.contracts.portfolio_output import (
    PortfolioRebalancePoint,
    PortfolioWeightOutput,
    RankedAsset,
)
from trading_algos.rebalance.runner import build_rebalance_result


def clamp_unit_interval(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def clamp_signed_unit(value: float) -> float:
    return max(-1.0, min(1.0, float(value)))


@dataclass(frozen=True)
class CompositeRebalanceRow:
    timestamp: str
    ranking: tuple[RankedAsset, ...]
    selected_symbols: tuple[str, ...]
    weights: dict[str, float]
    diagnostics: dict[str, Any]


def build_portfolio_weight_output(
    algorithm_key: str,
    rows: Sequence[CompositeRebalanceRow],
    *,
    family: str,
    subcategory: str,
    catalog_ref: str,
    reporting_mode: str,
) -> PortfolioWeightOutput:
    points = tuple(
        PortfolioRebalancePoint(
            timestamp=row.timestamp,
            ranking=row.ranking,
            selected_symbols=row.selected_symbols,
            weights=row.weights,
            diagnostics=row.diagnostics,
        )
        for row in rows
    )
    _ = build_rebalance_result(
        list(points), schedule=tuple(row.timestamp for row in rows)
    )
    return PortfolioWeightOutput(
        algorithm_key=algorithm_key,
        rebalances=points,
        metadata={
            "family": family,
            "subcategory": subcategory,
            "catalog_ref": catalog_ref,
            "reporting_mode": reporting_mode,
            "supports_composition": True,
            "output_contract_version": "1.0",
        },
    )


def build_rebalance_alert_output(
    *,
    algorithm_key: str,
    family: str,
    subcategory: str,
    catalog_ref: str,
    reporting_mode: str,
    warmup_period: int,
    rows: Sequence[CompositeRebalanceRow],
    signal_from_row: Callable[[CompositeRebalanceRow], str],
    score_from_row: Callable[[CompositeRebalanceRow], float],
    confidence_from_row: Callable[[CompositeRebalanceRow], float],
) -> AlertAlgorithmOutput:
    points: list[AlertSeriesPoint] = []
    derived_series: dict[str, list[Any]] = {
        "selected_symbols": [],
        "weights": [],
        "ranking": [],
        "top_symbol": [],
        "top_score": [],
        "warmup_ready": [],
        "selected_count": [],
        "gross_exposure": [],
        "net_exposure": [],
        "decision_reason": [],
        "reason_codes": [],
    }
    child_outputs: tuple[NormalizedChildOutput, ...] = ()
    for row in rows:
        signal_label = str(signal_from_row(row))
        score = clamp_signed_unit(float(score_from_row(row)))
        confidence = clamp_unit_interval(float(confidence_from_row(row)))
        reason_code = str(row.diagnostics.get("selection_reason", "no_selection"))
        top_asset = row.ranking[0] if row.ranking else None
        points.append(
            AlertSeriesPoint(
                timestamp=row.timestamp,
                signal_label=signal_label,
                score=score,
                confidence=confidence if signal_label != "neutral" else 0.0,
                reason_codes=(reason_code,),
            )
        )
        derived_series["selected_symbols"].append(list(row.selected_symbols))
        derived_series["weights"].append(dict(row.weights))
        derived_series["ranking"].append([asset.to_dict() for asset in row.ranking])
        derived_series["top_symbol"].append(top_asset.symbol if top_asset else None)
        derived_series["top_score"].append(top_asset.score if top_asset else None)
        derived_series["warmup_ready"].append(
            bool(row.diagnostics.get("warmup_ready", False))
        )
        derived_series["selected_count"].append(len(row.selected_symbols))
        derived_series["gross_exposure"].append(
            sum(abs(weight) for weight in row.weights.values())
        )
        derived_series["net_exposure"].append(sum(row.weights.values()))
        derived_series["decision_reason"].append(reason_code)
        derived_series["reason_codes"].append([reason_code])
    if rows:
        latest = rows[-1]
        latest_signal = str(signal_from_row(latest))
        latest_score = clamp_signed_unit(float(score_from_row(latest)))
        latest_confidence = clamp_unit_interval(float(confidence_from_row(latest)))
        latest_reason = str(latest.diagnostics.get("selection_reason", "no_selection"))
        child_outputs = (
            NormalizedChildOutput(
                child_key=algorithm_key,
                output_kind="diagnostics",
                signal_label=latest_signal,
                score=latest_score,
                confidence=latest_confidence if latest_signal != "neutral" else 0.0,
                regime_label="selected" if latest.selected_symbols else "neutral",
                direction=1
                if latest_signal == "buy"
                else -1
                if latest_signal == "sell"
                else 0,
                diagnostics={
                    "family": family,
                    "subcategory": subcategory,
                    "catalog_ref": catalog_ref,
                    "reporting_mode": reporting_mode,
                    "reason_codes": [latest_reason],
                    **latest.diagnostics,
                },
                reason_codes=(latest_reason,),
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
            "reporting_mode": reporting_mode,
            "warmup_period": warmup_period,
        },
        child_outputs=child_outputs,
    )


def equal_weight_selected_symbols(symbols: Sequence[str]) -> dict[str, float]:
    if not symbols:
        return {}
    weight = 1.0 / len(symbols)
    return {symbol: weight for symbol in symbols}


def normalize_weight_map(
    weights: Mapping[str, float], *, cap_gross_exposure: float = 1.0
) -> dict[str, float]:
    normalized = {
        str(symbol): float(weight)
        for symbol, weight in weights.items()
        if float(weight) != 0.0
    }
    gross_exposure = sum(abs(weight) for weight in normalized.values())
    if gross_exposure <= 0.0:
        return {}
    scale = min(1.0, float(cap_gross_exposure) / gross_exposure)
    return {symbol: weight * scale for symbol, weight in normalized.items()}
