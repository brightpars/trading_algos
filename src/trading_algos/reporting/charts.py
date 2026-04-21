from __future__ import annotations

from typing import Any

from trading_algos.alertgen.contracts.outputs import AlertAlgorithmOutput
from trading_algos.evaluation.models import EvaluationResult
from trading_algos.reporting.models import ChartAxis, ReportChart


def metric(result_list: list[EvaluationResult], group: str, name: str) -> Any:
    for result in result_list:
        if result.metric_group == group:
            return result.metrics.get(name)
    return None


def build_report_charts(
    *,
    output: AlertAlgorithmOutput,
    algorithm_chart_payload: dict[str, Any] | None,
    evaluation_results: list[EvaluationResult],
    title_prefix: str,
) -> list[ReportChart]:
    close_series = output.derived_series.get("close", [])
    buy_values = [
        close_series[index]
        if point.signal_label == "buy" and index < len(close_series)
        else None
        for index, point in enumerate(output.points)
    ]
    sell_values = [
        close_series[index]
        if point.signal_label == "sell" and index < len(close_series)
        else None
        for index, point in enumerate(output.points)
    ]
    confidence_values = [point.confidence for point in output.points]
    gt_trend = output.derived_series.get("gt_trend", [])
    predicted_trend = [point.signal_label for point in output.points]
    charts = [
        ReportChart(
            chart_id="price_signals",
            title=f"{title_prefix} Price and Signals",
            category="overview",
            chart_type="timeseries",
            required=True,
            series=[
                {"name": "close", "values": close_series},
                {"name": "buy", "values": buy_values},
                {"name": "sell", "values": sell_values},
            ],
            x_axis=ChartAxis(label="Time"),
            y_axis=ChartAxis(label="Price"),
            description="Shows close price with buy and sell markers.",
            tags=["baseline", "signals"],
            payload=algorithm_chart_payload,
        )
    ]

    indicator_series = [
        {"name": name, "values": values}
        for name, values in output.derived_series.items()
        if name not in {"close", "buy_signal", "sell_signal", "gt_trend"}
    ]
    if indicator_series:
        charts.append(
            ReportChart(
                chart_id="core_indicators",
                title=f"{title_prefix} Core Indicators",
                category="indicators",
                chart_type="timeseries",
                required=True,
                series=indicator_series,
                x_axis=ChartAxis(label="Time"),
                y_axis=ChartAxis(label="Indicator value"),
                description="Shows the main derived indicator series used by the algorithm.",
                tags=["baseline", "indicators"],
            )
        )

    if confidence_values and any(value is not None for value in confidence_values):
        charts.append(
            ReportChart(
                chart_id="signal_confidence",
                title=f"{title_prefix} Confidence",
                category="evaluation",
                chart_type="timeseries",
                required=True,
                series=[{"name": "confidence", "values": confidence_values}],
                x_axis=ChartAxis(label="Time"),
                y_axis=ChartAxis(label="Confidence"),
                description="Shows model confidence for each output point.",
                tags=["baseline", "confidence"],
            )
        )

    if gt_trend:
        charts.append(
            ReportChart(
                chart_id="ground_truth_comparison",
                title=f"{title_prefix} Ground Truth Comparison",
                category="evaluation",
                chart_type="timeseries",
                required=True,
                series=[
                    {"name": "predicted", "values": predicted_trend},
                    {"name": "ground_truth", "values": gt_trend},
                ],
                x_axis=ChartAxis(label="Time"),
                y_axis=ChartAxis(label="Class"),
                description="Shows predicted outputs against the current ground-truth labels.",
                tags=["baseline", "ground-truth"],
            )
        )

    equity_curve = metric(evaluation_results, "trading_backtest", "equity_curve")
    if isinstance(equity_curve, list) and equity_curve:
        charts.append(
            ReportChart(
                chart_id="equity_curve",
                title=f"{title_prefix} Equity Curve",
                category="performance",
                chart_type="timeseries",
                required=True,
                series=[{"name": "equity", "values": equity_curve}],
                x_axis=ChartAxis(label="Step"),
                y_axis=ChartAxis(label="Equity"),
                description="Baseline backtest cumulative equity curve.",
                tags=["baseline", "performance"],
            )
        )

    drawdown_curve = metric(evaluation_results, "trading_backtest", "drawdown_curve")
    if isinstance(drawdown_curve, list) and drawdown_curve:
        charts.append(
            ReportChart(
                chart_id="drawdown_curve",
                title=f"{title_prefix} Drawdown",
                category="performance",
                chart_type="timeseries",
                required=True,
                series=[{"name": "drawdown", "values": drawdown_curve}],
                x_axis=ChartAxis(label="Step"),
                y_axis=ChartAxis(label="Drawdown"),
                description="Baseline backtest drawdown profile.",
                tags=["baseline", "risk"],
            )
        )
    return charts
