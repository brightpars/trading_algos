from __future__ import annotations

import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

from trading_algos_dashboard.repositories.experiment_repository import (
    ExperimentRepository,
)
from trading_algos_dashboard.repositories.result_repository import ResultRepository
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

    def fetch_candles(self, **_kwargs):
        return [
            {
                "ts": "2025-01-01 10:00:00",
                "Open": 10,
                "High": 11,
                "Low": 9,
                "Close": 10.5,
            }
        ]


class _DeferredTaskHandle:
    def __init__(self, job):
        self._job = job
        self._done = threading.Event()

    def join(self):
        self._done.wait(timeout=2)

    def run_and_finish(self):
        self._job()
        self._done.set()


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
            "report": {"report_version": "1.0", "schema_version": "1.0", "charts": []},
        },
    )

    first_id = service.create_experiment(
        symbol="AAPL",
        start_date="2024-01-01",
        start_time="09:30",
        end_date="2024-01-01",
        end_time="16:00",
        algorithms=[
            {"alg_key": "close_high_channel_breakout", "alg_param": {"window": 2}}
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
            {"alg_key": "close_high_channel_breakout", "alg_param": {"window": 3}}
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
