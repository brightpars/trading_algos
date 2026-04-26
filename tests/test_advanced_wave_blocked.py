from __future__ import annotations

from typing import Any

import pytest

from trading_algos.algorithmspec import get_performance_smoke_case
from trading_algos.alertgen.core.algorithm_registry import (
    get_alert_algorithm_spec_by_key,
)
from trading_algos.alertgen.core.factory import create_alertgen_algorithm
from trading_algos.alertgen.core.validation import normalize_alertgen_sensor_config


def _microstructure_rows(*, phase: str = "continuous") -> list[dict[str, object]]:
    return [
        {
            "ts": "2025-01-02 09:30:00",
            "symbol": "AAA",
            "best_bid_price": 100.00,
            "best_ask_price": 100.03,
            "best_bid_size": 180.0,
            "best_ask_size": 90.0,
            "auction_imbalance": 75.0,
            "session_phase": phase,
        },
        {
            "ts": "2025-01-02 09:30:01",
            "symbol": "AAA",
            "best_bid_price": 100.01,
            "best_ask_price": 100.03,
            "best_bid_size": 90.0,
            "best_ask_size": 180.0,
            "auction_imbalance": -80.0,
            "session_phase": phase,
        },
    ]


def _own_order_rows() -> list[dict[str, object]]:
    return [
        {
            "ts": "2025-01-02 09:30:00",
            "symbol": "AAA",
            "side": "buy",
            "resting_quantity": 20.0,
            "queue_ahead": 100.0,
            "traded_volume_since_update": 70.0,
            "cancel_replace_count": 0,
        },
        {
            "ts": "2025-01-02 09:30:01",
            "symbol": "AAA",
            "side": "buy",
            "resting_quantity": 20.0,
            "queue_ahead": 200.0,
            "traded_volume_since_update": 10.0,
            "cancel_replace_count": 2,
        },
    ]


def _execution_rows() -> list[dict[str, object]]:
    return [
        {
            "ts": "2025-01-02 09:30:00",
            "symbol": "AAA",
            "available_volume": 100.0,
            "reference_price": 100.00,
            "spread": 0.03,
        },
        {
            "ts": "2025-01-02 09:35:00",
            "symbol": "AAA",
            "available_volume": 150.0,
            "reference_price": 100.04,
            "spread": 0.01,
        },
        {
            "ts": "2025-01-02 09:40:00",
            "symbol": "AAA",
            "available_volume": 250.0,
            "reference_price": 100.02,
            "spread": 0.01,
        },
    ]


def _parent_order(side: str = "buy", quantity: int = 300) -> dict[str, object]:
    return {
        "symbol": "AAA",
        "side": side,
        "quantity": quantity,
        "start_timestamp": "2025-01-02 09:30:00",
        "end_timestamp": "2025-01-02 09:40:00",
    }


def test_advanced_wave_blocked_registration_metadata_matches_manifest_contract() -> (
    None
):
    expected: dict[str, tuple[str, str, str]] = {
        "bid_ask_market_making": ("algorithm:62", "microstructure_hft", "bid"),
        "inventory_skewed_market_making": (
            "algorithm:63",
            "microstructure_hft",
            "inventory",
        ),
        "order_book_imbalance_strategy": (
            "algorithm:64",
            "microstructure_hft",
            "order",
        ),
        "microprice_strategy": ("algorithm:65", "microstructure_hft", "microprice"),
        "queue_position_strategy": ("algorithm:66", "microstructure_hft", "queue"),
        "liquidity_rebate_capture": ("algorithm:67", "microstructure_hft", "liquidity"),
        "opening_auction_strategy": ("algorithm:68", "microstructure_hft", "opening"),
        "closing_auction_strategy": ("algorithm:69", "microstructure_hft", "closing"),
        "twap": ("algorithm:94", "execution", "twap"),
        "vwap": ("algorithm:95", "execution", "vwap"),
        "pov_participation_rate": ("algorithm:96", "execution", "pov"),
        "implementation_shortfall_arrival_price": (
            "algorithm:97",
            "execution",
            "implementation",
        ),
        "iceberg_hidden_size": ("algorithm:98", "execution", "iceberg"),
        "sniper_opportunistic_execution": ("algorithm:99", "execution", "sniper"),
    }

    for alg_key, (catalog_ref, family, subcategory) in expected.items():
        spec = get_alert_algorithm_spec_by_key(alg_key)
        assert spec.catalog_ref == catalog_ref
        assert spec.family == family
        assert spec.subcategory == subcategory
        assert spec.warmup_period == 1


