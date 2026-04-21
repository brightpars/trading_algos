from __future__ import annotations

from typing import Any

from trading_algos.alertgen.contracts.outputs import AlertAlgorithmOutput
from trading_algos.evaluation.backtest import evaluate_baseline_backtest
from trading_algos.evaluation.family_specific import evaluate_family_specific
from trading_algos.evaluation.models import EvaluationResult
from trading_algos.evaluation.robustness import evaluate_robustness
from trading_algos.evaluation.signal_quality import evaluate_signal_quality


def evaluate_alert_algorithm_output(
    *,
    output: AlertAlgorithmOutput,
    signal_quality_metrics: dict[str, Any],
) -> list[EvaluationResult]:
    return [
        evaluate_signal_quality(output=output, metrics=signal_quality_metrics),
        evaluate_baseline_backtest(output),
        evaluate_robustness(output),
        evaluate_family_specific(output),
    ]
