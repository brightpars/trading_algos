from datetime import datetime, timezone
from pathlib import Path
from xmlrpc.client import Fault

from trading_algos_dashboard.app import create_app
from trading_algos_dashboard.config import DashboardConfig
from trading_algos_dashboard.services.data_source_service import (
    DataSourceUnavailableError,
    MarketDataUnavailableError,
    SmarttradeDataSourceService,
)


class _Collection:
    def __init__(self):
        self.docs = []

    class _DeleteResult:
        def __init__(self, deleted_count):
            self.deleted_count = deleted_count

    def find(self, *_args, **_kwargs):
        return self

    def sort(self, *_args, **_kwargs):
        return self

    def insert_one(self, payload):
        self.docs.append(dict(payload))

    def find_one(self, query):
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in query.items()):
                return doc
        return None

    def update_one(self, query, update):
        doc = self.find_one(query)
        if doc is None:
            return None
        if "$set" in update and isinstance(update["$set"], dict):
            doc.update(update["$set"])
        return None

    def delete_one(self, query):
        for index, doc in enumerate(self.docs):
            if all(doc.get(k) == v for k, v in query.items()):
                del self.docs[index]
                return self._DeleteResult(1)
        return self._DeleteResult(0)

    def delete_many(self, query):
        original_count = len(self.docs)
        self.docs = [
            doc
            for doc in self.docs
            if not all(doc.get(k) == v for k, v in query.items())
        ]
        return self._DeleteResult(original_count - len(self.docs))

    def __iter__(self):
        return iter(self.docs)


class _Db(dict):
    def __getitem__(self, key):
        if key not in self:
            self[key] = _Collection()
        return dict.__getitem__(self, key)


class _Client:
    def __init__(self):
        self.db = _Db()

    def __getitem__(self, _db_name):
        return self.db


def test_new_experiment_page_renders(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig("x", "mongodb://example", "db", "reports", "/tmp/smarttrade", 1)
    )
    client = app.test_client()
    response = client.get("/experiments/new")
    assert response.status_code == 200
    assert b"New experiment" in response.data
    assert b'name="symbol"' in response.data
    assert b'name="start_time"' in response.data
    assert b'name="end_time"' in response.data


def test_new_experiment_page_prefills_selected_configuration_from_draft(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig("x", "mongodb://example", "db", "reports", "/tmp/smarttrade", 1)
    )
    draft_id = app.extensions["configuration_builder_service"].create_draft(
        {
            "config_key": "combo_breakout",
            "version": "1",
            "name": "Combo Breakout",
            "root_node_id": "alg1",
            "nodes": [
                {
                    "node_id": "alg1",
                    "node_type": "algorithm",
                    "alg_key": "close_high_channel_breakout",
                    "alg_param": {"window": 2},
                    "buy_enabled": True,
                    "sell_enabled": True,
                }
            ],
            "compatibility_metadata": {},
        }
    )

    client = app.test_client()
    response = client.get(f"/experiments/new?draft_id={draft_id}")

    assert response.status_code == 200
    assert b"Selected configuration" in response.data
    assert b"Combo Breakout" in response.data
    assert draft_id.encode() in response.data
    assert b"close_high_channel_breakout" in response.data


