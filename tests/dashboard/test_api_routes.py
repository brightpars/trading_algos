from typing import Any

from trading_algos_dashboard.app import create_app
from trading_algos_dashboard.config import DashboardConfig


class _Collection:
    def __init__(self):
        self.docs = []

    def find(self, query=None, **_kwargs):
        effective_query = dict(query or {})
        filtered = [
            doc
            for doc in self.docs
            if all(doc.get(k) == v for k, v in effective_query.items())
        ]
        return _Cursor(filtered)

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

    def delete_many(self, query):
        original_count = len(self.docs)
        self.docs = [
            doc
            for doc in self.docs
            if not all(doc.get(k) == v for k, v in query.items())
        ]
        return type(
            "_DeleteResult", (), {"deleted_count": original_count - len(self.docs)}
        )()

    def count_documents(self, query):
        return sum(
            1 for doc in self.docs if all(doc.get(k) == v for k, v in query.items())
        )

    def __iter__(self):
        return iter(self.docs)


class _Cursor:
    def __init__(self, docs: list[dict[str, Any]]):
        self.docs = docs

    def sort(self, key, direction):
        reverse = direction == -1
        return sorted(
            self.docs,
            key=lambda item: str(item.get(key, "")),
            reverse=reverse,
        )

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
        DashboardConfig(
            "x",
            "mongodb://example",
            "db",
            "reports",
            "/tmp/smarttrade",
            1,
            experiment_max_concurrent_runs=2,
        )
    )


def _seed_algorithm_catalog(app) -> None:
    app.extensions["algorithm_catalog_repository"].upsert_entry(
        source_version="v2",
        catalog_type="algorithm",
        catalog_number=6,
        document={
            "id": "entry-1",
            "catalog_type": "algorithm",
            "catalog_number": 6,
            "name": "Breakout (Donchian Channel)",
            "slug": "breakout-donchian-channel",
            "category": "Trend Following",
            "subcategory": "",
            "advanced_label": "No",
            "best_use_horizon": "Swing / position trading",
            "home_suitability_score": 1,
            "core_idea": "Buy on breakout above rolling high; sell on breakdown below rolling low.",
            "typical_inputs": "OHLCV high/low, lookback window",
            "signal_style": "Discrete breakout entries/exits",
            "extended_implementation_details": "Detailed notes",
            "initial_reference": "INV-ALGO",
            "source_version": "v2",
            "source_path": "docs/file.md",
            "source_row_hash": "abc",
            "source_origin": "imported",
            "is_active": True,
            "implementation_id": "boundary_breakout",
            "implementation_catalog_ref": "algorithm:6",
            "implementation_source": "runtime_declared",
            "implementation_confidence": 1.0,
            "implementation_mapping_notes": "implementation declared",
            "implementation_mapping_reason": "implementation-declared catalog_ref",
            "review_state": "confirmed",
            "created_at": "now",
            "updated_at": "now",
        },
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


def test_algorithm_catalog_api_returns_imported_entries(monkeypatch):
    app = _build_app(monkeypatch)
    _seed_algorithm_catalog(app)
    response = app.test_client().get("/api/algorithms/catalog")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload
    assert any(item["name"] == "Breakout (Donchian Channel)" for item in payload)


def test_algorithm_catalog_api_supports_filters(monkeypatch):
    app = _build_app(monkeypatch)
    _seed_algorithm_catalog(app)
    response = app.test_client().get(
        "/api/algorithms/catalog?category=Trend%20Following&search=breakout"
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload) >= 1


def test_algorithm_catalog_detail_api_returns_rich_payload(monkeypatch):
    app = _build_app(monkeypatch)
    _seed_algorithm_catalog(app)
    entries = app.extensions["algorithm_catalog_service"].list_catalog_entries()
    response = app.test_client().get(f"/api/algorithms/catalog/{entries[0]['id']}")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["extended_implementation_details"]
    assert "implementation_status" in payload


def test_algorithm_catalog_admin_api_returns_filtered_queue(monkeypatch):
    app = _build_app(monkeypatch)
    _seed_algorithm_catalog(app)
    response = app.test_client().get(
        "/api/algorithms/catalog/admin?linked=true&advanced_label=No"
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["total_count"] >= 1
    assert payload["items"][0]["link_source_label"]


def test_algorithm_catalog_admin_api_search_matches_implementation_metadata(
    monkeypatch,
):
    app = _build_app(monkeypatch)
    _seed_algorithm_catalog(app)
    response = app.test_client().get(
        "/api/algorithms/catalog/admin?search=implementation%20declared"
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["total_count"] >= 1


def test_algorithm_catalog_admin_api_supports_full_filter_set(monkeypatch):
    app = _build_app(monkeypatch)
    _seed_algorithm_catalog(app)
    response = app.test_client().get(
        "/api/algorithms/catalog/admin"
        "?status=implemented"
        "&review_state=confirmed"
        "&only_broken=false"
        "&only_unresolved=false"
        "&category=Trend%20Following"
        "&catalog_type=algorithm"
        "&advanced_label=No"
        "&linked=true"
        "&search=breakout"
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["total_count"] == 1
    assert payload["items"][0]["name"] == "Breakout (Donchian Channel)"


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


def test_experiment_queue_api_returns_running_and_queued_items(monkeypatch):
    app = _build_app(monkeypatch)
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_running",
            "created_at": "2024-02-03T12:00:00Z",
            "started_at": "2024-02-03T12:01:00Z",
            "status": "running",
            "symbol": "AAPL",
        }
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_queued",
            "created_at": "2024-02-03T12:02:00Z",
            "queue_enqueued_at": "2024-02-03T12:02:00Z",
            "status": "queued",
            "symbol": "MSFT",
        }
    )

    response = app.test_client().get("/api/experiments/queue")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["running_experiments"][0]["experiment_id"] == "exp_running"
    assert payload["queued_experiments"][0]["experiment_id"] == "exp_queued"
    assert payload["queue_summary"]["running_count"] == 1
    assert payload["queue_summary"]["max_concurrent_experiments"] == 2
    assert payload["queue_summary"]["queued_count"] == 1
