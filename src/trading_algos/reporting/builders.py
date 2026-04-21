from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from trading_algos.alertgen.contracts.outputs import AlertAlgorithmOutput
from trading_algos.evaluation.models import EvaluationResult
from trading_algos.reporting.analysis import build_analysis_blocks
from trading_algos.reporting.charts import build_report_charts, metric
from trading_algos.reporting.models import ReportDocument
from trading_algos.reporting.tables import build_report_tables


def _build_summary_cards(result_list: list[EvaluationResult]) -> list[dict[str, Any]]:
    cards = []
    for title, group, key in (
        ("Buy precision", "signal_quality", "buy_precision"),
        ("Sell precision", "signal_quality", "sell_precision"),
        ("Cumulative return", "trading_backtest", "cumulative_return"),
        ("Max drawdown", "trading_backtest", "max_drawdown"),
        ("Win rate", "trading_backtest", "win_rate"),
    ):
        value = metric(result_list, group, key)
        cards.append({"label": title, "value": value, "metric_key": key})
    return cards


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
            "buy_precision": metric(
                evaluation_results, "signal_quality", "buy_precision"
            ),
            "sell_precision": metric(
                evaluation_results, "signal_quality", "sell_precision"
            ),
            "cumulative_return": metric(
                evaluation_results, "trading_backtest", "cumulative_return"
            ),
            "max_drawdown": metric(
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
        charts=build_report_charts(
            output=normalized_output,
            algorithm_chart_payload=algorithm_chart_payload,
            evaluation_results=evaluation_results,
            title_prefix=str(
                algorithm_summary.get("algorithm_name")
                or algorithm_summary.get("algorithm_key")
                or "Report"
            ),
        ),
        tables=build_report_tables(
            algorithm_summary=algorithm_summary,
            signal_summary=signal_summary,
            evaluation_results=evaluation_results,
        ),
        analysis_blocks=build_analysis_blocks(
            signal_summary=signal_summary,
            evaluation_results=evaluation_results,
        ),
        artifacts={
            "normalized_outputs": normalized_output.to_dict(),
            "trade_returns": metric(
                evaluation_results, "trading_backtest", "trade_returns"
            ),
        },
        diagnostics={
            "warnings": [
                warning for result in evaluation_results for warning in result.warnings
            ],
            "notes": [note for result in evaluation_results for note in result.notes],
            **(diagnostics or {}),
        },
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
