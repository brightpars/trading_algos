from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from trading_algos.alertgen.algorithms.composite.shared_rebalance import (
    CompositeRebalanceRow,
    build_portfolio_weight_output,
    build_rebalance_alert_output,
    clamp_signed_unit,
    clamp_unit_interval,
)
from trading_algos.alertgen.contracts.outputs import AlertAlgorithmOutput
from trading_algos.alertgen.shared_utils.models import (
    AlgorithmDecision,
    AlgorithmMetadata,
)
from trading_algos.contracts.portfolio_output import RankedAsset
from trading_algos.rl.environment import (
    RLActionDecision,
    RLParsedEnvironment,
    choose_action,
    parse_rl_environment_rows,
)


@dataclass(frozen=True)
class RLControllerConfig:
    action_weight_templates: dict[str, dict[str, float]]
    action_aliases: dict[str, str]
    action_overrides: dict[str, float]
    gross_exposure_limit: float
    min_history: int


def _normalize_weight_map(
    weights: Mapping[str, float], *, gross_exposure_limit: float
) -> dict[str, float]:
    cleaned = {
        str(symbol): float(weight)
        for symbol, weight in weights.items()
        if float(weight) != 0.0
    }
    gross = sum(abs(weight) for weight in cleaned.values())
    if gross <= 0.0:
        return {}
    scale = min(1.0, float(gross_exposure_limit) / gross)
    return {symbol: weight * scale for symbol, weight in cleaned.items()}


def build_rl_controller_config(params: Mapping[str, Any]) -> RLControllerConfig:
    raw_templates = params.get("action_weight_templates", {})
    action_weight_templates: dict[str, dict[str, float]] = {}
    if isinstance(raw_templates, Mapping):
        for action_key, raw_weight_map in raw_templates.items():
            if not isinstance(raw_weight_map, Mapping):
                continue
            action_weight_templates[str(action_key)] = {
                str(symbol): float(weight)
                for symbol, weight in raw_weight_map.items()
                if float(weight) != 0.0
            }
    raw_aliases = params.get("action_aliases", {})
    action_aliases = (
        {str(key): str(value) for key, value in raw_aliases.items()}
        if isinstance(raw_aliases, Mapping)
        else {}
    )
    raw_overrides = params.get("action_overrides", {})
    action_overrides = (
        {str(key): float(value) for key, value in raw_overrides.items()}
        if isinstance(raw_overrides, Mapping)
        else {}
    )
    return RLControllerConfig(
        action_weight_templates=action_weight_templates,
        action_aliases=action_aliases,
        action_overrides=action_overrides,
        gross_exposure_limit=float(params.get("gross_exposure_limit", 1.0)),
        min_history=int(params.get("min_history", 1)),
    )


def _extract_candidate_weights(
    parsed_environment: RLParsedEnvironment,
    row_index: int,
    action_key: str,
) -> dict[str, float]:
    row = parsed_environment.rows[row_index]
    prefix = f"{action_key}:"
    weights = {
        candidate_key[len(prefix) :]: weight
        for candidate_key, weight in row.candidate_weights.items()
        if candidate_key.startswith(prefix)
    }
    return weights


def resolve_rl_action_decision(
    parsed_environment: RLParsedEnvironment,
    *,
    row_index: int,
    allowed_actions: Sequence[str] | None,
    config: RLControllerConfig,
    diagnostics_builder: Callable[..., dict[str, Any]],
) -> RLActionDecision:
    row = parsed_environment.rows[row_index]
    raw_action_key, action_score = choose_action(
        row,
        allowed_actions=allowed_actions,
        action_overrides=config.action_overrides,
    )
    resolved_action_key = config.action_aliases.get(raw_action_key, raw_action_key)
    weights = _extract_candidate_weights(parsed_environment, row_index, raw_action_key)
    if not weights:
        weights = dict(config.action_weight_templates.get(resolved_action_key, {}))
    normalized_weights = _normalize_weight_map(
        weights,
        gross_exposure_limit=config.gross_exposure_limit,
    )
    confidence = clamp_unit_interval(
        (abs(action_score) + float(row.policy_confidence)) / 2.0
    )
    diagnostics = diagnostics_builder(
        row=row,
        raw_action_key=raw_action_key,
        resolved_action_key=resolved_action_key,
        action_score=action_score,
        normalized_weights=normalized_weights,
        confidence=confidence,
    )
    return RLActionDecision(
        action_key=resolved_action_key,
        weights=normalized_weights,
        score=clamp_signed_unit(action_score),
        confidence=confidence,
        diagnostics=diagnostics,
    )


