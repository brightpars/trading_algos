from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from trading_algos.alertgen.contracts.outputs import (
    AlertAlgorithmOutput,
    AlertSeriesPoint,
    NormalizedChildOutput,
)
from trading_algos.alertgen.shared_utils.models import AlgorithmDecision
from trading_algos.contracts.execution_plan import (
    ExecutionChildOrder,
    ExecutionPlanOutput,
    ExecutionPlanPoint,
)
from trading_algos.simulation.fills import estimate_child_fill


@dataclass(frozen=True)
class ExecutionMetrics:
    timestamp: str
    available_volume: float
    reference_price: float
    realized_volume_share: float


class BaseExecutionAlertAlgorithm:
    catalog_ref = ""
    output_modes = ("execution_plan", "child_order_actions", "diagnostics")

    def __init__(
        self,
        *,
        algorithm_key: str,
        symbol: str,
        subcategory: str,
        rows: list[dict[str, Any]],
        parent_order: dict[str, Any],
    ) -> None:
        self.algorithm_key = algorithm_key
        self.symbol = symbol
        self.family = "execution"
        self.subcategory = subcategory
        self.rows = list(rows)
        self.parent_order = dict(parent_order)
        self._normalized_output: AlertAlgorithmOutput | None = None
        self._execution_plan: ExecutionPlanOutput | None = None

    def minimum_history(self) -> int:
        return 1

    def reporting_mode(self) -> str:
        return "execution_trace"

    def process_list(self, _data_list: list[dict[str, Any]]) -> None:
        return None

    def _metrics_for_row(
        self, row: dict[str, Any], *, total_available_volume: float
    ) -> ExecutionMetrics:
        available_volume = float(row["available_volume"])
        realized_share = (
            0.0
            if total_available_volume <= 0.0
            else available_volume / total_available_volume
        )
        return ExecutionMetrics(
            timestamp=str(row["ts"]),
            available_volume=available_volume,
            reference_price=float(row["reference_price"]),
            realized_volume_share=realized_share,
        )

    def _target_quantities(self) -> list[float]:
        raise NotImplementedError

    def _row_reason(
        self, metrics: ExecutionMetrics, target_qty: float, achieved_qty: float
    ) -> str:
        return "schedule_active"

    def _extra_diagnostics(
        self, metrics: ExecutionMetrics, target_qty: float, achieved_qty: float
    ) -> dict[str, Any]:
        return {}

    def _build_outputs(self) -> None:
        total_volume = sum(float(row["available_volume"]) for row in self.rows)
        parent_qty = float(self.parent_order["quantity"])
        targets = self._target_quantities()
        achieved = 0.0
        plan_points: list[ExecutionPlanPoint] = []
        child_orders: list[ExecutionChildOrder] = []
        points: list[AlertSeriesPoint] = []
        for row, target_qty in zip(self.rows, targets, strict=True):
            metrics = self._metrics_for_row(row, total_available_volume=total_volume)
            requested_child = max(0.0, target_qty - achieved)
            fill = estimate_child_fill(
                requested_quantity=requested_child,
                available_quantity=metrics.available_volume,
                aggressiveness=1.0,
            )
            achieved += fill.filled_quantity
            reason = self._row_reason(metrics, target_qty, achieved)
            diagnostics = {
                "catalog_ref": self.catalog_ref,
                "family": self.family,
                "subcategory": self.subcategory,
                "reporting_mode": self.reporting_mode(),
                "parent_quantity": parent_qty,
                "target_cumulative_quantity": target_qty,
                "achieved_cumulative_quantity": achieved,
                "available_volume": metrics.available_volume,
                "reference_price": metrics.reference_price,
                "realized_volume_share": metrics.realized_volume_share,
                "fill_ratio": fill.fill_ratio,
                "decision_reason": reason,
            }
            diagnostics.update(self._extra_diagnostics(metrics, target_qty, achieved))
            plan_points.append(
                ExecutionPlanPoint(
                    timestamp=metrics.timestamp,
                    target_cumulative_quantity=target_qty,
                    achieved_cumulative_quantity=achieved,
                    benchmark_price=metrics.reference_price,
                    diagnostics=diagnostics,
                )
            )
            child_orders.append(
                ExecutionChildOrder(
                    timestamp=metrics.timestamp,
                    action="submit_child" if requested_child > 0 else "wait",
                    quantity=requested_child,
                    limit_price=metrics.reference_price,
                    diagnostics=diagnostics,
                )
            )
            signal_label = (
                "buy"
                if self.parent_order["side"] == "buy" and requested_child > 0
                else "sell"
                if self.parent_order["side"] == "sell" and requested_child > 0
                else "neutral"
            )
            score = 0.0 if parent_qty <= 0.0 else target_qty / parent_qty
            points.append(
                AlertSeriesPoint(
                    timestamp=metrics.timestamp,
                    signal_label=signal_label,
                    score=max(
                        -1.0,
                        min(
                            1.0,
                            score
                            if signal_label == "buy"
                            else -score
                            if signal_label == "sell"
                            else 0.0,
                        ),
                    ),
                    confidence=min(1.0, fill.fill_ratio),
                    diagnostics=diagnostics,
                    reason_codes=(reason,),
                )
            )
        self._execution_plan = ExecutionPlanOutput(
            algorithm_key=self.algorithm_key,
            plan_points=tuple(plan_points),
            child_orders=tuple(child_orders),
            metadata={
                "catalog_ref": self.catalog_ref,
                "reporting_mode": self.reporting_mode(),
            },
        )
        latest = points[-1]
        self._normalized_output = AlertAlgorithmOutput(
            algorithm_key=self.algorithm_key,
            points=tuple(points),
            derived_series={
                "target_cumulative_quantity": [
                    p.target_cumulative_quantity for p in plan_points
                ],
                "achieved_cumulative_quantity": [
                    p.achieved_cumulative_quantity for p in plan_points
                ],
                "decision_reason": [
                    p.diagnostics["decision_reason"] for p in plan_points
                ],
            },
            metadata={
                "catalog_ref": self.catalog_ref,
                "family": self.family,
                "subcategory": self.subcategory,
                "reporting_mode": self.reporting_mode(),
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

    def execution_plan_output(self) -> ExecutionPlanOutput:
        if self._execution_plan is None:
            self._build_outputs()
        assert self._execution_plan is not None
        return self._execution_plan

    def normalized_output(self) -> AlertAlgorithmOutput:
        if self._normalized_output is None:
            self._build_outputs()
        assert self._normalized_output is not None
        return self._normalized_output

    def current_decision(self) -> AlgorithmDecision:
        latest = self.normalized_output().points[-1]
        return AlgorithmDecision(
            trend=latest.signal_label,
            confidence=latest.confidence or 0.0,
            buy_signal=latest.signal_label == "buy",
            sell_signal=latest.signal_label == "sell",
            no_signal=latest.signal_label == "neutral",
            annotations={"alg_name": self.algorithm_key, **latest.diagnostics},
        )

    def interactive_report_payloads(self) -> list[tuple[dict[str, Any], str]]:
        return [
            (
                {
                    "algorithm_key": self.algorithm_key,
                    "data": self.normalized_output().to_dict(),
                    "execution_plan": self.execution_plan_output().to_dict(),
                },
                f"execution_{self.algorithm_key}_{self.symbol}",
            )
        ]
