from datetime import datetime
from io import BytesIO
from inspect import getsourcefile
from pathlib import Path

from trading_algos.alertgen import get_alert_algorithm_spec_by_key
from trading_algos_dashboard.app import create_app
from trading_algos_dashboard.config import DashboardConfig


class _DeleteResult:
    def __init__(self, deleted_count):
        self.deleted_count = deleted_count


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

    def sort(self, *_args, **_kwargs):
        return self

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
        return _DeleteResult(original_count - len(self.docs))

    def count_documents(self, query):
        return sum(
            1
            for doc in self.docs
            if all(doc.get(key) == value for key, value in query.items())
        )


class _Cursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, *_args, **_kwargs):
        return self.docs

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
        )
    )


def _assign_implementation(
    app,
    *,
    entry_id: str,
    implementation_id: str,
    notes: str = "implementation declared",
    review_state: str = "not_reviewed",
    implementation_source: str = "runtime_declared",
):
    spec = get_alert_algorithm_spec_by_key(implementation_id)
    source_file = getsourcefile(spec.builder)
    source_file_path = ""
    if source_file is not None:
        source_path = Path(source_file).resolve()
        project_root = Path(__file__).resolve().parents[2]
        try:
            source_file_path = str(source_path.relative_to(project_root))
        except ValueError:
            source_file_path = str(source_path)
    app.extensions["algorithm_catalog_repository"].update_entry_admin_fields(
        entry_id,
        {
            "implementation_id": implementation_id,
            "implementation_catalog_ref": "algorithm:6",
            "implementation_source": implementation_source,
            "implementation_confidence": 1.0,
            "implementation_mapping_notes": notes,
            "implementation_mapping_reason": "implementation-declared catalog_ref",
            "implementation_builder_name": getattr(spec.builder, "__name__", ""),
            "implementation_builder_module": str(
                getattr(spec.builder, "__module__", "")
            ),
            "implementation_source_file": source_file_path,
            "review_state": review_state,
        },
    )


def test_administration_page_renders_with_database_counts(monkeypatch):
    app = _build_app(monkeypatch)
    app.extensions["experiment_repository"].create_experiment(
        {"experiment_id": "exp_1", "created_at": "2026-04-21T10:00:00Z"}
    )
    app.extensions["result_repository"].insert_result(
        {
            "experiment_id": "exp_1",
            "alg_key": "alg_1",
            "created_at": "2026-04-21T10:00:00Z",
        }
    )

    response = app.test_client().get("/administration")

    assert response.status_code == 200
    assert b"Administration" in response.data
    assert b"Delete stored dashboard data" in response.data
    assert b"Experiments" in response.data
    assert b"Results" in response.data
    assert b"Algorithm catalog" in response.data
    assert b"Experiment scheduler settings" in response.data
    assert b">1<" in response.data


def test_experiment_runtime_settings_page_renders(monkeypatch):
    app = _build_app(monkeypatch)

    response = app.test_client().get("/administration/experiment-runtime-settings")

    assert response.status_code == 200
    assert b"Runtime settings" in response.data
    assert b'name="max_concurrent_experiments"' in response.data
    assert b"Save scheduler settings" in response.data
    assert b"Market data server" in response.data
    assert b'name="ip"' in response.data
    assert b'name="port"' in response.data
    assert b"Market data cache" in response.data
    assert b"Open cache management" in response.data


