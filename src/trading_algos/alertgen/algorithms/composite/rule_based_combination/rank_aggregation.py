from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from trading_algos.alertgen.algorithms.composite.shared_rebalance import (
    CompositeRebalanceRow,
    build_portfolio_weight_output,
    build_rebalance_alert_output,
    clamp_unit_interval,
    equal_weight_selected_symbols,
)
from trading_algos.alertgen.contracts.outputs import AlertAlgorithmOutput
from trading_algos.alertgen.shared_utils.models import (
    AlgorithmDecision,
    AlgorithmMetadata,
)
from trading_algos.contracts.portfolio_output import RankedAsset


@dataclass(frozen=True)
class RankAggregationAsset:
    symbol: str
    aggregate_score: float
    average_rank: float
    observed_input_count: int


def _coerce_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_asset_rows(raw_row: dict[str, Any]) -> list[dict[str, Any]]:
    asset_rows = raw_row.get("asset_rows", raw_row.get("assets", []))
    if not isinstance(asset_rows, list):
        raise ValueError("rank_aggregation: asset_rows must be a list")
    normalized_rows: list[dict[str, Any]] = []
    for index, asset_row in enumerate(asset_rows):
        if not isinstance(asset_row, dict):
            raise ValueError(f"rank_aggregation: asset_rows[{index}] must be a dict")
        symbol = str(asset_row.get("symbol", "")).strip()
        if symbol == "":
            raise ValueError(
                f"rank_aggregation: asset_rows[{index}] symbol is required"
            )
        normalized_rows.append(dict(asset_row))
    return normalized_rows


def _aggregate_asset_rank(
    asset_row: dict[str, Any],
    *,
    aggregation_method: str,
    rank_field_names: tuple[str, ...],
    score_field_names: tuple[str, ...],
) -> RankAggregationAsset | None:
    symbol = str(asset_row["symbol"])
    observed_ranks: list[float] = []
    observed_scores: list[float] = []
    for field_name in rank_field_names:
        value = _coerce_float(asset_row.get(field_name))
        if value is not None:
            observed_ranks.append(value)
    for field_name in score_field_names:
        value = _coerce_float(asset_row.get(field_name))
        if value is not None:
            observed_scores.append(value)
    if not observed_ranks and not observed_scores:
        return None
    if observed_ranks:
        if aggregation_method == "median_rank":
            ordered = sorted(observed_ranks)
            middle = len(ordered) // 2
            if len(ordered) % 2 == 0:
                average_rank = (ordered[middle - 1] + ordered[middle]) / 2.0
            else:
                average_rank = ordered[middle]
        else:
            average_rank = sum(observed_ranks) / len(observed_ranks)
    else:
        average_rank = 999_999.0
    aggregate_score = 0.0
    if observed_scores:
        aggregate_score += sum(observed_scores) / len(observed_scores)
    if observed_ranks:
        aggregate_score += 1.0 / average_rank
    return RankAggregationAsset(
        symbol=symbol,
        aggregate_score=aggregate_score,
        average_rank=average_rank,
        observed_input_count=len(observed_ranks) + len(observed_scores),
    )


def evaluate_rank_aggregation_rows(
    raw_rows: list[dict[str, Any]],
    *,
    aggregation_method: str,
    rank_field_names: tuple[str, ...],
    score_field_names: tuple[str, ...],
    top_k: int,
    minimum_child_count: int,
) -> tuple[CompositeRebalanceRow, ...]:
    rows: list[CompositeRebalanceRow] = []
    for raw_row in raw_rows:
        timestamp = str(raw_row.get("ts", raw_row.get("timestamp", ""))).strip()
        asset_rows = _extract_asset_rows(raw_row)
        aggregated_assets: list[RankAggregationAsset] = []
        missing_symbols: list[str] = []
        for asset_row in asset_rows:
            aggregated = _aggregate_asset_rank(
                asset_row,
                aggregation_method=aggregation_method,
                rank_field_names=rank_field_names,
                score_field_names=score_field_names,
            )
            if aggregated is None:
                missing_symbols.append(str(asset_row["symbol"]))
                continue
            if aggregated.observed_input_count < minimum_child_count:
                missing_symbols.append(aggregated.symbol)
                continue
            aggregated_assets.append(aggregated)
        ordered_assets = sorted(
            aggregated_assets,
            key=lambda asset: (
                -asset.aggregate_score,
                asset.average_rank,
                asset.symbol,
            ),
        )
        selected_symbols = tuple(asset.symbol for asset in ordered_assets[:top_k])
        weights = equal_weight_selected_symbols(selected_symbols)
        ranking = tuple(
            RankedAsset(
                symbol=asset.symbol,
                rank=index,
                score=asset.aggregate_score,
                weight=weights.get(asset.symbol, 0.0),
                selected=asset.symbol in selected_symbols,
                side="long" if asset.symbol in selected_symbols else "neutral",
            )
            for index, asset in enumerate(ordered_assets, start=1)
        )
        top_score = ordered_assets[0].aggregate_score if ordered_assets else 0.0
        min_score = ordered_assets[-1].aggregate_score if ordered_assets else 0.0
        selection_strength = 0.0
        if ordered_assets and top_score > min_score:
            selected_score = ordered_assets[
                min(top_k, len(ordered_assets)) - 1
            ].aggregate_score
            selection_strength = clamp_unit_interval(
                (top_score - selected_score) / (top_score - min_score)
            )
        elif selected_symbols:
            selection_strength = 1.0
        selection_reason = "selection_ready"
        if not ordered_assets:
            selection_reason = "warmup_pending"
        elif not selected_symbols:
            selection_reason = "no_selection"
        diagnostics = {
            "aggregation_method": aggregation_method,
            "rank_field_names": list(rank_field_names),
            "score_field_names": list(score_field_names),
            "asset_count": len(asset_rows),
            "scored_asset_count": len(ordered_assets),
            "minimum_child_count": minimum_child_count,
            "warmup_ready": bool(ordered_assets),
            "selection_reason": selection_reason,
            "selected_symbols": list(selected_symbols),
            "selected_count": len(selected_symbols),
            "selection_strength": selection_strength,
            "top_ranked_symbol": ranking[0].symbol if ranking else None,
            "top_ranked_score": ranking[0].score if ranking else None,
            "missing_symbols": tuple(sorted(missing_symbols)),
        }
        rows.append(
            CompositeRebalanceRow(
                timestamp=timestamp,
                ranking=ranking,
                selected_symbols=selected_symbols,
                weights=weights,
                diagnostics=diagnostics,
            )
        )
    return tuple(rows)


