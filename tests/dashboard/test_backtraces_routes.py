from __future__ import annotations

from typing import Any

from trading_algos_dashboard.app import create_app
from trading_algos_dashboard.config import DashboardConfig


class _Collection:
    def __init__(self) -> None:
        self.docs: list[dict[str, Any]] = []

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
        for doc in self.docs:
            if all(doc.get(key) == value for key, value in query.items()):
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
            if not all(doc.get(key) == value for key, value in query.items())
        ]
        return type(
            "_DeleteResult", (), {"deleted_count": original_count - len(self.docs)}
        )()

    def count_documents(self, query):
        return sum(
            1
            for doc in self.docs
            if all(doc.get(key) == value for key, value in query.items())
        )


class _Cursor:
    def __init__(self, docs: list[dict[str, Any]]) -> None:
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
    def __init__(self) -> None:
        self.db = _Db()

    def __getitem__(self, _db_name):
        return self.db


def _build_app(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    return create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))


def _backtrace_form_payload() -> dict[str, str]:
    return {
        "algorithm_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
        "symbol": "AAPL",
        "algorithm_params_json": '{"window": 2}',
        "candles_json": """[
  {
    \"ts\": \"2025-01-01T10:00:00Z\",
    \"Open\": 100.0,
    \"High\": 101.0,
    \"Low\": 99.0,
    \"Close\": 100.5,
    \"Volume\": 1000
  },
  {
    \"ts\": \"2025-01-01T10:01:00Z\",
    \"Open\": 100.5,
    \"High\": 101.5,
    \"Low\": 100.0,
    \"Close\": 101.0,
    \"Volume\": 1200
  },
  {
    \"ts\": \"2025-01-01T10:02:00Z\",
    \"Open\": 101.0,
    \"High\": 102.0,
    \"Low\": 100.5,
    \"Close\": 101.8,
    \"Volume\": 1400
  }
]""",
        "metadata_json": '{"source": "dashboard-test", "label": "demo"}',
    }


def test_new_backtrace_page_renders(monkeypatch):
    app = _build_app(monkeypatch)

    response = app.test_client().get("/backtraces/new")

    assert response.status_code == 200
    assert b"Manual backtrace" in response.data
    assert b'name="algorithm_key"' in response.data
    assert b'name="candles_json"' in response.data
    assert b"View recent runs" in response.data


def test_backtrace_submit_flow_redirects_to_detail(monkeypatch):
    app = _build_app(monkeypatch)

    response = app.test_client().post(
        "/backtraces",
        data=_backtrace_form_payload(),
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/backtraces/" in response.headers["Location"]

    run_id = response.headers["Location"].rsplit("/", 1)[-1]
    run = app.extensions["backtrace_client_service"].get_run(run_id)
    assert run is not None
    assert run["status"] == "completed"
    assert run["request"]["metadata"] == {"source": "dashboard-test", "label": "demo"}


def test_backtrace_detail_page_renders_result_summary(monkeypatch):
    app = _build_app(monkeypatch)
    client = app.test_client()

    create_response = client.post(
        "/backtraces",
        data=_backtrace_form_payload(),
        follow_redirects=False,
    )
    run_id = create_response.headers["Location"].rsplit("/", 1)[-1]

    response = client.get(f"/backtraces/{run_id}")

    assert response.status_code == 200
    assert b"Backtrace result" in response.data
    assert b"Signal and evaluation summary" in response.data
    assert b"Execution steps" in response.data
    assert b"Raw JSON" in response.data
    assert b"dashboard-test" in response.data


def test_backtrace_list_page_renders_recent_runs(monkeypatch):
    app = _build_app(monkeypatch)
    client = app.test_client()

    client.post("/backtraces", data=_backtrace_form_payload(), follow_redirects=False)

    response = client.get("/backtraces")

    assert response.status_code == 200
    assert b"Backtrace runs" in response.data
    assert b"AAPL" in response.data
    assert b"completed" in response.data


def test_backtrace_validation_error_renders_on_form(monkeypatch):
    app = _build_app(monkeypatch)

    response = app.test_client().post(
        "/backtraces",
        data={
            "algorithm_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
            "symbol": "AAPL",
            "algorithm_params_json": '{"window": 2}',
            "candles_json": "{}",
            "metadata_json": '{"source": "dashboard-test"}',
        },
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert b"Candles JSON must decode to a JSON array." in response.data
    assert b'name="algorithm_key"' in response.data
    assert b"AAPL" in response.data