@pytest.mark.parametrize(
    ("alg_key", "alg_param", "match"),
    [
        (
            "bid_ask_market_making",
            {
                "rows": _microstructure_rows(),
                "own_order_rows": _own_order_rows(),
                "min_spread": 0.0,
                "inventory_limit": 10.0,
            },
            "min_spread",
        ),
        (
            "queue_position_strategy",
            {
                "rows": _microstructure_rows(),
                "own_order_rows": _own_order_rows(),
                "keep_threshold": 0.1,
                "cancel_threshold": 0.2,
            },
            "cancel_threshold <= keep_threshold",
        ),
        (
            "vwap",
            {
                "rows": _execution_rows(),
                "parent_order": _parent_order(),
                "volume_curve": [],
            },
            "volume_curve must be a non-empty list",
        ),
        (
            "iceberg_hidden_size",
            {
                "rows": _execution_rows(),
                "parent_order": _parent_order(quantity=10),
                "display_quantity": 20,
            },
            "display_quantity must be <= parent order quantity",
        ),
    ],
)
def test_advanced_wave_blocked_validation_rejects_invalid_parameter_shapes(
    alg_key: str,
    alg_param: dict[str, Any],
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAA",
                "alg_key": alg_key,
                "alg_param": alg_param,
                "buy": True,
                "sell": False,
            }
        )


def test_advanced_wave_blocked_microstructure_fixture_behavior(tmp_path) -> None:
    imbalance_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAA",
            "alg_key": "order_book_imbalance_strategy",
            "alg_param": {
                "rows": _microstructure_rows(),
                "own_order_rows": _own_order_rows(),
                "imbalance_threshold": 0.2,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path / "imbalance"),
    )
    queue_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAA",
            "alg_key": "queue_position_strategy",
            "alg_param": {
                "rows": _microstructure_rows(),
                "own_order_rows": _own_order_rows(),
                "keep_threshold": 0.4,
                "cancel_threshold": 0.2,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path / "queue"),
    )

    imbalance_output = imbalance_algorithm.normalized_output()
    queue_output = queue_algorithm.normalized_output()

    assert imbalance_output.points[0].signal_label == "buy"
    assert imbalance_output.points[1].signal_label == "sell"
    assert imbalance_output.derived_series["imbalance"][0] > 0.0
    assert imbalance_output.derived_series["imbalance"][1] < 0.0
    assert queue_output.points[0].signal_label == "buy"
    assert queue_output.points[1].signal_label == "sell"
    assert (
        queue_output.derived_series["queue_fill_probability"][0]
        > queue_output.derived_series["queue_fill_probability"][1]
    )
    assert imbalance_output.derived_series["warmup_ready"] == [True, True]
    assert (
        imbalance_output.summary_metrics["latest_decision_reason"]
        == "ask_depth_dominant"
    )
    assert queue_output.points[1].diagnostics["action"] == "cancel_or_amend"
    imbalance_payload, imbalance_payload_name = (
        imbalance_algorithm.interactive_report_payloads()[0]
    )
    assert imbalance_payload_name == "microstructure_order_book_imbalance_strategy_AAA"
    assert imbalance_payload["data"]["metadata"]["catalog_ref"] == "algorithm:64"
    assert imbalance_payload["data"]["summary_metrics"]["latest_signal"] == "sell"