def test_experiment_history_allows_deleting_one_experiment(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig("x", "mongodb://example", "db", "reports", "/tmp/smarttrade", 1)
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_keep",
            "created_at": datetime(2024, 2, 1, 12, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 2, 1, 12, 0, tzinfo=timezone.utc),
            "status": "completed",
            "symbol": "AAPL",
            "time_range": {
                "start": "2024-01-01 09:30:00",
                "end": "2024-01-02 16:00:00",
            },
        }
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_delete",
            "created_at": datetime(2024, 2, 2, 12, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 2, 2, 12, 0, tzinfo=timezone.utc),
            "status": "completed",
            "symbol": "MSFT",
            "time_range": {
                "start": "2024-01-03 09:30:00",
                "end": "2024-01-04 16:00:00",
            },
        }
    )
    app.extensions["result_repository"].insert_result(
        {
            "experiment_id": "exp_delete",
            "alg_key": "alg_a",
            "alg_name": "Algorithm A",
        }
    )

    response = app.test_client().post(
        "/experiments/exp_delete/delete",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/experiments")
    assert app.extensions["experiment_repository"].get_experiment("exp_delete") is None
    assert (
        app.extensions["experiment_repository"].get_experiment("exp_keep") is not None
    )
    assert (
        app.extensions["result_repository"].list_results_for_experiment("exp_delete")
        == []
    )


def test_configuration_detail_offers_run_link(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig("x", "mongodb://example", "db", "reports", "/tmp/smarttrade", 1)
    )
    draft_id = app.extensions["configuration_builder_service"].create_draft(
        {
            "config_key": "combo_breakout",
            "version": "1",
            "name": "Combo Breakout",
            "root_node_id": "alg1",
            "nodes": [
                {
                    "node_id": "alg1",
                    "node_type": "algorithm",
                    "alg_key": "close_high_channel_breakout",
                    "alg_param": {"window": 2},
                    "buy_enabled": True,
                    "sell_enabled": True,
                }
            ],
            "compatibility_metadata": {},
        }
    )

    response = app.test_client().get(f"/configurations/{draft_id}")

    assert response.status_code == 200
    assert b"Run this configuration" in response.data
    assert f"/experiments/new?draft_id={draft_id}".encode() in response.data


def test_new_experiment_page_shows_recent_run_presets(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig("x", "mongodb://example", "db", "reports", "/tmp/smarttrade", 1)
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_newest",
            "created_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "symbol": "MSFT",
            "time_range": {
                "start": "2024-02-01 09:30:00",
                "end": "2024-02-03 16:00:00",
            },
            "selected_algorithms": [{"alg_key": "alg_b", "alg_param": {"window": 10}}],
            "notes": "second note",
        }
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_oldest",
            "created_at": datetime(2024, 2, 1, 12, 0, tzinfo=timezone.utc),
            "symbol": "AAPL",
            "time_range": {
                "start": "2024-01-01 09:30:00",
                "end": "2024-01-31 16:00:00",
            },
            "selected_algorithms": [{"alg_key": "alg_a", "alg_param": {"window": 5}}],
            "notes": "first note",
        }
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_middle",
            "created_at": datetime(2024, 2, 2, 12, 0, tzinfo=timezone.utc),
            "symbol": "NVDA",
            "time_range": {
                "start": "2024-01-15 09:30:00",
                "end": "2024-01-20 16:00:00",
            },
            "selected_algorithms": [{"alg_key": "alg_c", "alg_param": {"window": 7}}],
            "notes": "third note",
        }
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_ignored",
            "created_at": datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
            "symbol": "TSLA",
            "time_range": {
                "start": "2023-12-01 09:30:00",
                "end": "2023-12-31 16:00:00",
            },
            "selected_algorithms": [{"alg_key": "alg_d", "alg_param": {"window": 3}}],
            "notes": "too old",
        }
    )

    client = app.test_client()
    response = client.get("/experiments/new")

    assert response.status_code == 200
    assert b"Recent experiment runs" in response.data
    assert b"recent-experiment-preset" in response.data
    assert b'data-symbol="MSFT"' in response.data
    assert b'data-start-date="2024-02-01"' in response.data
    assert b'data-start-time="09:30"' in response.data
    assert b'data-end-date="2024-02-03"' in response.data
    assert b'data-end-time="16:00"' in response.data
    assert b"data-algorithms-json=" in response.data
    assert b"alg_b" in response.data
    assert b"window" in response.data
    assert b"10" in response.data
    assert b"second note" in response.data
    assert b"too old" not in response.data


def test_create_experiment_returns_503_when_data_source_dependencies_are_missing(
    monkeypatch,
):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig("x", "mongodb://example", "db", "reports", "/tmp/smarttrade", 1)
    )

    monkeypatch.setattr(
        app.extensions["experiment_service"],
        "create_experiment",
        lambda **_kwargs: (_ for _ in ()).throw(
            DataSourceUnavailableError(
                "Smarttrade data service is unavailable. "
                "Please make sure the data server is running. "
                "Tried to connect to 127.0.0.1:7003."
            )
        ),
    )
    client = app.test_client()
    response = client.post(
        "/experiments",
        data={
            "symbol": "AAPL",
            "start_date": "2024-01-01",
            "start_time": "09:30",
            "end_date": "2024-01-31",
            "end_time": "16:00",
            "algorithms_json": "[]",
            "notes": "",
        },
    )

    assert response.status_code == 503
    assert b"Smarttrade data service is unavailable." in response.data
    assert b"Tried to connect to 127.0.0.1:7003." in response.data
    assert b"New experiment" in response.data
    assert b'value="AAPL"' in response.data
    assert b'value="2024-01-01"' in response.data
    assert b'value="09:30"' in response.data
    assert b'value="2024-01-31"' in response.data
    assert b'value="16:00"' in response.data
    assert b"hello note" not in response.data


