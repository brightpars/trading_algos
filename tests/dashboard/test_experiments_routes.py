import json
from datetime import datetime, timezone
from pathlib import Path
from xmlrpc.client import Fault

from trading_algos_dashboard.app import create_app
from trading_algos_dashboard.config import DashboardConfig
from trading_algos_dashboard.services.data_source_service import (
    DataSourceUnavailableError,
    MarketDataFetchResult,
    MarketDataUnavailableError,
    MarketDataSourceService,
)


def _single_algorithm_configuration_payload(
    alg_key: str = "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
    alg_param: dict[str, object] | None = None,
) -> str:
    return json.dumps(
        {
            "config_key": "single-test",
            "version": "1",
            "name": "Single algorithm",
            "root_node_id": "alg1",
            "nodes": [
                {
                    "node_id": "alg1",
                    "node_type": "algorithm",
                    "alg_key": alg_key,
                    "alg_param": alg_param or {"window": 2},
                    "buy_enabled": True,
                    "sell_enabled": True,
                }
            ],
            "runtime_overrides": {},
            "compatibility_metadata": {},
        }
    )


class _Collection:
    def __init__(self):
        self.docs = []

    @staticmethod
    def _matches_query(doc, query):
        for key, value in query.items():
            if key == "$or":
                if not any(_Collection._matches_query(doc, item) for item in value):
                    return False
                continue
            if isinstance(value, dict):
                if "$lte" in value:
                    doc_value = doc.get(key)
                    if doc_value is None or doc_value > value["$lte"]:
                        return False
                    continue
            if doc.get(key) != value:
                return False
        return True

    class _DeleteResult:
        def __init__(self, deleted_count):
            self.deleted_count = deleted_count

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
        doc = self.find_one(query)
        if doc is None:
            if not upsert:
                return None
            doc = dict(query)
            self.docs.append(doc)
        if "$set" in update and isinstance(update["$set"], dict):
            doc.update(update["$set"])
        return None

    def count_documents(self, query):
        return sum(
            1 for doc in self.docs if all(doc.get(k) == v for k, v in query.items())
        )

    def find_one_and_update(
        self, query, update, sort=None, return_document=None, upsert=False
    ):
        matches = [doc for doc in self.docs if self._matches_query(doc, query)]
        if sort:
            for key, direction in reversed(sort):
                matches.sort(key=lambda item: item.get(key), reverse=direction == -1)
        if not matches:
            if not upsert:
                return None
            doc = {}
            for key, value in query.items():
                if key.startswith("$") or isinstance(value, dict):
                    continue
                doc[key] = value
            if "$set" in update and isinstance(update["$set"], dict):
                doc.update(update["$set"])
            self.docs.append(doc)
            return dict(doc)
        doc = matches[0]
        if "$set" in update and isinstance(update["$set"], dict):
            doc.update(update["$set"])
        return dict(doc)

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


class _Cursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, key=None, direction=None):
        if key is None:
            return self
        reverse = direction == -1
        return _Cursor(
            sorted(
                self.docs,
                key=lambda item: (
                    str(item.get(key, "")) if isinstance(item, dict) else ""
                ),
                reverse=reverse,
            )
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


def test_new_experiment_page_renders(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))
    client = app.test_client()
    response = client.get("/experiments/new")
    assert response.status_code == 200
    assert b"New experiment" in response.data
    assert b'name="symbol"' in response.data
    assert b'name="start_time"' in response.data
    assert b'name="end_time"' in response.data
    assert b'name="max_concurrent_experiments"' not in response.data
    assert b"Scheduler concurrency" in response.data
    assert b"Open scheduler settings" in response.data
    assert b"executed up to the configured concurrency limit" in response.data
    assert b"Engine chain (many alertgens + one decmaker)" in response.data
    assert b">Configuration<" in response.data
    assert b'name="alertgens_json"' in response.data
    assert b'name="configuration_json"' in response.data
    assert b'name="decmaker_key"' in response.data
    assert b'name="speed_factor"' in response.data
    assert b'id="run-mode-select"' in response.data
    assert b'data-run-mode-section="engine_chain"' in response.data
    assert b'data-run-mode-section="configuration"' in response.data
    assert b'name="configuration_source"' in response.data
    assert b"Quick builder (single algorithm)" in response.data
    assert b"Saved configuration" in response.data
    assert b'name="quick_builder_alg_key"' in response.data
    assert b'name="selected_draft_id"' in response.data
    assert b'data-configuration-source-section="quick_builder"' in response.data
    assert b'data-configuration-source-section="saved_configuration"' in response.data
    assert b'data-configuration-source-section="configuration_json"' in response.data
    assert (
        b"Recent configurations" in response.data
        or b"Select a saved configuration" in response.data
    )
    assert b"Starter templates" in response.data
    assert b"Search saved configurations by name or key" in response.data
    assert b'id="quick-builder-configuration-preview"' in response.data
    assert b"readonly" in response.data
    assert b"data-default-param=" in response.data
    assert (
        b'<option value="configuration" selected>Configuration</option>'
        in response.data
    )
    assert (
        b"/experiments/configuration-templates/single_algorithm/open-in-builder"
        in response.data
    )
    assert b'name="algorithms_json"' not in response.data


