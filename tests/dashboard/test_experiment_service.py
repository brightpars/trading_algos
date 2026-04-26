from __future__ import annotations

import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast
from xmlrpc.client import DateTime as XmlRpcDateTime

from trading_algos_dashboard.repositories.experiment_repository import (
    ExperimentRepository,
)
from trading_algos_dashboard.repositories.result_repository import ResultRepository
from trading_algos_dashboard.services.data_source_service import MarketDataFetchResult
from trading_algos_dashboard.services.experiment_service import ExperimentService


class _Cursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, *_args, **_kwargs):
        return self.docs

    def __iter__(self):
        return iter(self.docs)


class _Collection:
    def __init__(self):
        self.docs = []

    def find(self, query=None, **_kwargs):
        effective_query = dict(query or {})
        filtered = [
            doc
            for doc in self.docs
            if all(doc.get(key) == value for key, value in effective_query.items())
        ]
        return _Cursor(filtered)

    def insert_one(self, payload):
        self.docs.append(dict(payload))

    def find_one(self, query):
        for doc in self.docs:
            if all(doc.get(key) == value for key, value in query.items()):
                return doc
        return None

    def update_one(self, query, update, upsert=False):
        doc = self.find_one(query)
        if doc is None:
            if not upsert:
                return None
            doc = dict(query)
            self.docs.append(doc)
        if "$set" in update and isinstance(update["$set"], dict):
            doc.update(update["$set"])
        return None

    def delete_many(self, query):
        original_count = len(self.docs)
        self.docs = [
            doc
            for doc in self.docs
            if not all(doc.get(key) == value for key, value in query.items())
        ]
        return type(
            "DeleteResult", (), {"deleted_count": original_count - len(self.docs)}
        )()


class _Db(dict):
    def __getitem__(self, key):
        if key not in self:
            self[key] = _Collection()
        return dict.__getitem__(self, key)


class _FakeDataSourceService:
    def get_market_data_server_details(self):
        return {
            "kind": "smarttrade_dataserver",
            "ip": "127.0.0.1",
            "port": 7003,
            "endpoint": "127.0.0.1:7003",
        }

    def fetch_candles(self, *, symbol: str, start: datetime, end: datetime):
        return MarketDataFetchResult(
            candles=[
                {
                    "ts": "2025-01-01 10:00:00",
                    "Open": 10,
                    "High": 11,
                    "Low": 9,
                    "Close": 10.5,
                }
            ],
            cache_hit=False,
            source_kind="dataserver",
            symbol=symbol,
            start=start,
            end=end,
            candle_count=1,
        )


class _DeferredTaskHandle:
    def __init__(self, job):
        self._job = job
        self._done = threading.Event()

    def join(self):
        self._done.wait(timeout=2)

    def run_and_finish(self):
        self._job()
        self._done.set()


class _ExperimentRepositoryStub:
    def __init__(self) -> None:
        self.docs: dict[str, dict[str, Any]] = {}

    def create_experiment(self, payload: dict[str, Any]) -> None:
        self.docs[str(payload["experiment_id"])] = dict(payload)

    def update_experiment(self, experiment_id: str, payload: dict[str, Any]) -> None:
        self.docs[experiment_id].update(payload)

    def get_experiment(self, experiment_id: str) -> dict[str, Any] | None:
        doc = self.docs.get(experiment_id)
        return None if doc is None else dict(doc)

    def get_running_experiment(self) -> dict[str, Any] | None:
        return None

    def list_running_experiments(self) -> list[dict[str, Any]]:
        return [
            dict(doc) for doc in self.docs.values() if doc.get("status") == "running"
        ]

    def count_running_experiments(self) -> int:
        return len(self.list_running_experiments())

    def get_next_queued_experiment(self) -> dict[str, Any] | None:
        return None

    def claim_next_queued_experiment(
        self, *, started_at: datetime
    ) -> dict[str, Any] | None:
        queued = sorted(
            [doc for doc in self.docs.values() if doc.get("status") == "queued"],
            key=lambda item: str(item.get("experiment_id", "")),
        )
        if not queued:
            return None
        doc = queued[0]
        doc.update(
            {
                "status": "running",
                "started_at": started_at,
                "updated_at": started_at,
                "finished_at": None,
                "duration_seconds": None,
                "cancelled_at": None,
                "error_message": None,
            }
        )
        return dict(doc)

    def list_queued_experiments(self) -> list[dict[str, Any]]:
        return []