def test_experiment_form_reuses_cookie_values_on_next_render(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig("x", "mongodb://example", "db", "reports", "/tmp/smarttrade", 1)
    )
    client = app.test_client()
    client.set_cookie(
        "trading_algos_dashboard_experiment_form",
        '{"symbol": "MSFT", "start_date": "2024-02-01", "start_time": "09:30", "end_date": "2024-02-10", "end_time": "16:00", '
        '"algorithms_json": "[{\\"alg_key\\":\\"x\\"}]", "notes": "saved note"}',
    )
    response = client.get("/experiments/new")

    assert response.status_code == 200
    assert b'value="MSFT"' in response.data
    assert b'value="2024-02-01"' in response.data
    assert b'value="09:30"' in response.data
    assert b'value="2024-02-10"' in response.data
    assert b'value="16:00"' in response.data
    assert b"saved note" in response.data


def test_create_experiment_returns_400_for_malformed_algorithm_entries(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig("x", "mongodb://example", "db", "reports", "/tmp/smarttrade", 1)
    )
    client = app.test_client()
    response = client.post(
        "/experiments",
        data={
            "symbol": "AAPL",
            "start_date": "2024-01-01",
            "start_time": "09:30",
            "end_date": "2024-01-31",
            "end_time": "16:00",
            "algorithms_json": '["close_high_channel_breakout"]',
            "notes": "bad payload",
        },
    )

    assert response.status_code == 400
    assert b"Algorithm #1 must be a JSON object" in response.data
    assert b'value="AAPL"' in response.data
    assert b"bad payload" in response.data


