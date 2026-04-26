from __future__ import annotations

from typing import Any, Sequence

from trading_algos.alertgen.algorithms.event_driven.helpers import (
    EventDrivenRow,
    build_event_window_output,
)
from trading_algos.reporting.event_report import build_event_report_payload


class EventDrivenAlertAlgorithm:
    catalog_ref = ""

    def __init__(
        self,
        *,
        algorithm_key: str,
        symbol: str,
        alg_name: str,
        family: str,
        subcategory: str,
        rows: Sequence[EventDrivenRow],
    ) -> None:
        self.algorithm_key = algorithm_key
        self.symbol = symbol
        self.alg_name = alg_name
        self.family = family
        self.subcategory = subcategory
        self._rows = tuple(rows)
        self.evaluate_window_len = 1
        self.date = ""
        self.eval_dict: dict[str, Any] = {}
        latest = self._rows[-1] if self._rows else None
        self.latest_predicted_trend = (
            latest.signal_label if latest is not None else "neutral"
        )
        self.latest_predicted_trend_confidence = (
            latest.confidence if latest is not None else 0.0
        )

    def minimum_history(self) -> int:
        return 1

    def process_list(self, _data_list: list[dict[str, Any]]) -> None:
        return None

    def normalized_output(self):
        return build_event_window_output(
            algorithm_key=self.algorithm_key,
            family=self.family,
            subcategory=self.subcategory,
            catalog_ref=self.catalog_ref,
            rows=self._rows,
        )

    def interactive_report_payloads(self) -> list[tuple[dict[str, Any], str]]:
        output = self.normalized_output()
        payload = build_event_report_payload(
            algorithm_key=self.algorithm_key,
            output_data=output.to_dict(),
        )
        return [(payload, f"event_report_{self.algorithm_key}_{self.symbol}")]
