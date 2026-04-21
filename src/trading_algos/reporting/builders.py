from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from trading_algos.alertgen.contracts.outputs import AlertAlgorithmOutput
from trading_algos.evaluation.models import EvaluationResult
from trading_algos.reporting.models import (
    AnalysisBlock,
    ChartAxis,
    ReportChart,
    ReportDocument,
    ReportTable,
)


def _metric(result_list: list[EvaluationResult], group: str, name: str) -> Any:
    for result in result_list:
        if result.metric_group == group:
            return result.metrics.get(name)
    return None


def _build_summary_cards(result_list: list[EvaluationResult]) -> list[dict[str, Any]]:
    cards = []
    for title, group, key in (
        ("Buy precision", "signal_quality", "buy_precision"),
        ("Sell precision", "signal_quality", "sell_precision"),
        ("Cumulative return", "trading_backtest", "cumulative_return"),
        ("Max drawdown", "trading_backtest", "max_drawdown"),
        ("Win rate", "trading_backtest", "win_rate"),
    ):
        value = _metric(result_list, group, key)
        cards.append({"label": title, "value": value, "metric_key": key})
    return cards


def _build_charts(
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

    equity_curve = _metric(evaluation_results, "trading_backtest", "equity_curve")
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

    drawdown_curve = _metric(evaluation_results, "trading_backtest", "drawdown_curve")
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


def _build_tables(
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
    for result in evaluation_results:
        for key, value in result.metrics.items():
            if isinstance(value, list | dict):
                continue
            metric_rows.append(
                {
                    "group": result.metric_group,
                    "metric": key,
                    "value": value,
                }
            )
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
    ]


def _build_analysis_blocks(
    *,
    signal_summary: dict[str, Any],
    evaluation_results: list[EvaluationResult],
) -> list[AnalysisBlock]:
    total_rows = int(signal_summary.get("total_rows", 0) or 0)
    signal_count = int(signal_summary.get("buy_count", 0) or 0) + int(
        signal_summary.get("sell_count", 0) or 0
    )
    activity_ratio = (signal_count / total_rows) if total_rows else 0.0
    cumulative_return = _metric(
        evaluation_results, "trading_backtest", "cumulative_return"
    )
    max_drawdown = _metric(evaluation_results, "trading_backtest", "max_drawdown")
    buy_precision = _metric(evaluation_results, "signal_quality", "buy_precision")
    sell_precision = _metric(evaluation_results, "signal_quality", "sell_precision")
    trade_count = _metric(evaluation_results, "trading_backtest", "trade_count")
    warnings = [warning for result in evaluation_results for warning in result.warnings]

    return [
        AnalysisBlock(
            block_id="overall_behavior",
            title="Overall behavior summary",
            body=(
                f"Strategy activity_ratio={activity_ratio:.3f} with signal_count={signal_count} over total_rows={total_rows}; "
                "current implementation reflects alert-style signal behavior."
            ),
        ),
        AnalysisBlock(
            block_id="performance_summary",
            title="Performance summary",
            body=(
                f"Baseline backtest cumulative_return={cumulative_return} and max_drawdown={max_drawdown}; "
                "interpret these under the shared first-pass assumptions only."
            ),
        ),
        AnalysisBlock(
            block_id="signal_quality_summary",
            title="Signal quality summary",
            body=(
                f"Signal quality buy_precision={buy_precision} sell_precision={sell_precision}; "
                f"trade_count={trade_count}."
            ),
        ),
        AnalysisBlock(
            block_id="risk_summary",
            title="Risk summary",
            body=(
                f"Current risk read uses max_drawdown={max_drawdown}; "
                "robustness and subperiod diagnostics are not implemented yet."
            ),
        ),
        AnalysisBlock(
            block_id="limitations",
            title="Limitations / caveats",
            body=(
                "; ".join(warnings)
                if warnings
                else "This report currently implements signal quality and baseline backtest layers only."
            ),
            severity="warning",
        ),
    ]


def build_alert_algorithm_report(
    *,
    experiment_summary: dict[str, Any],
    algorithm_summary: dict[str, Any],
    signal_summary: dict[str, Any],
    normalized_output: AlertAlgorithmOutput,
    evaluation_results: list[EvaluationResult],
    algorithm_chart_payload: dict[str, Any] | None,
    diagnostics: dict[str, Any] | None = None,
) -> ReportDocument:
    evaluation_summary = {
        "evaluators": [result.to_dict() for result in evaluation_results],
        "headline_metrics": {
            "buy_precision": _metric(
                evaluation_results, "signal_quality", "buy_precision"
            ),
            "sell_precision": _metric(
                evaluation_results, "signal_quality", "sell_precision"
            ),
            "cumulative_return": _metric(
                evaluation_results, "trading_backtest", "cumulative_return"
            ),
            "max_drawdown": _metric(
                evaluation_results, "trading_backtest", "max_drawdown"
            ),
        },
        "metric_groups": [result.metric_group for result in evaluation_results],
        "notes_about_unavailable_metrics": [
            warning for result in evaluation_results for warning in result.warnings
        ],
    }
    return ReportDocument(
        report_version="1.0",
        experiment_summary=experiment_summary,
        algorithm_summary=algorithm_summary,
        evaluation_summary=evaluation_summary,
        charts=_build_charts(
            output=normalized_output,
            algorithm_chart_payload=algorithm_chart_payload,
            evaluation_results=evaluation_results,
            title_prefix=str(
                algorithm_summary.get("algorithm_name")
                or algorithm_summary.get("algorithm_key")
                or "Report"
            ),
        ),
        tables=_build_tables(
            algorithm_summary=algorithm_summary,
            signal_summary=signal_summary,
            evaluation_results=evaluation_results,
        ),
        analysis_blocks=_build_analysis_blocks(
            signal_summary=signal_summary,
            evaluation_results=evaluation_results,
        ),
        artifacts={
            "normalized_outputs": normalized_output.to_dict(),
        },
        diagnostics=diagnostics or {},
        summary_cards=_build_summary_cards(evaluation_results),
    )


def build_configuration_report(
    *,
    experiment_summary: dict[str, Any],
    algorithm_summary: dict[str, Any],
    signal_summary: dict[str, Any],
    normalized_output: AlertAlgorithmOutput,
    evaluation_results: list[EvaluationResult],
    algorithm_chart_payload: dict[str, Any] | None,
    node_results: list[dict[str, Any]],
) -> ReportDocument:
    report = build_alert_algorithm_report(
        experiment_summary=experiment_summary,
        algorithm_summary=algorithm_summary,
        signal_summary=signal_summary,
        normalized_output=normalized_output,
        evaluation_results=evaluation_results,
        algorithm_chart_payload=algorithm_chart_payload,
        diagnostics={
            "node_results": node_results,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    return report