def test_create_experiment_accepts_valid_algorithm_payload(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig(
            "x",
            "mongodb://example",
            "db",
            str(tmp_path / "reports"),
            "/tmp/smarttrade",
            1,
        )
    )

    monkeypatch.setattr(
        app.extensions["data_source_service"],
        "fetch_candles",
        lambda **_kwargs: [
            {
                "ts": "2025-01-01 10:00:00",
                "Open": 10,
                "High": 11,
                "Low": 9,
                "Close": 10.5,
            },
            {
                "ts": "2025-01-01 10:00:01",
                "Open": 11,
                "High": 12,
                "Low": 10,
                "Close": 11.5,
            },
            {
                "ts": "2025-01-01 10:00:02",
                "Open": 12,
                "High": 13,
                "Low": 11,
                "Close": 12.5,
            },
        ],
    )
    monkeypatch.setattr(
        app.extensions["data_source_service"],
        "get_market_data_server_details",
        lambda: {
            "kind": "smarttrade_dataserver",
            "ip": "10.0.0.5",
            "port": 7003,
            "endpoint": "10.0.0.5:7003",
        },
    )
    monkeypatch.setattr(
        app.extensions["experiment_service"],
        "_repo_revision",
        lambda: "abc123def456",
    )
    app.extensions["experiment_service"].task_launcher = lambda job: job()

    client = app.test_client()
    response = client.post(
        "/experiments",
        data={
            "symbol": "AAPL",
            "start_date": "2024-01-01",
            "start_time": "09:30",
            "end_date": "2024-01-31",
            "end_time": "16:00",
            "algorithms_json": (
                '[{"alg_key":"close_high_channel_breakout","alg_param":{"window":2}}]'
            ),
            "notes": "good payload",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers["Location"]
    assert "/experiments/exp_" in location

    stored_experiments = app.extensions["experiment_repository"].list_experiments()
    assert len(stored_experiments) == 1
    assert stored_experiments[0]["status"] == "completed"
    assert stored_experiments[0]["selected_algorithms"] == [
        {"alg_key": "close_high_channel_breakout", "alg_param": {"window": 2}}
    ]
    assert stored_experiments[0]["dataset_source"] == {
        "kind": "smarttrade_dataserver",
        "ip": "10.0.0.5",
        "port": 7003,
        "endpoint": "10.0.0.5:7003",
    }
    assert stored_experiments[0]["repo_revision"] == "abc123def456"
    assert isinstance(stored_experiments[0]["started_at"], datetime)
    assert isinstance(stored_experiments[0]["finished_at"], datetime)
    assert stored_experiments[0]["finished_at"] >= stored_experiments[0]["started_at"]
    assert stored_experiments[0]["duration_seconds"] >= 0
    assert Path(stored_experiments[0]["report_base_path"]).exists()
    stored_results = app.extensions["result_repository"].list_results_for_experiment(
        stored_experiments[0]["experiment_id"]
    )
    assert len(stored_results) == 1
    assert stored_results[0]["report"]["report_version"] == "1.0"
    assert stored_results[0]["report"]["charts"]


def test_create_experiment_redirects_to_running_detail_page(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig(
            "x",
            "mongodb://example",
            "db",
            str(tmp_path / "reports"),
            "/tmp/smarttrade",
            1,
        )
    )
    app.extensions["experiment_service"].task_launcher = lambda _job: None

    response = app.test_client().post(
        "/experiments",
        data={
            "symbol": "AAPL",
            "start_date": "2024-01-01",
            "start_time": "09:30",
            "end_date": "2024-01-31",
            "end_time": "16:00",
            "algorithms_json": (
                '[{"alg_key":"close_high_channel_breakout","alg_param":{"window":2}}]'
            ),
            "notes": "good payload",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers["Location"]
    assert "/experiments/exp_" in location

    stored_experiments = app.extensions["experiment_repository"].list_experiments()
    assert len(stored_experiments) == 1
    assert stored_experiments[0]["status"] == "running"
    assert stored_experiments[0]["finished_at"] is None
    assert stored_experiments[0]["duration_seconds"] is None


def test_experiment_detail_shows_runtime_metadata(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig("x", "mongodb://example", "db", "reports", "/tmp/smarttrade", 1)
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_runtime",
            "created_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "started_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "finished_at": datetime(2024, 2, 3, 12, 5, tzinfo=timezone.utc),
            "duration_seconds": 300.0,
            "repo_revision": "accfd73bac055e1555c2d6f8f031cea7095ff35d",
            "symbol": "AAPL",
            "status": "completed",
            "dataset_source": {
                "kind": "smarttrade_dataserver",
                "ip": "127.0.0.1",
                "port": 7003,
                "endpoint": "127.0.0.1:7003",
            },
            "time_range": {
                "start": "2024-02-01 09:30:00",
                "end": "2024-02-03 16:00:00",
            },
            "selected_algorithms": [],
            "notes": "runtime payload",
            "candle_count": 42,
            "execution_steps": [
                {
                    "step": "read_candles",
                    "label": "Read candles",
                    "started_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
                    "finished_at": datetime(2024, 2, 3, 12, 1, tzinfo=timezone.utc),
                    "duration_seconds": 60.0,
                    "metadata": {"candle_count": 42},
                },
                {
                    "step": "run_algorithm",
                    "label": "Run close_high_channel_breakout",
                    "started_at": datetime(2024, 2, 3, 12, 1, tzinfo=timezone.utc),
                    "finished_at": datetime(2024, 2, 3, 12, 5, tzinfo=timezone.utc),
                    "duration_seconds": 240.0,
                    "metadata": {"alg_key": "close_high_channel_breakout"},
                },
            ],
        }
    )

    response = app.test_client().get("/experiments/exp_runtime")

    assert response.status_code == 200
    assert b"Started:" in response.data
    assert b"Finished:" in response.data
    assert b"Duration (seconds):" in response.data
    assert b"Step durations" in response.data
    assert b"Read candles" in response.data
    assert b"Run close_high_channel_breakout" in response.data
    assert b"60.00s" in response.data
    assert b"240.00s" in response.data
    assert b"Git revision:" in response.data
    assert b"127.0.0.1:7003" in response.data
    assert b"accfd73bac055e1555c2d6f8f031cea7095ff35d" in response.data


def test_experiment_detail_renders_standardized_report_sections(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig("x", "mongodb://example", "db", "reports", "/tmp/smarttrade", 1)
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_reported",
            "created_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "started_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "finished_at": datetime(2024, 2, 3, 12, 5, tzinfo=timezone.utc),
            "duration_seconds": 300.0,
            "repo_revision": "abc123",
            "symbol": "AAPL",
            "status": "completed",
            "dataset_source": {"endpoint": "127.0.0.1:7003"},
            "time_range": {
                "start": "2024-02-01 09:30:00",
                "end": "2024-02-03 16:00:00",
            },
            "selected_algorithms": [],
            "input_kind": "single_algorithm",
            "input_snapshot": {"algorithms": []},
            "notes": "reported",
            "candle_count": 10,
        }
    )
    app.extensions["result_repository"].insert_result(
        {
            "experiment_id": "exp_reported",
            "alg_name": "Alg",
            "latest_decision": {"trend": "UP", "confidence": 5},
            "signal_summary": {"buy_count": 1, "sell_count": 1, "total_rows": 3},
            "report": {
                "report_version": "1.0",
                "experiment_summary": {},
                "algorithm_summary": {"algorithm_name": "Alg"},
                "evaluation_summary": {"headline_metrics": {"cumulative_return": 0.1}},
                "charts": [
                    {
                        "title": "Alg Price and Signals",
                        "description": "desc",
                        "payload": None,
                    }
                ],
                "tables": [
                    {
                        "title": "Parameters",
                        "rows": [{"parameter": "window", "value": 2}],
                    }
                ],
                "analysis_blocks": [
                    {"title": "Overall behavior summary", "body": "Body"}
                ],
                "summary_cards": [{"label": "Win rate", "value": 1.0}],
            },
        }
    )

    response = app.test_client().get("/experiments/exp_reported")

    assert response.status_code == 200
    assert b"Win rate" in response.data
    assert b"Overall behavior summary" in response.data
    assert b"Parameters" in response.data
    assert b"Diagnostics" in response.data


def test_running_experiment_detail_shows_runtime_panel(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig("x", "mongodb://example", "db", "reports", "/tmp/smarttrade", 1)
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_running",
            "created_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "started_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "finished_at": None,
            "duration_seconds": None,
            "repo_revision": "abc123",
            "symbol": "AAPL",
            "status": "running",
            "dataset_source": None,
            "time_range": {
                "start": "2024-02-01 09:30:00",
                "end": "2024-02-03 16:00:00",
            },
            "selected_algorithms": [
                {"alg_key": "close_high_channel_breakout", "alg_param": {"window": 2}}
            ],
            "input_kind": "single_algorithm",
            "input_snapshot": {
                "algorithms": [
                    {
                        "alg_key": "close_high_channel_breakout",
                        "alg_param": {"window": 2},
                    }
                ]
            },
            "notes": "runtime payload",
            "candle_count": None,
            "execution_steps": [
                {
                    "step": "read_candles",
                    "label": "Read candles",
                    "started_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
                    "finished_at": datetime(2024, 2, 3, 12, 0, 30, tzinfo=timezone.utc),
                    "duration_seconds": 30.0,
                    "metadata": {},
                }
            ],
        }
    )

    response = app.test_client().get("/experiments/exp_running")

    assert response.status_code == 200
    assert b"Running experiment" in response.data
    assert b"This page updates automatically every second" in response.data
    assert b"data-experiment-runtime=" in response.data
    assert b"data-status-api-url=" in response.data
    assert b"started_at_epoch_ms" in response.data
    assert b"00:00:00" in response.data
    assert b"close_high_channel_breakout" in response.data
    assert b"Step durations" in response.data
    assert b"Read candles" in response.data
    assert b"Stop experiment" in response.data


def test_cancel_experiment_requests_graceful_stop(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig("x", "mongodb://example", "db", "reports", "/tmp/smarttrade", 1)
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_running",
            "created_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "started_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "finished_at": None,
            "duration_seconds": None,
            "repo_revision": "abc123",
            "symbol": "AAPL",
            "status": "running",
            "dataset_source": None,
            "time_range": {
                "start": "2024-02-01 09:30:00",
                "end": "2024-02-03 16:00:00",
            },
            "selected_algorithms": [],
            "input_kind": "single_algorithm",
            "input_snapshot": {"algorithms": []},
            "notes": "runtime payload",
            "candle_count": None,
            "error_message": None,
            "cancel_requested_at": None,
            "cancelled_at": None,
        }
    )

    response = app.test_client().post(
        "/experiments/exp_running/cancel",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Experiment cancellation requested." in response.data
    stored = app.extensions["experiment_repository"].get_experiment("exp_running")
    assert stored is not None
    assert stored["status"] == "cancelled"
    assert stored["cancelled_at"] is not None
    assert stored["process_pid"] is None
    assert b"Experiment cancelled" in response.data


def test_cancel_experiment_marks_cancelled_immediately(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig(
            "x",
            "mongodb://example",
            "db",
            str(tmp_path / "reports"),
            "/tmp/smarttrade",
            1,
        )
    )

    service = app.extensions["experiment_service"]
    service.task_launcher = lambda _job: None

    experiment_id = service.create_experiment(
        symbol="AAPL",
        start_date="2024-01-01",
        start_time="09:30",
        end_date="2024-01-01",
        end_time="09:30",
        algorithms=[
            {"alg_key": "close_high_channel_breakout", "alg_param": {"window": 2}}
        ],
        notes="cancel me",
    )

    requested = service.request_cancel(experiment_id)

    assert requested is True

    stored = app.extensions["experiment_repository"].get_experiment(experiment_id)
    assert stored is not None
    assert stored["status"] == "cancelled"
    assert stored["cancelled_at"] is not None
    assert stored["finished_at"] is not None
    assert stored["process_pid"] is None


def test_cancel_experiment_rejects_completed_experiment(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig("x", "mongodb://example", "db", "reports", "/tmp/smarttrade", 1)
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_done",
            "created_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "started_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "finished_at": datetime(2024, 2, 3, 12, 5, tzinfo=timezone.utc),
            "duration_seconds": 300.0,
            "repo_revision": "abc123",
            "symbol": "AAPL",
            "status": "completed",
            "dataset_source": None,
            "time_range": {
                "start": "2024-02-01 09:30:00",
                "end": "2024-02-03 16:00:00",
            },
            "selected_algorithms": [],
            "input_kind": "single_algorithm",
            "input_snapshot": {"algorithms": []},
            "notes": "done",
            "candle_count": 1,
            "error_message": None,
            "cancel_requested_at": None,
            "cancelled_at": None,
        }
    )

    response = app.test_client().post(
        "/experiments/exp_done/cancel",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"cannot be cancelled" in response.data


def test_create_experiment_returns_400_when_data_fetch_fault_occurs(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig(
            "x",
            "mongodb://example",
            "db",
            str(tmp_path / "reports"),
            "/tmp/smarttrade",
            1,
        )
    )

    class _FaultyProxy:
        def get_data(self, _symbol, _ts):
            raise Fault(1, "<class 'Exception'>:")

    monkeypatch.setattr(
        app.extensions["data_source_service"],
        "_data_proxy",
        lambda: _FaultyProxy(),
    )
    app.extensions["experiment_service"].task_launcher = lambda job: job()

    client = app.test_client()
    response = client.post(
        "/experiments",
        data={
            "symbol": "AAPL",
            "start_date": "2024-01-01",
            "start_time": "09:30",
            "end_date": "2024-01-01",
            "end_time": "09:30",
            "algorithms_json": (
                '[{"alg_key":"close_high_channel_breakout","alg_param":{"window":2}}]'
            ),
            "notes": "fault payload",
        },
    )
    assert response.status_code == 302
    location = response.headers["Location"]
    assert "/experiments/exp_" in location

    stored_experiments = app.extensions["experiment_repository"].list_experiments()
    assert len(stored_experiments) == 1
    assert stored_experiments[0]["status"] == "failed"
    assert (
        stored_experiments[0]["error_message"]
        == "No candle data is available for the requested symbol and time range. Please choose a range that contains market data."
    )

    detail_response = client.get(location)
    assert detail_response.status_code == 200
    assert b"Experiment failed" in detail_response.data
    assert (
        b"No candle data is available for the requested symbol and time range."
        in detail_response.data
    )
    assert b"fault payload" in detail_response.data


def test_create_experiment_returns_400_when_no_market_data_is_available(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig(
            "x",
            "mongodb://example",
            "db",
            str(tmp_path / "reports"),
            "/tmp/smarttrade",
            1,
        )
    )

    monkeypatch.setattr(
        app.extensions["experiment_service"],
        "create_experiment",
        lambda **_kwargs: (_ for _ in ()).throw(
            MarketDataUnavailableError(
                "No candle data is available for the requested symbol and time range."
            )
        ),
    )

    client = app.test_client()
    response = client.post(
        "/experiments",
        data={
            "symbol": "AAPL",
            "start_date": "2024-01-01",
            "start_time": "09:30",
            "end_date": "2024-01-01",
            "end_time": "09:30",
            "algorithms_json": (
                '[{"alg_key":"close_high_channel_breakout","alg_param":{"window":2}}]'
            ),
            "notes": "no data payload",
        },
    )

    assert response.status_code == 400
    assert (
        b"No candle data is available for the requested symbol and time range."
        in response.data
    )
    assert b"New experiment" in response.data
    assert b'value="AAPL"' in response.data
    assert b"no data payload" in response.data


def test_fetch_candles_skips_missing_timestamps_when_other_data_exists():
    service = SmarttradeDataSourceService(smarttrade_path="/tmp/smarttrade", user_id=1)

    class _Proxy:
        def get_data(self, _symbol, ts):
            if ts.minute == 31:
                raise Fault(1, "missing candle")
            return {
                "_id": "mongo-id",
                "ts": ts.isoformat(sep=" "),
                "Open": 10,
                "High": 11,
                "Low": 9,
                "Close": 10.5,
            }

    service._data_proxy = lambda: _Proxy()  # type: ignore[method-assign]

    candles = service.fetch_candles(
        symbol="AAPL",
        start=datetime.fromisoformat("2024-01-01T09:30"),
        end=datetime.fromisoformat("2024-01-01T09:32"),
    )

    assert len(candles) == 2
    assert [item["ts"] for item in candles] == [
        "2024-01-01 09:30:00",
        "2024-01-01 09:32:00",
    ]
    assert all("_id" not in item for item in candles)


def test_fetch_candles_raises_market_data_error_when_all_timestamps_are_missing():
    service = SmarttradeDataSourceService(smarttrade_path="/tmp/smarttrade", user_id=1)

    class _Proxy:
        def get_data(self, _symbol, _ts):
            raise Fault(1, "missing candle")

    service._data_proxy = lambda: _Proxy()  # type: ignore[method-assign]

    try:
        service.fetch_candles(
            symbol="AAPL",
            start=datetime.fromisoformat("2024-01-01T09:30"),
            end=datetime.fromisoformat("2024-01-01T09:31"),
        )
    except MarketDataUnavailableError as exc:
        assert str(exc) == (
            "No candle data is available for the requested symbol and time range. "
            "Please choose a range that contains market data."
        )
    else:
        raise AssertionError("Expected MarketDataUnavailableError")


def test_data_source_unavailable_message_includes_data_server_endpoint(monkeypatch):
    service = SmarttradeDataSourceService(smarttrade_path="/tmp/smarttrade", user_id=1)

    monkeypatch.setattr(
        service,
        "_data_server_endpoint_label",
        lambda: "127.0.0.1:7003",
    )

    assert service._format_unavailable_message() == (
        "Smarttrade data service is unavailable. "
        "Please make sure the data server is running. "
        "Tried to connect to 127.0.0.1:7003."
    )


def test_new_experiment_page_shows_cleanup_action_for_legacy_selected_algorithms(
    monkeypatch,
):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig("x", "mongodb://example", "db", "reports", "/tmp/smarttrade", 1)
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_legacy",
            "created_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "symbol": "AAPL",
            "time_range": {
                "start": "2024-02-01 09:30:00",
                "end": "2024-02-03 16:00:00",
            },
            "selected_algorithms": ["close_high_channel_breakout"],
            "notes": "legacy payload",
        }
    )

    client = app.test_client()
    response = client.get("/experiments/new")

    assert response.status_code == 200
    assert b"Clean selected algos" in response.data
    assert b"/experiments/exp_legacy/cleanup-selected-algorithms" in response.data