def test_new_experiment_page_preserves_selected_engine_chain_run_mode(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))
    client = app.test_client()
    client.set_cookie(
        "trading_algos_dashboard_experiment_form",
        '{"run_mode": "engine_chain", "alertgens_json": "[]", "decmaker_key": "alg1", "decmaker_param_json": "{}", "speed_factor": "30"}',
    )

    response = client.get("/experiments/new")

    assert response.status_code == 200
    assert (
        b'<option value="engine_chain" selected>Engine chain (many alertgens + one decmaker)</option>'
        in response.data
    )
    assert b'data-run-mode-section="engine_chain"' in response.data
    assert b'id="engine-chain-payload-preview"' in response.data
    assert b"Advanced generated JSON details" in response.data


def test_new_experiment_page_shows_engine_chain_combined_preview(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))

    response = app.test_client().get("/experiments/new")

    assert response.status_code == 200
    assert b'id="engine-chain-payload-preview"' in response.data
    assert b"Generated engine chain payload" in response.data
    assert b"Advanced generated JSON details" in response.data
    assert b'id="engine-alertgen-add"' in response.data
    assert b'name="engine_alertgen_order"' in response.data


def test_bulk_experiment_page_renders(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))

    response = app.test_client().get("/experiments/bulk")

    assert response.status_code == 200
    assert b"Bulk runs" in response.data
    assert b"Run all runnable algorithms for one symbol" in response.data
    assert b"Run one algorithm for many symbols" in response.data
    assert b"Queue all runnable algorithms" in response.data
    assert b"Queue one experiment per symbol" in response.data


