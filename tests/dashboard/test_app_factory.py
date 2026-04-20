from trading_algos_dashboard.app import create_app
from trading_algos_dashboard.config import DashboardConfig


def test_create_app_registers_core_routes(monkeypatch):
    class _Cursor:
        def __init__(self, docs):
            self.docs = docs

        def sort(self, *_args, **_kwargs):
            return self.docs

    class _Collection:
        def __init__(self):
            self.docs = []

        def find(self, *_args, **_kwargs):
            return _Cursor(self.docs)

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

    class _Db(dict):
        def __getitem__(self, key):
            if key not in self:
                self[key] = _Collection()
            return dict.__getitem__(self, key)

    class _Client:
        def __init__(self):
            self.db = _Db()

        def __getitem__(self, db_name):
            return self.db

    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_args, **_kwargs: _Client()
    )

    app = create_app(
        DashboardConfig(
            secret_key="x",
            mongo_uri="mongodb://example",
            mongo_db_name="db",
            report_base_path="reports",
            smarttrade_path="/tmp/smarttrade",
            smarttrade_user_id=1,
        )
    )

    client = app.test_client()
    assert app.config["SESSION_COOKIE_NAME"] == "trading_algos_session"
    assert client.get("/").status_code == 200
    assert client.get("/health").status_code == 200
    assert client.get("/algorithms").status_code == 200
    response = client.get("/")
    assert b"Market data server" in response.data
    assert b'value="127.0.0.2"' in response.data
    assert b'value="6010"' in response.data
