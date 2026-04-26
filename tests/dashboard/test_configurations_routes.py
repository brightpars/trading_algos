from trading_algos_dashboard.app import create_app
from trading_algos_dashboard.config import DashboardConfig


class _Collection:
    def __init__(self):
        self.docs = []

    class _DeleteResult:
        def __init__(self, deleted_count):
            self.deleted_count = deleted_count

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

    def delete_one(self, query):
        for index, doc in enumerate(self.docs):
            if all(doc.get(key) == value for key, value in query.items()):
                del self.docs[index]
                return self._DeleteResult(1)
        return self._DeleteResult(0)

    def delete_many(self, query):
        original_count = len(self.docs)
        self.docs = [
            doc
            for doc in self.docs
            if not all(doc.get(key) == value for key, value in query.items())
        ]
        return self._DeleteResult(original_count - len(self.docs))

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
                "alg_key": "OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation",
                "alg_param": {"window": 2},
                "buy_enabled": True,
                "sell_enabled": True,
            },
            {
                "node_id": "alg2",
                "node_type": "algorithm",
                "alg_key": "OLD_boundary_breakout_NEW_breakout_donchian_channel",
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
    assert b"How this builder works" in response.data
    assert b"configuration-builder-root" in response.data
    assert b"configuration-payload-input" in response.data
    assert b"Start from a template" in response.data
    assert b"Configuration details" in response.data
    assert b"Algorithm reference" in response.data
    assert b"Generated JSON" in response.data


def test_create_configuration_creates_draft(monkeypatch):
    app = _build_app(monkeypatch)
    response = app.test_client().post(
        "/configurations",
        data={"payload": __import__("json").dumps(_sample_configuration_payload())},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/configurations/cfgdraft_" in response.headers["Location"]


def test_create_configuration_preserves_builder_state_on_validation_error(monkeypatch):
    app = _build_app(monkeypatch)
    response = app.test_client().post(
        "/configurations",
        data={
            "payload": __import__("json").dumps(
                {
                    **_sample_configuration_payload(),
                    "name": "",
                }
            )
        },
        follow_redirects=False,
    )
    assert response.status_code == 400
    assert b"configuration-builder-bootstrap" in response.data
    assert b"combo_breakout" in response.data


def test_edit_configuration_page_renders_existing_payload(monkeypatch):
    app = _build_app(monkeypatch)
    draft_id = app.extensions["configuration_builder_service"].create_draft(
        _sample_configuration_payload()
    )
    response = app.test_client().get(f"/configurations/{draft_id}/edit")
    assert response.status_code == 200
    assert b"Edit configuration draft" in response.data
    assert b"Save changes" in response.data
    assert b"configuration-builder-bootstrap" in response.data


def test_edit_configuration_updates_draft_and_creates_revision(monkeypatch):
    app = _build_app(monkeypatch)
    draft_id = app.extensions["configuration_builder_service"].create_draft(
        _sample_configuration_payload()
    )
    updated_payload = {
        **_sample_configuration_payload(),
        "name": "Updated Combo Breakout",
    }
    response = app.test_client().post(
        f"/configurations/{draft_id}/edit",
        data={"payload": __import__("json").dumps(updated_payload)},
        follow_redirects=False,
    )
    assert response.status_code == 302
    detail = app.extensions["configuration_builder_service"].get_draft_detail(draft_id)
    assert detail is not None
    assert detail["draft"]["name"] == "Updated Combo Breakout"
    assert len(detail["revisions"]) == 2


def test_delete_configuration_removes_draft_from_list_flow(monkeypatch):
    app = _build_app(monkeypatch)
    draft_id = app.extensions["configuration_builder_service"].create_draft(
        _sample_configuration_payload()
    )

    response = app.test_client().post(
        f"/configurations/{draft_id}/delete",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/configurations")
    assert (
        app.extensions["configuration_builder_service"].get_draft_detail(draft_id)
        is None
    )


def test_edit_configuration_preserves_state_on_validation_error(monkeypatch):
    app = _build_app(monkeypatch)
    draft_id = app.extensions["configuration_builder_service"].create_draft(
        _sample_configuration_payload()
    )
    invalid_payload = {
        **_sample_configuration_payload(),
        "root_node_id": "",
    }
    response = app.test_client().post(
        f"/configurations/{draft_id}/edit",
        data={"payload": __import__("json").dumps(invalid_payload)},
        follow_redirects=False,
    )
    assert response.status_code == 400
    assert b"configuration-builder-bootstrap" in response.data
    assert b"Save changes" in response.data


def test_configuration_detail_shows_publish_history(monkeypatch):
    app = _build_app(monkeypatch)
    draft_id = app.extensions["configuration_builder_service"].create_draft(
        _sample_configuration_payload()
    )
    response = app.test_client().get(f"/configurations/{draft_id}")
    assert response.status_code == 200
    assert b"Configuration summary" in response.data
    assert b"Structure summary" in response.data
    assert b"Edit draft" in response.data
    assert b"Delete draft" in response.data
    assert b"Revision 1" in response.data
    assert b"Initial revision created." in response.data


def test_configuration_detail_shows_revision_change_summary(monkeypatch):
    app = _build_app(monkeypatch)
    draft_id = app.extensions["configuration_builder_service"].create_draft(
        _sample_configuration_payload()
    )
    updated_payload = _sample_configuration_payload()
    updated_payload["name"] = "Combo Breakout Updated"
    updated_payload["nodes"] = [
        {
            "node_id": "root",
            "node_type": "and",
            "children": ["alg1", "alg3"],
        },
        updated_payload["nodes"][1],
        {
            "node_id": "alg3",
            "node_type": "algorithm",
            "alg_key": "OLD_boundary_breakout_NEW_breakout_donchian_channel",
            "alg_param": {"period": 7},
            "buy_enabled": True,
            "sell_enabled": True,
        },
    ]
    app.extensions["configuration_builder_service"].update_draft(
        draft_id,
        updated_payload,
    )
    response = app.test_client().get(f"/configurations/{draft_id}")
    assert response.status_code == 200
    assert b"Changed name from" in response.data
    assert b"Combo Breakout Updated" in response.data


def test_edit_configuration_missing_draft_returns_404(monkeypatch):
    app = _build_app(monkeypatch)
    response = app.test_client().get("/configurations/not-real/edit")
    assert response.status_code == 404


def test_delete_configuration_removes_draft_and_related_history(monkeypatch):
    app = _build_app(monkeypatch)
    draft_id = app.extensions["configuration_builder_service"].create_draft(
        _sample_configuration_payload()
    )
    app.extensions["configuration_builder_service"].update_draft(
        draft_id,
        {
            **_sample_configuration_payload(),
            "name": "Updated Combo Breakout",
        },
    )

    response = app.test_client().post(
        f"/configurations/{draft_id}/delete",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Configuration draft deleted; draft_id=" in response.data
    assert (
        app.extensions["configuration_builder_service"].get_draft_detail(draft_id)
        is None
    )
    assert (
        app.extensions["configuration_revision_repository"].list_revisions(draft_id)
        == []
    )


def test_delete_configuration_missing_draft_returns_404(monkeypatch):
    app = _build_app(monkeypatch)

    response = app.test_client().post(
        "/configurations/not-real/delete",
        follow_redirects=False,
    )

    assert response.status_code == 404
