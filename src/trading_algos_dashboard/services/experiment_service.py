from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from trading_algos.alertgen.core.validation import normalize_alertgen_sensor_config

from trading_algos_dashboard.repositories.experiment_repository import (
    ExperimentRepository,
)
from trading_algos_dashboard.repositories.result_repository import ResultRepository
from trading_algos_dashboard.services.algorithm_runner_service import (
    run_alert_algorithm,
)
from trading_algos_dashboard.services.configuration_run_service import (
    run_configuration_payload,
)
from trading_algos_dashboard.services.data_source_service import (
    SmarttradeDataSourceService,
    parse_date_range,
)


class ExperimentService:
    def __init__(
        self,
        *,
        experiment_repository: ExperimentRepository,
        result_repository: ResultRepository,
        data_source_service: SmarttradeDataSourceService,
        report_base_path: str,
    ):
        self.experiment_repository = experiment_repository
        self.result_repository = result_repository
        self.data_source_service = data_source_service
        self.report_base_path = report_base_path

    def create_experiment(
        self,
        *,
        symbol: str,
        start_date: str,
        start_time: str,
        end_date: str,
        end_time: str,
        algorithms: list[dict[str, Any]],
        configuration_payload: dict[str, Any] | None = None,
        notes: str = "",
    ) -> str:
        experiment_id = f"exp_{uuid4().hex[:12]}"
        created_at = datetime.now(timezone.utc)

        if configuration_payload is None and (
            not isinstance(algorithms, list) or len(algorithms) == 0
        ):
            raise ValueError("Algorithms must be a non-empty JSON array of objects")

        normalized_algorithms = []
        if configuration_payload is None:
            for index, algorithm in enumerate(algorithms, start=1):
                algorithm_config = self._require_algorithm_config(
                    algorithm, index=index
                )
                normalized_algorithms.append(
                    normalize_alertgen_sensor_config(
                        {
                            "symbol": symbol,
                            "alg_key": algorithm_config["alg_key"],
                            "alg_param": algorithm_config["alg_param"],
                            "buy": algorithm_config.get("buy", True),
                            "sell": algorithm_config.get("sell", True),
                        }
                    )
                )

        start_dt, end_dt = parse_date_range(
            start_date,
            start_time,
            end_date,
            end_time,
        )
        candles = self.data_source_service.fetch_candles(
            symbol=symbol,
            start=start_dt,
            end=end_dt,
        )
        report_dir = Path(self.report_base_path) / experiment_id
        report_dir.mkdir(parents=True, exist_ok=True)

        self.experiment_repository.create_experiment(
            {
                "experiment_id": experiment_id,
                "created_at": created_at,
                "updated_at": created_at,
                "status": "completed",
                "symbol": symbol,
                "dataset_source": {"kind": "smarttrade_dataserver"},
                "time_range": {"start": start_dt, "end": end_dt},
                "candle_count": len(candles),
                "input_kind": "configuration"
                if configuration_payload is not None
                else "single_algorithm",
                "input_snapshot": configuration_payload
                if configuration_payload is not None
                else {
                    "algorithms": [
                        {
                            "alg_key": alg["alg_key"],
                            "alg_param": alg["alg_param"],
                        }
                        for alg in normalized_algorithms
                    ]
                },
                "selected_algorithms": [
                    {
                        "alg_key": alg["alg_key"],
                        "alg_param": alg["alg_param"],
                    }
                    for alg in normalized_algorithms
                ],
                "notes": notes,
                "report_base_path": str(report_dir),
            }
        )

        if configuration_payload is not None:
            result = run_configuration_payload(
                payload=configuration_payload,
                symbol=symbol,
                report_base_path=str(report_dir),
                candles=candles,
            )
            self.result_repository.insert_result(
                {"experiment_id": experiment_id, "created_at": created_at, **result}
            )
        else:
            for sensor_config in normalized_algorithms:
                result = run_alert_algorithm(
                    sensor_config=sensor_config,
                    report_base_path=str(report_dir),
                    candles=candles,
                )
                self.result_repository.insert_result(
                    {
                        "experiment_id": experiment_id,
                        "created_at": created_at,
                        **result,
                    }
                )
        return experiment_id

    @staticmethod
    def _require_algorithm_config(algorithm: Any, *, index: int) -> dict[str, Any]:
        if not isinstance(algorithm, dict):
            raise ValueError(f"Algorithm #{index} must be a JSON object")
        if "alg_key" not in algorithm:
            raise ValueError(f"Algorithm #{index} is missing required key: alg_key")
        if "alg_param" not in algorithm:
            raise ValueError(f"Algorithm #{index} is missing required key: alg_param")
        return algorithm

    def get_experiment_detail(self, experiment_id: str) -> dict[str, Any] | None:
        experiment = self.experiment_repository.get_experiment(experiment_id)
        if experiment is None:
            return None
        return {
            "experiment": experiment,
            "results": self.result_repository.list_results_for_experiment(
                experiment_id
            ),
        }