def test_new_experiment_page_shows_cleanup_action_for_non_legacy_selected_algorithms(
    monkeypatch,
):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig("x", "mongodb://example", "db", "reports", "/tmp/smarttrade", 1)
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_clean",
            "created_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "symbol": "AAPL",
            "time_range": {
                "start": "2024-02-01 09:30:00",
                "end": "2024-02-03 16:00:00",
            },
            "selected_algorithms": [
                {"alg_key": "close_high_channel_breakout", "alg_param": {"window": 20}}
            ],
            "notes": "valid payload",
        }
    )

    client = app.test_client()
    response = client.get("/experiments/new")

    assert response.status_code == 200
    assert b"Clean selected algos" in response.data
    assert b"/experiments/exp_clean/cleanup-selected-algorithms" in response.data


def test_recent_preset_ignores_invalid_selected_algorithm_entries_in_algorithms_json(
    monkeypatch,
):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig("x", "mongodb://example", "db", "reports", "/tmp/smarttrade", 1)
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_mixed",
            "created_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "symbol": "AAPL",
            "time_range": {
                "start": "2024-02-01 09:30:00",
                "end": "2024-02-03 16:00:00",
            },
            "selected_algorithms": [
                "close_high_channel_breakout",
                {"alg_key": "close_high_channel_breakout", "alg_param": {"window": 20}},
                {"alg_param": {"window": 5}},
            ],
            "notes": "mixed payload",
        }
    )

    client = app.test_client()
    response = client.get("/experiments/new")

    assert response.status_code == 200
    assert b"data-algorithms-json=" in response.data
    assert b"close_high_channel_breakout" in response.data
    assert b"window" in response.data
    assert b"20" in response.data
    assert b'close_high_channel_breakout"]' not in response.data


