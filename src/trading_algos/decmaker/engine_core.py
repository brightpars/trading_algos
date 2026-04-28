from __future__ import annotations

from typing import Any

from trading_algos.decmaker.factory import create_decmaker_algorithm
from trading_algos.decmaker.validation import validate_decmaker_engine_payload


class DecmakerAlgorithmCore:
    """Algorithm-centric decision-maker wrapper independent from server hosting."""

    def __init__(
        self, *, container_obj: Any, engine_config: dict[str, Any], label: str
    ) -> None:
        self.engine_config = validate_decmaker_engine_payload(
            engine_config, label=label
        )
        self.confidence_threshold_buy = self.engine_config["confidence_threshold_buy"]
        self.confidence_threshold_sell = self.engine_config["confidence_threshold_sell"]
        self.max_percent_higher_price_buy = self.engine_config[
            "max_percent_higher_price_buy"
        ]
        self.max_percent_lower_price_sell = self.engine_config[
            "max_percent_lower_price_sell"
        ]
        self.algorithm = create_decmaker_algorithm(container_obj, self.engine_config)

    def process_alerts_list(self, available_alerts_list: list[Any]) -> None:
        self.algorithm.process_alerts_list(available_alerts_list)
