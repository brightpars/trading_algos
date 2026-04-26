from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from trading_algos.alertgen.contracts.outputs import (
    AlertAlgorithmOutput,
    AlertSeriesPoint,
    NormalizedChildOutput,
)
from trading_algos.alertgen.shared_utils.models import AlgorithmDecision

from trading_algos.alertgen.algorithms.volatility_options.options_surface_helpers import (
    OptionSurfaceDecisionMetrics,
    build_option_surface_metrics,
)


@dataclass(frozen=True)
class OptionsSurfaceRow:
    timestamp: str
    signal_label: str
    score: float
    confidence: float
    reason_codes: tuple[str, ...]
    diagnostics: dict[str, Any]


class BaseOptionsSurfaceAlgorithm:
    catalog_ref = ""
    output_modes = ("volatility_position", "greek_diagnostics", "diagnostics")

    def __init__(
        self,
        *,
        algorithm_key: str,
        symbol: str,
        family: str,
        subcategory: str,
        rows: list[dict[str, Any]],
        reporting_mode: str = "options_trace",
    ) -> None:
        self.algorithm_key = algorithm_key
        self.symbol = symbol
        self.family = family
        self.subcategory = subcategory
        self._rows_input = list(rows)
        self._rows: list[OptionsSurfaceRow] = []
        self._metrics_history: list[OptionSurfaceDecisionMetrics] = []
        self._reporting_mode = reporting_mode

    def minimum_history(self) -> int:
        return 2

    def reporting_mode(self) -> str:
        return self._reporting_mode

    def process_list(self, _data_list: list[dict[str, Any]]) -> None:
        return None

    def _selection_mode(self) -> str:
        return "straddle"

    def _hedge_band(self) -> float:
        return 0.0

    def _evaluate_row(
        self, metrics: OptionSurfaceDecisionMetrics, *, index: int
    ) -> tuple[str, float, float, tuple[str, ...], dict[str, Any]]:
        raise NotImplementedError

    def _build_rows(self) -> None:
        built_rows: list[OptionsSurfaceRow] = []
        metrics_history: list[OptionSurfaceDecisionMetrics] = []
        for index, row in enumerate(self._rows_input):
            metrics = build_option_surface_metrics(
                row,
                selection_mode=self._selection_mode(),
                hedge_band=self._hedge_band(),
            )
            metrics_history.append(metrics)
            if index + 1 < self.minimum_history():
                diagnostics = self._base_diagnostics(metrics)
                diagnostics.update(
                    {
                        "selection_reason": "warmup_pending",
                        "warmup_ready": False,
                    }
                )
                built_rows.append(
                    OptionsSurfaceRow(
                        timestamp=metrics.timestamp,
                        signal_label="neutral",
                        score=0.0,
                        confidence=0.0,
                        reason_codes=("warmup_pending",),
                        diagnostics=diagnostics,
                    )
                )
                continue
            signal_label, score, confidence, reason_codes, extra = self._evaluate_row(
                metrics,
                index=index,
            )
            diagnostics = self._base_diagnostics(metrics)
            diagnostics.update(extra)
            diagnostics.update(
                {
                    "warmup_ready": True,
                    "selection_reason": reason_codes[0] if reason_codes else "neutral",
                }
            )
            built_rows.append(
                OptionsSurfaceRow(
                    timestamp=metrics.timestamp,
                    signal_label=signal_label,
                    score=max(-1.0, min(1.0, score)),
                    confidence=max(0.0, min(1.0, confidence)),
                    reason_codes=reason_codes,
                    diagnostics=diagnostics,
                )
            )
        self._rows = built_rows
        self._metrics_history = metrics_history

    def _base_diagnostics(
        self, metrics: OptionSurfaceDecisionMetrics
    ) -> dict[str, Any]:
        return {
            "family": self.family,
            "subcategory": self.subcategory,
            "catalog_ref": self.catalog_ref,
            "reporting_mode": self.reporting_mode(),
            "underlying_symbol": metrics.underlying_symbol,
            "selected_contracts": list(metrics.selected_contracts),
            "contract_count": metrics.contract_count,
            "average_implied_vol": metrics.average_implied_vol,
            "realized_vol": metrics.realized_vol,
            "iv_rv_gap": metrics.iv_rv_gap,
            "net_delta": metrics.net_delta,
            "delta_abs": metrics.delta_abs,
            "hedge_units": metrics.hedge_units,
            "hedge_rebalance_required": metrics.hedge_rebalance_required,
            "net_gamma": metrics.net_gamma,
            "gamma_abs": metrics.gamma_abs,
            "net_vega": metrics.net_vega,
            "vega_abs": metrics.vega_abs,
            "dispersion_gap": metrics.dispersion_gap,
            "put_call_skew": metrics.put_call_skew,
            "term_structure_slope": metrics.term_structure_slope,
            "expected_move_gap": metrics.expected_move_gap,
            "warmup_period": self.minimum_history(),
        }

    def current_decision(self) -> AlgorithmDecision:
        if not self._rows:
            return AlgorithmDecision(
                trend="neutral",
                confidence=0.0,
                buy_signal=False,
                sell_signal=False,
                no_signal=True,
                annotations={"alg_name": self.algorithm_key},
            )
        latest = self._rows[-1]
        return AlgorithmDecision(
            trend=latest.signal_label,
            confidence=latest.confidence,
            buy_signal=latest.signal_label == "buy",
            sell_signal=latest.signal_label == "sell",
            no_signal=latest.signal_label == "neutral",
            annotations={"alg_name": self.algorithm_key, **latest.diagnostics},
        )

    def normalized_output(self) -> AlertAlgorithmOutput:
        if not self._rows:
            self._build_rows()
        points = tuple(
            AlertSeriesPoint(
                timestamp=row.timestamp,
                signal_label=row.signal_label,
                score=row.score,
                confidence=row.confidence,
                reason_codes=row.reason_codes,
                diagnostics=row.diagnostics,
            )
            for row in self._rows
        )
        derived_series: dict[str, list[Any]] = {
            "signal_label": [row.signal_label for row in self._rows],
            "score": [row.score for row in self._rows],
            "confidence": [row.confidence for row in self._rows],
            "warmup_ready": [
                row.diagnostics.get("warmup_ready", False) for row in self._rows
            ],
            "net_delta": [row.diagnostics.get("net_delta") for row in self._rows],
            "hedge_units": [row.diagnostics.get("hedge_units") for row in self._rows],
            "net_gamma": [row.diagnostics.get("net_gamma") for row in self._rows],
            "net_vega": [row.diagnostics.get("net_vega") for row in self._rows],
            "average_implied_vol": [
                row.diagnostics.get("average_implied_vol") for row in self._rows
            ],
            "realized_vol": [row.diagnostics.get("realized_vol") for row in self._rows],
            "iv_rv_gap": [row.diagnostics.get("iv_rv_gap") for row in self._rows],
            "dispersion_gap": [
                row.diagnostics.get("dispersion_gap") for row in self._rows
            ],
            "put_call_skew": [
                row.diagnostics.get("put_call_skew") for row in self._rows
            ],
            "term_structure_slope": [
                row.diagnostics.get("term_structure_slope") for row in self._rows
            ],
            "expected_move_gap": [
                row.diagnostics.get("expected_move_gap") for row in self._rows
            ],
            "reason_codes": [list(row.reason_codes) for row in self._rows],
        }
        latest = self._rows[-1]
        child_outputs = (
            NormalizedChildOutput(
                child_key=self.algorithm_key,
                output_kind="diagnostics",
                signal_label=latest.signal_label,
                score=latest.score,
                confidence=latest.confidence,
                regime_label=latest.signal_label,
                direction=1
                if latest.signal_label == "buy"
                else -1
                if latest.signal_label == "sell"
                else 0,
                diagnostics=latest.diagnostics
                | {"reason_codes": list(latest.reason_codes)},
                reason_codes=latest.reason_codes,
            ),
        )
        return AlertAlgorithmOutput(
            algorithm_key=self.algorithm_key,
            points=points,
            derived_series=derived_series,
            metadata={
                "family": self.family,
                "subcategory": self.subcategory,
                "catalog_ref": self.catalog_ref,
                "reporting_mode": self.reporting_mode(),
                "warmup_period": self.minimum_history(),
                "supports_composition": True,
                "output_modes": self.output_modes,
            },
            child_outputs=child_outputs,
        )

    def interactive_report_payloads(self) -> list[tuple[dict[str, Any], str]]:
        return [
            (
                {
                    "algorithm_key": self.algorithm_key,
                    "data": self.normalized_output().to_dict(),
                },
                f"options_surface_{self.algorithm_key}_{self.symbol}",
            )
        ]