def test_advanced_wave_blocked_microstructure_short_history_and_diagnostics(
    tmp_path,
) -> None:
    algorithms = {
        "bid_ask_market_making": {
            "rows": _microstructure_rows(),
            "own_order_rows": _own_order_rows(),
            "min_spread": 0.01,
            "inventory_limit": 10.0,
        },
        "inventory_skewed_market_making": {
            "rows": _microstructure_rows(),
            "own_order_rows": _own_order_rows(),
            "inventory_target": 5.0,
            "skew_sensitivity": 1.0,
        },
        "microprice_strategy": {
            "rows": _microstructure_rows(),
            "own_order_rows": _own_order_rows(),
            "edge_threshold": 0.002,
        },
        "liquidity_rebate_capture": {
            "rows": _microstructure_rows(),
            "own_order_rows": _own_order_rows(),
            "maker_rebate": 0.002,
            "adverse_selection_buffer": 0.001,
        },
    }

    for alg_key, alg_param in algorithms.items():
        algorithm, _ = create_alertgen_algorithm(
            sensor_config={
                "symbol": "AAA",
                "alg_key": alg_key,
                "alg_param": alg_param,
                "buy": True,
                "sell": True,
            },
            report_base_path=str(tmp_path / alg_key),
        )
        output = algorithm.normalized_output()
        assert output.metadata["warmup_period"] == 1
        assert output.derived_series["warmup_ready"] == [True, True]
        assert output.summary_metrics["point_count"] == 2
        assert (
            output.child_outputs[0].diagnostics["catalog_ref"]
            == output.metadata["catalog_ref"]
        )
        assert (
            output.child_outputs[0].diagnostics["reporting_mode"] == "order_book_trace"
        )


def test_advanced_wave_blocked_auction_phase_behavior(tmp_path) -> None:
    opening_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAA",
            "alg_key": "opening_auction_strategy",
            "alg_param": {
                "rows": _microstructure_rows(phase="opening"),
                "own_order_rows": _own_order_rows(),
                "auction_threshold": 50.0,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path / "opening"),
    )
    closing_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAA",
            "alg_key": "closing_auction_strategy",
            "alg_param": {
                "rows": _microstructure_rows(phase="closing"),
                "own_order_rows": _own_order_rows(),
                "auction_threshold": 50.0,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path / "closing"),
    )

    assert opening_algorithm.normalized_output().points[0].signal_label == "buy"
    assert closing_algorithm.normalized_output().points[1].signal_label == "sell"
    opening_output = opening_algorithm.normalized_output()
    closing_output = closing_algorithm.normalized_output()
    assert opening_output.derived_series["session_phase"] == ["opening", "opening"]
    assert closing_output.derived_series["session_phase"] == ["closing", "closing"]
    assert (
        opening_output.summary_metrics["latest_decision_reason"]
        == "opening_auction_sell_pressure"
    )
    assert (
        closing_output.summary_metrics["latest_decision_reason"]
        == "closing_auction_sell_pressure"
    )


def test_advanced_wave_blocked_execution_fixture_behavior(tmp_path) -> None:
    twap_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAA",
            "alg_key": "twap",
            "alg_param": {
                "rows": _execution_rows(),
                "parent_order": _parent_order(),
                "intervals": 3,
                "catch_up_factor": 1.2,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path / "twap"),
    )
    vwap_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAA",
            "alg_key": "vwap",
            "alg_param": {
                "rows": _execution_rows(),
                "parent_order": _parent_order(),
                "volume_curve": [1.0, 2.0, 3.0],
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path / "vwap"),
    )

    twap_output = twap_algorithm.normalized_output()
    twap_plan = twap_algorithm.execution_plan_output()
    vwap_output = vwap_algorithm.normalized_output()

    assert twap_output.derived_series["target_cumulative_quantity"] == [
        100.0,
        200.0,
        300.0,
    ]
    assert twap_output.derived_series["decision_reason"][0] in {
        "catch_up_active",
        "twap_on_schedule",
    }
    assert len(twap_plan.child_orders) == 3
    assert vwap_output.derived_series["target_cumulative_quantity"][
        -1
    ] == pytest.approx(300.0)
    assert (
        vwap_output.derived_series["target_cumulative_quantity"][1]
        > vwap_output.derived_series["target_cumulative_quantity"][0]
    )
    assert twap_output.derived_series["child_order_action"] == [
        "submit_child",
        "submit_child",
        "submit_child",
    ]
    assert twap_output.summary_metrics["child_order_count"] == 3
    assert twap_output.metadata["warmup_period"] == 1
    twap_payload, twap_payload_name = twap_algorithm.interactive_report_payloads()[0]
    assert twap_payload_name == "execution_twap_AAA"
    assert twap_payload["data"]["summary_metrics"]["final_target_quantity"] == 300.0
    assert twap_payload["execution_plan"]["metadata"]["catalog_ref"] == "algorithm:94"
    assert vwap_output.derived_series["realized_volume_share"] == pytest.approx(
        [0.2, 0.3, 0.5]
    )