class _ResultRepositoryStub:
    def __init__(self) -> None:
        self.results: list[dict[str, Any]] = []

    def insert_result(self, payload: dict[str, Any]) -> None:
        self.results.append(dict(payload))

    def list_results_for_experiment(self, experiment_id: str) -> list[dict[str, Any]]:
        return [r for r in self.results if r.get("experiment_id") == experiment_id]

    def delete_results_for_experiment(self, experiment_id: str) -> None:
        self.results = [
            r for r in self.results if r.get("experiment_id") != experiment_id
        ]


class _CacheAwareDataSourceService:
    def __init__(self, *, cache_hit: bool) -> None:
        self.cache_hit = cache_hit

    def get_market_data_server_details(self) -> dict[str, Any]:
        return {"kind": "smarttrade_dataserver", "endpoint": "127.0.0.2:6010"}

    def fetch_candles(
        self, *, symbol: str, start: datetime, end: datetime
    ) -> MarketDataFetchResult:
        return MarketDataFetchResult(
            candles=[{"ts": "2024-01-01 09:30:00", "Close": 10.5}],
            cache_hit=self.cache_hit,
            source_kind="cache" if self.cache_hit else "dataserver",
            symbol=symbol,
            start=start,
            end=end,
            candle_count=1,
        )


def _build_service(
    *, tmp_path: Path, task_handles: list[_DeferredTaskHandle]
) -> ExperimentService:
    db = _Db()
    experiment_repository = ExperimentRepository(db)
    result_repository = ResultRepository(db)

    def _task_launcher(job):
        handle = _DeferredTaskHandle(job)
        task_handles.append(handle)
        return handle

    service = ExperimentService(
        experiment_repository=experiment_repository,
        result_repository=result_repository,
        data_source_service=cast(Any, _FakeDataSourceService()),
        report_base_path=str(tmp_path / "reports"),
        task_launcher=_task_launcher,
    )
    return service


class _SchedulerLeaseManager:
    def __init__(self, *, granted: bool) -> None:
        self.granted = granted
        self.acquire_calls = 0
        self.release_calls = 0

    def try_acquire_lease(self, *, owner_id: str) -> bool:
        assert owner_id
        self.acquire_calls += 1
        return self.granted

    def release_lease(self, *, owner_id: str) -> None:
        assert owner_id
        self.release_calls += 1


def _wait_for(condition, *, timeout=2.0):
    deadline = threading.Event()
    end_time = datetime.now(timezone.utc).timestamp() + timeout
    while datetime.now(timezone.utc).timestamp() < end_time:
        if condition():
            return
        deadline.wait(0.01)
    raise AssertionError("Condition was not met before timeout")


