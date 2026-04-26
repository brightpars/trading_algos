from __future__ import annotations

from typing import Any

from trading_algos.alertgen.algorithms.composite.rule_based_combination.helpers import (
    align_child_outputs,
    build_child_contribution_rows,
    direction_to_signal_label,
    evaluate_child_row_warmup,
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
from trading_algos.regime.state import (
    apply_regime_hysteresis,
    clamp_probability,
    normalize_probability_map,
    smooth_regime_probabilities,
)


def _extract_regime_probabilities(
    row: dict[str, Any],
    *,
    regime_field: str,
) -> dict[str, float]:
    raw_map = row.get(regime_field, row.get("regime_probabilities", {}))
    if not isinstance(raw_map, dict):
        raise ValueError(
            "regime_switching_hmm_gating: regime probabilities must be a dict"
        )
    return normalize_probability_map(
        {str(key): float(value) for key, value in raw_map.items()}
    )


class RegimeSwitchingHmmGatingAlertAlgorithm:
    catalog_ref = "combination:7"

    def __init__(
        self, *, algorithm_key: str, symbol: str, params: dict[str, Any]
    ) -> None:
        self.algorithm_key = algorithm_key
        self.alg_name = algorithm_key
        self.symbol = symbol
        self.params = params
        self.evaluate_window_len = 1
        self.date = ""
        self.eval_dict: dict[str, Any] = {}

        raw_rows = [dict(row) for row in params["rows"]]
        self._aligned_rows = align_child_outputs(raw_rows)
        self._output = self._build_output()
        self.latest_predicted_trend = (
            self._output.points[-1].signal_label if self._output.points else "neutral"
        )
        self.latest_predicted_trend_confidence = (
            float(self._output.points[-1].confidence or 0.0)
            if self._output.points
            else 0.0
        )

    def minimum_history(self) -> int:
        return 1

    def algorithm_metadata(self) -> dict[str, Any]:
        return AlgorithmMetadata(
            alg_name=self.alg_name,
            symbol=self.symbol,
            date=self.date,
            evaluate_window_len=self.evaluate_window_len,
        ).to_dict()

    def current_decision(self) -> AlgorithmDecision:
        return AlgorithmDecision(
            trend=self.latest_predicted_trend,
            confidence=self.latest_predicted_trend_confidence,
            buy_signal=self.latest_predicted_trend == "buy",
            sell_signal=self.latest_predicted_trend == "sell",
            no_signal=self.latest_predicted_trend == "neutral",
            annotations={"alg_name": self.alg_name},
        )

    def process_list(self, _data_list: list[dict[str, Any]]) -> None:
        return None

    def normalized_output(self) -> AlertAlgorithmOutput:
        return self._output

    def interactive_report_payloads(self) -> list[tuple[dict[str, Any], str]]:
        return [
            (
                {
                    "algorithm_key": self.algorithm_key,
                    "data": self._output.to_dict(),
                },
                f"composite_report_{self.algorithm_key}_{self.symbol}",
            )
        ]

    def _build_output(self) -> AlertAlgorithmOutput:
        points: list[AlertSeriesPoint] = []
        derived_series: dict[str, list[Any]] = {
            "regime_label": [],
            "regime_confidence": [],
            "regime_probabilities": [],
            "active_child_keys": [],
            "gated_child_keys": [],
            "warmup_ready": [],
            "warmup_diagnostics": [],
            "child_contributions": [],
            "reason_codes": [],
        }
        previous_probability_map: dict[str, float] | None = None
        previous_label: str | None = None
        latest_child_outputs: tuple[NormalizedChildOutput, ...] = ()

        for aligned_row in self._aligned_rows:
            warmup = evaluate_child_row_warmup(
                aligned_row,
                required_child_count=int(self.params["expected_child_count"]),
            )
            raw_probabilities = _extract_regime_probabilities(
                {**aligned_row.metadata},
                regime_field=str(self.params["regime_field"]),
            )
            smoothed_probabilities = smooth_regime_probabilities(
                previous_probability_map,
                raw_probabilities,
                smoothing=float(self.params["smoothing"]),
            )
            regime_label = apply_regime_hysteresis(
                previous_label,
                smoothed_probabilities,
                switch_threshold=float(self.params["switch_threshold"]),
            )
            regime_confidence = clamp_probability(
                smoothed_probabilities.get(regime_label, 0.0)
            )
            active_child_keys = tuple(self.params["regime_map"].get(regime_label, []))
            child_by_key = {
                child.child_key: child for child in aligned_row.child_outputs
            }
            active_children = tuple(
                child_by_key[child_key]
                for child_key in active_child_keys
                if child_key in child_by_key
            )
            gated_child_keys = tuple(
                child.child_key
                for child in aligned_row.child_outputs
                if child.child_key not in active_child_keys
            )

            reason_codes: tuple[str, ...]
            if not warmup.is_ready:
                signal_label = str(self.params["default_signal"])
                confidence = 0.0
                score = 0.0
                reason_codes = ("warmup_pending", warmup.reason_code)
            elif not active_children:
                signal_label = str(self.params["default_signal"])
                confidence = regime_confidence if signal_label != "neutral" else 0.0
                score = 0.0
                reason_codes = ("no_active_children",)
            else:
                net_direction = sum(
                    int(child.direction or 0) for child in active_children
                )
                signal_label = direction_to_signal_label(net_direction)
                score = max(
                    -1.0,
                    min(
                        1.0,
                        sum(float(child.score or 0.0) for child in active_children)
                        / len(active_children),
                    ),
                )
                confidence = min(
                    1.0,
                    regime_confidence
                    * (
                        sum(float(child.confidence or 0.0) for child in active_children)
                        / len(active_children)
                    ),
                )
                reason_codes = ("regime_gate_active", f"regime={regime_label}")

            child_contributions = build_child_contribution_rows(active_children)
            diagnostics = {
                "active_regime": regime_label,
                "regime_confidence": regime_confidence,
                "regime_probabilities": dict(smoothed_probabilities),
                "active_child_keys": list(active_child_keys),
                "gated_child_keys": list(gated_child_keys),
                "warmup_ready": warmup.is_ready,
                **warmup.diagnostics,
            }
            points.append(
                AlertSeriesPoint(
                    timestamp=aligned_row.timestamp,
                    signal_label=signal_label,
                    score=score,
                    confidence=confidence,
                    reason_codes=reason_codes,
                    diagnostics=diagnostics,
                )
            )
            derived_series["regime_label"].append(regime_label)
            derived_series["regime_confidence"].append(regime_confidence)
            derived_series["regime_probabilities"].append(dict(smoothed_probabilities))
            derived_series["active_child_keys"].append(list(active_child_keys))
            derived_series["gated_child_keys"].append(list(gated_child_keys))
            derived_series["warmup_ready"].append(warmup.is_ready)
            derived_series["warmup_diagnostics"].append(dict(warmup.diagnostics))
            derived_series["child_contributions"].append(child_contributions)
            derived_series["reason_codes"].append(list(reason_codes))

            latest_child_outputs = tuple(
                NormalizedChildOutput(
                    child_key=child.child_key,
                    output_kind="composite_child",
                    signal_label=child.signal_label,
                    score=child.score,
                    confidence=child.confidence,
                    regime_label=regime_label,
                    direction=child.direction,
                    diagnostics={
                        **child.diagnostics,
                        "active_regime": regime_label,
                        "regime_confidence": regime_confidence,
                        "regime_probabilities": dict(smoothed_probabilities),
                        "active_child_keys": list(active_child_keys),
                        "gated_child_keys": list(gated_child_keys),
                        "warmup_ready": warmup.is_ready,
                        **warmup.diagnostics,
                        "gated": child.child_key in gated_child_keys,
                    },
                    reason_codes=child.reason_codes,
                    event_markers=child.event_markers,
                )
                for child in aligned_row.child_outputs
            )
            previous_probability_map = smoothed_probabilities
            previous_label = regime_label

        return AlertAlgorithmOutput(
            algorithm_key=self.algorithm_key,
            points=tuple(points),
            derived_series=derived_series,
            summary_metrics={"row_count": len(points)},
            metadata={
                "family": "adaptive_state_based",
                "subcategory": "regime",
                "catalog_ref": self.catalog_ref,
                "supports_composition": True,
                "output_contract_version": "1.0",
                "reporting_mode": "composite_trace",
                "warmup_period": 1,
            },
            child_outputs=latest_child_outputs,
        )


def build_regime_switching_hmm_gating_algorithm(
    *, algorithm_key: str, symbol: str, alg_param: dict[str, Any], **_kwargs: Any
) -> RegimeSwitchingHmmGatingAlertAlgorithm:
    return RegimeSwitchingHmmGatingAlertAlgorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        params=alg_param,
    )
