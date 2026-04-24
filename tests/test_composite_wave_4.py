from __future__ import annotations

import json
from pathlib import Path

import pytest

from trading_algos.alertgen import create_alertgen_algorithm
from trading_algos.alertgen.core.algorithm_registry import (
    get_alert_algorithm_spec_by_key,
)
from trading_algos.alertgen.core.validation import normalize_alertgen_sensor_config
from trading_algos.algorithmspec import get_performance_smoke_case


COMPOSITE_FIXTURES_ROOT = Path(__file__).resolve().parent / "fixtures" / "composite"


def _load_composite_fixture_rows(name: str) -> list[dict[str, object]]:
    return json.loads((COMPOSITE_FIXTURES_ROOT / name).read_text(encoding="utf-8"))


def test_composite_wave_4_registration_metadata_matches_manifest_contract() -> None:
    expected = {
        "bagging_ensemble": (
            "combination:8",
            "machine_learning_ensemble",
            "bagging",
            "single_asset",
        ),
        "boosting_ensemble": (
            "combination:9",
            "machine_learning_ensemble",
            "boosting",
            "single_asset",
        ),
        "stacking_meta_learning": (
            "combination:10",
            "machine_learning_ensemble",
            "stacking",
            "single_asset",
        ),
    }

    for alg_key, (catalog_ref, family, subcategory, asset_scope) in expected.items():
        spec = get_alert_algorithm_spec_by_key(alg_key)
        assert spec.catalog_ref == catalog_ref
        assert spec.family == family
        assert spec.subcategory == subcategory
        assert spec.asset_scope == asset_scope