def test_back_to_back_queued_experiments_advance_automatically(monkeypatch, tmp_path):
    task_handles: list[_DeferredTaskHandle] = []
    service = _build_service(tmp_path=tmp_path, task_handles=task_handles)

    monkeypatch.setattr(service, "_repo_revision", lambda: "abc123")
    monkeypatch.setattr(
        "trading_algos_dashboard.services.experiment_service.run_alert_algorithm",
        lambda **kwargs: {
            "alg_key": kwargs["sensor_config"]["alg_key"],
            "alg_name": kwargs["sensor_config"]["alg_key"],
            "execution_steps": [
                {
                    "step": "run_algorithm",
                    "label": "Run algorithm",
                    "started_at": datetime.now(timezone.utc),
                    "finished_at": datetime.now(timezone.utc),
                    "duration_seconds": 0.0,
                    "metadata": {"candle_count": len(kwargs["candles"])},
                }
            ],
            "report": {
                "report_version": "1.0",
                "schema_version": "1.0",
                "charts": [],
            },
        },
    )

    first_id = service.create_experiment(
        symbol="AAPL",
        start_date="2024-01-01",
        start_time="09:30",
        end_date="2024-01-01",
        end_time="16:00",
        algorithms=[
            {
                "alg_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
                "alg_param": {"window": 2},
            }
        ],
        notes="first",
    )
    second_id = service.create_experiment(
        symbol="MSFT",
        start_date="2024-01-02",
        start_time="09:30",
        end_date="2024-01-02",
        end_time="16:00",
        algorithms=[
            {
                "alg_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
                "alg_param": {"window": 3},
            }
        ],
        notes="second",
    )

    assert len(task_handles) == 1
    first_experiment = service.experiment_repository.get_experiment(first_id)
    second_experiment = service.experiment_repository.get_experiment(second_id)
    assert first_experiment is not None
    assert second_experiment is not None
    assert first_experiment["status"] == "running"
    assert second_experiment["status"] == "queued"

    task_handles[0].run_and_finish()

    _wait_for(lambda: len(task_handles) == 2)
    _wait_for(
        lambda: (
            (service.experiment_repository.get_experiment(first_id) or {}).get("status")
            == "completed"
        )
    )
    _wait_for(
        lambda: (
            (service.experiment_repository.get_experiment(second_id) or {}).get(
                "status"
            )
            == "running"
        )
    )

    task_handles[1].run_and_finish()

    _wait_for(
        lambda: (
            (service.experiment_repository.get_experiment(second_id) or {}).get(
                "status"
            )
            == "completed"
        )
    )

    first_result = service.result_repository.list_results_for_experiment(first_id)
    second_result = service.result_repository.list_results_for_experiment(second_id)
    assert len(first_result) == 1
    assert len(second_result) == 1


def test_run_experiment_job_records_datasource_cache_metadata(monkeypatch, tmp_path):
    experiment_repository = _ExperimentRepositoryStub()
    result_repository = _ResultRepositoryStub()
    service = ExperimentService(
        experiment_repository=cast(Any, experiment_repository),
        result_repository=cast(Any, result_repository),
        data_source_service=cast(Any, _CacheAwareDataSourceService(cache_hit=True)),
        report_base_path=str(tmp_path),
    )
    experiment_repository.create_experiment({"experiment_id": "exp_1"})

    monkeypatch.setattr(
        "trading_algos_dashboard.services.experiment_service.run_alert_algorithm",
        lambda **_kwargs: {
            "execution_steps": [],
            "alg_key": "OLD_boundary_breakout_NEW_breakout_donchian_channel",
            "alg_name": "OLD Boundary Breakout NEW Breakout Donchian Channel",
            "report": {},
        },
    )
    monkeypatch.setattr(service, "dispatch_available_experiments", lambda: [])

    service._run_experiment_job(
        experiment_id="exp_1",
        created_at=datetime.now(timezone.utc),
        started_at=datetime.now(timezone.utc),
        symbol="AAPL",
        start_dt=datetime.fromisoformat("2024-01-01T09:30"),
        end_dt=datetime.fromisoformat("2024-01-01T09:30"),
        normalized_algorithms=[
            {
                "symbol": "AAPL",
                "alg_key": "OLD_boundary_breakout_NEW_breakout_donchian_channel",
                "alg_param": {},
                "buy": True,
                "sell": True,
            }
        ],
        configuration_payload=None,
        report_dir=Path(tmp_path),
    )

    experiment = experiment_repository.get_experiment("exp_1")

    assert experiment is not None
    assert experiment["dataset_source"]["cache"]["cache_hit"] is True
    assert experiment["dataset_source"]["cache"]["source_kind"] == "cache"
    assert experiment["execution_steps"][0]["step"] == "read_candles"
    assert experiment["execution_steps"][0]["metadata"]["cache_hit"] is True
    assert experiment["execution_steps"][0]["metadata"]["source_kind"] == "cache"


