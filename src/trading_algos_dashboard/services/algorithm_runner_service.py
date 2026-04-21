from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from trading_algos.alertgen import create_alertgen_algorithm
from trading_algos.evaluation import evaluate_alert_algorithm_output
from trading_algos.reporting import build_alert_algorithm_report

from trading_algos_dashboard.services.chart_service import (
    normalize_interactive_payloads,
)


def run_alert_algorithm(
    *,
    sensor_config: dict[str, Any],
    report_base_path: str,
    candles: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    algorithm, alg_param = create_alertgen_algorithm(
        sensor_config=sensor_config,
        report_base_path=report_base_path,
    )
    algorithm.process_list(list(candles))
    algorithm.evaluate()
    algorithm.write_analysis_report()

    latest_decision = algorithm.current_decision()
    interactive_payloads = normalize_interactive_payloads(
        algorithm.interactive_report_payloads()
    )
    default_chart = algorithm._build_default_signal_chart_payload(  # noqa: SLF001
        title=f"{algorithm.alg_name} signals"
    )

    signal_summary = {
        "buy_count": len(algorithm.buy_signals),
        "sell_count": len(algorithm.sell_signals),
        "total_rows": len(algorithm.data_list),
        "no_signal_count": sum(
            1 for row in algorithm.data_list if row.get("no_SIGNAL")
        ),
    }
    normalized_output = algorithm.normalized_output()
    evaluation_results = evaluate_alert_algorithm_output(
        output=normalized_output,
        signal_quality_metrics=algorithm.eval_dict,
    )
    algorithm_metadata = algorithm.algorithm_metadata()
    report = build_alert_algorithm_report(
        experiment_summary={},
        algorithm_summary={
            "algorithm_key": sensor_config["alg_key"],
            "algorithm_name": algorithm.alg_name,
            "family": algorithm_metadata.get("family", "alertgen"),
            "subcategory": algorithm_metadata.get("subcategory", "trend"),
            "algorithm_version": "1.0",
            "parameter_values": alg_param,
            "runtime_kind": "single_algorithm",
            "asset_scope": sensor_config["symbol"],
            "input_domains": ["candles"],
            "output_modes": ["alerts"],
            "warmup_period": algorithm.minimum_history(),
        },
        signal_summary=signal_summary,
        normalized_output=normalized_output,
        evaluation_results=evaluation_results,
        algorithm_chart_payload=default_chart,
        diagnostics={
            "interactive_payloads": interactive_payloads,
        },
    )

    return {
        "input_kind": "single_algorithm",
        "alg_key": sensor_config["alg_key"],
        "alg_name": algorithm.alg_name,
        "alg_param": alg_param,
        "algorithm_metadata": algorithm_metadata,
        "eval_dict": algorithm.eval_dict,
        "evaluator_outputs": [result.to_dict() for result in evaluation_results],
        "latest_decision": {
            "trend": latest_decision.trend,
            "confidence": latest_decision.confidence,
            "buy_signal": latest_decision.buy_signal,
            "sell_signal": latest_decision.sell_signal,
            "buy_range_signal": latest_decision.buy_range_signal,
            "sell_range_signal": latest_decision.sell_range_signal,
            "no_signal": latest_decision.no_signal,
            "annotations": latest_decision.annotations,
        },
        "signal_summary": signal_summary,
        "report_refs": {
            "report_path": algorithm.report_path,
            "report_data_path": f"{algorithm.report_path}/{algorithm.data_name}.dict",
            "figure_path": f"{algorithm.report_path}/{algorithm.data_name}.png",
        },
        "interactive_payloads": interactive_payloads,
        "chart_payload": default_chart,
        "normalized_output": normalized_output.to_dict(),
        "report": report.to_dict(),
    }
