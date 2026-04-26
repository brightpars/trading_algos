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
    return create_app(DashboardConfig("x", "mongodb://example", "db", "reports"))


def test_home_page_renders_saved_data_source_settings(monkeypatch):
    app = _build_app(monkeypatch)
    app.extensions["data_source_settings_service"].save_settings(
        ip="10.0.0.5", port=7003
    )

    response = app.test_client().get("/")

    assert response.status_code == 200
    assert b"Trading algorithm development dashboard" in response.data
    assert b"Market data server" not in response.data
    assert b"Open runtime settings" in response.data


def test_runtime_settings_link_is_present_on_home_page(monkeypatch):
    app = _build_app(monkeypatch)

    response = app.test_client().get("/")

    assert response.status_code == 200
    assert b"/administration/experiment-runtime-settings" in response.data
    assert b"/experiments/bulk" in response.data
