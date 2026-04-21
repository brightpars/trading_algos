from __future__ import annotations

from trading_algos.alertgen.contracts.outputs import AlertAlgorithmOutput
from trading_algos.evaluation.models import EvaluationResult


def evaluate_family_specific(output: AlertAlgorithmOutput) -> EvaluationResult:
    family = str(output.metadata.get("family", "trend"))
    return EvaluationResult(
        evaluator_id="family_specific_v1",
        evaluator_version="1.0",
        metric_group="family_specific",
        applies=True,
        metrics={
            "family": family,
            "extension_status": "base extension hook implemented",
        },
        warnings=(
            "Specialized family metrics are implemented as extension hooks only in this phase.",
        ),
    )