def test_bulk_experiment_creates_one_queued_experiment_per_runnable_algorithm(
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
        )
    )
    app.extensions["experiment_service"].dispatch_available_experiments = lambda: []

    response = app.test_client().post(
        "/experiments/bulk",
        data={
            "bulk_mode": "all_algorithms_for_symbol",
            "symbol": "AAPL",
            "skip_non_executable_defaults": "true",
            "start_date": "2024-01-01",
            "start_time": "09:30",
            "end_date": "2024-01-31",
            "end_time": "16:00",
            "notes": "bulk all algos",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/experiments")
    experiments = app.extensions["experiment_repository"].list_experiments()
    assert len(experiments) >= 1
    assert all(experiment["symbol"] == "AAPL" for experiment in experiments)
    assert all(experiment["status"] == "queued" for experiment in experiments)
    assert all(
        len(experiment["selected_algorithms"]) == 1 for experiment in experiments
    )


def test_bulk_experiment_creates_one_queued_experiment_per_symbol(
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
        )
    )
    app.extensions["experiment_service"].dispatch_available_experiments = lambda: []

    response = app.test_client().post(
        "/experiments/bulk",
        data={
            "bulk_mode": "single_algorithm_for_symbols",
            "alg_key": "OLD_boundary_breakout_NEW_breakout_donchian_channel",
            "symbols_text": "AAPL\nMSFT\nAAPL",
            "start_date": "2024-01-01",
            "start_time": "09:30",
            "end_date": "2024-01-31",
            "end_time": "16:00",
            "notes": "bulk many symbols",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/experiments")
    experiments = app.extensions["experiment_repository"].list_experiments()
    assert len(experiments) == 2
    assert sorted(experiment["symbol"] for experiment in experiments) == [
        "AAPL",
        "MSFT",
    ]
    assert all(
        experiment["selected_algorithms"][0]["alg_key"]
        == "OLD_boundary_breakout_NEW_breakout_donchian_channel"
        for experiment in experiments
    )


def test_bulk_experiment_returns_400_and_preserves_form_state_for_invalid_symbols(
    monkeypatch,
):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))

    response = app.test_client().post(
        "/experiments/bulk",
        data={
            "bulk_mode": "single_algorithm_for_symbols",
            "alg_key": "OLD_boundary_breakout_NEW_breakout_donchian_channel",
            "symbols_text": " , \n  ",
            "start_date": "2024-01-01",
            "start_time": "09:30",
            "end_date": "2024-01-31",
            "end_time": "16:00",
            "notes": "bad bulk",
        },
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert b"At least one symbol is required." in response.data
    assert b"bad bulk" in response.data
    assert b"OLD_boundary_breakout_NEW_breakout_donchian_channel" in response.data


def test_create_experiment_does_not_update_runtime_concurrency_setting(
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
            experiment_max_concurrent_runs=2,
        )
    )
    app.extensions["experiment_service"].dispatch_available_experiments = lambda: []

    response = app.test_client().post(
        "/experiments",
        data={
            "symbol": "AAPL",
            "start_date": "2024-01-01",
            "start_time": "09:30",
            "end_date": "2024-01-31",
            "end_time": "16:00",
            "configuration_json": _single_algorithm_configuration_payload(),
            "notes": "runtime setting",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    settings = app.extensions[
        "experiment_runtime_settings_service"
    ].get_effective_settings()
    assert settings["max_concurrent_experiments"] == 2


def test_create_experiment_accepts_engine_chain_payload(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig(
            "x",
            "mongodb://example",
            "db",
            str(tmp_path / "reports"),
        )
    )
    app.extensions["experiment_service"].dispatch_available_experiments = lambda: []

    response = app.test_client().post(
        "/experiments",
        data={
            "run_mode": "engine_chain",
            "symbol": "AAPL",
            "start_date": "2024-01-01",
            "start_time": "09:30",
            "end_date": "2024-01-01",
            "end_time": "16:00",
            "alertgens_json": (
                '[{"alg_key":"OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation","alg_param":{"window":2}}]'
            ),
            "decmaker_key": "alg1",
            "decmaker_param_json": (
                '{"confidence_threshold_buy":0.6,"confidence_threshold_sell":0.6,"max_percent_higher_price_buy":0.0,"max_percent_lower_price_sell":0.0}'
            ),
            "speed_factor": "30",
            "notes": "engine chain run",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    experiments = app.extensions["experiment_repository"].list_experiments()
    assert len(experiments) == 1
    assert experiments[0]["input_kind"] == "engine_chain"
    assert experiments[0]["input_snapshot"]["speed_factor"] == 30
    assert experiments[0]["input_snapshot"]["decmaker"]["decmaker_key"] == "alg1"


def test_create_experiment_accepts_engine_chain_guided_builder_payload(
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
        )
    )
    app.extensions["experiment_service"].dispatch_available_experiments = lambda: []

    response = app.test_client().post(
        "/experiments",
        data={
            "run_mode": "engine_chain",
            "symbol": "AAPL",
            "start_date": "2024-01-01",
            "start_time": "09:30",
            "end_date": "2024-01-01",
            "end_time": "16:00",
            "engine_alertgen_count": "2",
            "engine_alertgen_1_alg_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
            "engine_alertgen_1_param__window": "2",
            "engine_alertgen_2_alg_key": "OLD_boundary_breakout_NEW_breakout_donchian_channel",
            "engine_alertgen_2_param__period": "5",
            "decmaker_key": "alg1",
            "engine_decmaker_param__confidence_threshold_buy": "0.7",
            "engine_decmaker_param__confidence_threshold_sell": "0.4",
            "engine_decmaker_param__max_percent_higher_price_buy": "0.0",
            "engine_decmaker_param__max_percent_lower_price_sell": "0.0",
            "speed_factor": "45",
            "notes": "engine chain gui run",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    experiments = app.extensions["experiment_repository"].list_experiments()
    assert len(experiments) == 1
    assert experiments[0]["input_kind"] == "engine_chain"
    assert experiments[0]["input_snapshot"]["speed_factor"] == 45
    assert experiments[0]["input_snapshot"]["alertgens"] == [
        {
            "symbol": "AAPL",
            "alg_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
            "alg_param": {"window": 2},
            "buy": True,
            "sell": True,
        },
        {
            "symbol": "AAPL",
            "alg_key": "OLD_boundary_breakout_NEW_breakout_donchian_channel",
            "alg_param": {"period": 5},
            "buy": True,
            "sell": True,
        },
    ]
    assert experiments[0]["input_snapshot"]["decmaker"] == {
        "decmaker_key": "alg1",
        "decmaker_param": {
            "confidence_threshold_buy": 0.7,
            "confidence_threshold_sell": 0.4,
            "max_percent_higher_price_buy": 0.0,
            "max_percent_lower_price_sell": 0.0,
        },
    }


def test_create_experiment_accepts_engine_chain_guided_builder_with_four_alertgens(
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
        )
    )
    app.extensions["experiment_service"].dispatch_available_experiments = lambda: []

    response = app.test_client().post(
        "/experiments",
        data={
            "run_mode": "engine_chain",
            "symbol": "AAPL",
            "start_date": "2024-01-01",
            "start_time": "09:30",
            "end_date": "2024-01-01",
            "end_time": "16:00",
            "engine_alertgen_order": "[1,2,3,4]",
            "engine_alertgen_1_alg_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
            "engine_alertgen_1_param__window": "2",
            "engine_alertgen_2_alg_key": "OLD_boundary_breakout_NEW_breakout_donchian_channel",
            "engine_alertgen_2_param__period": "5",
            "engine_alertgen_3_alg_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
            "engine_alertgen_3_param__window": "3",
            "engine_alertgen_4_alg_key": "OLD_boundary_breakout_NEW_breakout_donchian_channel",
            "engine_alertgen_4_param__period": "8",
            "decmaker_key": "alg1",
            "engine_decmaker_param__confidence_threshold_buy": "0.6",
            "engine_decmaker_param__confidence_threshold_sell": "0.6",
            "engine_decmaker_param__max_percent_higher_price_buy": "0.0",
            "engine_decmaker_param__max_percent_lower_price_sell": "0.0",
            "speed_factor": "30",
            "notes": "four alertgens",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    experiments = app.extensions["experiment_repository"].list_experiments()
    assert len(experiments) == 1
    assert len(experiments[0]["input_snapshot"]["alertgens"]) == 4
    assert experiments[0]["input_snapshot"]["alertgens"][3]["alg_param"] == {
        "period": 8
    }


def test_new_experiment_page_prefills_selected_configuration_from_draft(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))
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
                    "alg_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
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
    assert b'value="saved_configuration" selected' in response.data
    assert f'value="{draft_id}"'.encode() in response.data
    assert b"saved-configuration-summary-card" in response.data
    assert b"saved-configuration-preview" in response.data
    assert (
        b"OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation"
        in response.data
    )


def test_create_experiment_accepts_saved_configuration_selection(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig(
            "x",
            "mongodb://example",
            "db",
            str(tmp_path / "reports"),
        )
    )
    app.extensions["experiment_service"].dispatch_available_experiments = lambda: []
    draft_id = app.extensions["configuration_builder_service"].create_draft(
        {
            "config_key": "phase2_combo",
            "version": "1",
            "name": "Phase 2 Combo",
            "root_node_id": "alg1",
            "nodes": [
                {
                    "node_id": "alg1",
                    "node_type": "algorithm",
                    "alg_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
                    "alg_param": {"window": 4},
                    "buy_enabled": True,
                    "sell_enabled": True,
                }
            ],
            "compatibility_metadata": {},
        }
    )

    response = app.test_client().post(
        "/experiments",
        data={
            "run_mode": "configuration",
            "configuration_source": "saved_configuration",
            "selected_draft_id": draft_id,
            "symbol": "AAPL",
            "start_date": "2024-01-01",
            "start_time": "09:30",
            "end_date": "2024-01-31",
            "end_time": "16:00",
            "notes": "saved configuration run",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    experiments = app.extensions["experiment_repository"].list_experiments()
    assert len(experiments) == 1
    assert experiments[0]["input_kind"] == "configuration"
    assert experiments[0]["input_snapshot"]["config_key"] == "phase2_combo"
    assert experiments[0]["input_snapshot"]["name"] == "Phase 2 Combo"
    assert experiments[0]["input_snapshot"]["nodes"][0]["alg_param"] == {"window": 4}


def test_new_experiment_page_shows_recent_saved_configuration_presets(
    monkeypatch,
):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))
    first_draft_id = app.extensions["configuration_builder_service"].create_draft(
        {
            "config_key": "recent_a",
            "version": "1",
            "name": "Recent A",
            "root_node_id": "alg1",
            "nodes": [
                {
                    "node_id": "alg1",
                    "node_type": "algorithm",
                    "alg_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
                    "alg_param": {"window": 2},
                    "buy_enabled": True,
                    "sell_enabled": True,
                }
            ],
            "compatibility_metadata": {},
        }
    )
    second_draft_id = app.extensions["configuration_builder_service"].create_draft(
        {
            "config_key": "recent_b",
            "version": "1",
            "name": "Recent B",
            "root_node_id": "alg1",
            "nodes": [
                {
                    "node_id": "alg1",
                    "node_type": "algorithm",
                    "alg_key": "OLD_boundary_breakout_NEW_breakout_donchian_channel",
                    "alg_param": {"period": 5},
                    "buy_enabled": True,
                    "sell_enabled": True,
                }
            ],
            "compatibility_metadata": {},
        }
    )

    response = app.test_client().get("/experiments/new")

    assert response.status_code == 200
    assert b"Recent configurations" in response.data
    assert first_draft_id.encode() in response.data
    assert second_draft_id.encode() in response.data
    assert b"recent-configuration-preset" in response.data


def test_new_experiment_page_prefills_selected_algorithm_from_query(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))

    response = app.test_client().get(
        "/experiments/new?alg_key=OLD_boundary_breakout_NEW_breakout_donchian_channel"
    )

    assert response.status_code == 200
    assert b"OLD_boundary_breakout_NEW_breakout_donchian_channel" in response.data
    assert (
        b"&#34;alg_key&#34;: &#34;OLD_boundary_breakout_NEW_breakout_donchian_channel&#34;"
        in response.data
    )
    assert b'name="configuration_json"' in response.data
    assert b'name="quick_builder_alg_key"' in response.data
    assert (
        b'value="OLD_boundary_breakout_NEW_breakout_donchian_channel"' in response.data
    )
    assert b"data-default-param=" in response.data
    assert b"quick_param__period" in response.data
    assert b">5<" in response.data or b'value="5"' in response.data


def test_create_experiment_accepts_quick_builder_configuration(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig(
            "x",
            "mongodb://example",
            "db",
            str(tmp_path / "reports"),
        )
    )
    app.extensions["experiment_service"].dispatch_available_experiments = lambda: []

    response = app.test_client().post(
        "/experiments",
        data={
            "run_mode": "configuration",
            "configuration_source": "quick_builder",
            "quick_builder_alg_key": "OLD_boundary_breakout_NEW_breakout_donchian_channel",
            "quick_param__period": "7",
            "quick_builder_buy_enabled": "true",
            "quick_builder_sell_enabled": "false",
            "symbol": "AAPL",
            "start_date": "2024-01-01",
            "start_time": "09:30",
            "end_date": "2024-01-01",
            "end_time": "16:00",
            "notes": "quick builder run",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    experiments = app.extensions["experiment_repository"].list_experiments()
    assert len(experiments) == 1
    assert experiments[0]["input_kind"] == "configuration"
    assert experiments[0]["input_snapshot"]["nodes"][0]["alg_key"] == (
        "OLD_boundary_breakout_NEW_breakout_donchian_channel"
    )
    assert experiments[0]["input_snapshot"]["nodes"][0]["alg_param"] == {"period": 7}
    assert experiments[0]["input_snapshot"]["nodes"][0]["buy_enabled"] is True
    assert experiments[0]["input_snapshot"]["nodes"][0]["sell_enabled"] is False


def test_quick_builder_can_save_configuration_as_draft(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))

    response = app.test_client().post(
        "/experiments/quick-builder/save-draft",
        data={
            "run_mode": "configuration",
            "configuration_source": "quick_builder",
            "quick_builder_alg_key": "OLD_boundary_breakout_NEW_breakout_donchian_channel",
            "quick_param__period": "9",
            "quick_builder_buy_enabled": "true",
            "quick_builder_sell_enabled": "true",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    drafts = app.extensions["configuration_builder_service"].list_drafts()
    assert len(drafts) == 1
    assert (
        drafts[0]["config_key"]
        == "single-OLD-boundary-breakout-NEW-breakout-donchian-channel"
    )
    assert drafts[0]["payload"]["nodes"][0]["alg_param"] == {"period": 9}


def test_quick_builder_can_open_generated_configuration_in_builder(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))

    response = app.test_client().post(
        "/experiments/quick-builder/open-in-builder",
        data={
            "run_mode": "configuration",
            "configuration_source": "quick_builder",
            "quick_builder_alg_key": "OLD_boundary_breakout_NEW_breakout_donchian_channel",
            "quick_param__period": "11",
            "quick_builder_buy_enabled": "true",
            "quick_builder_sell_enabled": "false",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers["Location"]
    assert "/configurations/cfgdraft_" in location
    assert location.endswith("/edit")
    drafts = app.extensions["configuration_builder_service"].list_drafts()
    assert len(drafts) == 1
    assert drafts[0]["payload"]["nodes"][0]["alg_param"] == {"period": 11}
    assert drafts[0]["payload"]["nodes"][0]["sell_enabled"] is False


def test_configuration_template_can_open_in_builder(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))

    response = app.test_client().post(
        "/experiments/configuration-templates/and_strategy/open-in-builder",
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers["Location"]
    assert "/configurations/cfgdraft_" in location
    assert location.endswith("/edit")
    drafts = app.extensions["configuration_builder_service"].list_drafts()
    assert len(drafts) == 1
    assert drafts[0]["payload"]["config_key"] == "template-and-strategy"
    assert drafts[0]["payload"]["root_node_id"] == "group1"
    assert len(drafts[0]["payload"]["nodes"]) == 3


def test_experiment_history_allows_deleting_one_experiment(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))
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
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))
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
                    "alg_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
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
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))
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
    assert b"data-configuration-json=" in response.data
    assert b"alg_b" in response.data
    assert b"window" in response.data
    assert b"10" in response.data
    assert b"second note" in response.data
    assert b"too old" not in response.data


def test_new_experiment_page_deduplicates_recent_run_presets_by_config(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_duplicate_newest",
            "created_at": datetime(2024, 2, 4, 12, 0, tzinfo=timezone.utc),
            "input_kind": "single_algorithm",
            "input_snapshot": {
                "algorithms": [{"alg_key": "alg_a", "alg_param": {"window": 5}}]
            },
            "symbol": "MSFT",
            "time_range": {
                "start": "2024-02-01 09:30:00",
                "end": "2024-02-03 16:00:00",
            },
            "selected_algorithms": [{"alg_key": "alg_a", "alg_param": {"window": 5}}],
            "notes": "newest duplicate",
        }
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_duplicate_older",
            "created_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "input_kind": "single_algorithm",
            "input_snapshot": {
                "algorithms": [{"alg_key": "alg_a", "alg_param": {"window": 5}}]
            },
            "symbol": "MSFT",
            "time_range": {
                "start": "2024-02-01 09:30:00",
                "end": "2024-02-03 16:00:00",
            },
            "selected_algorithms": [{"alg_key": "alg_a", "alg_param": {"window": 5}}],
            "notes": "newest duplicate",
        }
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_distinct_b",
            "created_at": datetime(2024, 2, 2, 12, 0, tzinfo=timezone.utc),
            "input_kind": "single_algorithm",
            "input_snapshot": {
                "algorithms": [{"alg_key": "alg_b", "alg_param": {"window": 7}}]
            },
            "symbol": "NVDA",
            "time_range": {
                "start": "2024-01-15 09:30:00",
                "end": "2024-01-20 16:00:00",
            },
            "selected_algorithms": [{"alg_key": "alg_b", "alg_param": {"window": 7}}],
            "notes": "distinct b",
        }
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_distinct_c",
            "created_at": datetime(2024, 2, 1, 12, 0, tzinfo=timezone.utc),
            "input_kind": "single_algorithm",
            "input_snapshot": {
                "algorithms": [{"alg_key": "alg_c", "alg_param": {"window": 9}}]
            },
            "symbol": "TSLA",
            "time_range": {
                "start": "2024-01-10 09:30:00",
                "end": "2024-01-12 16:00:00",
            },
            "selected_algorithms": [{"alg_key": "alg_c", "alg_param": {"window": 9}}],
            "notes": "distinct c",
        }
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_distinct_d",
            "created_at": datetime(2024, 1, 31, 12, 0, tzinfo=timezone.utc),
            "input_kind": "single_algorithm",
            "input_snapshot": {
                "algorithms": [{"alg_key": "alg_d", "alg_param": {"window": 11}}]
            },
            "symbol": "AMD",
            "time_range": {
                "start": "2024-01-05 09:30:00",
                "end": "2024-01-07 16:00:00",
            },
            "selected_algorithms": [{"alg_key": "alg_d", "alg_param": {"window": 11}}],
            "notes": "distinct d",
        }
    )

    response = app.test_client().get("/experiments/new")

    assert response.status_code == 200
    assert response.data.count(b"recent-experiment-preset") == 3
    assert b"newest duplicate" in response.data
    assert b"exp_duplicate_older" not in response.data
    assert b"distinct b" in response.data
    assert b"distinct c" in response.data
    assert b"distinct d" not in response.data


