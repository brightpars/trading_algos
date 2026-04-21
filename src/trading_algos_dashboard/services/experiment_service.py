from __future__ import annotations

import subprocess
import multiprocessing
import os
import signal
import threading
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
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
        task_launcher: Callable[[Callable[[], None]], Any | None] | None = None,
    ):
        self.experiment_repository = experiment_repository
        self.result_repository = result_repository
        self.data_source_service = data_source_service
        self.report_base_path = report_base_path
        self.task_launcher = task_launcher or self._launch_background_task
        self._active_runs: dict[str, Any] = {}
        self._active_runs_lock = threading.Lock()

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
        started_at = created_at

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
        repo_revision = self._repo_revision()
        report_dir = Path(self.report_base_path) / experiment_id
        report_dir.mkdir(parents=True, exist_ok=True)

        self.experiment_repository.create_experiment(
            {
                "experiment_id": experiment_id,
                "created_at": created_at,
                "updated_at": started_at,
                "status": "running",
                "started_at": started_at,
                "finished_at": None,
                "duration_seconds": None,
                "repo_revision": repo_revision,
                "symbol": symbol,
                "dataset_source": None,
                "time_range": {"start": start_dt, "end": end_dt},
                "candle_count": None,
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
                "execution_steps": [],
                "error_message": None,
                "cancelled_at": None,
                "process_pid": None,
            }
        )
        task_handle = self.task_launcher(
            lambda: self._run_experiment_job(
                experiment_id=experiment_id,
                created_at=created_at,
                started_at=started_at,
                symbol=symbol,
                start_dt=start_dt,
                end_dt=end_dt,
                normalized_algorithms=normalized_algorithms,
                configuration_payload=configuration_payload,
                report_dir=report_dir,
            )
        )
        if task_handle is not None:
            with self._active_runs_lock:
                self._active_runs[experiment_id] = task_handle
            process_pid = getattr(task_handle, "pid", None)
            if isinstance(process_pid, int):
                self.experiment_repository.update_experiment(
                    experiment_id,
                    {
                        "process_pid": process_pid,
                        "updated_at": datetime.now(timezone.utc),
                    },
                )
        return experiment_id

    def delete_experiment(self, experiment_id: str) -> bool:
        experiment = self.experiment_repository.get_experiment(experiment_id)
        if experiment is None:
            return False
        self.result_repository.delete_results_for_experiment(experiment_id)
        self.experiment_repository.delete_experiment(experiment_id)
        return True

    def _run_experiment_job(
        self,
        *,
        experiment_id: str,
        created_at: datetime,
        started_at: datetime,
        symbol: str,
        start_dt: datetime,
        end_dt: datetime,
        normalized_algorithms: list[dict[str, Any]],
        configuration_payload: dict[str, Any] | None,
        report_dir: Path,
    ) -> None:
        execution_steps: list[dict[str, Any]] = []
        try:
            self.experiment_repository.update_experiment(
                experiment_id,
                {"process_pid": os.getpid(), "updated_at": datetime.now(timezone.utc)},
            )
            dataset_source = self.data_source_service.get_market_data_server_details()
            read_started_at = datetime.now(timezone.utc)
            read_started_at_perf = perf_counter()
            candles = self.data_source_service.fetch_candles(
                symbol=symbol,
                start=start_dt,
                end=end_dt,
            )
            read_finished_at = datetime.now(timezone.utc)
            execution_steps.append(
                {
                    "step": "read_candles",
                    "label": "Read candles",
                    "started_at": read_started_at,
                    "finished_at": read_finished_at,
                    "duration_seconds": perf_counter() - read_started_at_perf,
                    "metadata": {
                        "symbol": symbol,
                        "candle_count": len(candles),
                    },
                }
            )
            self.experiment_repository.update_experiment(
                experiment_id,
                {
                    "dataset_source": dataset_source,
                    "candle_count": len(candles),
                    "execution_steps": execution_steps,
                    "updated_at": datetime.now(timezone.utc),
                },
            )

            if configuration_payload is not None:
                result = run_configuration_payload(
                    payload=configuration_payload,
                    symbol=symbol,
                    report_base_path=str(report_dir),
                    candles=candles,
                )
                execution_steps.extend(self._result_execution_steps(result))
                self.experiment_repository.update_experiment(
                    experiment_id,
                    {
                        "execution_steps": execution_steps,
                        "updated_at": datetime.now(timezone.utc),
                    },
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
                    execution_steps.extend(self._result_execution_steps(result))
                    self.experiment_repository.update_experiment(
                        experiment_id,
                        {
                            "execution_steps": execution_steps,
                            "updated_at": datetime.now(timezone.utc),
                        },
                    )
                    self.result_repository.insert_result(
                        {
                            "experiment_id": experiment_id,
                            "created_at": created_at,
                            **result,
                        }
                    )
        except Exception as exc:
            finished_at = datetime.now(timezone.utc)
            self.experiment_repository.update_experiment(
                experiment_id,
                {
                    "updated_at": finished_at,
                    "status": "failed",
                    "finished_at": finished_at,
                    "duration_seconds": (finished_at - started_at).total_seconds(),
                    "execution_steps": execution_steps,
                    "error_message": str(exc),
                    "cancelled_at": None,
                    "process_pid": None,
                },
            )
            return

        finished_at = datetime.now(timezone.utc)
        self.experiment_repository.update_experiment(
            experiment_id,
            {
                "updated_at": finished_at,
                "status": "completed",
                "finished_at": finished_at,
                "duration_seconds": (finished_at - started_at).total_seconds(),
                "execution_steps": execution_steps,
                "error_message": None,
                "cancelled_at": None,
                "process_pid": None,
            },
        )
        self._discard_active_run(experiment_id)

    def request_cancel(self, experiment_id: str) -> bool:
        experiment = self.experiment_repository.get_experiment(experiment_id)
        if experiment is None:
            raise ValueError("Experiment was not found")

        status = experiment.get("status")
        if status != "running":
            return False

        started_at = experiment.get("started_at")
        started_at = self._normalize_runtime_datetime(started_at)
        if started_at is None:
            started_at = datetime.now(timezone.utc)

        self._terminate_active_run(experiment_id, experiment)
        self._mark_cancelled(experiment_id=experiment_id, started_at=started_at)
        return True

    def _terminate_active_run(
        self, experiment_id: str, experiment: dict[str, Any]
    ) -> None:
        with self._active_runs_lock:
            active_run = self._active_runs.pop(experiment_id, None)

        if active_run is not None:
            terminate = getattr(active_run, "terminate", None)
            if callable(terminate):
                terminate()
                return

        process_pid = experiment.get("process_pid")
        if isinstance(process_pid, int):
            try:
                os.kill(process_pid, signal.SIGTERM)
            except ProcessLookupError:
                return

    def _discard_active_run(self, experiment_id: str) -> None:
        with self._active_runs_lock:
            self._active_runs.pop(experiment_id, None)

    def _mark_cancelled(self, *, experiment_id: str, started_at: datetime) -> None:
        cancelled_at = datetime.now(timezone.utc)
        self._discard_active_run(experiment_id)
        self.experiment_repository.update_experiment(
            experiment_id,
            {
                "updated_at": cancelled_at,
                "status": "cancelled",
                "finished_at": cancelled_at,
                "cancelled_at": cancelled_at,
                "duration_seconds": (cancelled_at - started_at).total_seconds(),
                "error_message": None,
                "process_pid": None,
            },
        )

    @staticmethod
    def _normalize_runtime_datetime(value: object) -> datetime | None:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        return None

    @staticmethod
    def _launch_background_task(job: Callable[[], None]) -> multiprocessing.Process:
        process = multiprocessing.Process(target=job, daemon=True)
        process.start()
        return process

    @staticmethod
    def _repo_revision() -> str | None:
        try:
            completed = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            return None
        revision = completed.stdout.strip()
        return revision or None

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
        results = self.result_repository.list_results_for_experiment(experiment_id)
        experiment_summary = self._build_experiment_summary(experiment)
        for result in results:
            report = result.get("report")
            if isinstance(report, dict):
                report["experiment_summary"] = {
                    **experiment_summary,
                    **dict(report.get("experiment_summary") or {}),
                }
        return {
            "experiment": experiment,
            "results": results,
        }

    @staticmethod
    def _build_experiment_summary(experiment: dict[str, Any]) -> dict[str, Any]:
        dataset_source = experiment.get("dataset_source")
        if not isinstance(dataset_source, dict):
            dataset_source = {}
        time_range = experiment.get("time_range")
        if not isinstance(time_range, dict):
            time_range = {}
        return {
            "experiment_id": experiment.get("experiment_id"),
            "experiment_type": experiment.get("input_kind"),
            "created_at": experiment.get("created_at"),
            "started_at": experiment.get("started_at"),
            "finished_at": experiment.get("finished_at"),
            "symbol_or_input_scope": experiment.get("symbol"),
            "data_source_metadata": dataset_source,
            "candle_count": experiment.get("candle_count"),
            "repository_revision": experiment.get("repo_revision"),
            "time_range": time_range,
            "report_generated_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _result_execution_steps(result: dict[str, Any]) -> list[dict[str, Any]]:
        execution_steps = result.get("execution_steps")
        if not isinstance(execution_steps, list):
            return []
        return [step for step in execution_steps if isinstance(step, dict)]
