from __future__ import annotations

from typing import Any

from trading_algos.alertgen.contracts.outputs import AlertAlgorithmOutput
from trading_algos.evaluation.models import EvaluationResult


def evaluate_signal_quality(
    *,
    output: AlertAlgorithmOutput,
    metrics: dict[str, Any],
) -> EvaluationResult:
    return EvaluationResult(
        evaluator_id="signal_quality_v1",
        evaluator_version="1.0",
        metric_group="signal_quality",
        applies=True,
        metrics=dict(metrics),
        warnings=(),
        applicability_status="applicable",
        notes=("Current implementation wraps the existing alert evaluation metrics.",),
    )
