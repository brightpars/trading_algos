from __future__ import annotations

from typing import Any

from trading_algos.alertgen.core.factory import create_alertgen_algorithm
from trading_algos.alertgen.core.validation import normalize_alertgen_sensor_config


class AlertgenAlgorithmCore:
    """Algorithm-centric alertgen wrapper independent from server hosting."""

    def __init__(
        self,
        *,
        name: str,
        engine_config: dict[str, Any],
        sensor_config: dict[str, Any],
        report_base_path: str,
    ) -> None:
        self.name = name
        self.engine_config = dict(engine_config)
        self.sensor_config = normalize_alertgen_sensor_config(sensor_config, label=f"{name} sensor_config")
        self.do_buy = bool(self.sensor_config["buy"])
        self.do_sell = bool(self.sensor_config["sell"])
        self.symbol = str(self.sensor_config["symbol"])
        self.alg_key = str(
            self.sensor_config.get(
                "alg_key",
                f"config:{self.sensor_config.get('published_config_id', 'unknown')}",
            )
        )
        self.algorithm, self.alg_param_for_logging = create_alertgen_algorithm(
            self.sensor_config,
            report_base_path=report_base_path,
        )

    @property
    def alg_param(self) -> Any:
        return self.sensor_config.get(
            "alg_param",
            self.sensor_config.get("configuration_payload", {}),
        )

    @property
    def latest_data_modifiable(self) -> Any:
        return self.algorithm.latest_data_modifiable

    def process(self, data: Any) -> None:
        self.algorithm.process(data)

    def buy_signal(self, data: Any) -> bool:
        return bool(data["buy_SIGNAL"])

    def sell_signal(self, data: Any) -> bool:
        return bool(data["sell_SIGNAL"])

    def signal_confidence(self, data: Any) -> float:
        return float(data["trend_confidence"])

    def interactive_report_payloads(self) -> list[tuple[Any, str]]:
        return list(self.algorithm.interactive_report_payloads())

    def alg_specific_report(self) -> list[tuple[str, str]]:
        return list(self.algorithm.alg_specific_report())

    def resolved_sensor_config(self) -> dict[str, Any]:
        resolved = dict(self.sensor_config)
        resolved["buy"] = self.do_buy
        resolved["sell"] = self.do_sell
        resolved["symbol"] = self.symbol
        resolved["alg_key"] = self.alg_key
        resolved["alg_param"] = self.alg_param_for_logging
        return resolved