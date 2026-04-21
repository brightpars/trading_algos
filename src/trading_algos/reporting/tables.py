from __future__ import annotations

from typing import Any

from trading_algos.evaluation.models import EvaluationResult
from trading_algos.reporting.models import ReportTable


def build_report_tables(
    *,
    algorithm_summary: dict[str, Any],
    signal_summary: dict[str, Any],
    evaluation_results: list[EvaluationResult],
) -> list[ReportTable]:
    parameter_rows = [
        {"parameter": key, "value": value}
        for key, value in (algorithm_summary.get("parameter_values") or {}).items()
    ]
    metric_rows = []
    trade_rows: list[dict[str, Any]] = []
    for result in evaluation_results:
        for key, value in result.metrics.items():
            if isinstance(value, list | dict):
                continue
            metric_rows.append(
                {"group": result.metric_group, "metric": key, "value": value}
            )
        if result.metric_group == "trading_backtest":
            trade_rows = [
                {"metric": metric, "value": result.metrics.get(metric)}
                for metric in (
                    "trade_count",
                    "win_rate",
                    "loss_rate",
                    "average_return_per_trade",
                    "median_return_per_trade",
                    "cumulative_return",
                    "max_drawdown",
                    "average_holding_duration_bars",
                    "exposure_ratio",
                    "turnover_estimate",
                    "profit_factor",
                    "recovery_factor",
                )
                if metric in result.metrics
            ]
    return [
        ReportTable(
            table_id="parameter_table",
            title="Parameters",
            columns=["parameter", "value"],
            rows=parameter_rows,
            description="Parameter values used for this run.",
        ),
        ReportTable(
            table_id="algorithm_metadata",
            title="Algorithm metadata",
            columns=["field", "value"],
            rows=[
                {"field": key, "value": value}
                for key, value in algorithm_summary.items()
            ],
            description="Normalized algorithm or configuration metadata.",
        ),
        ReportTable(
            table_id="signal_summary",
            title="Signal summary",
            columns=["metric", "value"],
            rows=[
                {"metric": key, "value": value} for key, value in signal_summary.items()
            ],
            description="Counts and density of generated signals.",
        ),
        ReportTable(
            table_id="evaluation_metrics",
            title="Evaluation metrics",
            columns=["group", "metric", "value"],
            rows=metric_rows,
            description="Metrics grouped by evaluation layer.",
        ),
        ReportTable(
            table_id="trade_summary",
            title="Trade summary",
            columns=["metric", "value"],
            rows=trade_rows,
            description="Trade and backtest summary under shared assumptions.",
        ),
    ]