def test_bagging_ensemble_fixture_behavior_and_contract(tmp_path: Path) -> None:
    rows = _load_composite_fixture_rows("ml_ensemble.json")
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "bagging_ensemble",
            "alg_param": {
                "rows": rows,
                "buy_threshold": 0.2,
                "sell_threshold": -0.2,
                "min_history": 2,
                "expected_child_count": 3,
                "confidence_power": 1.0,
                "bootstrap_diversity_multiplier": 1.0,
                "child_weights": {"model_a": 1.0, "model_b": 1.0, "model_c": 0.5},
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    assert output.metadata["catalog_ref"] == "combination:8"
    assert output.metadata["family"] == "machine_learning_ensemble"
    assert output.points[0].signal_label == "neutral"
    assert output.points[0].reason_codes == ("warmup_pending",)
    assert output.points[1].signal_label == "sell"
    assert output.points[1].diagnostics["aggregation_method"] == "bagging_average"
    assert output.points[1].diagnostics["warmup_ready"] is True
    assert output.points[1].diagnostics["history_ready"] is True
    assert output.points[1].diagnostics["buy_threshold"] == pytest.approx(0.2)
    assert output.points[1].diagnostics["sell_threshold"] == pytest.approx(-0.2)
    assert (
        output.points[1].diagnostics["child_contributions"][0]["child_key"] == "model_a"
    )
    assert output.derived_series["child_count"] == [3, 3]
    assert output.derived_series["warmup_diagnostics"][0] == {
        "expected_child_count": 3,
        "actual_child_count": 3,
        "missing_child_count": 0,
    }
    assert output.derived_series["buy_threshold"] == [0.2, 0.2]
    assert output.derived_series["sell_threshold"] == [-0.2, -0.2]
    assert output.summary_metrics["decision_reason_counts"]["threshold_sell"] == 1
    assert output.summary_metrics["latest_signal"] == "sell"
    assert output.summary_metrics["latest_decision_reason"] == "threshold_sell"


def test_boosting_ensemble_fixture_behavior_and_contract(tmp_path: Path) -> None:
    rows = _load_composite_fixture_rows("ml_ensemble.json")
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "boosting_ensemble",
            "alg_param": {
                "rows": rows,
                "buy_threshold": 0.2,
                "sell_threshold": -0.2,
                "min_history": 1,
                "expected_child_count": 3,
                "confidence_power": 1.5,
                "learning_rate": 1.2,
                "stage_weights": {"model_a": 1.4, "model_b": 1.0, "model_c": 0.6},
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    assert output.metadata["catalog_ref"] == "combination:9"
    assert output.points[0].signal_label == "buy"
    assert output.points[1].signal_label == "sell"
    assert output.points[0].diagnostics["learning_rate"] == pytest.approx(1.2)
    assert output.points[0].diagnostics["aggregation_method"] == (
        "boosting_weighted_stage_average"
    )
    assert len(output.points[0].diagnostics["weighted_children"]) == 3
    assert (
        output.points[0].diagnostics["weighted_children"][0]["effective_weight"] > 0.0
    )
    assert output.summary_metrics["latest_signal"] == "sell"


def test_stacking_meta_learning_fixture_behavior_and_contract(tmp_path: Path) -> None:
    rows = _load_composite_fixture_rows("ml_ensemble.json")
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "stacking_meta_learning",
            "alg_param": {
                "rows": rows,
                "buy_threshold": 0.1,
                "sell_threshold": -0.1,
                "min_history": 1,
                "expected_child_count": 3,
                "confidence_power": 1.0,
                "meta_bias": 0.05,
                "meta_feature_scale": 0.1,
                "meta_model_weights": {"model_a": 1.1, "model_b": 0.9, "model_c": 0.4},
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    payload, payload_name = algorithm.interactive_report_payloads()[0]
    assert output.metadata["catalog_ref"] == "combination:10"
    assert output.points[0].signal_label == "buy"
    assert output.points[1].signal_label == "sell"
    assert output.points[0].diagnostics["aggregation_method"] == "stacking_meta_model"
    assert output.points[0].diagnostics["meta_feature_values"] == {
        "breadth": pytest.approx(0.1),
        "regime_confidence": pytest.approx(0.2),
    }
    assert payload_name == "composite_report_stacking_meta_learning_AAPL"
    assert payload["data"]["metadata"]["catalog_ref"] == "combination:10"
    assert payload["latest_point"]["signal_label"] == "sell"
    assert payload["latest_diagnostics"]["aggregation_method"] == "stacking_meta_model"
    assert payload["summary"]["latest_decision_reason"] == "threshold_sell"


def test_composite_wave_4_validation_and_warmup_behaviors(tmp_path: Path) -> None:
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "bagging_ensemble",
            "alg_param": {
                "rows": [
                    {
                        "timestamp": "2025-01-01",
                        "child_outputs": [
                            {
                                "child_key": "model_a",
                                "signal_label": "buy",
                                "score": 0.6,
                                "confidence": 0.7,
                            }
                        ],
                    }
                ],
                "buy_threshold": 0.2,
                "sell_threshold": -0.2,
                "min_history": 2,
                "expected_child_count": 2,
                "child_weights": {"model_a": 1.0},
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path),
    )
    output = algorithm.normalized_output()
    assert output.points[-1].signal_label == "neutral"
    assert output.points[-1].reason_codes == ("warmup_pending_incomplete_child_set",)

    with pytest.raises(ValueError, match="learning_rate must be > 0"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "boosting_ensemble",
                "alg_param": {
                    "rows": _load_composite_fixture_rows("ml_ensemble.json"),
                    "buy_threshold": 0.2,
                    "sell_threshold": -0.2,
                    "min_history": 1,
                    "expected_child_count": 3,
                    "learning_rate": 0.0,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="sell_threshold <= buy_threshold"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "bagging_ensemble",
                "alg_param": {
                    "rows": _load_composite_fixture_rows("ml_ensemble.json"),
                    "buy_threshold": -0.1,
                    "sell_threshold": 0.2,
                    "min_history": 1,
                    "expected_child_count": 3,
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="meta_model_weights must be a dict"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "stacking_meta_learning",
                "alg_param": {
                    "rows": _load_composite_fixture_rows("ml_ensemble.json"),
                    "buy_threshold": 0.1,
                    "sell_threshold": -0.1,
                    "min_history": 1,
                    "expected_child_count": 3,
                    "meta_model_weights": [],
                },
                "buy": True,
                "sell": True,
            }
        )

    with pytest.raises(ValueError, match="confidence_power must be >= 0"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "AAPL",
                "alg_key": "bagging_ensemble",
                "alg_param": {
                    "rows": _load_composite_fixture_rows("ml_ensemble.json"),
                    "buy_threshold": 0.2,
                    "sell_threshold": -0.2,
                    "min_history": 1,
                    "expected_child_count": 3,
                    "confidence_power": -0.1,
                },
                "buy": True,
                "sell": True,
            }
        )


def test_composite_wave_4_short_history_and_clamped_score_behaviors(
    tmp_path: Path,
) -> None:
    rows = _load_composite_fixture_rows("ml_ensemble.json")
    boosting_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "boosting_ensemble",
            "alg_param": {
                "rows": rows,
                "buy_threshold": 0.6,
                "sell_threshold": -0.6,
                "min_history": 3,
                "expected_child_count": 3,
                "learning_rate": 5.0,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path),
    )
    boosting_output = boosting_algorithm.normalized_output()
    assert [point.signal_label for point in boosting_output.points] == [
        "neutral",
        "neutral",
    ]
    assert [point.reason_codes for point in boosting_output.points] == [
        ("warmup_pending",),
        ("warmup_pending",),
    ]

    stacking_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "AAPL",
            "alg_key": "stacking_meta_learning",
            "alg_param": {
                "rows": rows,
                "buy_threshold": 0.9,
                "sell_threshold": -0.9,
                "min_history": 1,
                "expected_child_count": 3,
                "meta_bias": 0.7,
                "meta_feature_scale": 1.0,
                "meta_model_weights": {
                    "model_a": 3.0,
                    "model_b": 3.0,
                    "model_c": 1.0,
                },
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path),
    )
    stacking_output = stacking_algorithm.normalized_output()
    assert stacking_output.points[0].score == pytest.approx(1.0)
    assert stacking_output.points[0].signal_label == "buy"
    assert stacking_output.points[0].diagnostics["raw_ensemble_score"] == pytest.approx(
        1.0
    )


def test_composite_wave_4_performance_smoke_mapping() -> None:
    assert get_performance_smoke_case("combination:8").performance_budget_id == (
        "perf.composite_signal_v1"
    )
    assert get_performance_smoke_case("combination:9").fixture_ids == (
        "fixture.composite_ml_ensemble_v1",
    )
    assert get_performance_smoke_case("combination:10").name == (
        "Stacking / Meta-Learning"
    )