def test_recent_preset_does_not_double_encode_algorithms_json(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig("x", "mongodb://example", "db", "reports", "/tmp/smarttrade", 1)
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_boundary",
            "created_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "symbol": "AAPL",
            "time_range": {
                "start": "2024-02-01 09:30:00",
                "end": "2024-02-03 16:00:00",
            },
            "selected_algorithms": [
                {"alg_key": "boundary_breakout", "alg_param": {"period": 5}}
            ],
            "notes": "boundary payload",
        }
    )

    client = app.test_client()
    response = client.get("/experiments/new")

    assert response.status_code == 200
    assert b'data-algorithms-json="[{' not in response.data
    assert (
        b"data-algorithms-json='[{&#34;alg_key&#34;: &#34;boundary_breakout&#34;, &#34;alg_param&#34;: {&#34;period&#34;: 5}}]'"
        in response.data
    )


def test_cleanup_selected_algorithms_rewrites_legacy_entries(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig("x", "mongodb://example", "db", "reports", "/tmp/smarttrade", 1)
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_legacy",
            "created_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "symbol": "AAPL",
            "time_range": {
                "start": "2024-02-01 09:30:00",
                "end": "2024-02-03 16:00:00",
            },
            "selected_algorithms": ["close_high_channel_breakout"],
            "notes": "legacy payload",
        }
    )

    client = app.test_client()
    response = client.post("/experiments/exp_legacy/cleanup-selected-algorithms")

    assert response.status_code == 302
    stored = app.extensions["experiment_repository"].get_experiment("exp_legacy")
    assert stored is not None
    assert stored["selected_algorithms"] == []


