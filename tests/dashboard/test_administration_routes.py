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
    assert b">1<" in response.data


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
