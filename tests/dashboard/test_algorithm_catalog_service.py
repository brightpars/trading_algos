from trading_algos_dashboard.repositories.algorithm_catalog_repository import (
    AlgorithmCatalogRepository,
)
from trading_algos_dashboard.services.algorithm_catalog_service import (
    AlgorithmCatalogService,
)
from typing import Any


class _Collection:
    def __init__(self):
        self.docs = []

    def find(self, query=None, **_kwargs):
        query = dict(query or {})
        return _Cursor(
            [
                doc
                for doc in self.docs
                if all(doc.get(key) == value for key, value in query.items())
            ]
        )

    def find_one(self, query):
        for doc in self.docs:
            if all(doc.get(key) == value for key, value in query.items()):
                return doc
        return None

    def sort(self, key: str, direction: int):
        reverse = direction == -1
        return sorted(
            self.docs,
            key=lambda item: str(item.get(key, "")),
            reverse=reverse,
        )

    def insert_one(self, payload):
        self.docs.append(dict(payload))

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
        self.docs = [
            doc
            for doc in self.docs
            if not all(doc.get(key) == value for key, value in query.items())
        ]
        return type("_Delete", (), {"deleted_count": 0})()

    def count_documents(self, query):
        return sum(
            1
            for doc in self.docs
            if all(doc.get(key) == value for key, value in query.items())
        )


class _Cursor:
    def __init__(self, docs: list[dict[str, Any]]):
        self.docs = docs

    def sort(self, key: str, direction: int):
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


def _build_service():
    db = _Db()
    catalog_repository = AlgorithmCatalogRepository(db)
    catalog_repository.upsert_entry(
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
            "source_path": "docs/file.md",
            "source_row_hash": "abc",
            "source_origin": "imported",
            "is_active": True,
            "implementation_id": "boundary_breakout",
            "implementation_catalog_ref": "algorithm:6",
            "implementation_source": "runtime_declared",
            "implementation_confidence": 1.0,
            "implementation_mapping_notes": "implementation declared",
            "implementation_mapping_reason": "implementation-declared catalog_ref",
            "review_state": "not_reviewed",
            "created_at": "now",
            "updated_at": "now",
        },
    )
    catalog_repository.upsert_entry(
        source_version="v2",
        catalog_type="algorithm",
        catalog_number=7,
        document={
            "id": "entry-2",
            "catalog_type": "algorithm",
            "catalog_number": 7,
            "name": "Channel Breakout with Confirmation",
            "slug": "channel-breakout-with-confirmation",
            "category": "Trend Following",
            "subcategory": "",
            "advanced_label": "No",
            "best_use_horizon": "Swing / position trading",
            "home_suitability_score": 1,
            "core_idea": "Breakout must persist for N bars or exceed threshold.",
            "typical_inputs": "OHLCV, lookback, confirmation bars/threshold",
            "signal_style": "Buy/sell with confirmation",
            "extended_implementation_details": "Detailed notes",
            "initial_reference": "INV-ALGO",
            "source_version": "v2",
            "source_path": "docs/file.md",
            "source_row_hash": "def",
            "source_origin": "imported",
            "is_active": True,
            "created_at": "now",
            "updated_at": "now",
        },
    )
    return AlgorithmCatalogService(
        catalog_repository=catalog_repository,
    )


def test_catalog_service_exposes_catalog_entries_with_status():
    service = _build_service()
    items = service.list_catalog_entries()
    assert items
    assert items[0]["implementation_status"] == "implementation_needs_review"
    assert items[0]["alg_impl_id"] == "boundary_breakout"


def test_catalog_service_returns_single_catalog_detail():
    service = _build_service()
    item = service.get_catalog_entry("breakout-donchian-channel")
    assert item["name"] == "Breakout (Donchian Channel)"
    assert item["alg_impl_spec"] is not None
    assert item["alg_impl_spec"]["key"] == "boundary_breakout"
    assert item["typical_inputs"] == "OHLCV high/low, lookback window"
    assert item["link_source_label"] == "Implementation declared"
    assert item["review_state_label"] == "Not reviewed"


def test_catalog_service_filters_entries_for_public_queries():
    service = _build_service()
    items = service.list_catalog_entries_filtered(
        implementation_status="implementation_needs_review",
        category="Trend Following",
        search_text="breakout",
    )
    assert len(items) == 1


def test_catalog_service_lists_only_runnable_algorithm_implementations():
    service = _build_service()

    items = service.list_runnable_algorithm_implementations()

    assert items
    assert all(item["status"] in {"stable", "runnable"} for item in items)


