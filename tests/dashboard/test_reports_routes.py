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

    def append(self, payload):
        self.docs.append(payload)

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
    def __getitem__(self, _db_name):
        db = _Db()
        db["dashboard_results"].append(
            {
                "experiment_id": "exp1",
                "alg_name": "Alg",
                "report": {
                    "report_version": "1.0",
                    "algorithm_summary": {"algorithm_name": "Alg"},
                    "charts": [],
                    "tables": [],
                    "analysis_blocks": [],
                    "evaluation_summary": {},
                    "experiment_summary": {},
                    "summary_cards": [],
                },
            }
        )
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
    assert b"report=1.0 schema=1.0" in response.data
