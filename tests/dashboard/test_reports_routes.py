from trading_algos_dashboard.app import create_app
from trading_algos_dashboard.config import DashboardConfig


class _Collection:
    def __init__(self):
        self.docs = []

    def find(self, *_args, **_kwargs):
        return self

    def sort(self, *_args, **_kwargs):
        return self

    def append(self, payload):
        self.docs.append(payload)

    def __iter__(self):
        return iter(self.docs)


class _Db(dict):
    def __getitem__(self, key):
        if key not in self:
            self[key] = _Collection()
        return dict.__getitem__(self, key)


class _Client:
    def __getitem__(self, _db_name):
        db = _Db()
        db["dashboard_results"].append({"experiment_id": "exp1", "alg_name": "Alg"})
        return db


def test_reports_page_renders(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig("x", "mongodb://example", "db", "reports", "/tmp/smarttrade", 1)
    )
    client = app.test_client()
    response = client.get("/reports")
    assert response.status_code == 200
