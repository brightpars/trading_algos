from trading_algos_dashboard.app import create_app
from trading_algos_dashboard.config import DashboardConfig


class _Collection:
    def __init__(self):
        self.docs = []

    def find(self, *_args, **_kwargs):
        return self

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
        if "$set" in update:
            doc.update(update["$set"])
        return None

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


def _sample_configuration_payload():
    return {
        "config_key": "combo_breakout",
        "version": "1",
        "name": "Combo Breakout",
        "root_node_id": "root",
        "nodes": [
            {
                "node_id": "root",
                "node_type": "and",
                "children": ["alg1", "alg2"],
            },
            {
                "node_id": "alg1",
                "node_type": "algorithm",
                "alg_key": "close_high_channel_breakout",
                "alg_param": {"window": 2},
                "buy_enabled": True,
                "sell_enabled": True,
            },
            {
                "node_id": "alg2",
                "node_type": "algorithm",
                "alg_key": "boundary_breakout",
                "alg_param": {"period": 5},
                "buy_enabled": True,
                "sell_enabled": True,
            },
        ],
        "compatibility_metadata": {},
    }


def test_new_configuration_page_renders(monkeypatch):
    app = _build_app(monkeypatch)
    response = app.test_client().get("/configurations/new")
    assert response.status_code == 200
    assert b"New configuration draft" in response.data


def test_create_configuration_creates_draft(monkeypatch):
    app = _build_app(monkeypatch)
    response = app.test_client().post(
        "/configurations",
        data={"payload": __import__("json").dumps(_sample_configuration_payload())},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/configurations/cfgdraft_" in response.headers["Location"]


def test_configuration_detail_shows_publish_history(monkeypatch):
    app = _build_app(monkeypatch)
    draft_id = app.extensions["configuration_builder_service"].create_draft(
        _sample_configuration_payload()
    )
    app.extensions["publication_record_repository"].create_record(
        {
            "draft_id": draft_id,
            "created_at": "2026-04-21T10:00:00Z",
            "remote_config_id": "algcfg_1",
            "remote_status": "published",
            "result": {"config_id": "algcfg_1"},
        }
    )
    response = app.test_client().get(f"/configurations/{draft_id}")
    assert response.status_code == 200
    assert b"Publish history" in response.data
    assert b"algcfg_1" in response.data


def test_configuration_detail_validate_remote_uses_publish_service(monkeypatch):
    app = _build_app(monkeypatch)
    draft_id = app.extensions["configuration_builder_service"].create_draft(
        _sample_configuration_payload()
    )
    monkeypatch.setattr(
        app.extensions["configuration_publish_service"],
        "validate_remote",
        lambda payload: {
            "compatibility": {"compatibility_state": "compatible"},
            "payload": payload,
        },
    )
    response = app.test_client().post(
        f"/configurations/{draft_id}/validate-remote",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Remote validation ok" in response.data


def test_configuration_detail_publish_uses_publish_service(monkeypatch):
    app = _build_app(monkeypatch)
    draft_id = app.extensions["configuration_builder_service"].create_draft(
        _sample_configuration_payload()
    )
    monkeypatch.setattr(
        app.extensions["configuration_publish_service"],
        "publish",
        lambda draft_id, payload: {"config_id": "algcfg_1", "status": "published"},
    )
    response = app.test_client().post(
        f"/configurations/{draft_id}/publish",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Published configuration remote_config_id=algcfg_1" in response.data