def test_new_experiment_page_treats_different_time_ranges_as_distinct_presets(
    monkeypatch,
):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_same_algos_time_1",
            "created_at": datetime(2024, 2, 4, 12, 0, tzinfo=timezone.utc),
            "input_kind": "single_algorithm",
            "input_snapshot": {
                "algorithms": [{"alg_key": "alg_a", "alg_param": {"window": 5}}]
            },
            "symbol": "MSFT",
            "time_range": {
                "start": "2024-02-01 09:30:00",
                "end": "2024-02-03 16:00:00",
            },
            "selected_algorithms": [{"alg_key": "alg_a", "alg_param": {"window": 5}}],
            "notes": "same algos first time range",
        }
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_same_algos_time_2",
            "created_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "input_kind": "single_algorithm",
            "input_snapshot": {
                "algorithms": [{"alg_key": "alg_a", "alg_param": {"window": 5}}]
            },
            "symbol": "MSFT",
            "time_range": {
                "start": "2024-01-01 09:30:00",
                "end": "2024-01-31 16:00:00",
            },
            "selected_algorithms": [{"alg_key": "alg_a", "alg_param": {"window": 5}}],
            "notes": "same algos second time range",
        }
    )

    response = app.test_client().get("/experiments/new")

    assert response.status_code == 200
    assert response.data.count(b"recent-experiment-preset") == 2
    assert b"same algos first time range" in response.data
    assert b"same algos second time range" in response.data


