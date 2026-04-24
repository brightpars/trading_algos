from __future__ import annotations

from typing import Any

from trading_algos.alertgen.contracts.outputs import (
    AlertAlgorithmOutput,
    AlertSeriesPoint,
    NormalizedChildOutput,
)
from trading_algos.alertgen.algorithms.momentum.momentum_helpers import (
    CrossSectionalMomentumRow,
    build_portfolio_weight_output,
    evaluate_cross_sectional_momentum,
)
from trading_algos.alertgen.shared_utils.models import (
    AlgorithmDecision,
    AlgorithmMetadata,
)
from trading_algos.data.panel_dataset import MultiAssetPanel


class CrossSectionalMomentumAlertAlgorithm:
    catalog_ref = "algorithm:16"

    def __init__(
        self,
        *,
        algorithm_key: str,
        symbol: str,
        alg_name: str,
        subcategory: str,
        rows: list[dict[str, Any]],
        params: dict[str, Any],
    ) -> None:
        self.algorithm_key = algorithm_key
        self.alg_name = alg_name
        self.symbol = symbol
        self.subcategory = subcategory
        self.params = params
        self.evaluate_window_len = 1
        self.date = ""
        self.eval_dict: dict[str, Any] = {}
        self._rows = self._evaluate(rows)
        self.latest_predicted_trend = "neutral"
        self.latest_predicted_trend_confidence = 0.0
        if self._rows and self._rows[-1].selected_symbols:
            self.latest_predicted_trend = "buy"
            self.latest_predicted_trend_confidence = 1.0

    def _evaluate(
        self, rows: list[dict[str, Any]]
    ) -> tuple[CrossSectionalMomentumRow, ...]:
        panel = MultiAssetPanel.from_rows(rows)
        return evaluate_cross_sectional_momentum(
            panel,
            lookback_window=int(self.params["lookback_window"]),
            top_n=int(self.params["top_n"]),
            bottom_n=int(self.params.get("bottom_n", 0)),
            rebalance_frequency=str(self.params["rebalance_frequency"]),
            long_only=bool(self.params["long_only"]),
            score_adjustments={
                str(key): float(value)
                for key, value in self.params.get("score_adjustments", {}).items()
            },
            absolute_momentum_threshold=(
                float(self.params["absolute_momentum_threshold"])
                if self.params.get("absolute_momentum_threshold") is not None
                else None
            ),
            defensive_symbol=self.params.get("defensive_symbol"),
        )

    def minimum_history(self) -> int:
        return int(self.params["lookback_window"]) + 1

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

    def _latest_child_output(self) -> tuple[NormalizedChildOutput, ...]:
        if not self._rows:
            return ()
        latest = self._rows[-1]
        diagnostics = {
            "family": "momentum",
            "subcategory": self.subcategory,
            "catalog_ref": self.catalog_ref,
            "reporting_mode": "rebalance_report",
            "warmup_ready": len(latest.ranking) > 0,
            "selected_symbols": list(latest.selected_symbols),
            "weights": dict(latest.weights),
            "reason_codes": (
                "selection_ready" if latest.selected_symbols else "warmup_pending"
            ),
            **latest.diagnostics,
        }
        return (
            NormalizedChildOutput(
                child_key=self.algorithm_key,
                output_kind="diagnostics",
                signal_label="buy" if latest.selected_symbols else "neutral",
                score=1.0 if latest.selected_symbols else 0.0,
                confidence=1.0 if latest.selected_symbols else 0.0,
                regime_label="selected" if latest.selected_symbols else "neutral",
                direction=1 if latest.selected_symbols else 0,
                diagnostics=diagnostics,
                reason_codes=(
                    "selection_ready" if latest.selected_symbols else "warmup_pending",
                ),
            ),
        )

    def normalized_output(self) -> AlertAlgorithmOutput:
        points = []
        derived_series: dict[str, list[Any]] = {
            "selected_count": [],
            "selected_symbols": [],
            "top_symbol": [],
            "top_score": [],
            "ranking": [],
            "weights": [],
            "warmup_ready": [],
        }
        for row in self._rows:
            top_asset = row.ranking[0] if row.ranking else None
            raw_scored_universe_size = row.diagnostics.get("scored_universe_size", 0)
            scored_universe_size = (
                int(raw_scored_universe_size)
                if isinstance(raw_scored_universe_size, (int, float, str))
                else 0
            )
            ready = scored_universe_size > 0
            points.append(
                AlertSeriesPoint(
                    timestamp=row.timestamp,
                    signal_label="buy" if row.selected_symbols else "neutral",
                    score=float(top_asset.score / 100.0)
                    if top_asset is not None
                    else 0.0,
                    confidence=1.0 if row.selected_symbols else 0.0,
                    reason_codes=(
                        "selection_ready" if row.selected_symbols else "warmup_pending",
                    ),
                )
            )
            derived_series["selected_count"].append(len(row.selected_symbols))
            derived_series["selected_symbols"].append(list(row.selected_symbols))
            derived_series["top_symbol"].append(top_asset.symbol if top_asset else None)
            derived_series["top_score"].append(top_asset.score if top_asset else None)
            derived_series["ranking"].append([asset.to_dict() for asset in row.ranking])
            derived_series["weights"].append(dict(row.weights))
            derived_series["warmup_ready"].append(ready)
        return AlertAlgorithmOutput(
            algorithm_key=self.algorithm_key,
            points=tuple(points),
            derived_series=derived_series,
            summary_metrics={
                "rebalance_count": len(self._rows),
                "selection_count": sum(1 for row in self._rows if row.selected_symbols),
            },
            metadata={
                "family": "momentum",
                "subcategory": self.subcategory,
                "catalog_ref": self.catalog_ref,
                "supports_composition": True,
                "output_contract_version": "1.0",
                "warmup_period": self.minimum_history(),
                "reporting_mode": "rebalance_report",
            },
            child_outputs=self._latest_child_output(),
        )


def build_cross_sectional_momentum_algorithm(
    *,
    algorithm_key: str,
    symbol: str,
    alg_name: str,
    subcategory: str,
    alg_param: dict[str, Any],
    **_kwargs: Any,
) -> CrossSectionalMomentumAlertAlgorithm:
    return CrossSectionalMomentumAlertAlgorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        alg_name=alg_name,
        subcategory=subcategory,
        rows=list(alg_param["rows"]),
        params=alg_param,
    )