def test_run_experiment_job_normalizes_xmlrpc_datetime_values_in_persisted_payloads(
    monkeypatch, tmp_path
):
    experiment_repository = _ExperimentRepositoryStub()
    result_repository = _ResultRepositoryStub()

    class _XmlRpcDataSourceService:
        def get_market_data_server_details(self) -> dict[str, Any]:
            return {"kind": "smarttrade_dataserver", "endpoint": "127.0.0.2:6010"}

        def fetch_candles(
            self, *, symbol: str, start: datetime, end: datetime
        ) -> MarketDataFetchResult:
            return MarketDataFetchResult(
                candles=[
                    {
                        "ts": XmlRpcDateTime("20260402T09:30:00"),
                        "Close": 10.5,
                    }
                ],
                cache_hit=False,
                source_kind="dataserver",
                symbol=symbol,
                start=cast(Any, XmlRpcDateTime("20260402T09:30:00")),
                end=cast(Any, XmlRpcDateTime("20260402T09:30:00")),
                candle_count=1,
            )

    service = ExperimentService(
        experiment_repository=cast(Any, experiment_repository),
        result_repository=cast(Any, result_repository),
        data_source_service=cast(Any, _XmlRpcDataSourceService()),
        report_base_path=str(tmp_path),
    )
    experiment_repository.create_experiment({"experiment_id": "exp_xmlrpc"})

    monkeypatch.setattr(
        "trading_algos_dashboard.services.experiment_service.run_alert_algorithm",
        lambda **kwargs: {
            "execution_steps": [
                {
                    "step": "run_algorithm",
                    "label": "Run algorithm",
                    "started_at": XmlRpcDateTime("20260402T09:30:00"),
                    "finished_at": XmlRpcDateTime("20260402T09:31:00"),
                    "duration_seconds": 60.0,
                    "metadata": {"last_candle_ts": kwargs["candles"][0]["ts"]},
                }
            ],
            "alg_key": "OLD_boundary_breakout_NEW_breakout_donchian_channel",
            "alg_name": "OLD Boundary Breakout NEW Breakout Donchian Channel",
            "report": {
                "generated_at": XmlRpcDateTime("20260402T09:31:00"),
            },
        },
    )
    monkeypatch.setattr(service, "dispatch_available_experiments", lambda: [])

    service._run_experiment_job(
        experiment_id="exp_xmlrpc",
        created_at=datetime.now(timezone.utc),
        started_at=datetime.now(timezone.utc),
        symbol="AAPL",
        start_dt=datetime.fromisoformat("2026-04-02T09:30"),
        end_dt=datetime.fromisoformat("2026-04-02T09:30"),
        normalized_algorithms=[
            {
                "symbol": "AAPL",
                "alg_key": "OLD_boundary_breakout_NEW_breakout_donchian_channel",
                "alg_param": {},
                "buy": True,
                "sell": True,
            }
        ],
        configuration_payload=None,
        report_dir=Path(tmp_path),
    )

    experiment = experiment_repository.get_experiment("exp_xmlrpc")
    assert experiment is not None
    assert experiment["status"] == "completed"
    assert experiment["execution_steps"][0]["metadata"][
        "start"
    ] == datetime.fromisoformat("2026-04-02T09:30:00+00:00")
    assert experiment["execution_steps"][0]["metadata"][
        "end"
    ] == datetime.fromisoformat("2026-04-02T09:30:00+00:00")
    assert experiment["execution_steps"][1]["started_at"] == datetime.fromisoformat(
        "2026-04-02T09:30:00+00:00"
    )

    persisted_result = result_repository.results[0]
    assert persisted_result["report"]["generated_at"] == datetime.fromisoformat(
        "2026-04-02T09:31:00+00:00"
    )
    assert persisted_result["execution_steps"][0]["metadata"][
        "last_candle_ts"
    ] == datetime.fromisoformat("2026-04-02T09:30:00+00:00")


def test_dispatch_available_experiments_starts_up_to_capacity(tmp_path):
    db = _Db()
    experiment_repository = ExperimentRepository(db)
    result_repository = ResultRepository(db)
    launched: list[str] = []

    service = ExperimentService(
        experiment_repository=experiment_repository,
        result_repository=result_repository,
        data_source_service=_CacheAwareDataSourceService(cache_hit=False),
        report_base_path=str(tmp_path),
        max_concurrent_experiments=2,
        task_launcher=lambda job: launched.append("launched") or None,
    )
    for experiment_id in ("exp_a", "exp_b", "exp_c"):
        experiment_repository.create_experiment(
            {
                "experiment_id": experiment_id,
                "status": "queued",
                "symbol": "AAPL",
                "report_base_path": str(tmp_path / experiment_id),
                "time_range": {
                    "start": datetime(2024, 1, 1, 9, 30, tzinfo=timezone.utc),
                    "end": datetime(2024, 1, 1, 9, 31, tzinfo=timezone.utc),
                },
                "selected_algorithms": [],
                "created_at": datetime.now(timezone.utc),
            }
        )

    launched_ids = service.dispatch_available_experiments()

    assert len(launched_ids) == 2
    assert len(launched) == 2


