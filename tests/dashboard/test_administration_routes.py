e
def test_algorithm_catalog_admin_page_shows_queue_pagination_controls(monkeypatch):
    app = _build_app(monkeypatch)
    repository = app.extensions["algorithm_catalog_repository"]

    for index in range(1, 52):
        repository.upsert_entry(
            source_version="seed",
            catalog_type="algorithm",
            catalog_number=index,
            document={
                "id": f"entry-{index}",
                "catalog_type": "algorithm",
                "catalog_number": index,
                "name": f"Algorithm {index}",
                "slug": f"algorithm-{index}",
                "category": "Trend Following",
                "subcategory": "",
                "advanced_label": "No",
                "best_use_horizon": "Swing",
                "home_suitability_score": 3,
                "core_idea": f"Idea {index}",
                "typical_inputs": "Price",
                "signal_style": "Trend",
                "extended_implementation_details": "Details",
                "initial_reference": f"Ref-{index}",
                "source_version": "seed",
                "is_active": True,
                "created_at": "2026-04-21T10:00:00Z",
                "updated_at": "2026-04-21T10:00:00Z",
            },
        )

    response = app.test_client().get("/algorithms")

    assert response.status_code == 200
    assert b"All algorithms" in response.data
    assert b"51 items" in response.data
    assert b"Page 1 / 2" in response.data
    assert b"page=2" in response.data
    assert b"Algorithm 1" in response.data
    assert b"Algorithm 50" in response.data


def test_algorithm_catalog_admin_page_shows_paginated_unresolved_card(monkeypatch):
    app = _build_app(monkeypatch)
    repository = app.extensions["algorithm_catalog_repository"]

    for index in range(1, 28):
        repository.upsert_entry(
            source_version="seed",
            catalog_type="algorithm",
            catalog_number=index,
            document={
                "id": f"entry-{index}",
                "catalog_type": "algorithm",
                "catalog_number": index,
                "name": f"Unresolved Algorithm {index}",
                "slug": f"unresolved-algorithm-{index}",
                "category": "Trend Following",
                "subcategory": "",
                "advanced_label": "No",
                "best_use_horizon": "Swing",
                "home_suitability_score": 3,
                "core_idea": f"Idea {index}",
                "typical_inputs": "Price",
                "signal_style": "Trend",
                "extended_implementation_details": "Details",
                "initial_reference": f"Ref-{index}",
                "source_version": "seed",
                "is_active": True,
                "created_at": "2026-04-21T10:00:00Z",
                "updated_at": "2026-04-21T10:00:00Z",
            },
        )

    response = app.test_client().get("/algorithms")

    assert response.status_code == 200
    assert b"Unresolved entries" in response.data
    assert b"unresolved_page=2" in response.data
    assert b"Unresolved Algorithm 25" in response.data

    page_two_response = app.test_client().get("/algorithms?unresolved_page=2")

    assert page_two_response.status_code == 200
    assert b"Unresolved Algorithm 26" in page_two_response.data
    assert b"Unresolved Algorithm 27" in page_two_response.data


