from __future__ import annotations

from typing import Any

from trading_algos.alertgen.algorithms.composite.reinforcement_learning.helpers import (
    BaseReinforcementLearningAlertAlgorithm,
    resolve_rl_action_decision,
)
from trading_algos.rl.environment import RLActionDecision


class HierarchicalControllerMetaPolicyAlertAlgorithm(
    BaseReinforcementLearningAlertAlgorithm
):
    catalog_ref = "combination:12"

    def __init__(
        self, *, algorithm_key: str, symbol: str, params: dict[str, Any]
    ) -> None:
        super().__init__(
            algorithm_key=algorithm_key,
            symbol=symbol,
            params=params,
            subcategory="hierarchical",
        )

    def allowed_actions_for_row(self, row_index: int) -> list[str] | None:
        row = self._environment.rows[row_index]
        preferred_family = row.metadata.get("preferred_family")
        if not preferred_family:
            return None
        allowed = [
            action_key
            for action_key in row.action_scores
            if preferred_family in action_key
            or self._config.action_aliases.get(action_key, "").startswith(
                str(preferred_family)
            )
        ]
        return allowed or None

    def build_decision(self, row_index: int) -> RLActionDecision:
        return resolve_rl_action_decision(
            self._environment,
            row_index=row_index,
            allowed_actions=self.allowed_actions_for_row(row_index),
            config=self._config,
            diagnostics_builder=lambda **kwargs: {
                "aggregation_method": "hierarchical_controller_meta_policy",
                "raw_action_key": kwargs["raw_action_key"],
                "resolved_action_key": kwargs["resolved_action_key"],
                "action_score": kwargs["action_score"],
                "policy_confidence": kwargs["confidence"],
                "selected_weights": kwargs["normalized_weights"],
                "reward": kwargs["row"].reward,
                "state": dict(kwargs["row"].state),
                "action_scores": dict(kwargs["row"].action_scores),
                "preferred_family": kwargs["row"].metadata.get("preferred_family"),
                "environment_contract": {
                    "state_key_count": len(kwargs["row"].state),
                    "action_key_count": len(kwargs["row"].action_scores),
                },
                "warmup_ready": True,
            },
        )


def build_hierarchical_controller_meta_policy_algorithm(
    *, algorithm_key: str, symbol: str, alg_param: dict[str, Any], **_kwargs: Any
) -> HierarchicalControllerMetaPolicyAlertAlgorithm:
    return HierarchicalControllerMetaPolicyAlertAlgorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        params=alg_param,
    )