def test_catalog_service_rejects_non_runnable_algorithm_lookup():
    service = _build_service()

    try:
        service.get_runnable_algorithm_implementation("nonexistent_algorithm")
    except ValueError as exc:
        assert "unsupported" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown runnable algorithm")


def test_catalog_service_filters_entries_for_admin_queries():
    service = _build_service()
    payload = service.list_admin_catalog_entries(
        linked=True,
        advanced_label="No",
        page=1,
        page_size=10,
    )
    assert payload["total_count"] == 1


def test_catalog_service_admin_search_matches_extended_catalog_fields():
    service = _build_service()

    assert (
        service.list_admin_catalog_entries(
            search_text="INV-ALGO", page=1, page_size=10
        )["total_count"]
        == 2
    )
    assert (
        service.list_admin_catalog_entries(
            search_text="Swing / position", page=1, page_size=10
        )["total_count"]
        == 2
    )
    assert (
        service.list_admin_catalog_entries(
            search_text="implementation declared", page=1, page_size=10
        )["total_count"]
        == 1
    )
    assert (
        service.list_admin_catalog_entries(
            search_text="not reviewed", page=1, page_size=10
        )["total_count"]
        == 2
    )


def test_catalog_service_admin_search_matches_runtime_spec_metadata():
    service = _build_service()

    payload = service.list_admin_catalog_entries(
        search_text="boundary_breakout",
        page=1,
        page_size=10,
    )

    assert payload["total_count"] >= 1


def test_catalog_service_builds_catalog_workspace_payload():
    service = _build_service()

    payload = service.get_catalog_page_data(search_text="breakout")

    assert payload["summary"]["entry_count"] == 2
    assert payload["summary"]["implemented_count"] == 0
    assert payload["queue_payload"]["total_count"] == 2
    assert payload["review_payload"]["total_count"] == 1
    assert payload["filters"]["search_text"] == "breakout"


def test_catalog_service_marks_not_reviewed_links_as_needing_manual_review():
    service = _build_service()

    payload = service.list_admin_catalog_entries(
        review_state="not_reviewed",
        page=1,
        page_size=10,
    )

    assert payload["total_count"] == 1
    assert payload["items"][0]["review_state_label"] == "Not reviewed"


def test_catalog_service_updates_catalog_fields_and_review_state():
    service = _build_service()

    updated = service.update_catalog_entry(
        "breakout-donchian-channel",
        catalog_values={
            "name": "Updated Breakout",
            "category": "Trend",
            "subcategory": "Breakout",
            "advanced_label": "Yes",
            "best_use_horizon": "Position",
            "home_suitability_score": "4",
            "core_idea": "Updated idea",
            "typical_inputs": "Updated inputs",
            "signal_style": "Updated style",
            "extended_implementation_details": "Updated details",
            "initial_reference": "Updated ref",
            "implementation_decision": "Build",
            "implementation_notes": "Updated notes",
            "admin_annotations": "Updated annotations",
        },
        review_state="needs_review",
        link_notes=None,
    )

    assert updated["name"] == "Updated Breakout"
    assert updated["home_suitability_score"] == 4
    assert updated["review_state_label"] == "Needs review"
    assert updated["alg_impl_link"]["notes"] == "implementation declared"


def test_catalog_service_creates_manual_catalog_entry_without_implementation():
    service = _build_service()

    created = service.create_catalog_entry(
        catalog_values={
            "name": "Manual Algo",
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
        catalog_type="algorithm",
        alg_impl_id=None,
    )

    assert created["name"] == "Manual Algo"
    assert created["slug"] == "manual-algo"
    assert created["source_version"] == "manual"
    assert created["implementation_status"] == "not_implemented"
    assert created["review_state_label"] == "Not reviewed"
    assert created["alg_impl_link"] is None


def test_catalog_service_creates_manual_catalog_entry_with_implementation():
    service = _build_service()

    created = service.create_catalog_entry(
        catalog_values={
            "name": "Manual Boundary Breakout",
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
            "implementation_decision": "Use existing implementation",
            "implementation_notes": "",
            "admin_annotations": "",
        },
        catalog_type="algorithm",
        alg_impl_id="boundary_breakout",
    )

    assert created["source_version"] == "manual"
    assert created["alg_impl_id"] == "boundary_breakout"
    assert created["review_state_label"] == "Not reviewed"
    assert created["alg_impl_link"] is not None
    assert created["alg_impl_link"]["notes"] == (
        "algorithm_catalog: manually assigned implementation"
    )