def test_new_experiment_page_deduplicates_recent_configuration_run_presets(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))
    configuration_payload = {
        "config_key": "combo_breakout",
        "name": "Combo Breakout",
        "version": "1",
        "root_node_id": "alg1",
        "nodes": [
            {
                "node_id": "alg1",
                "node_type": "algorithm",
                "alg_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
                "alg_param": {"window": 2},
            }
        ],
    }
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_config_newest",
            "created_at": datetime(2024, 2, 4, 12, 0, tzinfo=timezone.utc),
            "input_kind": "configuration",
            "input_snapshot": configuration_payload,
            "symbol": "MSFT",
            "time_range": {
                "start": "2024-02-01 09:30:00",
                "end": "2024-02-03 16:00:00",
            },
            "selected_algorithms": [],
            "notes": "newest config",
        }
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_config_older",
            "created_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "input_kind": "configuration",
            "input_snapshot": dict(configuration_payload),
            "symbol": "MSFT",
            "time_range": {
                "start": "2024-02-01 09:30:00",
                "end": "2024-02-03 16:00:00",
            },
            "selected_algorithms": [],
            "notes": "newest config",
        }
    )

    response = app.test_client().get("/experiments/new")

    assert response.status_code == 200
    assert response.data.count(b"recent-experiment-preset") == 1
    assert b"newest config" in response.data
    assert b"exp_config_older" not in response.data


