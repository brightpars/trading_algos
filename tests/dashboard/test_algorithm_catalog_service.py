from trading_algos_dashboard.services.algorithm_catalog_service import (
    get_algorithm_catalog_entry,
    list_algorithm_catalog,
)


def test_catalog_service_exposes_registered_algorithms():
    items = list_algorithm_catalog()
    assert items
    assert any(item["key"] == "boundary_breakout" for item in items)


def test_catalog_service_returns_single_entry():
    item = get_algorithm_catalog_entry("close_high_channel_breakout")
    assert item["name"] == "Close/High Channel Breakout"
    assert item["param_schema"]
    assert item["param_schema"][0]["key"] == "window"
