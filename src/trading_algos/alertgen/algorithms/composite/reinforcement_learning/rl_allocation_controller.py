from __future__ import annotations

from typing import Any

from trading_algos.alertgen.algorithms.composite.reinforcement_learning.helpers import (
    BaseReinforcementLearningAlertAlgorithm,
    resolve_rl_action_decision,
)
from trading_algos.rl.environment import RLActionDecision


class RLAllocationControllerAlertAlgorithm(BaseReinforcementLearningAlertAlgorithm):
    catalog_ref = "combination:11"

    def __init__(
        self, *, algorithm_key: str, symbol: str, params: dict[str, Any]
    ) -> None:
        super().__init__(
            algorithm_key=algorithm_key,
            symbol=symbol,
            params=params,
            subcategory="rl",
        )

    def build_decision(self, row_index: int) -> RLActionDecision:
        return resolve_rl_action_decision(
            self._environment,
            row_index=row_index,
            allowed_actions=self.allowed_actions_for_row(row_index),
            config=self._config,
            diagnostics_builder=lambda **kwargs: {
                "aggregation_method": "rl_allocation_controller",
                "raw_action_key": kwargs["raw_action_key"],
                "resolved_action_key": kwargs["resolved_action_key"],
                "action_score": kwargs["action_score"],
                "policy_confidence": kwargs["confidence"],
                "selected_weights": kwargs["normalized_weights"],
                "reward": kwargs["row"].reward,
                "state": dict(kwargs["row"].state),
                "action_scores": dict(kwargs["row"].action_scores),
                "environment_contract": {
                    "state_key_count": len(kwargs["row"].state),
                    "action_key_count": len(kwargs["row"].action_scores),
                },
                "warmup_ready": True,
            },
        )


def build_rl_allocation_controller_algorithm(
    *, algorithm_key: str, symbol: str, alg_param: dict[str, Any], **_kwargs: Any
) -> RLAllocationControllerAlertAlgorithm:
    return RLAllocationControllerAlertAlgorithm(
        algorithm_key=algorithm_key,
        symbol=symbol,
        params=alg_param,
    )