def test_new_experiment_page_treats_configuration_runs_with_different_time_ranges_as_distinct(
    monkeypatch,
):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))
    configuration_payload = {
        "config_key": "combo_breakout",
        "name": "Combo Breakout",
        "version": "1",
        "root_node_id": "alg1",
        "nodes": [
            {
                "node_id": "alg1",
                "node_type": "algorithm",
                "alg_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
                "alg_param": {"window": 2},
            }
        ],
    }
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_config_time_1",
            "created_at": datetime(2024, 2, 4, 12, 0, tzinfo=timezone.utc),
            "input_kind": "configuration",
            "input_snapshot": configuration_payload,
            "symbol": "MSFT",
            "time_range": {
                "start": "2024-02-01 09:30:00",
                "end": "2024-02-03 16:00:00",
            },
            "selected_algorithms": [],
            "notes": "config first time range",
        }
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_config_time_2",
            "created_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "input_kind": "configuration",
            "input_snapshot": dict(configuration_payload),
            "symbol": "MSFT",
            "time_range": {
                "start": "2024-01-01 09:30:00",
                "end": "2024-01-31 16:00:00",
            },
            "selected_algorithms": [],
            "notes": "config second time range",
        }
    )

    response = app.test_client().get("/experiments/new")

    assert response.status_code == 200
    assert response.data.count(b"recent-experiment-preset") == 2
    assert b"config first time range" in response.data
    assert b"config second time range" in response.data


def test_create_experiment_returns_503_when_data_source_dependencies_are_missing(
    monkeypatch,
):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))

    monkeypatch.setattr(
        app.extensions["experiment_service"],
        "create_experiment",
        lambda **_kwargs: (_ for _ in ()).throw(
            DataSourceUnavailableError(
                "Market data service is unavailable. "
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
            "configuration_json": _single_algorithm_configuration_payload(),
            "notes": "",
        },
    )

    assert response.status_code == 503
    assert b"Market data service is unavailable." in response.data
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
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))
    client = app.test_client()
    client.set_cookie(
        "trading_algos_dashboard_experiment_form",
        '{"symbol": "MSFT", "start_date": "2024-02-01", "start_time": "09:30", "end_date": "2024-02-10", "end_time": "16:00", '
        '"configuration_json": "{\\"config_key\\":\\"saved\\",\\"version\\":\\"1\\",\\"name\\":\\"Saved\\",\\"root_node_id\\":\\"alg1\\",\\"nodes\\":[{\\"node_id\\":\\"alg1\\",\\"node_type\\":\\"algorithm\\",\\"alg_key\\":\\"x\\",\\"alg_param\\":{},\\"buy_enabled\\":true,\\"sell_enabled\\":true}],\\"runtime_overrides\\":{},\\"compatibility_metadata\\":{}}", "notes": "saved note"}',
    )
    response = client.get("/experiments/new")

    assert response.status_code == 200
    assert b'value="MSFT"' in response.data
    assert b'value="2024-02-01"' in response.data
    assert b'value="09:30"' in response.data
    assert b'value="2024-02-10"' in response.data
    assert b'value="16:00"' in response.data
    assert b"saved note" in response.data