class RankAggregationAlertAlgorithm:
    catalog_ref = "combination:3"

    def __init__(
        self,
        *,
        algorithm_key: str,
        symbol: str,
        params: dict[str, Any],
    ) -> None:
        self.algorithm_key = algorithm_key
        self.alg_name = algorithm_key
        self.symbol = symbol
        self.params = params
        self.evaluate_window_len = 1
        self.date = ""
        self.eval_dict: dict[str, Any] = {}
        self._rows = evaluate_rank_aggregation_rows(
            list(params["rows"]),
            aggregation_method=str(params["aggregation_method"]),
            rank_field_names=tuple(
                str(item) for item in params.get("rank_field_names", [])
            ),
            score_field_names=tuple(
                str(item) for item in params.get("score_field_names", [])
            ),
            top_k=int(params["top_k"]),
            minimum_child_count=int(params["minimum_child_count"]),
        )
        self.latest_predicted_trend = (
            "buy" if self._rows and self._rows[-1].selected_symbols else "neutral"
        )
        self.latest_predicted_trend_confidence = (
            float(self._rows[-1].diagnostics.get("selection_strength", 0.0))
            if self._rows
            else 0.0
        )

    def minimum_history(self) -> int:
        return 1

    def algorithm_metadata(self) -> dict[str, Any]:
        return AlgorithmMetadata(
            alg_name=self.alg_name,
            symbol=self.symbol,
            date=self.date,
            evaluate_window_len=self.evaluate_window_len,
        ).to_dict()

    def current_decision(self) -> AlgorithmDecision:
        return AlgorithmDecision(
            trend=self.latest_predicted_trend,
            confidence=self.latest_predicted_trend_confidence,
            buy_signal=self.latest_predicted_trend == "buy",
            sell_signal=False,
            no_signal=self.latest_predicted_trend != "buy",
            annotations={"alg_name": self.alg_name},
        )

    def process_list(self, _data_list: list[dict[str, Any]]) -> None:
        return None

    def portfolio_output(self):
        return build_portfolio_weight_output(
            self.algorithm_key,
            self._rows,
            family="rule_based_combination",
            subcategory="rank",
            catalog_ref=self.catalog_ref,
            reporting_mode="composite_trace",
        )

    def normalized_output(self) -> AlertAlgorithmOutput:
        return build_rebalance_alert_output(
            algorithm_key=self.algorithm_key,
            family="rule_based_combination",
            subcategory="rank",
            catalog_ref=self.catalog_ref,
            reporting_mode="composite_trace",
            warmup_period=self.minimum_history(),
            rows=self._rows,
            signal_from_row=lambda row: "buy" if row.selected_symbols else "neutral",
            score_from_row=lambda row: float(
                row.diagnostics.get("selection_strength", 0.0)
            ),
            confidence_from_row=lambda row: float(
                row.diagnostics.get("selection_strength", 0.0)
            ),
        )

    def interactive_report_payloads(self) -> list[tuple[dict[str, Any], str]]:
        return [
            (
                {
                    "algorithm_key": self.algorithm_key,
                    "data": self.normalized_output().to_dict(),
                    "portfolio": self.portfolio_output().to_dict(),
                },
                f"rebalance_report_{self.algorithm_key}_{self.symbol}",
            )
        ]


def build_rank_aggregation_algorithm(
    *,
    algorithm_key: str,
    symbol: str,
    alg_param: dict[str, Any],
    **_kwargs: Any,
) -> RankAggregationAlertAlgorithm:
    return RankAggregationAlertAlgorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        params=alg_param,
    )