def test_advanced_wave_blocked_execution_variants_behavior(tmp_path) -> None:
    pov_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAA",
            "alg_key": "pov_participation_rate",
            "alg_param": {
                "rows": _execution_rows(),
                "parent_order": _parent_order(),
                "participation_rate": 0.5,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path / "pov"),
    )
    iceberg_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAA",
            "alg_key": "iceberg_hidden_size",
            "alg_param": {
                "rows": _execution_rows(),
                "parent_order": _parent_order(),
                "display_quantity": 100,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path / "iceberg"),
    )
    sniper_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAA",
            "alg_key": "sniper_opportunistic_execution",
            "alg_param": {
                "rows": _execution_rows(),
                "parent_order": _parent_order(),
                "spread_threshold": 0.015,
                "volume_threshold": 140.0,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path / "sniper"),
    )

    assert pov_algorithm.normalized_output().derived_series[
        "target_cumulative_quantity"
    ] == [50.0, 125.0, 250.0]
    assert iceberg_algorithm.normalized_output().derived_series[
        "target_cumulative_quantity"
    ] == [100.0, 200.0, 300.0]
    assert sniper_algorithm.normalized_output().derived_series["decision_reason"] == [
        "waiting_for_liquidity",
        "sniper_triggered",
        "sniper_triggered",
    ]
    implementation_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAA",
            "alg_key": "implementation_shortfall_arrival_price",
            "alg_param": {
                "rows": _execution_rows(),
                "parent_order": _parent_order(),
                "urgency": 0.8,
                "arrival_price": 100.01,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path / "implementation"),
    )
    implementation_output = implementation_algorithm.normalized_output()
    assert implementation_output.derived_series["decision_reason"] == [
        "implementation_shortfall_active",
        "arrival_price_slippage_risk",
        "arrival_price_slippage_risk",
    ]
    assert implementation_output.summary_metrics[
        "final_target_quantity"
    ] == pytest.approx(300.0)
    assert (
        implementation_output.child_outputs[0].diagnostics["catalog_ref"]
        == "algorithm:97"
    )


def test_advanced_wave_blocked_execution_report_payload_fields(tmp_path) -> None:
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAA",
            "alg_key": "pov_participation_rate",
            "alg_param": {
                "rows": _execution_rows(),
                "parent_order": _parent_order(),
                "participation_rate": 0.5,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path / "payloads"),
    )

    payload, payload_name = algorithm.interactive_report_payloads()[0]
    assert payload_name == "execution_pov_participation_rate_AAA"
    assert payload["data"]["metadata"]["catalog_ref"] == "algorithm:96"
    assert payload["data"]["summary_metrics"]["latest_signal"] == "buy"
    assert payload["data"]["derived_series"]["requested_child_quantity"] == [
        50.0,
        75.0,
        125.0,
    ]
    assert payload["execution_plan"]["child_orders"][0]["action"] == "submit_child"
    assert (
        payload["execution_plan"]["plan_points"][-1]["diagnostics"]["decision_reason"]
        == "schedule_active"
    )


def test_advanced_wave_blocked_performance_smoke_mappings() -> None:
    assert (
        get_performance_smoke_case("algorithm:62").performance_budget_id
        == "perf.microstructure_v1"
    )
    assert get_performance_smoke_case("algorithm:66").fixture_ids == (
        "fixture.microstructure_queue_state_v1",
    )
    assert (
        get_performance_smoke_case("algorithm:94").performance_budget_id
        == "perf.execution_engine_v1"
    )
    assert get_performance_smoke_case("algorithm:95").fixture_ids == (
        "fixture.execution_vwap_curve_drift_v1",
    )


def test_advanced_wave_blocked_performance_smoke_on_fixture_repetition(
    tmp_path,
) -> None:
    rows = _execution_rows() * 60
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAA",
            "alg_key": "twap",
            "alg_param": {
                "rows": rows,
                "parent_order": _parent_order(quantity=6000),
                "intervals": len(rows),
                "catch_up_factor": 1.0,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path / "perf"),
    )

    output = algorithm.normalized_output()
    assert len(output.points) == len(rows)
    assert output.derived_series["target_cumulative_quantity"][-1] == pytest.approx(
        6000.0
    )