def test_create_experiment_returns_400_for_malformed_configuration_json(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))
    client = app.test_client()
    response = client.post(
        "/experiments",
        data={
            "symbol": "AAPL",
            "start_date": "2024-01-01",
            "start_time": "09:30",
            "end_date": "2024-01-31",
            "end_time": "16:00",
            "configuration_json": '{"config_key":',
            "notes": "bad payload",
        },
    )

    assert response.status_code == 400
    assert b"Configuration JSON must be valid JSON." in response.data
    assert b'value="AAPL"' in response.data
    assert b"bad payload" in response.data


def test_create_experiment_accepts_valid_configuration_payload(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig(
            "x",
            "mongodb://example",
            "db",
            str(tmp_path / "reports"),
        )
    )

    monkeypatch.setattr(
        app.extensions["data_source_service"],
        "fetch_candles",
        lambda **_kwargs: MarketDataFetchResult(
            candles=[
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
            cache_hit=False,
            source_kind="dataserver",
            symbol="AAPL",
            start=datetime.fromisoformat("2024-01-01T09:30"),
            end=datetime.fromisoformat("2024-01-31T16:00"),
            candle_count=3,
        ),
    )
    monkeypatch.setattr(
        app.extensions["data_source_service"],
        "get_market_data_server_details",
        lambda: {
            "kind": "xmlrpc_dataserver",
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
            "configuration_json": _single_algorithm_configuration_payload(),
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
    assert stored_experiments[0]["queue_enqueued_at"] is not None
    assert stored_experiments[0]["selected_algorithms"] == [
        {
            "alg_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
            "alg_param": {"window": 2},
        }
    ]
    assert stored_experiments[0]["dataset_source"] == {
        "kind": "xmlrpc_dataserver",
        "ip": "10.0.0.5",
        "port": 7003,
        "endpoint": "10.0.0.5:7003",
        "cache": {
            "source_kind": "dataserver",
            "cache_hit": False,
        },
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


def test_create_experiment_redirects_to_queued_detail_page_when_dispatch_is_idle(
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
        )
    )
    app.extensions["experiment_service"].dispatch_available_experiments = lambda: []

    response = app.test_client().post(
        "/experiments",
        data={
            "symbol": "AAPL",
            "start_date": "2024-01-01",
            "start_time": "09:30",
            "end_date": "2024-01-31",
            "end_time": "16:00",
            "configuration_json": _single_algorithm_configuration_payload(),
            "notes": "good payload",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers["Location"]
    assert "/experiments/exp_" in location

    stored_experiments = app.extensions["experiment_repository"].list_experiments()
    assert len(stored_experiments) == 1
    assert stored_experiments[0]["status"] == "queued"
    assert stored_experiments[0]["queue_enqueued_at"] is not None
    assert stored_experiments[0]["started_at"] is None
    assert stored_experiments[0]["finished_at"] is None
    assert stored_experiments[0]["duration_seconds"] is None


def test_experiment_detail_shows_runtime_metadata(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))
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
                "kind": "xmlrpc_dataserver",
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
                    "label": "Run OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
                    "started_at": datetime(2024, 2, 3, 12, 1, tzinfo=timezone.utc),
                    "finished_at": datetime(2024, 2, 3, 12, 5, tzinfo=timezone.utc),
                    "duration_seconds": 240.0,
                    "metadata": {
                        "alg_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation"
                    },
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
    assert (
        b"Run OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation"
        in response.data
    )
    assert b"60.00s" in response.data
    assert b"240.00s" in response.data
    assert b"Git revision:" in response.data
    assert b"127.0.0.1:7003" in response.data
    assert b"accfd73bac055e1555c2d6f8f031cea7095ff35d" in response.data


def test_experiment_detail_renders_standardized_report_sections(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))
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


def test_experiment_detail_links_to_evaluations(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_linked",
            "created_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "status": "completed",
            "symbol": "AAPL",
            "time_range": {
                "start": "2024-02-01 09:30:00",
                "end": "2024-02-03 16:00:00",
            },
            "selected_algorithms": [],
            "candle_count": 10,
        }
    )

    response = app.test_client().get("/experiments/exp_linked")

    assert response.status_code == 200
    assert b"Find comparable runs" in response.data
    assert b"/evaluations/cohort?symbol=AAPL" in response.data


def test_running_experiment_detail_shows_runtime_panel(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))
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
                {
                    "alg_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
                    "alg_param": {"window": 2},
                }
            ],
            "input_kind": "single_algorithm",
            "input_snapshot": {
                "algorithms": [
                    {
                        "alg_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
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
    assert (
        b"OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation"
        in response.data
    )
    assert b"Step durations" in response.data
    assert b"Read candles" in response.data
    assert b"Stop experiment" in response.data


def test_queued_experiment_detail_shows_queue_panel(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_queued",
            "created_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "queue_enqueued_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "started_at": None,
            "finished_at": None,
            "duration_seconds": None,
            "repo_revision": "abc123",
            "symbol": "AAPL",
            "status": "queued",
            "dataset_source": None,
            "time_range": {
                "start": "2024-02-01 09:30:00",
                "end": "2024-02-03 16:00:00",
            },
            "selected_algorithms": [
                {
                    "alg_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
                    "alg_param": {"window": 2},
                }
            ],
            "input_kind": "single_algorithm",
            "input_snapshot": {
                "algorithms": [
                    {
                        "alg_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
                        "alg_param": {"window": 2},
                    }
                ]
            },
            "notes": "queued payload",
            "candle_count": None,
        }
    )

    response = app.test_client().get("/experiments/exp_queued")

    assert response.status_code == 200
    assert b"Queued for execution" in response.data
    assert b"Remove from queue" in response.data
    assert b"Queue position" in response.data


def test_experiment_history_shows_queue_sections(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_running",
            "created_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "started_at": datetime(2024, 2, 3, 12, 1, tzinfo=timezone.utc),
            "status": "running",
            "symbol": "AAPL",
        }
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_queued",
            "created_at": datetime(2024, 2, 3, 12, 2, tzinfo=timezone.utc),
            "queue_enqueued_at": datetime(2024, 2, 3, 12, 2, tzinfo=timezone.utc),
            "status": "queued",
            "symbol": "MSFT",
        }
    )
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_done",
            "created_at": datetime(2024, 2, 3, 11, 0, tzinfo=timezone.utc),
            "started_at": datetime(2024, 2, 3, 11, 0, tzinfo=timezone.utc),
            "finished_at": datetime(2024, 2, 3, 11, 5, tzinfo=timezone.utc),
            "status": "completed",
            "symbol": "NVDA",
        }
    )

    response = app.test_client().get("/experiments")

    assert response.status_code == 200
    assert b"Currently running" in response.data
    assert b"Execution queue" in response.data
    assert b"Past experiments" in response.data
    assert b"exp_queued" in response.data