def test_experiment_runtime_settings_page_updates_global_limit(monkeypatch):
    app = _build_app(monkeypatch)

    response = app.test_client().post(
        "/administration/experiment-runtime-settings",
        data={"max_concurrent_experiments": "4"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/administration/experiment-runtime-settings"
    )
    assert (
        app.extensions["experiment_runtime_settings_service"].get_effective_settings()[
            "max_concurrent_experiments"
        ]
        == 4
    )


def test_experiment_runtime_settings_page_updates_data_source_settings(monkeypatch):
    app = _build_app(monkeypatch)

    response = app.test_client().post(
        "/administration/data-source-settings",
        data={"ip": "192.168.1.10", "port": "7010"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Data server settings saved." in response.data
    settings = app.extensions["data_source_settings_service"].get_effective_settings()
    assert settings["ip"] == "192.168.1.10"
    assert settings["port"] == 7010


def test_experiment_runtime_settings_page_checks_data_source_connection(monkeypatch):
    app = _build_app(monkeypatch)
    monkeypatch.setattr(
        app.extensions["data_source_service"],
        "check_connection",
        lambda: {"status": "ok", "endpoint": "127.0.0.1:7003", "server_up": True},
    )

    response = app.test_client().post(
        "/administration/data-source-settings/check",
        data={"ip": "127.0.0.1", "port": "7003"},
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ok",
        "endpoint": "127.0.0.1:7003",
        "server_up": True,
    }


def test_experiment_runtime_settings_page_returns_data_source_error_json(monkeypatch):
    app = _build_app(monkeypatch)

    def _raise_error():
        from trading_algos_dashboard.services.data_source_service import (
            DataSourceUnavailableError,
        )

        raise DataSourceUnavailableError("not responding")

    monkeypatch.setattr(
        app.extensions["data_source_service"], "check_connection", _raise_error
    )

    response = app.test_client().post(
        "/administration/data-source-settings/check",
        data={"ip": "127.0.0.1", "port": "7003"},
    )

    assert response.status_code == 503
    assert response.get_json()["status"] == "error"
    assert response.get_json()["message"] == "not responding"


def test_experiment_runtime_settings_page_updates_cache_settings(monkeypatch):
    app = _build_app(monkeypatch)

    response = app.test_client().post(
        "/administration/market-data-cache-settings",
        data={
            "memory_enabled": "on",
            "memory_max_entries": "12",
            "shared_enabled": "on",
            "shared_max_entries": "34",
            "shared_ttl_hours": "48",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"market data cache settings updated" in response.data
    settings = app.extensions[
        "market_data_cache_settings_service"
    ].get_effective_settings()
    assert settings["memory_max_entries"] == 12
    assert settings["shared_max_entries"] == 34
    assert settings["shared_ttl_hours"] == 48
    assert b"Cache management" in response.data


def test_experiment_runtime_settings_page_clears_memory_cache(monkeypatch):
    app = _build_app(monkeypatch)
    cache = app.extensions["market_data_cache"]
    start = Path
    del start
    cache.memory_cache.put(
        symbol="AAPL",
        start=__import__("datetime").datetime.fromisoformat("2024-01-01T09:30"),
        end=__import__("datetime").datetime.fromisoformat("2024-01-01T09:31"),
        candles=[{"ts": "x"}],
    )

    response = app.test_client().post(
        "/administration/market-data-cache/clear-memory",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"memory cache cleared" in response.data
    assert cache.stats()["memory_entry_count"] == 0
    assert b"Cache management" in response.data


def test_experiment_runtime_settings_page_clears_shared_cache(monkeypatch):
    app = _build_app(monkeypatch)
    cache = app.extensions["market_data_cache"]
    cache.shared_cache.put(
        symbol="AAPL",
        start=__import__("datetime").datetime.fromisoformat("2024-01-01T09:30"),
        end=__import__("datetime").datetime.fromisoformat("2024-01-01T09:31"),
        candles=[{"ts": "x"}],
    )

    response = app.test_client().post(
        "/administration/market-data-cache/clear-shared",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"shared cache cleared" in response.data
    assert cache.stats()["shared_entry_count"] == 0
    assert b"Cache management" in response.data


def test_cache_management_page_renders_entries_and_metadata(monkeypatch):
    app = _build_app(monkeypatch)
    cache = app.extensions["market_data_cache"]
    start = datetime.fromisoformat("2024-01-01T09:30")
    end = datetime.fromisoformat("2024-01-01T09:31")
    candles = [{"ts": "2024-01-01 09:30:00", "Close": 10.5}]
    cache.memory_cache.put(symbol="AAPL", start=start, end=end, candles=candles)
    cache.shared_cache.put(symbol="AAPL", start=start, end=end, candles=candles)

    response = app.test_client().get("/administration/cache")

    assert response.status_code == 200
    assert b"Cache management" in response.data
    assert b"AAPL" in response.data
    assert b"Memory" in response.data
    assert b"DB" in response.data
    assert b"DB TTL:" in response.data
    assert b"View chart" in response.data
    assert b"Delete" in response.data


def test_cache_management_page_fills_cache_entry(monkeypatch):
    app = _build_app(monkeypatch)

    def _fill_entry(*, symbol, start, end):
        return (
            app.extensions[
                "cache_management_service"
            ].fill_entry.__self__.list_entries()
            or []
        )

    monkeypatch.setattr(
        app.extensions["cache_management_service"],
        "fill_entry",
        lambda *, symbol, start, end: type(
            "Entry",
            (),
            {
                "symbol": symbol.upper(),
                "start": start,
                "end": end,
                "candle_count": 2,
            },
        )(),
    )

    response = app.test_client().post(
        "/administration/market-data-cache/fill",
        data={
            "symbol": "aapl",
            "start": "2024-01-01T09:30",
            "end": "2024-01-01T09:31",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"cache entry filled; symbol=AAPL candle_count=2" in response.data


def test_cache_management_page_deletes_cache_entry(monkeypatch):
    app = _build_app(monkeypatch)
    cache = app.extensions["market_data_cache"]
    start = datetime.fromisoformat("2024-01-01T09:30")
    end = datetime.fromisoformat("2024-01-01T09:31")
    candles = [{"ts": "2024-01-01 09:30:00", "Close": 10.5}]
    cache.memory_cache.put(symbol="AAPL", start=start, end=end, candles=candles)
    cache.shared_cache.put(symbol="AAPL", start=start, end=end, candles=candles)

    response = app.test_client().post(
        "/administration/market-data-cache/delete",
        data={
            "symbol": "AAPL",
            "start": "2024-01-01T09:30",
            "end": "2024-01-01T09:31",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"cache entry deleted; symbol=AAPL memory=True shared=True" in response.data
    assert cache.stats()["memory_entry_count"] == 0
    assert cache.stats()["shared_entry_count"] == 0


def test_cache_management_chart_route_returns_chart_payload(monkeypatch):
    app = _build_app(monkeypatch)
    cache = app.extensions["market_data_cache"]
    start = datetime.fromisoformat("2024-01-01T09:30")
    end = datetime.fromisoformat("2024-01-01T09:31")
    candles = [{"ts": "2024-01-01 09:30:00", "Close": 10.5}]
    cache.memory_cache.put(symbol="AAPL", start=start, end=end, candles=candles)
    cache.shared_cache.put(symbol="AAPL", start=start, end=end, candles=candles)

    response = app.test_client().get(
        "/administration/market-data-cache/chart?symbol=AAPL&start=2024-01-01T09:30&end=2024-01-01T09:31"
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["symbol"] == "AAPL"
    assert payload["chart"]["data"][0]["x"] == ["2024-01-01 09:30:00"]


def test_import_algorithm_catalog_route_runs_import(monkeypatch):
    app = _build_app(monkeypatch)
    response = app.test_client().post(
        "/administration/algorithm-catalog/import",
        data={
            "catalog_file": (
                BytesIO(
                    b"<table><tr><td>1</td><td>Trend</td><td>Example Algo</td><td>Yes</td><td>Swing</td><td>4</td><td>Idea</td><td>Inputs</td><td>Signals</td><td>Details</td><td>Ref</td></tr></table>"
                ),
                "catalog_upload.md",
            )
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"administration: algorithm catalog imported;" in response.data
    assert b"catalog_upload.md" in response.data


def test_import_algorithm_catalog_route_requires_file(monkeypatch):
    app = _build_app(monkeypatch)
    response = app.test_client().post(
        "/administration/algorithm-catalog/import",
        data={},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert (
        b"administration: algorithm catalog import not executed; reason=missing_file"
        in response.data
    )


def test_import_algorithm_catalog_route_rejects_unsupported_extension(monkeypatch):
    app = _build_app(monkeypatch)
    response = app.test_client().post(
        "/administration/algorithm-catalog/import",
        data={"catalog_file": (BytesIO(b"x"), "catalog.csv")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert (
        b"administration: algorithm catalog import not executed; reason=unsupported_file_type"
        in response.data
    )


def test_algorithm_catalog_admin_page_renders(monkeypatch):
    app = _build_app(monkeypatch)
    response = app.test_client().get("/administration/algorithm-catalog")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/algorithms")


def test_algorithm_catalog_workspace_page_renders(monkeypatch):
    app = _build_app(monkeypatch)
    response = app.test_client().get("/algorithms")
    assert response.status_code == 200
    assert b"Algorithm Catalog" in response.data
    assert b"Import history" in response.data
    assert b"Sync implementation linkages" in response.data
    assert (
        b"Search names, IDs, links, notes, references, and implementation metadata"
        in response.data
    )
    assert b"Status" in response.data
    assert b"Review state" in response.data
    assert b"Catalog type" in response.data
    assert b"Show only broken links" in response.data
    assert b"New algorithm" in response.data
    assert b"Create algorithm entry" in response.data


def test_algorithm_catalog_workspace_shows_run_action_for_implemented_entries(
    monkeypatch,
):
    app = _build_app(monkeypatch)
    app.extensions["algorithm_catalog_repository"].upsert_entry(
        source_version="seed",
        catalog_type="algorithm",
        catalog_number=1,
        document={
            "id": "entry-1",
            "catalog_type": "algorithm",
            "catalog_number": 1,
            "name": "Seed Entry",
            "slug": "seed-entry",
            "category": "Trend Following",
            "subcategory": "",
            "advanced_label": "No",
            "best_use_horizon": "Swing",
            "home_suitability_score": 3,
            "core_idea": "Seed idea",
            "typical_inputs": "Price",
            "signal_style": "Trend",
            "extended_implementation_details": "Details",
            "initial_reference": "Ref",
            "source_version": "seed",
            "is_active": True,
            "created_at": "2026-04-21T10:00:00Z",
            "updated_at": "2026-04-21T10:00:00Z",
        },
    )
    _assign_implementation(
        app,
        entry_id="entry-1",
        implementation_id="OLD_boundary_breakout_NEW_breakout_donchian_channel",
        review_state="confirmed",
    )

    response = app.test_client().get("/algorithms")

    assert response.status_code == 200
    assert b">Run<" in response.data
    assert (
        b"/experiments/new?alg_key=OLD_boundary_breakout_NEW_breakout_donchian_channel"
        in response.data
    )
    assert b">Runnable<" in response.data
    assert b">Confirmed<" in response.data


def test_algorithm_catalog_search_results_show_run_for_runnable_unreviewed_entries(
    monkeypatch,
):
    app = _build_app(monkeypatch)
    app.extensions["algorithm_catalog_repository"].upsert_entry(
        source_version="seed",
        catalog_type="algorithm",
        catalog_number=1,
        document={
            "id": "entry-1",
            "catalog_type": "algorithm",
            "catalog_number": 1,
            "name": "OLD Boundary Breakout NEW Breakout Donchian Channel Searchable",
            "slug": "boundary-breakout-searchable",
            "category": "Trend Following",
            "subcategory": "",
            "advanced_label": "No",
            "best_use_horizon": "Swing",
            "home_suitability_score": 3,
            "core_idea": "Seed idea",
            "typical_inputs": "Price",
            "signal_style": "Trend",
            "extended_implementation_details": "Details",
            "initial_reference": "Ref",
            "source_version": "seed",
            "is_active": True,
            "created_at": "2026-04-21T10:00:00Z",
            "updated_at": "2026-04-21T10:00:00Z",
        },
    )
    _assign_implementation(
        app,
        entry_id="entry-1",
        implementation_id="OLD_boundary_breakout_NEW_breakout_donchian_channel",
        review_state="not_reviewed",
    )

    response = app.test_client().get("/algorithms?q=searchable")

    assert response.status_code == 200
    assert (
        b"OLD Boundary Breakout NEW Breakout Donchian Channel Searchable"
        in response.data
    )
    assert b">Runnable<" in response.data
    assert b">Not reviewed<" in response.data
    assert b">Run<" in response.data
    assert (
        b"/experiments/new?alg_key=OLD_boundary_breakout_NEW_breakout_donchian_channel"
        in response.data
    )


def test_algorithm_catalog_hides_run_for_rejected_linked_entry(monkeypatch):
    app = _build_app(monkeypatch)
    app.extensions["algorithm_catalog_repository"].upsert_entry(
        source_version="seed",
        catalog_type="algorithm",
        catalog_number=1,
        document={
            "id": "entry-1",
            "catalog_type": "algorithm",
            "catalog_number": 1,
            "name": "Rejected Breakout",
            "slug": "rejected-breakout",
            "category": "Trend Following",
            "subcategory": "",
            "advanced_label": "No",
            "best_use_horizon": "Swing",
            "home_suitability_score": 3,
            "core_idea": "Seed idea",
            "typical_inputs": "Price",
            "signal_style": "Trend",
            "extended_implementation_details": "Details",
            "initial_reference": "Ref",
            "source_version": "seed",
            "is_active": True,
            "created_at": "2026-04-21T10:00:00Z",
            "updated_at": "2026-04-21T10:00:00Z",
        },
    )
    _assign_implementation(
        app,
        entry_id="entry-1",
        implementation_id="OLD_boundary_breakout_NEW_breakout_donchian_channel",
        review_state="rejected",
    )

    response = app.test_client().get("/algorithms?q=rejected")

    assert response.status_code == 200
    assert b"Rejected Breakout" in response.data
    assert b">Not runnable<" in response.data
    assert b">Rejected<" in response.data
    assert (
        b"/experiments/new?alg_key=OLD_boundary_breakout_NEW_breakout_donchian_channel"
        not in response.data
    )


def test_algorithm_catalog_hides_run_for_deferred_linked_entry(monkeypatch):
    app = _build_app(monkeypatch)
    app.extensions["algorithm_catalog_repository"].upsert_entry(
        source_version="seed",
        catalog_type="algorithm",
        catalog_number=1,
        document={
            "id": "entry-1",
            "catalog_type": "algorithm",
            "catalog_number": 1,
            "name": "Deferred Breakout",
            "slug": "deferred-breakout",
            "category": "Trend Following",
            "subcategory": "",
            "advanced_label": "No",
            "best_use_horizon": "Swing",
            "home_suitability_score": 3,
            "core_idea": "Seed idea",
            "typical_inputs": "Price",
            "signal_style": "Trend",
            "extended_implementation_details": "Details",
            "initial_reference": "Ref",
            "source_version": "seed",
            "is_active": True,
            "created_at": "2026-04-21T10:00:00Z",
            "updated_at": "2026-04-21T10:00:00Z",
        },
    )
    _assign_implementation(
        app,
        entry_id="entry-1",
        implementation_id="OLD_boundary_breakout_NEW_breakout_donchian_channel",
        review_state="deferred",
    )

    response = app.test_client().get("/algorithms?q=deferred")

    assert response.status_code == 200
    assert b"Deferred Breakout" in response.data
    assert b">Not runnable<" in response.data
    assert b">Deferred<" in response.data
    assert (
        b"/experiments/new?alg_key=OLD_boundary_breakout_NEW_breakout_donchian_channel"
        not in response.data
    )


def test_algorithm_detail_hides_run_for_rejected_linked_entry(monkeypatch):
    app = _build_app(monkeypatch)
    app.extensions["algorithm_catalog_repository"].upsert_entry(
        source_version="seed",
        catalog_type="algorithm",
        catalog_number=1,
        document={
            "id": "entry-1",
            "catalog_type": "algorithm",
            "catalog_number": 1,
            "name": "Rejected Detail Entry",
            "slug": "rejected-detail-entry",
            "category": "Trend Following",
            "subcategory": "",
            "advanced_label": "No",
            "best_use_horizon": "Swing",
            "home_suitability_score": 3,
            "core_idea": "Seed idea",
            "typical_inputs": "Price",
            "signal_style": "Trend",
            "extended_implementation_details": "Details",
            "initial_reference": "Ref",
            "implementation_decision": "",
            "implementation_notes": "",
            "admin_annotations": "",
            "source_version": "seed",
            "is_active": True,
            "created_at": "2026-04-21T10:00:00Z",
            "updated_at": "2026-04-21T10:00:00Z",
        },
    )
    _assign_implementation(
        app,
        entry_id="entry-1",
        implementation_id="OLD_boundary_breakout_NEW_breakout_donchian_channel",
        review_state="rejected",
    )

    response = app.test_client().get("/algorithms/rejected-detail-entry")

    assert response.status_code == 200
    assert b">Not runnable<" in response.data
    assert b">Rejected<" in response.data
    assert b"Run this algorithm" not in response.data


def test_algorithm_catalog_workspace_creates_manual_algorithm(monkeypatch):
    app = _build_app(monkeypatch)

    response = app.test_client().post(
        "/algorithms/new",
        data={
            "name": "Manual Algo",
            "catalog_type": "algorithm",
            "alg_impl_id": "",
            "category": "Custom",
            "subcategory": "",
            "advanced_label": "No",
            "best_use_horizon": "Swing",
            "home_suitability_score": "2",
            "core_idea": "Manual idea",
            "typical_inputs": "Price",
            "signal_style": "Trend",
            "extended_implementation_details": "Manual details",
            "initial_reference": "Manual ref",
            "implementation_decision": "",
            "implementation_notes": "",
            "admin_annotations": "",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"algorithm_catalog: algorithm created;" in response.data
    assert b"Manual Algo" in response.data
    assert b">Not runnable<" in response.data
    assert b">Not reviewed<" in response.data


def test_algorithm_catalog_workspace_creates_manual_algorithm_with_implementation(
    monkeypatch,
):
    app = _build_app(monkeypatch)

    response = app.test_client().post(
        "/algorithms/new",
        data={
            "name": "Manual OLD Boundary Breakout NEW Breakout Donchian Channel",
            "catalog_type": "algorithm",
            "alg_impl_id": "OLD_boundary_breakout_NEW_breakout_donchian_channel",
            "category": "Custom",
            "subcategory": "",
            "advanced_label": "No",
            "best_use_horizon": "Swing",
            "home_suitability_score": "3",
            "core_idea": "Manual mapped idea",
            "typical_inputs": "Price",
            "signal_style": "Trend",
            "extended_implementation_details": "Manual mapped details",
            "initial_reference": "Manual ref",
            "implementation_decision": "Use implementation",
            "implementation_notes": "",
            "admin_annotations": "",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"algorithm_catalog: algorithm created;" in response.data
    assert (
        b"Manual OLD Boundary Breakout NEW Breakout Donchian Channel" in response.data
    )
    assert b"OLD_boundary_breakout_NEW_breakout_donchian_channel" in response.data
    assert b"Linked implementation" in response.data
    assert b"Builder" in response.data


def test_algorithm_catalog_admin_page_shows_global_search_results(monkeypatch):
    app = _build_app(monkeypatch)
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
            "is_active": True,
            "created_at": "now",
            "updated_at": "now",
        },
    )
    _assign_implementation(
        app,
        entry_id="entry-1",
        implementation_id="OLD_boundary_breakout_NEW_breakout_donchian_channel",
    )

    response = app.test_client().get("/algorithms?q=implementation%20declared")

    assert response.status_code == 200
    assert b"Search results for" in response.data
    assert b"implementation declared" in response.data
    assert b"Breakout (Donchian Channel)" in response.data


def test_algorithm_catalog_admin_page_without_filters_shows_all_active_entries(
    monkeypatch,
):
    app = _build_app(monkeypatch)
    app.extensions["algorithm_catalog_repository"].upsert_entry(
        source_version="seed",
        catalog_type="algorithm",
        catalog_number=1,
        document={
            "id": "entry-1",
            "catalog_type": "algorithm",
            "catalog_number": 1,
            "name": "Alpha Breakout",
            "slug": "alpha-breakout",
            "category": "Trend Following",
            "subcategory": "",
            "advanced_label": "No",
            "best_use_horizon": "Swing",
            "home_suitability_score": 3,
            "core_idea": "Alpha idea",
            "typical_inputs": "Price",
            "signal_style": "Trend",
            "extended_implementation_details": "Alpha details",
            "initial_reference": "Ref-A",
            "source_version": "seed",
            "is_active": True,
            "created_at": "2026-04-21T10:00:00Z",
            "updated_at": "2026-04-21T10:00:00Z",
        },
    )
    app.extensions["algorithm_catalog_repository"].upsert_entry(
        source_version="seed",
        catalog_type="setup",
        catalog_number=2,
        document={
            "id": "entry-2",
            "catalog_type": "setup",
            "catalog_number": 2,
            "name": "Beta Mean Reversion",
            "slug": "beta-mean-reversion",
            "category": "Mean Reversion",
            "subcategory": "",
            "advanced_label": "Yes",
            "best_use_horizon": "Intraday",
            "home_suitability_score": 2,
            "core_idea": "Beta idea",
            "typical_inputs": "OHLCV",
            "signal_style": "Reversion",
            "extended_implementation_details": "Beta details",
            "initial_reference": "Ref-B",
            "source_version": "seed",
            "is_active": True,
            "created_at": "2026-04-21T10:00:00Z",
            "updated_at": "2026-04-21T10:00:00Z",
        },
    )

    response = app.test_client().get("/algorithms")

    assert response.status_code == 200
    assert b"All algorithms" in response.data
    assert b"2 items" in response.data
    assert b"Alpha Breakout" in response.data
    assert b"Beta Mean Reversion" in response.data


def test_algorithm_catalog_admin_page_shows_queue_pagination_controls(monkeypatch):
    app = _build_app(monkeypatch)
    repository = app.extensions["algorithm_catalog_repository"]

    for index in range(1, 52):
        repository.upsert_entry(
            source_version="seed",
            catalog_type="algorithm",
            catalog_number=index,
            document={
                "id": f"entry-{index}",
                "catalog_type": "algorithm",
                "catalog_number": index,
                "name": f"Algorithm {index}",
                "slug": f"algorithm-{index}",
                "category": "Trend Following",
                "subcategory": "",
                "advanced_label": "No",
                "best_use_horizon": "Swing",
                "home_suitability_score": 3,
                "core_idea": f"Idea {index}",
                "typical_inputs": "Price",
                "signal_style": "Trend",
                "extended_implementation_details": "Details",
                "initial_reference": f"Ref-{index}",
                "source_version": "seed",
                "is_active": True,
                "created_at": "2026-04-21T10:00:00Z",
                "updated_at": "2026-04-21T10:00:00Z",
            },
        )

    response = app.test_client().get("/algorithms")

    assert response.status_code == 200
    assert b"All algorithms" in response.data
    assert b"51 items" in response.data
    assert b"Page 1 / 2" in response.data
    assert b"page=2" in response.data
    assert b"Algorithm 1" in response.data
    assert b"Algorithm 50" in response.data


def test_algorithm_catalog_admin_page_shows_paginated_unresolved_card(monkeypatch):
    app = _build_app(monkeypatch)
    repository = app.extensions["algorithm_catalog_repository"]

    for index in range(1, 28):
        repository.upsert_entry(
            source_version="seed",
            catalog_type="algorithm",
            catalog_number=index,
            document={
                "id": f"entry-{index}",
                "catalog_type": "algorithm",
                "catalog_number": index,
                "name": f"Unresolved Algorithm {index}",
                "slug": f"unresolved-algorithm-{index}",
                "category": "Trend Following",
                "subcategory": "",
                "advanced_label": "No",
                "best_use_horizon": "Swing",
                "home_suitability_score": 3,
                "core_idea": f"Idea {index}",
                "typical_inputs": "Price",
                "signal_style": "Trend",
                "extended_implementation_details": "Details",
                "initial_reference": f"Ref-{index}",
                "source_version": "seed",
                "is_active": True,
                "created_at": "2026-04-21T10:00:00Z",
                "updated_at": "2026-04-21T10:00:00Z",
            },
        )

    response = app.test_client().get("/algorithms")

    assert response.status_code == 200
    assert b"Unresolved entries" in response.data
    assert b"unresolved_page=2" in response.data
    assert b"Unresolved Algorithm 25" in response.data

    page_two_response = app.test_client().get("/algorithms?unresolved_page=2")

    assert page_two_response.status_code == 200
    assert b"Unresolved Algorithm 26" in page_two_response.data
    assert b"Unresolved Algorithm 27" in page_two_response.data


def test_algorithm_catalog_admin_page_preserves_other_page_state_in_card_links(
    monkeypatch,
):
    app = _build_app(monkeypatch)
    response = app.test_client().get(
        "/administration/algorithm-catalog?unresolved_page=2&page=2"
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/algorithms?unresolved_page=2&page=2")


def test_algorithm_catalog_admin_page_clamps_out_of_range_pages(monkeypatch):
    app = _build_app(monkeypatch)
    repository = app.extensions["algorithm_catalog_repository"]

    for index in range(1, 28):
        repository.upsert_entry(
            source_version="seed",
            catalog_type="algorithm",
            catalog_number=index,
            document={
                "id": f"entry-{index}",
                "catalog_type": "algorithm",
                "catalog_number": index,
                "name": f"Algorithm {index}",
                "slug": f"algorithm-{index}",
                "category": "Trend Following",
                "subcategory": "",
                "advanced_label": "No",
                "best_use_horizon": "Swing",
                "home_suitability_score": 3,
                "core_idea": f"Idea {index}",
                "typical_inputs": "Price",
                "signal_style": "Trend",
                "extended_implementation_details": "Details",
                "initial_reference": f"Ref-{index}",
                "source_version": "seed",
                "is_active": True,
                "created_at": "2026-04-21T10:00:00Z",
                "updated_at": "2026-04-21T10:00:00Z",
            },
        )

    response = app.test_client().get("/algorithms?unresolved_page=99&page=99")

    assert response.status_code == 200
    assert b"Unresolved entries" in response.data
    assert b"Page 2 / 2" in response.data
    assert b"Algorithm 26" in response.data


def test_algorithm_detail_page_updates_catalog_fields_and_review_state(monkeypatch):
    app = _build_app(monkeypatch)
    app.extensions["algorithm_catalog_repository"].upsert_entry(
        source_version="seed",
        catalog_type="algorithm",
        catalog_number=1,
        document={
            "id": "entry-1",
            "catalog_type": "algorithm",
            "catalog_number": 1,
            "name": "Seed Entry",
            "slug": "seed-entry",
            "category": "Trend Following",
            "subcategory": "",
            "advanced_label": "No",
            "best_use_horizon": "Swing",
            "home_suitability_score": 3,
            "core_idea": "Seed idea",
            "typical_inputs": "Price",
            "signal_style": "Trend",
            "extended_implementation_details": "Details",
            "initial_reference": "Ref",
            "implementation_decision": "",
            "implementation_notes": "",
            "admin_annotations": "",
            "source_version": "seed",
            "is_active": True,
            "created_at": "2026-04-21T10:00:00Z",
            "updated_at": "2026-04-21T10:00:00Z",
        },
    )
    _assign_implementation(
        app,
        entry_id="entry-1",
        implementation_id="OLD_boundary_breakout_NEW_breakout_donchian_channel",
        review_state="confirmed",
    )

    response = app.test_client().post(
        "/algorithms/seed-entry",
        data={
            "name": "Updated Seed Entry",
            "category": "Trend",
            "subcategory": "Momentum",
            "advanced_label": "Yes",
            "best_use_horizon": "Position",
            "home_suitability_score": "5",
            "core_idea": "Updated idea",
            "typical_inputs": "Updated inputs",
            "signal_style": "Updated style",
            "extended_implementation_details": "Updated details",
            "initial_reference": "Updated ref",
            "implementation_decision": "Build",
            "implementation_notes": "Updated notes",
            "admin_annotations": "Updated annotations",
            "review_state": "needs_review",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"algorithm_catalog: algorithm updated;" in response.data
    assert b"Updated Seed Entry" in response.data
    assert b">Runnable<" in response.data
    assert b">Needs review<" in response.data
    assert b"Linked implementation" in response.data
    assert b"_build_boundary_breakout" in response.data

    stored = app.extensions["algorithm_catalog_repository"].get_entry_by_id("entry-1")
    assert stored is not None
    assert stored["name"] == "Updated Seed Entry"
    assert stored["category"] == "Trend"
    assert stored["subcategory"] == "Momentum"
    assert stored["advanced_label"] == "Yes"
    assert stored["best_use_horizon"] == "Position"
    assert stored["home_suitability_score"] == 5
    assert stored["core_idea"] == "Updated idea"
    assert stored["typical_inputs"] == "Updated inputs"
    assert stored["signal_style"] == "Updated style"
    assert stored["extended_implementation_details"] == "Updated details"
    assert stored["initial_reference"] == "Updated ref"
    assert stored["implementation_decision"] == "Build"
    assert stored["implementation_notes"] == "Updated notes"
    assert stored["admin_annotations"] == "Updated annotations"
    assert stored["review_state"] == "needs_review"


def test_algorithm_detail_page_can_update_only_review_state(monkeypatch):
    app = _build_app(monkeypatch)
    app.extensions["algorithm_catalog_repository"].upsert_entry(
        source_version="seed",
        catalog_type="algorithm",
        catalog_number=1,
        document={
            "id": "entry-1",
            "catalog_type": "algorithm",
            "catalog_number": 1,
            "name": "Seed Entry",
            "slug": "seed-entry",
            "category": "Trend Following",
            "subcategory": "",
            "advanced_label": "No",
            "best_use_horizon": "Swing",
            "home_suitability_score": 3,
            "core_idea": "Seed idea",
            "typical_inputs": "Price",
            "signal_style": "Trend",
            "extended_implementation_details": "Details",
            "initial_reference": "Ref",
            "implementation_decision": "",
            "implementation_notes": "",
            "admin_annotations": "",
            "source_version": "seed",
            "is_active": True,
            "created_at": "2026-04-21T10:00:00Z",
            "updated_at": "2026-04-21T10:00:00Z",
        },
    )
    _assign_implementation(
        app,
        entry_id="entry-1",
        implementation_id="OLD_boundary_breakout_NEW_breakout_donchian_channel",
    )

    response = app.test_client().post(
        "/algorithms/seed-entry",
        data={
            "review_state": "confirmed",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b">Confirmed<" in response.data
    assert b"Linked implementation" in response.data
    assert b"_build_boundary_breakout" in response.data

    stored = app.extensions["algorithm_catalog_repository"].get_entry_by_id("entry-1")
    assert stored is not None
    assert stored["review_state"] == "confirmed"
    assert stored["name"] == "Seed Entry"
    assert stored["category"] == "Trend Following"
    assert (
        stored["implementation_id"]
        == "OLD_boundary_breakout_NEW_breakout_donchian_channel"
    )


def test_algorithm_detail_page_shows_linked_implementation_details(monkeypatch):
    app = _build_app(monkeypatch)
    app.extensions["algorithm_catalog_repository"].upsert_entry(
        source_version="seed",
        catalog_type="algorithm",
        catalog_number=1,
        document={
            "id": "entry-1",
            "catalog_type": "algorithm",
            "catalog_number": 1,
            "name": "Seed Entry",
            "slug": "seed-entry",
            "category": "Trend Following",
            "subcategory": "",
            "advanced_label": "No",
            "best_use_horizon": "Swing",
            "home_suitability_score": 3,
            "core_idea": "Seed idea",
            "typical_inputs": "Price",
            "signal_style": "Trend",
            "extended_implementation_details": "Details",
            "initial_reference": "Ref",
            "implementation_decision": "",
            "implementation_notes": "",
            "admin_annotations": "",
            "source_version": "seed",
            "is_active": True,
            "created_at": "2026-04-21T10:00:00Z",
            "updated_at": "2026-04-21T10:00:00Z",
        },
    )
    _assign_implementation(
        app,
        entry_id="entry-1",
        implementation_id="OLD_boundary_breakout_NEW_breakout_donchian_channel",
    )

    response = app.test_client().get("/algorithms/seed-entry")

    assert response.status_code == 200
    assert b"Linked implementation" in response.data
    assert b"_build_boundary_breakout" in response.data
    assert b"trading_algos.alertgen.algorithms.trend.catalog" in response.data
    assert (
        b"/experiments/new?alg_key=OLD_boundary_breakout_NEW_breakout_donchian_channel"
        in response.data
    )


def test_algorithm_detail_page_rejects_invalid_updates(monkeypatch):
    app = _build_app(monkeypatch)
    app.extensions["algorithm_catalog_repository"].upsert_entry(
        source_version="seed",
        catalog_type="algorithm",
        catalog_number=1,
        document={
            "id": "entry-1",
            "catalog_type": "algorithm",
            "catalog_number": 1,
            "name": "Seed Entry",
            "slug": "seed-entry",
            "category": "Trend Following",
            "subcategory": "",
            "advanced_label": "No",
            "best_use_horizon": "Swing",
            "home_suitability_score": 3,
            "core_idea": "Seed idea",
            "typical_inputs": "Price",
            "signal_style": "Trend",
            "extended_implementation_details": "Details",
            "initial_reference": "Ref",
            "source_version": "seed",
            "is_active": True,
            "created_at": "2026-04-21T10:00:00Z",
            "updated_at": "2026-04-21T10:00:00Z",
        },
    )

    response = app.test_client().post(
        "/algorithms/seed-entry",
        data={
            "name": "",
            "category": "Trend",
            "subcategory": "",
            "advanced_label": "No",
            "best_use_horizon": "Swing",
            "home_suitability_score": "3",
            "core_idea": "Idea",
            "typical_inputs": "Inputs",
            "signal_style": "Style",
            "extended_implementation_details": "Details",
            "initial_reference": "Ref",
            "implementation_decision": "",
            "implementation_notes": "",
            "admin_annotations": "",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Algorithm name cannot be empty." in response.data


def test_algorithm_catalog_admin_page_preserves_all_filter_options(monkeypatch):
    app = _build_app(monkeypatch)
    app.extensions["algorithm_catalog_repository"].upsert_entry(
        source_version="seed",
        catalog_type="algorithm",
        catalog_number=1,
        document={
            "id": "seed-entry",
            "catalog_type": "algorithm",
            "catalog_number": 1,
            "name": "Seed Entry",
            "slug": "seed-entry",
            "category": "Trend Following",
            "subcategory": "",
            "advanced_label": "No",
            "best_use_horizon": "Swing",
            "home_suitability_score": 3,
            "core_idea": "Seed idea",
            "typical_inputs": "Price",
            "signal_style": "Trend",
            "extended_implementation_details": "Details",
            "initial_reference": "Ref",
            "source_version": "seed",
            "is_active": True,
            "created_at": "2026-04-21T10:00:00Z",
            "updated_at": "2026-04-21T10:00:00Z",
        },
    )
    _assign_implementation(
        app,
        entry_id="seed-entry",
        implementation_id="OLD_boundary_breakout_NEW_breakout_donchian_channel",
    )

    response = app.test_client().get(
        "/algorithms"
        "?status=implemented"
        "&review_state=confirmed"
        "&catalog_type=algorithm"
        "&category=Trend%20Following"
        "&advanced_label=No"
        "&linked=true"
        "&only_broken=true"
        "&only_unresolved=true"
        "&q=breakout"
    )

    assert response.status_code == 200
    assert b'name="status"' in response.data
    assert b'value="implemented" selected' in response.data
    assert b'name="review_state"' in response.data
    assert b'value="confirmed" selected' in response.data
    assert b'name="catalog_type"' in response.data
    assert b'value="algorithm" selected' in response.data
    assert b'name="only_broken" value="true" checked' in response.data
    assert b'name="only_unresolved" value="true" checked' in response.data


def test_algorithm_catalog_admin_page_summary_matches_filtered_unresolved_rows(
    monkeypatch,
):
    app = _build_app(monkeypatch)
    repository = app.extensions["algorithm_catalog_repository"]

    for index in range(1, 18):
        repository.upsert_entry(
            source_version="seed",
            catalog_type="algorithm",
            catalog_number=index,
            document={
                "id": f"matching-entry-{index}",
                "catalog_type": "algorithm",
                "catalog_number": index,
                "name": f"Matching unresolved {index}",
                "slug": f"matching-unresolved-{index}",
                "category": "Trend Following",
                "subcategory": "",
                "advanced_label": "No",
                "best_use_horizon": "Swing",
                "home_suitability_score": 3,
                "core_idea": f"Idea {index}",
                "typical_inputs": "Price",
                "signal_style": "Trend",
                "extended_implementation_details": "Details",
                "initial_reference": f"Ref-{index}",
                "source_version": "seed",
                "is_active": True,
                "created_at": "2026-04-21T10:00:00Z",
                "updated_at": "2026-04-21T10:00:00Z",
            },
        )

    for index in range(18, 26):
        repository.upsert_entry(
            source_version="seed",
            catalog_type="algorithm",
            catalog_number=index,
            document={
                "id": f"other-entry-{index}",
                "catalog_type": "algorithm",
                "catalog_number": index,
                "name": f"Other unresolved {index}",
                "slug": f"other-unresolved-{index}",
                "category": "Mean Reversion",
                "subcategory": "",
                "advanced_label": "No",
                "best_use_horizon": "Swing",
                "home_suitability_score": 3,
                "core_idea": f"Idea {index}",
                "typical_inputs": "Price",
                "signal_style": "Trend",
                "extended_implementation_details": "Details",
                "initial_reference": f"Ref-{index}",
                "source_version": "seed",
                "is_active": True,
                "created_at": "2026-04-21T10:00:00Z",
                "updated_at": "2026-04-21T10:00:00Z",
            },
        )

    response = app.test_client().get("/algorithms?category=Trend%20Following")

    assert response.status_code == 200
    assert b">17</div>" in response.data
    assert b"17 items" in response.data
    assert b"Matching unresolved 17" in response.data
    assert b"Other unresolved 18" not in response.data


def test_algorithm_catalog_sync_route_rebuilds_links(monkeypatch):
    app = _build_app(monkeypatch)
    response = app.test_client().post(
        "/administration/algorithm-catalog/sync-links",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"administration: algorithm catalog links synced;" in response.data
    assert b"Algorithm Catalog" in response.data


def test_algorithm_catalog_sync_route_defaults_review_state_to_not_reviewed(
    monkeypatch,
):
    app = _build_app(monkeypatch)
    app.extensions["algorithm_catalog_repository"].upsert_entry(
        source_version="seed",
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
            "best_use_horizon": "Swing",
            "home_suitability_score": 3,
            "core_idea": "Idea",
            "typical_inputs": "Price",
            "signal_style": "Trend",
            "extended_implementation_details": "Details",
            "initial_reference": "Ref",
            "source_version": "seed",
            "is_active": True,
            "created_at": "2026-04-21T10:00:00Z",
            "updated_at": "2026-04-21T10:00:00Z",
        },
    )

    response = app.test_client().post(
        "/administration/algorithm-catalog/sync-links",
        follow_redirects=True,
    )

    assert response.status_code == 200
    detail_response = app.test_client().get("/algorithms/breakout-donchian-channel")
    assert detail_response.status_code == 200
    assert b">Runnable<" in detail_response.data
    assert b">Not reviewed<" in detail_response.data


def test_algorithm_catalog_sync_route_preserves_rejected_review_state(
    monkeypatch,
):
    app = _build_app(monkeypatch)
    app.extensions["algorithm_catalog_repository"].upsert_entry(
        source_version="seed",
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
            "best_use_horizon": "Swing",
            "home_suitability_score": 3,
            "core_idea": "Idea",
            "typical_inputs": "Price",
            "signal_style": "Trend",
            "extended_implementation_details": "Details",
            "initial_reference": "Ref",
            "source_version": "seed",
            "is_active": True,
            "implementation_id": "OLD_boundary_breakout_NEW_breakout_donchian_channel",
            "implementation_catalog_ref": "algorithm:6",
            "implementation_source": "runtime_declared",
            "implementation_confidence": 1.0,
            "implementation_mapping_notes": "implementation declared",
            "implementation_mapping_reason": "implementation-declared catalog_ref",
            "review_state": "rejected",
            "created_at": "2026-04-21T10:00:00Z",
            "updated_at": "2026-04-21T10:00:00Z",
        },
    )

    response = app.test_client().post(
        "/administration/algorithm-catalog/sync-links",
        follow_redirects=True,
    )

    assert response.status_code == 200
    detail_response = app.test_client().get("/algorithms/breakout-donchian-channel")
    assert detail_response.status_code == 200
    assert b">Not runnable<" in detail_response.data
    assert b">Rejected<" in detail_response.data


def test_app_startup_rebuild_preserves_existing_rejected_review_state(monkeypatch):
    client = _Client()
    client.db["algorithm_catalog_entries"].insert_one(
        {
            "id": "entry-1",
            "catalog_type": "algorithm",
            "catalog_number": 6,
            "name": "Breakout (Donchian Channel)",
            "slug": "breakout-donchian-channel",
            "category": "Trend Following",
            "subcategory": "",
            "advanced_label": "No",
            "best_use_horizon": "Swing",
            "home_suitability_score": 3,
            "core_idea": "Idea",
            "typical_inputs": "Price",
            "signal_style": "Trend",
            "extended_implementation_details": "Details",
            "initial_reference": "Ref",
            "source_version": "seed",
            "is_active": True,
            "implementation_id": "OLD_boundary_breakout_NEW_breakout_donchian_channel",
            "implementation_catalog_ref": "algorithm:6",
            "implementation_source": "runtime_declared",
            "implementation_confidence": 1.0,
            "implementation_mapping_notes": "implementation declared",
            "implementation_mapping_reason": "implementation-declared catalog_ref",
            "implementation_builder_name": "_build_boundary_breakout",
            "implementation_builder_module": "trading_algos.alertgen.algorithms.trend.catalog",
            "implementation_source_file": "src/trading_algos/alertgen/algorithms/trend/catalog.py",
            "review_state": "rejected",
            "created_at": "2026-04-21T10:00:00Z",
            "updated_at": "2026-04-21T10:00:00Z",
        }
    )
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: client
    )

    app = create_app(
        DashboardConfig(
            "x",
            "mongodb://example",
            "db",
            "reports",
            "/tmp/smarttrade",
            1,
        )
    )

    stored = app.extensions["algorithm_catalog_repository"].get_entry_by_id("entry-1")
    assert stored is not None
    assert stored["review_state"] == "rejected"


def test_app_startup_rebuild_preserves_regular_catalog_fields(monkeypatch):
    client = _Client()
    client.db["algorithm_catalog_entries"].insert_one(
        {
            "id": "entry-1",
            "catalog_type": "algorithm",
            "catalog_number": 6,
            "name": "Custom Breakout Name",
            "slug": "breakout-donchian-channel",
            "category": "Custom Trend",
            "subcategory": "Custom Subcategory",
            "advanced_label": "Yes",
            "best_use_horizon": "Position",
            "home_suitability_score": 7,
            "core_idea": "Custom idea",
            "typical_inputs": "Custom inputs",
            "signal_style": "Custom style",
            "extended_implementation_details": "Custom details",
            "initial_reference": "Custom ref",
            "implementation_decision": "Custom decision",
            "implementation_notes": "Custom notes",
            "admin_annotations": "Custom annotations",
            "source_version": "seed",
            "is_active": True,
            "implementation_id": "OLD_boundary_breakout_NEW_breakout_donchian_channel",
            "implementation_catalog_ref": "algorithm:6",
            "implementation_source": "runtime_declared",
            "implementation_confidence": 1.0,
            "implementation_mapping_notes": "implementation declared",
            "implementation_mapping_reason": "implementation-declared catalog_ref",
            "implementation_builder_name": "_build_boundary_breakout",
            "implementation_builder_module": "trading_algos.alertgen.algorithms.trend.catalog",
            "implementation_source_file": "src/trading_algos/alertgen/algorithms/trend/catalog.py",
            "review_state": "confirmed",
            "created_at": "2026-04-21T10:00:00Z",
            "updated_at": "2026-04-21T10:00:00Z",
        }
    )
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: client
    )

    app = create_app(
        DashboardConfig(
            "x",
            "mongodb://example",
            "db",
            "reports",
            "/tmp/smarttrade",
            1,
        )
    )

    stored = app.extensions["algorithm_catalog_repository"].get_entry_by_id("entry-1")
    assert stored is not None
    assert stored["name"] == "Custom Breakout Name"
    assert stored["category"] == "Custom Trend"
    assert stored["subcategory"] == "Custom Subcategory"
    assert stored["advanced_label"] == "Yes"
    assert stored["best_use_horizon"] == "Position"
    assert stored["home_suitability_score"] == 7
    assert stored["core_idea"] == "Custom idea"
    assert stored["typical_inputs"] == "Custom inputs"
    assert stored["signal_style"] == "Custom style"
    assert stored["extended_implementation_details"] == "Custom details"
    assert stored["initial_reference"] == "Custom ref"
    assert stored["implementation_decision"] == "Custom decision"
    assert stored["implementation_notes"] == "Custom notes"
    assert stored["admin_annotations"] == "Custom annotations"
    assert stored["review_state"] == "confirmed"


def test_algorithm_catalog_delete_requires_exact_confirmation(monkeypatch):
    app = _build_app(monkeypatch)
    app.extensions["algorithm_catalog_repository"].upsert_entry(
        source_version="seed",
        catalog_type="algorithm",
        catalog_number=1,
        document={
            "catalog_type": "algorithm",
            "catalog_number": 1,
            "name": "Seed Entry",
            "slug": "seed-entry",
            "category": "Trend",
            "subcategory": "",
            "advanced_label": "No",
            "best_use_horizon": "Swing",
            "home_suitability_score": 3,
            "core_idea": "Seed idea",
            "typical_inputs": "Price",
            "signal_style": "Trend",
            "extended_implementation_details": "Details",
            "initial_reference": "Ref",
            "source_version": "seed",
            "is_active": True,
            "created_at": "2026-04-21T10:00:00Z",
            "updated_at": "2026-04-21T10:00:00Z",
        },
    )
    response = app.test_client().post(
        "/administration/algorithm-catalog/delete-all",
        data={"confirmation_text": "delete all algorithm catalog entries"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert (
        b"administration: algorithm catalog deletion not executed; reason=invalid_confirmation_text"
        in response.data
    )
    assert app.extensions["algorithm_catalog_repository"].count_entries() > 0


def test_algorithm_catalog_delete_removes_entries_and_links(monkeypatch):
    app = _build_app(monkeypatch)
    response = app.test_client().post(
        "/administration/algorithm-catalog/delete-all",
        data={
            "confirmation_text": "DELETE ALL ALGORITHM CATALOG ENTRIES",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"administration: algorithm catalog deleted;" in response.data
    assert app.extensions["algorithm_catalog_repository"].count_entries() == 0
    assert (
        app.extensions[
            "algorithm_catalog_repository"
        ].count_entries_with_implementation()
        == 0
    )


def test_algorithm_catalog_import_detail_page_renders(monkeypatch):
    app = _build_app(monkeypatch)
    run = app.extensions["algorithm_catalog_import_run_repository"].create_run(
        {
            "source_version": "catalog-upload",
            "source_filename": "catalog-upload.md",
            "source_content_type": "text/markdown",
            "status": "completed",
            "started_at": "2026-04-21T10:00:00Z",
            "completed_at": "2026-04-21T10:00:10Z",
            "rows_seen": 1,
            "rows_created": 1,
            "rows_updated": 0,
            "rows_unchanged": 0,
            "rows_deactivated": 0,
            "warnings": [],
            "links_written": 0,
            "created_entry_ids": [],
            "updated_entry_ids": [],
            "unchanged_entry_ids": [],
            "deactivated_entry_ids": [],
            "unresolved_entry_ids": [],
            "preserved_manual_link_entry_ids": [],
            "changed_link_entry_ids": [],
        }
    )
    assert run is not None
    response = app.test_client().get(
        f"/administration/algorithm-catalog/imports/{run['id']}"
    )
    assert response.status_code == 200
    assert b"Algorithm catalog import detail" in response.data
    assert b"catalog-upload.md" in response.data


def test_clear_results_removes_only_results(monkeypatch):
    app = _build_app(monkeypatch)
    app.extensions["experiment_repository"].create_experiment(
        {"experiment_id": "exp_1", "created_at": "2026-04-21T10:00:00Z"}
    )
    app.extensions["result_repository"].insert_result(
        {
            "experiment_id": "exp_1",
            "alg_key": "alg_1",
            "created_at": "2026-04-21T10:00:00Z",
        }
    )

    response = app.test_client().post(
        "/administration/results/clear",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"administration: results cleared; deleted_results=1" in response.data
    assert app.extensions["result_repository"].count_results() == 0
    assert app.extensions["experiment_repository"].count_experiments() == 1


def test_clear_experiments_removes_experiments_and_related_results(monkeypatch):
    app = _build_app(monkeypatch)
    app.extensions["experiment_repository"].create_experiment(
        {"experiment_id": "exp_1", "created_at": "2026-04-21T10:00:00Z"}
    )
    app.extensions["experiment_repository"].create_experiment(
        {"experiment_id": "exp_2", "created_at": "2026-04-21T10:05:00Z"}
    )
    app.extensions["result_repository"].insert_result(
        {
            "experiment_id": "exp_1",
            "alg_key": "alg_1",
            "created_at": "2026-04-21T10:00:00Z",
        }
    )
    app.extensions["result_repository"].insert_result(
        {
            "experiment_id": "exp_2",
            "alg_key": "alg_2",
            "created_at": "2026-04-21T10:05:00Z",
        }
    )

    response = app.test_client().post(
        "/administration/experiments/clear",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert (
        b"administration: experiments cleared; deleted_experiments=2 deleted_results=2"
        in response.data
    )
    assert app.extensions["experiment_repository"].count_experiments() == 0
    assert app.extensions["result_repository"].count_results() == 0