def build_rl_rebalance_row(
    *,
    timestamp: str,
    decision: RLActionDecision,
    selection_reason: str,
) -> CompositeRebalanceRow:
    ordered_weights = sorted(
        decision.weights.items(),
        key=lambda item: (-abs(item[1]), item[0]),
    )
    ranking = tuple(
        RankedAsset(
            symbol=symbol,
            rank=index,
            score=abs(weight),
            weight=weight,
            selected=True,
            side="long" if weight > 0.0 else "short",
        )
        for index, (symbol, weight) in enumerate(ordered_weights, start=1)
    )
    diagnostics = dict(decision.diagnostics)
    diagnostics.update(
        {
            "selected_symbols": [symbol for symbol, _weight in ordered_weights],
            "selected_count": len(ordered_weights),
            "selection_reason": selection_reason,
            "gross_exposure": sum(abs(weight) for _symbol, weight in ordered_weights),
            "net_exposure": sum(weight for _symbol, weight in ordered_weights),
        }
    )
    return CompositeRebalanceRow(
        timestamp=timestamp,
        ranking=ranking,
        selected_symbols=tuple(symbol for symbol, _weight in ordered_weights),
        weights=dict(ordered_weights),
        diagnostics=diagnostics,
    )


class BaseReinforcementLearningAlertAlgorithm:
    catalog_ref = ""
    family = "reinforcement_learning"
    reporting_mode = "allocation_trace"

    def __init__(
        self,
        *,
        algorithm_key: str,
        symbol: str,
        params: dict[str, Any],
        subcategory: str,
    ) -> None:
        self.algorithm_key = algorithm_key
        self.alg_name = algorithm_key
        self.symbol = symbol
        self.params = params
        self.subcategory = subcategory
        self.evaluate_window_len = 1
        self.date = ""
        self.eval_dict: dict[str, Any] = {}
        self._environment = parse_rl_environment_rows(list(params["rows"]))
        self._config = build_rl_controller_config(params)
        self._rows = self.build_rows()
        self.latest_predicted_trend = (
            "buy" if self._rows and self._rows[-1].weights else "neutral"
        )
        self.latest_predicted_trend_confidence = (
            clamp_unit_interval(
                float(self._rows[-1].diagnostics.get("policy_confidence", 0.0))
            )
            if self._rows
            else 0.0
        )

    def minimum_history(self) -> int:
        return self._config.min_history

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
            sell_signal=False,
            no_signal=self.latest_predicted_trend != "buy",
            annotations={"alg_name": self.alg_name},
        )

    def process_list(self, _data_list: list[dict[str, Any]]) -> None:
        return None

    def allowed_actions_for_row(self, _row_index: int) -> Sequence[str] | None:
        return None

    def build_decision(self, row_index: int) -> RLActionDecision:
        raise NotImplementedError

    def build_rows(self) -> tuple[CompositeRebalanceRow, ...]:
        rows: list[CompositeRebalanceRow] = []
        for index, environment_row in enumerate(self._environment.rows, start=1):
            if index < self.minimum_history():
                rows.append(
                    CompositeRebalanceRow(
                        timestamp=environment_row.timestamp,
                        ranking=(),
                        selected_symbols=(),
                        weights={},
                        diagnostics={
                            "selection_reason": "warmup_pending",
                            "warmup_ready": False,
                            "policy_confidence": environment_row.policy_confidence,
                            "reward": environment_row.reward,
                            "action_scores": dict(environment_row.action_scores),
                            "state": dict(environment_row.state),
                            "environment_contract": {
                                "state_key_count": len(environment_row.state),
                                "action_key_count": len(environment_row.action_scores),
                            },
                        },
                    )
                )
                continue
            decision = self.build_decision(index - 1)
            rows.append(
                build_rl_rebalance_row(
                    timestamp=environment_row.timestamp,
                    decision=decision,
                    selection_reason="selection_ready",
                )
            )
        return tuple(rows)

    def portfolio_output(self):
        return build_portfolio_weight_output(
            self.algorithm_key,
            self._rows,
            family=self.family,
            subcategory=self.subcategory,
            catalog_ref=self.catalog_ref,
            reporting_mode=self.reporting_mode,
        )

    def normalized_output(self) -> AlertAlgorithmOutput:
        return build_rebalance_alert_output(
            algorithm_key=self.algorithm_key,
            family=self.family,
            subcategory=self.subcategory,
            catalog_ref=self.catalog_ref,
            reporting_mode=self.reporting_mode,
            warmup_period=self.minimum_history(),
            rows=self._rows,
            signal_from_row=lambda row: "buy" if row.weights else "neutral",
            score_from_row=lambda row: clamp_signed_unit(
                float(row.diagnostics.get("action_score", 0.0))
            ),
            confidence_from_row=lambda row: clamp_unit_interval(
                float(row.diagnostics.get("policy_confidence", 0.0))
            ),
        )

    def interactive_report_payloads(self) -> list[tuple[dict[str, Any], str]]:
        return [
            (
                {
                    "algorithm_key": self.algorithm_key,
                    "data": self.normalized_output().to_dict(),
                    "portfolio": self.portfolio_output().to_dict(),
                },
                f"rl_report_{self.algorithm_key}_{self.symbol}",
            )
        ]