def test_cancel_queued_experiment_removes_it_from_queue(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_queued",
            "created_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "queue_enqueued_at": datetime(2024, 2, 3, 12, 0, tzinfo=timezone.utc),
            "status": "queued",
            "symbol": "AAPL",
            "input_kind": "single_algorithm",
            "input_snapshot": {"algorithms": []},
            "selected_algorithms": [],
        }
    )

    response = app.test_client().post(
        "/experiments/exp_queued/cancel",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"removed from execution queue" in response.data
    stored = app.extensions["experiment_repository"].get_experiment("exp_queued")
    assert stored is not None
    assert stored["status"] == "cancelled"


def test_cancel_experiment_requests_graceful_stop(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))
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
    assert b"removed from execution queue" in response.data
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
            {
                "alg_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
                "alg_param": {"window": 2},
            }
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
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))
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
            "configuration_json": _single_algorithm_configuration_payload(),
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
            "configuration_json": _single_algorithm_configuration_payload(),
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
    service = MarketDataSourceService()

    class _Proxy:
        def get_data(self, _symbol, ts):
            ts_obj = datetime.fromisoformat(ts)
            if ts_obj.minute == 31:
                raise Fault(1, "missing candle")
            return {
                "_id": "mongo-id",
                "ts": ts_obj.isoformat(sep=" "),
                "Open": 10,
                "High": 11,
                "Low": 9,
                "Close": 10.5,
            }

    service._data_proxy = lambda: _Proxy()  # type: ignore[method-assign]

    fetch_result = service.fetch_candles(
        symbol="AAPL",
        start=datetime.fromisoformat("2024-01-01T09:30"),
        end=datetime.fromisoformat("2024-01-01T09:32"),
    )
    candles = fetch_result.candles

    assert len(candles) == 2
    assert [item["ts"] for item in candles] == [
        "2024-01-01 09:30:00",
        "2024-01-01 09:32:00",
    ]
    assert all("_id" not in item for item in candles)


def test_fetch_candles_raises_market_data_error_when_all_timestamps_are_missing():
    service = MarketDataSourceService()

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
    service = MarketDataSourceService()

    monkeypatch.setattr(
        service,
        "_data_server_endpoint_label",
        lambda: "127.0.0.1:7003",
    )

    assert service._format_unavailable_message() == (
        "Market data service is unavailable. "
        "Please make sure the data server is running. "
        "Tried to connect to 127.0.0.1:7003."
    )


def test_recent_preset_does_not_double_encode_configuration_json(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))
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
                {
                    "alg_key": "OLD_boundary_breakout_NEW_breakout_donchian_channel",
                    "alg_param": {"period": 5},
                }
            ],
            "notes": "boundary payload",
        }
    )

    client = app.test_client()
    response = client.get("/experiments/new")

    assert response.status_code == 200
    assert b'data-configuration-json="{' not in response.data
    assert (
        b"data-configuration-json='{&#34;config_key&#34;: &#34;single-OLD-boundary-breakout-NEW-breakout-donchian-channel&#34;"
        in response.data
    )
