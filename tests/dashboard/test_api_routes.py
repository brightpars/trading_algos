from trading_algos_dashboard.app import create_app
from trading_algos_dashboard.config import DashboardConfig


class _Collection:
    def __init__(self):
        self.docs = []

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

    def update_one(self, query, update, upsert=False):
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in query.items()):
                if "$set" in update:
                    doc.update(update["$set"])
                return None
        if upsert:
            payload = dict(query)
            if "$set" in update:
                payload.update(update["$set"])
            self.docs.append(payload)
        return None

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


def _build_app(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    return create_app(
        DashboardConfig("x", "mongodb://example", "db", "reports", "/tmp/smarttrade", 1)
    )


def test_algorithms_api_exposes_param_schema(monkeypatch):
    app = _build_app(monkeypatch)
    response = app.test_client().get("/api/algorithms")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload
    close_high = next(
        item for item in payload if item["key"] == "close_high_channel_breakout"
    )
    assert close_high["param_schema"]
    assert close_high["param_schema"][0]["key"] == "window"


def test_validate_configuration_api_returns_structured_errors(monkeypatch):
    app = _build_app(monkeypatch)
    response = app.test_client().post(
        "/api/configurations/validate",
        json={
            "config_key": "demo",
            "version": "1",
            "name": "Demo",
            "root_node_id": "group-1",
            "nodes": [
                {
                    "node_id": "group-1",
                    "node_type": "and",
                    "children": ["missing-child"],
                }
            ],
        },
    )
    assert response.status_code == 400
    payload = response.get_json()
    assert payload["ok"] is False
    assert payload["errors"]


def test_validate_configuration_api_returns_normalized_configuration(monkeypatch):
    app = _build_app(monkeypatch)
    response = app.test_client().post(
        "/api/configurations/validate",
        json={
            "config_key": "demo",
            "version": "1",
            "name": "Demo",
            "root_node_id": "alg-1",
            "nodes": [
                {
                    "node_id": "alg-1",
                    "node_type": "algorithm",
                    "alg_key": "close_high_channel_breakout",
                    "alg_param": {"window": 2},
                    "buy_enabled": True,
                    "sell_enabled": True,
                }
            ],
        },
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["configuration"]["config_key"] == "demo"


def test_experiment_api_returns_runtime_metadata(monkeypatch):
    app = _build_app(monkeypatch)
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_meta",
            "created_at": "2024-02-03T12:00:00Z",
            "started_at": "2024-02-03T12:00:00Z",
            "finished_at": "2024-02-03T12:05:00Z",
            "duration_seconds": 300.0,
            "repo_revision": "abc123",
            "status": "completed",
            "symbol": "AAPL",
            "dataset_source": {
                "kind": "smarttrade_dataserver",
                "ip": "127.0.0.1",
                "port": 7003,
                "endpoint": "127.0.0.1:7003",
            },
            "candle_count": 42,
        }
    )

    response = app.test_client().get("/api/experiments/exp_meta")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["experiment"]["started_at"] == "2024-02-03T12:00:00Z"
    assert payload["experiment"]["finished_at"] == "2024-02-03T12:05:00Z"
    assert payload["experiment"]["duration_seconds"] == 300.0
    assert payload["experiment"]["repo_revision"] == "abc123"
    assert payload["experiment"]["dataset_source"]["endpoint"] == "127.0.0.1:7003"


def test_experiment_api_returns_running_status_metadata(monkeypatch):
    app = _build_app(monkeypatch)
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_running",
            "created_at": "2024-02-03T12:00:00Z",
            "started_at": "2024-02-03T12:00:00Z",
            "finished_at": None,
            "duration_seconds": None,
            "repo_revision": "abc123",
            "status": "running",
            "symbol": "AAPL",
            "dataset_source": None,
            "candle_count": None,
            "error_message": None,
        }
    )

    response = app.test_client().get("/api/experiments/exp_running")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["experiment"]["status"] == "running"
    assert payload["experiment"]["finished_at"] is None
    assert payload["experiment"]["duration_seconds"] is None
    assert payload["experiment"]["dataset_source"] is None
    assert isinstance(payload["experiment"]["started_at_epoch_ms"], int)
