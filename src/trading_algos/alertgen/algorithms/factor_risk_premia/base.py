from __future__ import annotations

from typing import Any, Sequence

from trading_algos.alertgen.contracts.outputs import (
    AlertAlgorithmOutput,
    AlertSeriesPoint,
    NormalizedChildOutput,
)
from trading_algos.alertgen.algorithms.factor_risk_premia.helpers import (
    FactorStrategyRow,
    build_factor_portfolio_weight_output,
    evaluate_factor_strategy,
)
from trading_algos.alertgen.shared_utils.models import (
    AlgorithmDecision,
    AlgorithmMetadata,
)
from trading_algos.data.panel_dataset import MultiAssetPanel


def _diagnostic_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        return int(value)
    return 0


def _diagnostic_float(value: object, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        return float(value)
    return default


class FactorPortfolioAlertAlgorithm:
    catalog_ref = ""

    def __init__(
        self,
        *,
        algorithm_key: str,
        symbol: str,
        alg_name: str,
        subcategory: str,
        params: dict[str, Any],
        factor_name: str,
        field_names: Sequence[str],
        higher_is_better: bool,
    ) -> None:
        self.algorithm_key = algorithm_key
        self.symbol = symbol
        self.alg_name = alg_name
        self.subcategory = subcategory
        self.params = params
        self.factor_name = factor_name
        self.field_names = tuple(field_names)
        self.higher_is_better = higher_is_better
        self.evaluate_window_len = 1
        self.date = ""
        self.eval_dict: dict[str, Any] = {}
        self._rows = self._evaluate_rows(list(params["rows"]))
        self.latest_predicted_trend = "neutral"
        self.latest_predicted_trend_confidence = 0.0
        if self._rows and self._rows[-1].selected_symbols:
            self.latest_predicted_trend = "buy"
            self.latest_predicted_trend_confidence = _diagnostic_float(
                self._rows[-1].diagnostics.get("selection_strength", 0.0)
            )

    def _evaluate_rows(
        self, rows: list[dict[str, Any]]
    ) -> tuple[FactorStrategyRow, ...]:
        panel = MultiAssetPanel.from_rows(rows)
        return evaluate_factor_strategy(
            panel,
            factor_name=self.factor_name,
            field_names=self.field_names,
            higher_is_better=self.higher_is_better,
            rebalance_frequency=str(self.params["rebalance_frequency"]),
            top_n=int(self.params["top_n"]),
            bottom_n=int(self.params.get("bottom_n", 0)),
            long_only=bool(self.params["long_only"]),
            minimum_universe_size=int(self.params["minimum_universe_size"]),
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
            sell_signal=self.latest_predicted_trend == "sell",
            no_signal=self.latest_predicted_trend == "neutral",
            annotations={"alg_name": self.alg_name, "factor_name": self.factor_name},
        )

    def process_list(self, _data_list: list[dict[str, Any]]) -> None:
        return None

    def portfolio_output(self):
        return build_factor_portfolio_weight_output(
            self.algorithm_key,
            self._rows,
            catalog_ref=self.catalog_ref,
            subcategory=self.subcategory,
        )

    def interactive_report_payloads(self) -> list[tuple[dict[str, Any], str]]:
        output = self.normalized_output()
        payload = {
            "algorithm_key": self.algorithm_key,
            "data": output.to_dict(),
            "portfolio": self.portfolio_output().to_dict(),
        }
        return [(payload, f"rebalance_report_{self.algorithm_key}_{self.symbol}")]

    def _build_child_output(self, row: FactorStrategyRow) -> NormalizedChildOutput:
        selection_reason = str(row.diagnostics.get("selection_reason", "no_selection"))
        selection_strength = _diagnostic_float(
            row.diagnostics.get("selection_strength", 0.0)
        )
        return NormalizedChildOutput(
            child_key=self.algorithm_key,
            output_kind="diagnostics",
            signal_label="buy" if row.selected_symbols else "neutral",
            score=selection_strength if row.selected_symbols else 0.0,
            confidence=selection_strength if row.selected_symbols else 0.0,
            regime_label="selected" if row.selected_symbols else "neutral",
            direction=1 if row.selected_symbols else 0,
            diagnostics={
                "family": "factor_risk_premia",
                "subcategory": self.subcategory,
                "catalog_ref": self.catalog_ref,
                "reporting_mode": "rebalance_report",
                "selected_symbols": list(row.selected_symbols),
                "weights": dict(row.weights),
                "reason_codes": (selection_reason,),
                "selection_strength": selection_strength,
                **row.diagnostics,
            },
            reason_codes=(selection_reason,),
        )

    def normalized_output(self) -> AlertAlgorithmOutput:
        points: list[AlertSeriesPoint] = []
        derived_series: dict[str, list[Any]] = {
            "selected_count": [],
            "selected_symbols": [],
            "top_symbol": [],
            "top_score": [],
            "selection_strength": [],
            "ranking": [],
            "weights": [],
            "warmup_ready": [],
            "selection_reason": [],
            "eligible_universe_size": [],
            "scored_universe_size": [],
            "gross_exposure": [],
            "net_exposure": [],
            "long_count": [],
            "short_count": [],
        }
        for row in self._rows:
            top_asset = row.ranking[0] if row.ranking else None
            selection_reason = str(
                row.diagnostics.get("selection_reason", "no_selection")
            )
            selection_strength = _diagnostic_float(
                row.diagnostics.get("selection_strength", 0.0)
            )
            points.append(
                AlertSeriesPoint(
                    timestamp=row.timestamp,
                    signal_label="buy" if row.selected_symbols else "neutral",
                    score=selection_strength,
                    confidence=selection_strength if row.selected_symbols else 0.0,
                    reason_codes=(selection_reason,),
                )
            )
            derived_series["selected_count"].append(len(row.selected_symbols))
            derived_series["selected_symbols"].append(list(row.selected_symbols))
            derived_series["top_symbol"].append(top_asset.symbol if top_asset else None)
            derived_series["top_score"].append(top_asset.score if top_asset else None)
            derived_series["selection_strength"].append(selection_strength)
            derived_series["ranking"].append([asset.to_dict() for asset in row.ranking])
            derived_series["weights"].append(dict(row.weights))
            derived_series["warmup_ready"].append(
                bool(row.diagnostics.get("warmup_ready", False))
            )
            derived_series["selection_reason"].append(selection_reason)
            derived_series["eligible_universe_size"].append(
                _diagnostic_int(row.diagnostics.get("eligible_universe_size", 0))
            )
            derived_series["scored_universe_size"].append(
                _diagnostic_int(row.diagnostics.get("scored_universe_size", 0))
            )
            derived_series["gross_exposure"].append(
                _diagnostic_float(row.diagnostics.get("gross_exposure", 0.0))
            )
            derived_series["net_exposure"].append(
                _diagnostic_float(row.diagnostics.get("net_exposure", 0.0))
            )
            derived_series["long_count"].append(
                _diagnostic_int(row.diagnostics.get("long_count", 0))
            )
            derived_series["short_count"].append(
                _diagnostic_int(row.diagnostics.get("short_count", 0))
            )
        child_outputs = (
            (self._build_child_output(self._rows[-1]),) if self._rows else ()
        )
        return AlertAlgorithmOutput(
            algorithm_key=self.algorithm_key,
            points=tuple(points),
            derived_series=derived_series,
            summary_metrics={
                "rebalance_count": len(self._rows),
                "selection_count": sum(1 for row in self._rows if row.selected_symbols),
            },
            metadata={
                "family": "factor_risk_premia",
                "subcategory": self.subcategory,
                "catalog_ref": self.catalog_ref,
                "supports_composition": True,
                "output_contract_version": "1.0",
                "warmup_period": self.minimum_history(),
                "reporting_mode": "rebalance_report",
            },
            child_outputs=child_outputs,
        )


def build_factor_portfolio_algorithm(
    *,
    algorithm_key: str,
    symbol: str,
    alg_name: str,
    subcategory: str,
    alg_param: dict[str, Any],
    factor_name: str,
    field_names: Sequence[str],
    higher_is_better: bool,
) -> FactorPortfolioAlertAlgorithm:
    return FactorPortfolioAlertAlgorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        alg_name=alg_name,
        subcategory=subcategory,
        params=alg_param,
        factor_name=factor_name,
        field_names=field_names,
        higher_is_better=higher_is_better,
    )