def test_get_queue_overview_reports_parallel_capacity(tmp_path):
    db = _Db()
    experiment_repository = ExperimentRepository(db)
    result_repository = ResultRepository(db)
    service = ExperimentService(
        experiment_repository=experiment_repository,
        result_repository=result_repository,
        data_source_service=_CacheAwareDataSourceService(cache_hit=False),
        report_base_path=str(tmp_path),
        max_concurrent_experiments=3,
    )
    experiment_repository.create_experiment(
        {"experiment_id": "exp_running", "status": "running"}
    )
    experiment_repository.create_experiment(
        {"experiment_id": "exp_queued", "status": "queued"}
    )

    overview = service.get_queue_overview()

    assert overview["queue_summary"]["running_count"] == 1
    assert overview["queue_summary"]["max_concurrent_experiments"] == 3
    assert overview["queue_summary"]["available_slots"] == 2


def test_queue_overview_uses_runtime_concurrency_provider(tmp_path):
    db = _Db()
    experiment_repository = ExperimentRepository(db)
    result_repository = ResultRepository(db)
    service = ExperimentService(
        experiment_repository=experiment_repository,
        result_repository=result_repository,
        data_source_service=_CacheAwareDataSourceService(cache_hit=False),
        report_base_path=str(tmp_path),
        max_concurrent_experiments=1,
        max_concurrent_experiments_provider=lambda: 4,
    )
    overview = service.get_queue_overview()

    assert overview["queue_summary"]["max_concurrent_experiments"] == 4
    assert overview["queue_summary"]["available_slots"] == 4


def test_dispatch_available_experiments_returns_empty_when_lease_not_acquired(tmp_path):
    db = _Db()
    experiment_repository = ExperimentRepository(db)
    result_repository = ResultRepository(db)
    lease_manager = _SchedulerLeaseManager(granted=False)
    service = ExperimentService(
        experiment_repository=experiment_repository,
        result_repository=result_repository,
        data_source_service=_CacheAwareDataSourceService(cache_hit=False),
        report_base_path=str(tmp_path),
        scheduler_lease_manager=lease_manager,
    )
    experiment_repository.create_experiment(
        {
            "experiment_id": "exp_a",
            "status": "queued",
            "symbol": "AAPL",
            "report_base_path": str(tmp_path / "exp_a"),
            "time_range": {
                "start": datetime(2024, 1, 1, 9, 30, tzinfo=timezone.utc),
                "end": datetime(2024, 1, 1, 9, 31, tzinfo=timezone.utc),
            },
            "selected_algorithms": [],
            "created_at": datetime.now(timezone.utc),
        }
    )

    launched = service.dispatch_available_experiments()

    assert launched == []
    assert lease_manager.acquire_calls == 1
    assert lease_manager.release_calls == 0


def test_dispatch_available_experiments_releases_lease_after_dispatch(tmp_path):
    db = _Db()
    experiment_repository = ExperimentRepository(db)
    result_repository = ResultRepository(db)
    lease_manager = _SchedulerLeaseManager(granted=True)
    service = ExperimentService(
        experiment_repository=experiment_repository,
        result_repository=result_repository,
        data_source_service=_CacheAwareDataSourceService(cache_hit=False),
        report_base_path=str(tmp_path),
        scheduler_lease_manager=lease_manager,
        task_launcher=lambda _job: None,
    )
    experiment_repository.create_experiment(
        {
            "experiment_id": "exp_a",
            "status": "queued",
            "symbol": "AAPL",
            "report_base_path": str(tmp_path / "exp_a"),
            "time_range": {
                "start": datetime(2024, 1, 1, 9, 30, tzinfo=timezone.utc),
                "end": datetime(2024, 1, 1, 9, 31, tzinfo=timezone.utc),
            },
            "selected_algorithms": [],
            "created_at": datetime.now(timezone.utc),
        }
    )

    launched = service.dispatch_available_experiments()

    assert launched == ["exp_a"]
    assert lease_manager.acquire_calls == 1
    assert lease_manager.release_calls == 1
