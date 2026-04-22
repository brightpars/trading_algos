from __future__ import annotations

import multiprocessing
import os
import signal
import subprocess
import threading
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any
from xmlrpc.client import DateTime as XmlRpcDateTime
from uuid import uuid4

from trading_algos.alertgen.core.validation import normalize_alertgen_sensor_config

from trading_algos_dashboard.services.algorithm_runner_service import (
    run_alert_algorithm,
)
from trading_algos_dashboard.services.configuration_run_service import (
    run_configuration_payload,
)
from trading_algos_dashboard.services.data_source_service import (
    parse_date_range,
)


class ExperimentService:
    def __init__(
        self,
        *,
        experiment_repository: Any,
        result_repository: Any,
        data_source_service: Any,
        report_base_path: str,
        max_concurrent_experiments: int = 1,
        max_concurrent_experiments_provider: Callable[[], int] | None = None,
        scheduler_lease_manager: Any | None = None,
        task_launcher: Callable[[Callable[[], None]], Any | None] | None = None,
    ):
        if max_concurrent_experiments < 1:
            raise ValueError("max_concurrent_experiments must be at least 1")
        self.experiment_repository = experiment_repository
        self.result_repository = result_repository
        self.data_source_service = data_source_service
        self.report_base_path = report_base_path
        self.max_concurrent_experiments = max_concurrent_experiments
        self.max_concurrent_experiments_provider = max_concurrent_experiments_provider
        self.scheduler_lease_manager = scheduler_lease_manager
        self.task_launcher = task_launcher or self._launch_background_task
        self._active_runs: dict[str, Any] = {}
        self._active_runs_lock = threading.Lock()
        self._dispatch_lock = threading.RLock()
        self._dispatch_owner_id = f"dispatcher_{uuid4().hex}"

    class _InlineTaskHandle:
        def join(self) -> None:
            return None

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
        repo_revision = self._repo_revision()
        report_dir = Path(self.report_base_path) / experiment_id
        report_dir.mkdir(parents=True, exist_ok=True)

        self.experiment_repository.create_experiment(
            {
                "experiment_id": experiment_id,
                "created_at": created_at,
                "updated_at": created_at,
                "status": "queued",
                "queue_enqueued_at": created_at,
                "started_at": None,
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
        self.dispatch_available_experiments()
        return experiment_id

    def dispatch_next_experiment(self) -> str | None:
        launched = self.dispatch_available_experiments()
        if not launched:
            return None
        return launched[0]

    def dispatch_available_experiments(self) -> list[str]:
        with self._dispatch_lock:
            if not self._try_acquire_scheduler_lease():
                return []
            launched: list[str] = []
            try:
                running_count = self.experiment_repository.count_running_experiments()
                available_slots = (
                    self._current_max_concurrent_experiments() - running_count
                )
                while available_slots > 0:
                    started_at = datetime.now(timezone.utc)
                    experiment = (
                        self.experiment_repository.claim_next_queued_experiment(
                            started_at=started_at
                        )
                    )
                    if experiment is None:
                        break
                    launched.append(
                        self._start_claimed_experiment(
                            experiment=experiment,
                            started_at=started_at,
                        )
                    )
                    available_slots -= 1
                return launched
            finally:
                self._release_scheduler_lease()

    def _start_claimed_experiment(
        self, *, experiment: dict[str, Any], started_at: datetime
    ) -> str:
        experiment_id = str(experiment["experiment_id"])
        start_dt, end_dt = self._require_time_range(experiment)
        report_dir = Path(str(experiment["report_base_path"]))
        normalized_algorithms = self._normalized_algorithms_from_experiment(experiment)
        configuration_payload = self._configuration_payload_from_experiment(experiment)
        created_at = self._normalize_runtime_datetime(experiment.get("created_at"))
        if created_at is None:
            created_at = started_at

        task_handle = self.task_launcher(
            lambda: self._run_experiment_job(
                experiment_id=experiment_id,
                created_at=created_at,
                started_at=started_at,
                symbol=str(experiment.get("symbol", "")),
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
        if experiment.get("status") == "running":
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
            fetch_result = self.data_source_service.fetch_candles(
                symbol=symbol,
                start=start_dt,
                end=end_dt,
            )
            candles = fetch_result.candles
            read_finished_at = datetime.now(timezone.utc)
            dataset_source["cache"] = {
                **dict(dataset_source.get("cache") or {}),
                "source_kind": fetch_result.source_kind,
                "cache_hit": fetch_result.cache_hit,
            }
            execution_steps.append(
                self._normalize_runtime_document(
                    {
                        "step": "read_candles",
                        "label": "Read candles",
                        "started_at": read_started_at,
                        "finished_at": read_finished_at,
                        "duration_seconds": perf_counter() - read_started_at_perf,
                        "metadata": {
                            "symbol": symbol,
                            "candle_count": fetch_result.candle_count,
                            "cache_hit": fetch_result.cache_hit,
                            "source_kind": fetch_result.source_kind,
                            "start": fetch_result.start,
                            "end": fetch_result.end,
                        },
                    }
                )
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
                    self._normalize_runtime_document(
                        {
                            "experiment_id": experiment_id,
                            "created_at": created_at,
                            **result,
                        }
                    )
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
                        self._normalize_runtime_document(
                            {
                                "experiment_id": experiment_id,
                                "created_at": created_at,
                                **result,
                            }
                        )
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
            self._discard_active_run(experiment_id)
            self.dispatch_available_experiments()
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
        self.dispatch_available_experiments()

    def request_cancel(self, experiment_id: str) -> bool:
        experiment = self.experiment_repository.get_experiment(experiment_id)
        if experiment is None:
            raise ValueError("Experiment was not found")

        status = experiment.get("status")
        if status == "queued":
            self._mark_queued_cancelled(experiment_id=experiment_id)
            return True
        if status != "running":
            return False

        started_at = experiment.get("started_at")
        started_at = self._normalize_runtime_datetime(started_at)
        if started_at is None:
            started_at = datetime.now(timezone.utc)

        self._terminate_active_run(experiment_id, experiment)
        self._mark_cancelled(experiment_id=experiment_id, started_at=started_at)
        self.dispatch_available_experiments()
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

    def _track_active_run(self, *, experiment_id: str, task_handle: Any | None) -> None:
        effective_task_handle = task_handle or self._InlineTaskHandle()
        with self._active_runs_lock:
            self._active_runs[experiment_id] = effective_task_handle
        process_pid = getattr(effective_task_handle, "pid", None)
        if isinstance(process_pid, int):
            self.experiment_repository.update_experiment(
                experiment_id,
                {
                    "process_pid": process_pid,
                    "updated_at": datetime.now(timezone.utc),
                },
            )
        watcher = threading.Thread(
            target=self._await_run_completion,
            kwargs={
                "experiment_id": experiment_id,
                "task_handle": effective_task_handle,
            },
            daemon=True,
        )
        watcher.start()

    def _await_run_completion(self, *, experiment_id: str, task_handle: Any) -> None:
        join = getattr(task_handle, "join", None)
        if callable(join):
            join()
        self._discard_active_run(experiment_id)
        self.dispatch_next_experiment()

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

    def _mark_queued_cancelled(self, *, experiment_id: str) -> None:
        cancelled_at = datetime.now(timezone.utc)
        self.experiment_repository.update_experiment(
            experiment_id,
            {
                "updated_at": cancelled_at,
                "status": "cancelled",
                "finished_at": cancelled_at,
                "cancelled_at": cancelled_at,
                "duration_seconds": None,
                "error_message": None,
                "process_pid": None,
            },
        )

    @staticmethod
    def _normalize_runtime_datetime(value: object) -> datetime | None:
        if isinstance(value, XmlRpcDateTime):
            parsed = datetime.strptime(value.value, "%Y%m%dT%H:%M:%S")
            return parsed.replace(tzinfo=timezone.utc)
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

    @classmethod
    def _normalize_runtime_value(cls, value: Any) -> Any:
        normalized_datetime = cls._normalize_runtime_datetime(value)
        if normalized_datetime is not None:
            return normalized_datetime
        if isinstance(value, dict):
            return {
                str(key): cls._normalize_runtime_value(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [cls._normalize_runtime_value(item) for item in value]
        if isinstance(value, tuple):
            return tuple(cls._normalize_runtime_value(item) for item in value)
        return value

    @classmethod
    def _normalize_runtime_document(cls, document: dict[str, Any]) -> dict[str, Any]:
        normalized = cls._normalize_runtime_value(document)
        if not isinstance(normalized, dict):
            raise TypeError("Normalized runtime document must be a mapping")
        return normalized

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
        queue_overview = self.get_queue_overview()
        queue_position = self._queue_position_for_experiment(
            experiment=experiment,
            queued_experiments=queue_overview["queued_experiments"],
        )
        experiment["queue_position"] = queue_position
        experiment["queue_items_ahead"] = queue_position - 1 if queue_position else None
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
            "queue_overview": queue_overview,
        }

    def get_queue_overview(self) -> dict[str, Any]:
        running_experiments = self.experiment_repository.list_running_experiments()
        queued_experiments = self.experiment_repository.list_queued_experiments()
        running_count = len(running_experiments)
        max_concurrent_experiments = self._current_max_concurrent_experiments()
        available_slots = max(0, max_concurrent_experiments - running_count)
        return {
            "running_experiments": running_experiments,
            "queued_experiments": queued_experiments,
            "queue_summary": {
                "running_count": running_count,
                "queued_count": len(queued_experiments),
                "max_concurrent_experiments": max_concurrent_experiments,
                "available_slots": available_slots,
                "capacity_reached": available_slots == 0,
                "has_running": running_count > 0,
            },
        }

    def _current_max_concurrent_experiments(self) -> int:
        if self.max_concurrent_experiments_provider is None:
            return self.max_concurrent_experiments
        return max(1, int(self.max_concurrent_experiments_provider()))

    def _try_acquire_scheduler_lease(self) -> bool:
        if self.scheduler_lease_manager is None:
            return True
        return bool(
            self.scheduler_lease_manager.try_acquire_lease(
                owner_id=self._dispatch_owner_id
            )
        )

    def _release_scheduler_lease(self) -> None:
        if self.scheduler_lease_manager is None:
            return
        self.scheduler_lease_manager.release_lease(owner_id=self._dispatch_owner_id)

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
    def _queue_position_for_experiment(
        *, experiment: dict[str, Any], queued_experiments: list[dict[str, Any]]
    ) -> int | None:
        if experiment.get("status") != "queued":
            return None
        experiment_id = experiment.get("experiment_id")
        for index, queued in enumerate(queued_experiments, start=1):
            if queued.get("experiment_id") == experiment_id:
                return index
        return None

    def _normalized_algorithms_from_experiment(
        self, experiment: dict[str, Any]
    ) -> list[dict[str, Any]]:
        selected_algorithms = experiment.get("selected_algorithms")
        if not isinstance(selected_algorithms, list):
            return []
        normalized: list[dict[str, Any]] = []
        symbol = str(experiment.get("symbol", ""))
        for index, algorithm in enumerate(selected_algorithms, start=1):
            algorithm_config = self._require_algorithm_config(algorithm, index=index)
            normalized.append(
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
        return normalized

    @staticmethod
    def _configuration_payload_from_experiment(
        experiment: dict[str, Any],
    ) -> dict[str, Any] | None:
        if experiment.get("input_kind") != "configuration":
            return None
        input_snapshot = experiment.get("input_snapshot")
        if isinstance(input_snapshot, dict):
            return input_snapshot
        return None

    def _require_time_range(
        self, experiment: dict[str, Any]
    ) -> tuple[datetime, datetime]:
        time_range = experiment.get("time_range")
        if not isinstance(time_range, dict):
            raise ValueError("Experiment time range is invalid")
        start_dt = self._normalize_runtime_datetime(time_range.get("start"))
        end_dt = self._normalize_runtime_datetime(time_range.get("end"))
        if start_dt is None or end_dt is None:
            raise ValueError("Experiment time range is invalid")
        return start_dt, end_dt

    @staticmethod
    def _result_execution_steps(result: dict[str, Any]) -> list[dict[str, Any]]:
        execution_steps = result.get("execution_steps")
        if not isinstance(execution_steps, list):
            return []
        return [
            ExperimentService._normalize_runtime_document(step)
            for step in execution_steps
            if isinstance(step, dict)
        ]