def test_cleanup_selected_algorithms_returns_error_for_unknown_legacy_algorithm(
    monkeypatch,
):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig("x", "mongodb://example", "db", "reports", "/tmp/smarttrade", 1)
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_unknown",
            "created_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "symbol": "AAPL",
            "time_range": {
                "start": "2024-02-01 09:30:00",
                "end": "2024-02-03 16:00:00",
            },
            "selected_algorithms": ["missing_alg"],
            "notes": "legacy payload",
        }
    )

    client = app.test_client()
    response = client.post(
        "/experiments/exp_unknown/cleanup-selected-algorithms",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Removed saved selected algorithm config." in response.data
    stored = app.extensions["experiment_repository"].get_experiment("exp_unknown")
    assert stored is not None
    assert stored["selected_algorithms"] == []


def test_experiment_detail_shows_cleanup_action_for_legacy_selected_algorithms(
    monkeypatch,
):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig("x", "mongodb://example", "db", "reports", "/tmp/smarttrade", 1)
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_legacy",
            "created_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "symbol": "AAPL",
            "time_range": {
                "start": "2024-02-01 09:30:00",
                "end": "2024-02-03 16:00:00",
            },
            "selected_algorithms": ["close_high_channel_breakout"],
            "notes": "legacy payload",
            "candle_count": 0,
        }
    )

    client = app.test_client()
    response = client.get("/experiments/exp_legacy")

    assert response.status_code == 200
    assert b"Clean selected algos" not in response.data
    assert b"/experiments/exp_legacy/cleanup-selected-algorithms" not in response.data