def test_algorithm_catalog_admin_page_preserves_other_page_state_in_card_links(
    monkeypatch,
):
    app = _build_app(monkeypatch)
    response = app.test_client().get(
        "/administration/algorithm-catalog?unresolved_page=2&page=2"
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/algorithms?unresolved_page=2&page=2")


def test_algorithm_catalog_admin_page_clamps_out_of_range_pages(monkeypatch):
    app = _build_app(monkeypatch)
    repository = app.extensions["algorithm_catalog_repository"]

    for index in range(1, 28):
        repository.upsert_entry(
            source_version="seed",
            catalog_type="algorithm",
            catalog_number=index,
            document={
                "id": f"entry-{index}",
                "catalog_type": "algorithm",
                "catalog_number": index,
                "name": f"Algorithm {index}",
                "slug": f"algorithm-{index}",
                "category": "Trend Following",
                "subcategory": "",
                "advanced_label": "No",
                "best_use_horizon": "Swing",
                "home_suitability_score": 3,
                "core_idea": f"Idea {index}",
                "typical_inputs": "Price",
                "signal_style": "Trend",
                "extended_implementation_details": "Details",
                "initial_reference": f"Ref-{index}",
                "source_version": "seed",
                "is_active": True,
                "created_at": "2026-04-21T10:00:00Z",
                "updated_at": "2026-04-21T10:00:00Z",
            },
        )

    response = app.test_client().get("/algorithms?unresolved_page=99&page=99")

    assert response.status_code == 200
    assert b"Unresolved entries" in response.data
    assert b"Page 2 / 2" in response.data
    assert b"Algorithm 26" in response.data


def test_algorithm_detail_page_updates_catalog_fields_and_review_state(monkeypatch):
    app = _build_app(monkeypatch)
    app.extensions["algorithm_catalog_repository"].upsert_entry(
        source_version="seed",
        catalog_type="algorithm",
        catalog_number=1,
        document={
            "id": "entry-1",
            "catalog_type": "algorithm",
            "catalog_number": 1,
            "name": "Seed Entry",
            "slug": "seed-entry",
            "category": "Trend Following",
            "subcategory": "",
            "advanced_label": "No",
            "best_use_horizon": "Swing",
            "home_suitability_score": 3,
            "core_idea": "Seed idea",
            "typical_inputs": "Price",
            "signal_style": "Trend",
            "extended_implementation_details": "Details",
            "initial_reference": "Ref",
            "implementation_decision": "",
            "implementation_notes": "",
            "admin_annotations": "",
            "source_version": "seed",
            "is_active": True,
            "created_at": "2026-04-21T10:00:00Z",
            "updated_at": "2026-04-21T10:00:00Z",
        },
    )
    _assign_implementation(
        app,
        entry_id="entry-1",
        implementation_id="OLD_boundary_breakout_NEW_breakout_donchian_channel",
        review_state="confirmed",
    )

    response = app.test_client().post(
        "/algorithms/seed-entry",
        data={
            "name": "Updated Seed Entry",
            "category": "Trend",
            "subcategory": "Momentum",
            "advanced_label": "Yes",
            "best_use_horizon": "Position",
            "home_suitability_score": "5",
            "core_idea": "Updated idea",
            "typical_inputs": "Updated inputs",
            "signal_style": "Updated style",
            "extended_implementation_details": "Updated details",
            "initial_reference": "Updated ref",
            "implementation_decision": "Build",
            "implementation_notes": "Updated notes",
            "admin_annotations": "Updated annotations",
            "review_state": "needs_review",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"algorithm_catalog: algorithm updated;" in response.data
    assert b"Updated Seed Entry" in response.data
    assert b">Runnable<" in response.data
    assert b">Needs review<" in response.data
    assert b"Linked implementation" in response.data
    assert b"_build_boundary_breakout" in response.data

    stored = app.extensions["algorithm_catalog_repository"].get_entry_by_id("entry-1")
    assert stored is not None
    assert stored["name"] == "Updated Seed Entry"
    assert stored["category"] == "Trend"
    assert stored["subcategory"] == "Momentum"
    assert stored["advanced_label"] == "Yes"
    assert stored["best_use_horizon"] == "Position"
    assert stored["home_suitability_score"] == 5
    assert stored["core_idea"] == "Updated idea"
    assert stored["typical_inputs"] == "Updated inputs"
    assert stored["signal_style"] == "Updated style"
    assert stored["extended_implementation_details"] == "Updated details"
    assert stored["initial_reference"] == "Updated ref"
    assert stored["implementation_decision"] == "Build"
    assert stored["implementation_notes"] == "Updated notes"
    assert stored["admin_annotations"] == "Updated annotations"
    assert stored["review_state"] == "needs_review"


def test_algorithm_detail_page_can_update_only_review_state(monkeypatch):
    app = _build_app(monkeypatch)
    app.extensions["algorithm_catalog_repository"].upsert_entry(
        source_version="seed",
        catalog_type="algorithm",
        catalog_number=1,
        document={
            "id": "entry-1",
            "catalog_type": "algorithm",
            "catalog_number": 1,
            "name": "Seed Entry",
            "slug": "seed-entry",
            "category": "Trend Following",
            "subcategory": "",
            "advanced_label": "No",
            "best_use_horizon": "Swing",
            "home_suitability_score": 3,
            "core_idea": "Seed idea",
            "typical_inputs": "Price",
            "signal_style": "Trend",
            "extended_implementation_details": "Details",
            "initial_reference": "Ref",
            "implementation_decision": "",
            "implementation_notes": "",
            "admin_annotations": "",
            "source_version": "seed",
            "is_active": True,
            "created_at": "2026-04-21T10:00:00Z",
            "updated_at": "2026-04-21T10:00:00Z",
        },
    )
    _assign_implementation(
        app,
        entry_id="entry-1",
        implementation_id="OLD_boundary_breakout_NEW_breakout_donchian_channel",
    )

    response = app.test_client().post(
        "/algorithms/seed-entry",
        data={
            "review_state": "confirmed",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b">Confirmed<" in response.data
    assert b"Linked implementation" in response.data
    assert b"_build_boundary_breakout" in response.data

    stored = app.extensions["algorithm_catalog_repository"].get_entry_by_id("entry-1")
    assert stored is not None
    assert stored["review_state"] == "confirmed"
    assert stored["name"] == "Seed Entry"
    assert stored["category"] == "Trend Following"
    assert (
        stored["implementation_id"]
        == "OLD_boundary_breakout_NEW_breakout_donchian_channel"
    )


def test_algorithm_detail_page_shows_linked_implementation_details(monkeypatch):
    app = _build_app(monkeypatch)
    app.extensions["algorithm_catalog_repository"].upsert_entry(
        source_version="seed",
        catalog_type="algorithm",
        catalog_number=1,
        document={
            "id": "entry-1",
            "catalog_type": "algorithm",
            "catalog_number": 1,
            "name": "Seed Entry",
            "slug": "seed-entry",
            "category": "Trend Following",
            "subcategory": "",
            "advanced_label": "No",
            "best_use_horizon": "Swing",
            "home_suitability_score": 3,
            "core_idea": "Seed idea",
            "typical_inputs": "Price",
            "signal_style": "Trend",
            "extended_implementation_details": "Details",
            "initial_reference": "Ref",
            "implementation_decision": "",
            "implementation_notes": "",
            "admin_annotations": "",
            "source_version": "seed",
            "is_active": True,
            "created_at": "2026-04-21T10:00:00Z",
            "updated_at": "2026-04-21T10:00:00Z",
        },
    )
    _assign_implementation(
        app,
        entry_id="entry-1",
        implementation_id="OLD_boundary_breakout_NEW_breakout_donchian_channel",
    )

    response = app.test_client().get("/algorithms/seed-entry")

    assert response.status_code == 200
    assert b"Linked implementation" in response.data
    assert b"_build_boundary_breakout" in response.data
    assert b"trading_algos.alertgen.algorithms.trend.catalog" in response.data
    assert (
        b"/experiments/new?alg_key=OLD_boundary_breakout_NEW_breakout_donchian_channel"
        in response.data
    )


def test_algorithm_detail_page_rejects_invalid_updates(monkeypatch):
    app = _build_app(monkeypatch)
    app.extensions["algorithm_catalog_repository"].upsert_entry(
        source_version="seed",
        catalog_type="algorithm",
        catalog_number=1,
        document={
            "id": "entry-1",
            "catalog_type": "algorithm",
            "catalog_number": 1,
            "name": "Seed Entry",
            "slug": "seed-entry",
            "category": "Trend Following",
            "subcategory": "",
            "advanced_label": "No",
            "best_use_horizon": "Swing",
            "home_suitability_score": 3,
            "core_idea": "Seed idea",
            "typical_inputs": "Price",
            "signal_style": "Trend",
            "extended_implementation_details": "Details",
            "initial_reference": "Ref",
            "source_version": "seed",
            "is_active": True,
            "created_at": "2026-04-21T10:00:00Z",
            "updated_at": "2026-04-21T10:00:00Z",
        },
    )

    response = app.test_client().post(
        "/algorithms/seed-entry",
        data={
            "name": "",
            "category": "Trend",
            "subcategory": "",
            "advanced_label": "No",
            "best_use_horizon": "Swing",
            "home_suitability_score": "3",
            "core_idea": "Idea",
            "typical_inputs": "Inputs",
            "signal_style": "Style",
            "extended_implementation_details": "Details",
            "initial_reference": "Ref",
            "implementation_decision": "",
            "implementation_notes": "",
            "admin_annotations": "",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Algorithm name cannot be empty." in response.data


def test_algorithm_catalog_admin_page_preserves_all_filter_options(monkeypatch):
    app = _build_app(monkeypatch)
    app.extensions["algorithm_catalog_repository"].upsert_entry(
        source_version="seed",
        catalog_type="algorithm",
        catalog_number=1,
        document={
            "id": "seed-entry",
            "catalog_type": "algorithm",
            "catalog_number": 1,
            "name": "Seed Entry",
            "slug": "seed-entry",
            "category": "Trend Following",
            "subcategory": "",
            "advanced_label": "No",
            "best_use_horizon": "Swing",
            "home_suitability_score": 3,
            "core_idea": "Seed idea",
            "typical_inputs": "Price",
            "signal_style": "Trend",
            "extended_implementation_details": "Details",
            "initial_reference": "Ref",
            "source_version": "seed",
            "is_active": True,
            "created_at": "2026-04-21T10:00:00Z",
            "updated_at": "2026-04-21T10:00:00Z",
        },
    )
    _assign_implementation(
        app,
        entry_id="seed-entry",
        implementation_id="OLD_boundary_breakout_NEW_breakout_donchian_channel",
    )

    response = app.test_client().get(
        "/algorithms"
        "?status=implemented"
        "&review_state=confirmed"
        "&catalog_type=algorithm"
        "&category=Trend%20Following"
        "&advanced_label=No"
        "&linked=true"
        "&only_broken=true"
        "&only_unresolved=true"
        "&q=breakout"
    )

    assert response.status_code == 200
    assert b'name="status"' in response.data
    assert b'value="implemented" selected' in response.data
    assert b'name="review_state"' in response.data
    assert b'value="confirmed" selected' in response.data
    assert b'name="catalog_type"' in response.data
    assert b'value="algorithm" selected' in response.data
    assert b'name="only_broken" value="true" checked' in response.data
    assert b'name="only_unresolved" value="true" checked' in response.data


def test_algorithm_catalog_admin_page_summary_matches_filtered_unresolved_rows(
    monkeypatch,
):
    app = _build_app(monkeypatch)
    repository = app.extensions["algorithm_catalog_repository"]

    for index in range(1, 18):
        repository.upsert_entry(
            source_version="seed",
            catalog_type="algorithm",
            catalog_number=index,
            document={
                "id": f"matching-entry-{index}",
                "catalog_type": "algorithm",
                "catalog_number": index,
                "name": f"Matching unresolved {index}",
                "slug": f"matching-unresolved-{index}",
                "category": "Trend Following",
                "subcategory": "",
                "advanced_label": "No",
                "best_use_horizon": "Swing",
                "home_suitability_score": 3,
                "core_idea": f"Idea {index}",
                "typical_inputs": "Price",
                "signal_style": "Trend",
                "extended_implementation_details": "Details",
                "initial_reference": f"Ref-{index}",
                "source_version": "seed",
                "is_active": True,
                "created_at": "2026-04-21T10:00:00Z",
                "updated_at": "2026-04-21T10:00:00Z",
            },
        )

    for index in range(18, 26):
        repository.upsert_entry(
            source_version="seed",
            catalog_type="algorithm",
            catalog_number=index,
            document={
                "id": f"other-entry-{index}",
                "catalog_type": "algorithm",
                "catalog_number": index,
                "name": f"Other unresolved {index}",
                "slug": f"other-unresolved-{index}",
                "category": "Mean Reversion",
                "subcategory": "",
                "advanced_label": "No",
                "best_use_horizon": "Swing",
                "home_suitability_score": 3,
                "core_idea": f"Idea {index}",
                "typical_inputs": "Price",
                "signal_style": "Trend",
                "extended_implementation_details": "Details",
                "initial_reference": f"Ref-{index}",
                "source_version": "seed",
                "is_active": True,
                "created_at": "2026-04-21T10:00:00Z",
                "updated_at": "2026-04-21T10:00:00Z",
            },
        )

    response = app.test_client().get("/algorithms?category=Trend%20Following")

    assert response.status_code == 200
    assert b">17</div>" in response.data
    assert b"17 items" in response.data
    assert b"Matching unresolved 17" in response.data
    assert b"Other unresolved 18" not in response.data


def test_algorithm_catalog_sync_route_rebuilds_links(monkeypatch):
    app = _build_app(monkeypatch)
    response = app.test_client().post(
        "/administration/algorithm-catalog/sync-links",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"administration: algorithm catalog links synced;" in response.data
    assert b"Algorithm Catalog" in response.data


def test_algorithm_catalog_sync_route_defaults_review_state_to_not_reviewed(
    monkeypatch,
):
    app = _build_app(monkeypatch)
    app.extensions["algorithm_catalog_repository"].upsert_entry(
        source_version="seed",
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
            "best_use_horizon": "Swing",
            "home_suitability_score": 3,
            "core_idea": "Idea",
            "typical_inputs": "Price",
            "signal_style": "Trend",
            "extended_implementation_details": "Details",
            "initial_reference": "Ref",
            "source_version": "seed",
            "is_active": True,
            "created_at": "2026-04-21T10:00:00Z",
            "updated_at": "2026-04-21T10:00:00Z",
        },
    )

    response = app.test_client().post(
        "/administration/algorithm-catalog/sync-links",
        follow_redirects=True,
    )

    assert response.status_code == 200
    detail_response = app.test_client().get("/algorithms/breakout-donchian-channel")
    assert detail_response.status_code == 200
    assert b">Runnable<" in detail_response.data
    assert b">Not reviewed<" in detail_response.data


def test_algorithm_catalog_sync_route_preserves_rejected_review_state(
    monkeypatch,
):
    app = _build_app(monkeypatch)
    app.extensions["algorithm_catalog_repository"].upsert_entry(
        source_version="seed",
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
            "best_use_horizon": "Swing",
            "home_suitability_score": 3,
            "core_idea": "Idea",
            "typical_inputs": "Price",
            "signal_style": "Trend",
            "extended_implementation_details": "Details",
            "initial_reference": "Ref",
            "source_version": "seed",
            "is_active": True,
            "implementation_id": "OLD_boundary_breakout_NEW_breakout_donchian_channel",
            "implementation_catalog_ref": "algorithm:6",
            "implementation_source": "runtime_declared",
            "implementation_confidence": 1.0,
            "implementation_mapping_notes": "implementation declared",
            "implementation_mapping_reason": "implementation-declared catalog_ref",
            "review_state": "rejected",
            "created_at": "2026-04-21T10:00:00Z",
            "updated_at": "2026-04-21T10:00:00Z",
        },
    )

    response = app.test_client().post(
        "/administration/algorithm-catalog/sync-links",
        follow_redirects=True,
    )

    assert response.status_code == 200
    detail_response = app.test_client().get("/algorithms/breakout-donchian-channel")
    assert detail_response.status_code == 200
    assert b">Not runnable<" in detail_response.data
    assert b">Rejected<" in detail_response.data


def test_app_startup_rebuild_preserves_existing_rejected_review_state(monkeypatch):
    client = _Client()
    client.db["algorithm_catalog_entries"].insert_one(
        {
            "id": "entry-1",
            "catalog_type": "algorithm",
            "catalog_number": 6,
            "name": "Breakout (Donchian Channel)",
            "slug": "breakout-donchian-channel",
            "category": "Trend Following",
            "subcategory": "",
            "advanced_label": "No",
            "best_use_horizon": "Swing",
            "home_suitability_score": 3,
            "core_idea": "Idea",
            "typical_inputs": "Price",
            "signal_style": "Trend",
            "extended_implementation_details": "Details",
            "initial_reference": "Ref",
            "source_version": "seed",
            "is_active": True,
            "implementation_id": "OLD_boundary_breakout_NEW_breakout_donchian_channel",
            "implementation_catalog_ref": "algorithm:6",
            "implementation_source": "runtime_declared",
            "implementation_confidence": 1.0,
            "implementation_mapping_notes": "implementation declared",
            "implementation_mapping_reason": "implementation-declared catalog_ref",
            "implementation_builder_name": "_build_boundary_breakout",
            "implementation_builder_module": "trading_algos.alertgen.algorithms.trend.catalog",
            "implementation_source_file": "src/trading_algos/alertgen/algorithms/trend/catalog.py",
            "review_state": "rejected",
            "created_at": "2026-04-21T10:00:00Z",
            "updated_at": "2026-04-21T10:00:00Z",
        }
    )
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: client
    )

    app = create_app(
        DashboardConfig(
            "x",
            "mongodb://example",
            "db",
            "reports",
            "/tmp/smarttrade",
            1,
        )
    )

    stored = app.extensions["algorithm_catalog_repository"].get_entry_by_id("entry-1")
    assert stored is not None
    assert stored["review_state"] == "rejected"


def test_app_startup_rebuild_preserves_regular_catalog_fields(monkeypatch):
    client = _Client()
    client.db["algorithm_catalog_entries"].insert_one(
        {
            "id": "entry-1",
            "catalog_type": "algorithm",
            "catalog_number": 6,
            "name": "Custom Breakout Name",
            "slug": "breakout-donchian-channel",
            "category": "Custom Trend",
            "subcategory": "Custom Subcategory",
            "advanced_label": "Yes",
            "best_use_horizon": "Position",
            "home_suitability_score": 7,
            "core_idea": "Custom idea",
            "typical_inputs": "Custom inputs",
            "signal_style": "Custom style",
            "extended_implementation_details": "Custom details",
            "initial_reference": "Custom ref",
            "implementation_decision": "Custom decision",
            "implementation_notes": "Custom notes",
            "admin_annotations": "Custom annotations",
            "source_version": "seed",
            "is_active": True,
            "implementation_id": "OLD_boundary_breakout_NEW_breakout_donchian_channel",
            "implementation_catalog_ref": "algorithm:6",
            "implementation_source": "runtime_declared",
            "implementation_confidence": 1.0,
            "implementation_mapping_notes": "implementation declared",
            "implementation_mapping_reason": "implementation-declared catalog_ref",
            "implementation_builder_name": "_build_boundary_breakout",
            "implementation_builder_module": "trading_algos.alertgen.algorithms.trend.catalog",
            "implementation_source_file": "src/trading_algos/alertgen/algorithms/trend/catalog.py",
            "review_state": "confirmed",
            "created_at": "2026-04-21T10:00:00Z",
            "updated_at": "2026-04-21T10:00:00Z",
        }
    )
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: client
    )

    app = create_app(
        DashboardConfig(
            "x",
            "mongodb://example",
            "db",
            "reports",
            "/tmp/smarttrade",
            1,
        )
    )

    stored = app.extensions["algorithm_catalog_repository"].get_entry_by_id("entry-1")
    assert stored is not None
    assert stored["name"] == "Custom Breakout Name"
    assert stored["category"] == "Custom Trend"
    assert stored["subcategory"] == "Custom Subcategory"
    assert stored["advanced_label"] == "Yes"
    assert stored["best_use_horizon"] == "Position"
    assert stored["home_suitability_score"] == 7
    assert stored["core_idea"] == "Custom idea"
    assert stored["typical_inputs"] == "Custom inputs"
    assert stored["signal_style"] == "Custom style"
    assert stored["extended_implementation_details"] == "Custom details"
    assert stored["initial_reference"] == "Custom ref"
    assert stored["implementation_decision"] == "Custom decision"
    assert stored["implementation_notes"] == "Custom notes"
    assert stored["admin_annotations"] == "Custom annotations"
    assert stored["review_state"] == "confirmed"


def test_algorithm_catalog_delete_requires_exact_confirmation(monkeypatch):
    app = _build_app(monkeypatch)
    app.extensions["algorithm_catalog_repository"].upsert_entry(
        source_version="seed",
        catalog_type="algorithm",
        catalog_number=1,
        document={
            "catalog_type": "algorithm",
            "catalog_number": 1,
            "name": "Seed Entry",
            "slug": "seed-entry",
            "category": "Trend",
            "subcategory": "",
            "advanced_label": "No",
            "best_use_horizon": "Swing",
            "home_suitability_score": 3,
            "core_idea": "Seed idea",
            "typical_inputs": "Price",
            "signal_style": "Trend",
            "extended_implementation_details": "Details",
            "initial_reference": "Ref",
            "source_version": "seed",
            "is_active": True,
            "created_at": "2026-04-21T10:00:00Z",
            "updated_at": "2026-04-21T10:00:00Z",
        },
    )
    response = app.test_client().post(
        "/administration/algorithm-catalog/delete-all",
        data={"confirmation_text": "delete all algorithm catalog entries"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert (
        b"administration: algorithm catalog deletion not executed; reason=invalid_confirmation_text"
        in response.data
    )
    assert app.extensions["algorithm_catalog_repository"].count_entries() > 0


def test_algorithm_catalog_delete_removes_entries_and_links(monkeypatch):
    app = _build_app(monkeypatch)
    response = app.test_client().post(
        "/administration/algorithm-catalog/delete-all",
        data={
            "confirmation_text": "DELETE ALL ALGORITHM CATALOG ENTRIES",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"administration: algorithm catalog deleted;" in response.data
    assert app.extensions["algorithm_catalog_repository"].count_entries() == 0
    assert (
        app.extensions[
            "algorithm_catalog_repository"
        ].count_entries_with_implementation()
        == 0
    )


def test_algorithm_catalog_import_detail_page_renders(monkeypatch):
    app = _build_app(monkeypatch)
    run = app.extensions["algorithm_catalog_import_run_repository"].create_run(
        {
            "source_version": "catalog-upload",
            "source_filename": "catalog-upload.md",
            "source_content_type": "text/markdown",
            "status": "completed",
            "started_at": "2026-04-21T10:00:00Z",
            "completed_at": "2026-04-21T10:00:10Z",
            "rows_seen": 1,
            "rows_created": 1,
            "rows_updated": 0,
            "rows_unchanged": 0,
            "rows_deactivated": 0,
            "warnings": [],
            "links_written": 0,
            "created_entry_ids": [],
            "updated_entry_ids": [],
            "unchanged_entry_ids": [],
            "deactivated_entry_ids": [],
            "unresolved_entry_ids": [],
            "preserved_manual_link_entry_ids": [],
            "changed_link_entry_ids": [],
        }
    )
    assert run is not None
    response = app.test_client().get(
        f"/administration/algorithm-catalog/imports/{run['id']}"
    )
    assert response.status_code == 200
    assert b"Algorithm catalog import detail" in response.data
    assert b"catalog-upload.md" in response.data


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
