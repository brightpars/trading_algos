from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from trading_algos.alertgen.algorithms.composite.rule_based_combination.helpers import (
    AlignedCompositeInputRow,
    align_child_outputs,
    build_child_contribution_rows,
    clamp_confidence,
    direction_to_signal_label,
)
from trading_algos.alertgen.contracts.outputs import (
    AlertAlgorithmOutput,
    AlertSeriesPoint,
    NormalizedChildOutput,
)
from trading_algos.alertgen.shared_utils.models import (
    AlgorithmDecision,
    AlgorithmMetadata,
)


@dataclass(frozen=True)
class BooleanCombinationDecision:
    direction: int
    confidence: float
    diagnostics: dict[str, Any]


def evaluate_boolean_gating_row(
    row: AlignedCompositeInputRow,
    *,
    mode: str,
    tie_policy: str,
    veto_sell_count: int,
) -> BooleanCombinationDecision:
    directions = [child.direction or 0 for child in row.child_outputs]
    buy_count = sum(1 for direction in directions if direction > 0)
    sell_count = sum(1 for direction in directions if direction < 0)
    neutral_count = sum(1 for direction in directions if direction == 0)
    child_count = len(directions)
    bullish_confidences = [
        child.confidence or 0.0
        for child in row.child_outputs
        if (child.direction or 0) > 0
    ]
    bearish_confidences = [
        child.confidence or 0.0
        for child in row.child_outputs
        if (child.direction or 0) < 0
    ]

    resolved_direction = 0
    if sell_count >= veto_sell_count > 0:
        resolved_direction = -1
        decision_reason = "sell_veto"
    elif mode == "and":
        if child_count > 0 and buy_count == child_count:
            resolved_direction = 1
            decision_reason = "all_buy"
        elif child_count > 0 and sell_count == child_count:
            resolved_direction = -1
            decision_reason = "all_sell"
        else:
            decision_reason = "and_neutral"
    elif mode == "or":
        if buy_count > 0 and sell_count == 0:
            resolved_direction = 1
            decision_reason = "any_buy"
        elif sell_count > 0 and buy_count == 0:
            resolved_direction = -1
            decision_reason = "any_sell"
        else:
            decision_reason = "or_conflict"
    else:
        if buy_count > sell_count:
            resolved_direction = 1
            decision_reason = "majority_buy"
        elif sell_count > buy_count:
            resolved_direction = -1
            decision_reason = "majority_sell"
        elif tie_policy == "buy":
            resolved_direction = 1
            decision_reason = "tie_break_buy"
        elif tie_policy == "sell":
            resolved_direction = -1
            decision_reason = "tie_break_sell"
        else:
            decision_reason = "tie_neutral"

    if resolved_direction > 0:
        confidence = min(bullish_confidences) if bullish_confidences else 0.0
    elif resolved_direction < 0:
        confidence = min(bearish_confidences) if bearish_confidences else 0.0
    else:
        confidence = 0.0

    diagnostics = {
        "mode": mode,
        "buy_count": buy_count,
        "sell_count": sell_count,
        "neutral_count": neutral_count,
        "child_count": child_count,
        "tie_policy": tie_policy,
        "veto_sell_count": veto_sell_count,
        "decision_reason": decision_reason,
        "child_contributions": build_child_contribution_rows(row.child_outputs),
    }
    return BooleanCombinationDecision(
        direction=resolved_direction,
        confidence=clamp_confidence(confidence),
        diagnostics=diagnostics,
    )


class HardBooleanGatingAlertAlgorithm:
    def __init__(
        self,
        *,
        algorithm_key: str,
        symbol: str,
        rows: tuple[AlignedCompositeInputRow, ...],
        params: dict[str, Any],
    ):
        self.algorithm_key = algorithm_key
        self.alg_name = algorithm_key
        self.symbol = symbol
        self.rows = rows
        self.params = params
        self.evaluate_window_len = 1
        self.date = ""
        self.eval_dict: dict[str, Any] = {}
        self.latest_predicted_trend = "neutral"
        self.latest_predicted_trend_confidence = 0.0

    def process_list(self, _data_list: list[dict[str, Any]]) -> None:
        output = self.normalized_output()
        if not output.points:
            self.latest_predicted_trend = "neutral"
            self.latest_predicted_trend_confidence = 0.0
            return
        latest = output.points[-1]
        self.latest_predicted_trend = latest.signal_label
        self.latest_predicted_trend_confidence = float(latest.confidence or 0.0)

    def algorithm_metadata(self) -> dict[str, Any]:
        return AlgorithmMetadata(
            alg_name=self.alg_name,
            symbol=self.symbol,
            date=self.date,
            evaluate_window_len=self.evaluate_window_len,
        ).to_dict()

    def minimum_history(self) -> int:
        return 1

    def current_decision(self) -> AlgorithmDecision:
        return AlgorithmDecision(
            trend=self.latest_predicted_trend,
            confidence=self.latest_predicted_trend_confidence,
            buy_signal=self.latest_predicted_trend == "buy",
            sell_signal=self.latest_predicted_trend == "sell",
            no_signal=self.latest_predicted_trend == "neutral",
            annotations={"alg_name": self.alg_name},
        )

    def interactive_report_payloads(self) -> list[tuple[dict[str, Any], str]]:
        return []

    def normalized_output(self) -> AlertAlgorithmOutput:
        points: list[AlertSeriesPoint] = []
        derived_series: dict[str, list[Any]] = {
            "buy_signal": [],
            "sell_signal": [],
            "composite_score": [],
            "mode": [],
        }
        child_outputs: list[NormalizedChildOutput] = []
        for row in self.rows:
            decision = evaluate_boolean_gating_row(
                row,
                mode=str(self.params["mode"]),
                tie_policy=str(self.params["tie_policy"]),
                veto_sell_count=int(self.params["veto_sell_count"]),
            )
            signal_label = direction_to_signal_label(decision.direction)
            reason_codes = (str(decision.diagnostics["decision_reason"]),)
            points.append(
                AlertSeriesPoint(
                    timestamp=row.timestamp,
                    signal_label=signal_label,
                    score=float(decision.direction),
                    confidence=decision.confidence,
                    reason_codes=reason_codes,
                )
            )
            derived_series["buy_signal"].append(decision.direction > 0)
            derived_series["sell_signal"].append(decision.direction < 0)
            derived_series["composite_score"].append(float(decision.direction))
            derived_series["mode"].append(self.params["mode"])
            child_outputs.extend(row.child_outputs)
        return AlertAlgorithmOutput(
            algorithm_key=self.algorithm_key,
            points=tuple(points),
            derived_series=derived_series,
            metadata={
                "family": "rule_based_combination",
                "subcategory": "hard",
                "catalog_ref": "combination:1",
                "supports_composition": True,
                "output_contract_version": "1.0",
                "params": dict(self.params),
            },
            child_outputs=tuple(child_outputs),
        )


def build_hard_boolean_gating_algorithm(
    *,
    algorithm_key: str,
    symbol: str,
    alg_param: dict[str, Any],
    sensor_config: dict[str, Any] | None = None,
    **_kwargs: Any,
) -> HardBooleanGatingAlertAlgorithm:
    del sensor_config
    rows = align_child_outputs(list(alg_param["rows"]))
    return HardBooleanGatingAlertAlgorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        rows=rows,
        params=alg_param,
    )