def test_cleanup_selected_algorithms_hides_action_after_success(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig("x", "mongodb://example", "db", "reports", "/tmp/smarttrade", 1)
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_legacy",
            "created_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "symbol": "AAPL",
            "time_range": {
                "start": "2024-02-01 09:30:00",
                "end": "2024-02-03 16:00:00",
            },
            "selected_algorithms": ["close_high_channel_breakout"],
            "notes": "legacy payload",
            "candle_count": 0,
        }
    )

    client = app.test_client()
    cleanup_response = client.post(
        "/experiments/exp_legacy/cleanup-selected-algorithms",
        headers={"Referer": "/experiments/exp_legacy"},
        follow_redirects=True,
    )

    assert cleanup_response.status_code == 200
    assert b"Removed saved selected algorithm config." in cleanup_response.data
    assert b"Clean selected algos" not in cleanup_response.data

    history_response = client.get("/experiments")
    assert history_response.status_code == 200
    assert b"Clean selected algos" not in history_response.data


def test_history_page_does_not_show_cleanup_action(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig("x", "mongodb://example", "db", "reports", "/tmp/smarttrade", 1)
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_history",
            "created_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "symbol": "AAPL",
            "time_range": {
                "start": "2024-02-01 09:30:00",
                "end": "2024-02-03 16:00:00",
            },
            "selected_algorithms": ["close_high_channel_breakout"],
            "notes": "history payload",
            "candle_count": 0,
        }
    )

    client = app.test_client()
    response = client.get("/experiments")

    assert response.status_code == 200
    assert b"Clean selected algos" not in response.data


def test_cleanup_selected_algorithms_removes_recent_preset_box(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig("x", "mongodb://example", "db", "reports", "/tmp/smarttrade", 1)
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_legacy",
            "created_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "symbol": "AAPL",
            "time_range": {
                "start": "2024-02-01 09:30:00",
                "end": "2024-02-03 16:00:00",
            },
            "selected_algorithms": ["close_high_channel_breakout"],
            "notes": "legacy payload",
        }
    )

    client = app.test_client()
    cleanup_response = client.post(
        "/experiments/exp_legacy/cleanup-selected-algorithms",
        headers={"Referer": "/experiments/new"},
        follow_redirects=True,
    )

    assert cleanup_response.status_code == 200
    assert b"Removed saved selected algorithm config." in cleanup_response.data
    assert b"recent-experiment-preset" not in cleanup_response.data
