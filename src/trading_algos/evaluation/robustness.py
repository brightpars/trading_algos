from __future__ import annotations

from trading_algos.alertgen.contracts.outputs import AlertAlgorithmOutput
from trading_algos.evaluation.models import EvaluationResult


def evaluate_robustness(output: AlertAlgorithmOutput) -> EvaluationResult:
    close_values = [
        float(value)
        for value in output.derived_series.get("close", [])
        if isinstance(value, int | float)
    ]
    if len(close_values) < 4:
        return EvaluationResult(
            evaluator_id="robustness_v1",
            evaluator_version="1.0",
            metric_group="robustness",
            applies=False,
            metrics={},
            warnings=("Not enough history for robustness evaluation.",),
        )
    midpoint = len(close_values) // 2
    first_half = close_values[:midpoint]
    second_half = close_values[midpoint:]
    first_return = (first_half[-1] / first_half[0]) - 1.0 if first_half[0] else 0.0
    second_return = (second_half[-1] / second_half[0]) - 1.0 if second_half[0] else 0.0
    regime_split = {
        "up_bars": sum(
            1 for current, nxt in zip(close_values, close_values[1:]) if nxt > current
        ),
        "down_bars": sum(
            1 for current, nxt in zip(close_values, close_values[1:]) if nxt < current
        ),
    }
    return EvaluationResult(
        evaluator_id="robustness_v1",
        evaluator_version="1.0",
        metric_group="robustness",
        applies=True,
        metrics={
            "rolling_window_count": 2,
            "best_subperiod_return": max(first_return, second_return),
            "worst_subperiod_return": min(first_return, second_return),
            "subperiod_returns": [first_return, second_return],
            "performance_by_regime": regime_split,
        },
        warnings=(),
    )
