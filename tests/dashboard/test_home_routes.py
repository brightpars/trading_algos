from trading_algos_dashboard.app import create_app
from trading_algos_dashboard.config import DashboardConfig


class _Collection:
    def __init__(self):
        self.docs = []

    def _matches(self, doc, query):
        return all(doc.get(k) == v for k, v in query.items())

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
        doc = self.find_one(query)
        if doc is None:
            if not upsert:
                return None
            doc = dict(query)
            self.docs.append(doc)
        if "$set" in update:
            doc.update(update["$set"])
        return None

    def delete_many(self, query):
        effective_query = dict(query or {})
        original_count = len(self.docs)
        self.docs = [
            doc for doc in self.docs if not self._matches(doc, effective_query)
        ]

        class _DeleteResult:
            def __init__(self, deleted_count):
                self.deleted_count = deleted_count

        return _DeleteResult(original_count - len(self.docs))

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


def test_home_page_renders_saved_data_source_settings(monkeypatch):
    app = _build_app(monkeypatch)
    app.extensions["data_source_settings_service"].save_settings(
        ip="10.0.0.5", port=7003
    )

    response = app.test_client().get("/")

    assert response.status_code == 200
    assert b'value="10.0.0.5"' in response.data
    assert b'value="7003"' in response.data


def test_save_data_source_settings_persists_values(monkeypatch):
    app = _build_app(monkeypatch)

    response = app.test_client().post(
        "/data-source-settings",
        data={"ip": "192.168.1.10", "port": "7010"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Data server settings saved." in response.data
    settings = app.extensions["data_source_settings_service"].get_effective_settings()
    assert settings["ip"] == "192.168.1.10"
    assert settings["port"] == 7010


def test_check_data_source_settings_returns_success_json(monkeypatch):
    app = _build_app(monkeypatch)
    monkeypatch.setattr(
        app.extensions["data_source_service"],
        "check_connection",
        lambda: {"status": "ok", "endpoint": "127.0.0.1:7003", "server_up": True},
    )

    response = app.test_client().post(
        "/data-source-settings/check",
        data={"ip": "127.0.0.1", "port": "7003"},
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ok",
        "endpoint": "127.0.0.1:7003",
        "server_up": True,
    }


def test_check_data_source_settings_returns_error_json(monkeypatch):
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
        "/data-source-settings/check",
        data={"ip": "127.0.0.1", "port": "7003"},
    )

    assert response.status_code == 503
    assert response.get_json()["status"] == "error"
    assert response.get_json()["message"] == "not responding"
