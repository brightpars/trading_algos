from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from trading_algos.alertgen.contracts.outputs import (
    AlertAlgorithmOutput,
    AlertSeriesPoint,
    NormalizedChildOutput,
)
from trading_algos.alertgen.shared_utils.models import AlgorithmDecision
from trading_algos.execution.own_order_state import (
    OwnOrderState,
    own_order_state_from_mapping,
)
from trading_algos.market_data.order_book import (
    OrderBookSnapshot,
    snapshot_from_mapping,
)

from trading_algos.alertgen.algorithms.microstructure_hft.helpers import (
    MicrostructureMetrics,
    build_microstructure_metrics,
)


@dataclass(frozen=True)
class MicrostructureRow:
    timestamp: str
    signal_label: str
    score: float
    confidence: float
    reason_codes: tuple[str, ...]
    diagnostics: dict[str, Any]


class BaseMicrostructureAlertAlgorithm:
    catalog_ref = ""
    output_modes = ("quote_action", "signal", "diagnostics")

    def __init__(
        self,
        *,
        algorithm_key: str,
        symbol: str,
        subcategory: str,
        rows: list[dict[str, Any]],
        own_order_rows: list[dict[str, Any]] | None = None,
        reporting_mode: str = "order_book_trace",
    ) -> None:
        self.algorithm_key = algorithm_key
        self.symbol = symbol
        self.family = "microstructure_hft"
        self.subcategory = subcategory
        self._rows_input = list(rows)
        self._own_order_input = list(own_order_rows or [])
        self._rows: list[MicrostructureRow] = []
        self._reporting_mode = reporting_mode

    def minimum_history(self) -> int:
        return 1

    def reporting_mode(self) -> str:
        return self._reporting_mode

    def process_list(self, _data_list: list[dict[str, Any]]) -> None:
        return None

    def _own_state_for_index(self, index: int) -> OwnOrderState | None:
        if index >= len(self._own_order_input):
            return None
        return own_order_state_from_mapping(self._own_order_input[index])

    def _evaluate_row(
        self, metrics: MicrostructureMetrics, *, index: int
    ) -> tuple[str, float, float, tuple[str, ...], dict[str, Any]]:
        raise NotImplementedError

    def _build_rows(self) -> None:
        built_rows: list[MicrostructureRow] = []
        for index, row in enumerate(self._rows_input):
            snapshot: OrderBookSnapshot = snapshot_from_mapping(row)
            metrics = build_microstructure_metrics(
                snapshot, self._own_state_for_index(index)
            )
            signal_label, score, confidence, reason_codes, extra = self._evaluate_row(
                metrics,
                index=index,
            )
            diagnostics = {
                "catalog_ref": self.catalog_ref,
                "family": self.family,
                "subcategory": self.subcategory,
                "reporting_mode": self.reporting_mode(),
                "midprice": metrics.midprice,
                "spread": metrics.spread,
                "imbalance": metrics.imbalance,
                "microprice": metrics.microprice,
                "microprice_edge": metrics.microprice_edge,
                "inventory": metrics.inventory,
                "queue_fill_probability": metrics.queue_fill_probability,
                "auction_imbalance": metrics.auction_imbalance,
                "auction_phase": metrics.auction_phase,
                "session_phase": metrics.session_phase,
                "warmup_ready": index + 1 >= self.minimum_history(),
            }
            diagnostics.update(extra)
            built_rows.append(
                MicrostructureRow(
                    timestamp=metrics.timestamp,
                    signal_label=signal_label,
                    score=max(-1.0, min(1.0, score)),
                    confidence=max(0.0, min(1.0, confidence)),
                    reason_codes=reason_codes,
                    diagnostics=diagnostics,
                )
            )
        self._rows = built_rows

    def current_decision(self) -> AlgorithmDecision:
        if not self._rows:
            self._build_rows()
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
                diagnostics=row.diagnostics,
                reason_codes=row.reason_codes,
            )
            for row in self._rows
        )
        latest = self._rows[-1]
        return AlertAlgorithmOutput(
            algorithm_key=self.algorithm_key,
            points=points,
            derived_series={
                "signal_label": [row.signal_label for row in self._rows],
                "imbalance": [row.diagnostics.get("imbalance") for row in self._rows],
                "microprice_edge": [
                    row.diagnostics.get("microprice_edge") for row in self._rows
                ],
                "queue_fill_probability": [
                    row.diagnostics.get("queue_fill_probability") for row in self._rows
                ],
                "decision_reason": [row.reason_codes[0] for row in self._rows],
            },
            metadata={
                "catalog_ref": self.catalog_ref,
                "family": self.family,
                "subcategory": self.subcategory,
                "reporting_mode": self.reporting_mode(),
                "warmup_period": self.minimum_history(),
            },
            child_outputs=(
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
                    diagnostics=latest.diagnostics,
                    reason_codes=latest.reason_codes,
                ),
            ),
        )

    def interactive_report_payloads(self) -> list[tuple[dict[str, Any], str]]:
        return [
            (
                {
                    "algorithm_key": self.algorithm_key,
                    "data": self.normalized_output().to_dict(),
                },
                f"microstructure_{self.algorithm_key}_{self.symbol}",
            )
        ]
