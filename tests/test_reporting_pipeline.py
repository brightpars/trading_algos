from trading_algos.alertgen.contracts.outputs import (
    AlertAlgorithmOutput,
    AlertSeriesPoint,
)
from trading_algos.evaluation.pipeline import evaluate_alert_algorithm_output
from trading_algos.reporting.builders import build_alert_algorithm_report


def test_reporting_pipeline_builds_standardized_report() -> None:
    output = AlertAlgorithmOutput(
        algorithm_key="sample_alg",
        points=(
            AlertSeriesPoint(
                timestamp="2025-01-01 10:00:00", signal_label="buy", confidence=0.8
            ),
            AlertSeriesPoint(
                timestamp="2025-01-01 10:01:00", signal_label="neutral", confidence=0.5
            ),
            AlertSeriesPoint(
                timestamp="2025-01-01 10:02:00", signal_label="sell", confidence=0.9
            ),
        ),
        derived_series={"close": [10.0, 11.0, 10.5]},
        summary_metrics={"buy_precision": 1.0},
        metadata={"algorithm_name": "sample_alg"},
    )
    evaluations = evaluate_alert_algorithm_output(
        output=output,
        signal_quality_metrics={"buy_precision": 1.0, "sell_precision": 1.0},
    )

    report = build_alert_algorithm_report(
        experiment_summary={"experiment_id": "exp_1"},
        algorithm_summary={
            "algorithm_key": "sample_alg",
            "algorithm_name": "sample_alg",
            "parameter_values": {},
        },
        signal_summary={"buy_count": 1, "sell_count": 1, "total_rows": 3},
        normalized_output=output,
        evaluation_results=evaluations,
        algorithm_chart_payload={"data": [], "layout": {}},
    )

    payload = report.to_dict()
    assert payload["report_version"] == "1.0"
    assert payload["experiment_summary"]["experiment_id"] == "exp_1"
    assert payload["charts"]
    assert payload["tables"]
    assert payload["analysis_blocks"]
    assert payload["evaluation_summary"]["metric_groups"] == [
        "signal_quality",
        "trading_backtest",
    ]
