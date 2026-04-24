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


def test_composite_wave_3_registration_metadata_matches_manifest_contract() -> None:
    expected = {
        "constrained_multi_factor_optimization": (
            "combination:4",
            "optimization_based",
            "constrained",
            "portfolio",
        ),
        "regime_switching_hmm_gating": (
            "combination:7",
            "adaptive_state_based",
            "regime",
            "single_asset",
        ),
    }

    for alg_key, (catalog_ref, family, subcategory, asset_scope) in expected.items():
        spec = get_alert_algorithm_spec_by_key(alg_key)
        assert spec.catalog_ref == catalog_ref
        assert spec.family == family
        assert spec.subcategory == subcategory
        assert spec.asset_scope == asset_scope


def test_constrained_multi_factor_optimization_fixture_behavior_and_contract(
    tmp_path: Path,
) -> None:
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "PORTFOLIO",
            "alg_key": "constrained_multi_factor_optimization",
            "alg_param": {
                "rows": _load_composite_fixture_rows("risk_budget.json"),
                "rebalance_frequency": "monthly",
                "target_gross_exposure": 1.0,
                "min_history": 3,
                "max_weight": 0.55,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    portfolio = algorithm.portfolio_output()
    latest = portfolio.rebalances[-1]

    assert output.metadata["catalog_ref"] == "combination:4"
    assert output.metadata["family"] == "optimization_based"
    assert output.points[-1].signal_label == "buy"
    assert latest.selected_symbols == ("trend", "carry", "value")
    assert latest.weights["trend"] > 0.0
    assert latest.weights["carry"] > 0.0
    assert latest.weights["value"] > 0.0
    assert sum(abs(weight) for weight in latest.weights.values()) == pytest.approx(1.0)
    assert (
        latest.diagnostics["optimization_score_by_sleeve"]["trend"]
        > latest.diagnostics["optimization_score_by_sleeve"]["value"]
    )


def test_regime_switching_hmm_gating_fixture_behavior_and_contract(
    tmp_path: Path,
) -> None:
    rows = [
        {
            "timestamp": "2025-01-01",
            "regime_probabilities": {"risk_on": 0.8, "risk_off": 0.2},
            "child_outputs": [
                {
                    "child_key": "trend_child",
                    "signal_label": "buy",
                    "score": 0.8,
                    "confidence": 0.9,
                },
                {
                    "child_key": "defense_child",
                    "signal_label": "sell",
                    "score": -0.4,
                    "confidence": 0.6,
                },
            ],
        },
        {
            "timestamp": "2025-01-02",
            "regime_probabilities": {"risk_on": 0.2, "risk_off": 0.8},
            "child_outputs": [
                {
                    "child_key": "trend_child",
                    "signal_label": "buy",
                    "score": 0.7,
                    "confidence": 0.8,
                },
                {
                    "child_key": "defense_child",
                    "signal_label": "sell",
                    "score": -0.9,
                    "confidence": 0.9,
                },
            ],
        },
    ]
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "BTCUSD",
            "alg_key": "regime_switching_hmm_gating",
            "alg_param": {
                "rows": rows,
                "regime_field": "regime_probabilities",
                "regime_map": {
                    "risk_on": ["trend_child"],
                    "risk_off": ["defense_child"],
                },
                "default_signal": "neutral",
                "smoothing": 0.0,
                "switch_threshold": 0.55,
                "expected_child_count": 2,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    assert output.metadata["catalog_ref"] == "combination:7"
    assert output.derived_series["regime_label"] == ["risk_on", "risk_off"]
    assert output.points[0].signal_label == "buy"
    assert output.points[1].signal_label == "sell"
    assert output.derived_series["active_child_keys"][1] == ["defense_child"]
    assert output.child_outputs[0].diagnostics["active_regime"] == "risk_off"


def test_composite_wave_3_warmup_and_validation_behaviors(tmp_path: Path) -> None:
    optimization_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "PORTFOLIO",
            "alg_key": "constrained_multi_factor_optimization",
            "alg_param": {
                "rows": [
                    {
                        "timestamp": "2025-03-31",
                        "sleeve_returns": {"trend": [0.01], "carry": [0.02]},
                    }
                ],
                "rebalance_frequency": "monthly",
                "target_gross_exposure": 1.0,
                "min_history": 3,
                "max_weight": 0.5,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )
    optimization_output = optimization_algorithm.normalized_output()
    assert optimization_output.points[-1].signal_label == "neutral"
    assert optimization_output.points[-1].reason_codes == ("warmup_pending",)

    regime_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "BTCUSD",
            "alg_key": "regime_switching_hmm_gating",
            "alg_param": {
                "rows": [
                    {
                        "timestamp": "2025-03-31",
                        "regime_probabilities": {"risk_on": 0.7, "risk_off": 0.3},
                        "child_outputs": [],
                    }
                ],
                "regime_field": "regime_probabilities",
                "regime_map": {"risk_on": ["trend_child"]},
                "default_signal": "neutral",
                "smoothing": 0.1,
                "switch_threshold": 0.55,
                "expected_child_count": 1,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path),
    )
    regime_output = regime_algorithm.normalized_output()
    assert regime_output.points[-1].signal_label == "neutral"
    assert regime_output.points[-1].reason_codes[0] == "warmup_pending"

    with pytest.raises(ValueError, match="max_weight must be > 0"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "PORTFOLIO",
                "alg_key": "constrained_multi_factor_optimization",
                "alg_param": {
                    "rows": _load_composite_fixture_rows("risk_budget.json"),
                    "rebalance_frequency": "monthly",
                    "target_gross_exposure": 1.0,
                    "min_history": 3,
                    "max_weight": 0.0,
                },
                "buy": True,
                "sell": False,
            }
        )

    with pytest.raises(ValueError, match="regime_map must be a dict"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "BTCUSD",
                "alg_key": "regime_switching_hmm_gating",
                "alg_param": {
                    "rows": [],
                    "regime_field": "regime_probabilities",
                    "regime_map": [],
                    "smoothing": 0.1,
                    "switch_threshold": 0.55,
                },
                "buy": True,
                "sell": True,
            }
        )


def test_composite_wave_3_interactive_payloads_and_performance_smoke_mapping(
    tmp_path: Path,
) -> None:
    optimization_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "PORTFOLIO",
            "alg_key": "constrained_multi_factor_optimization",
            "alg_param": {
                "rows": _load_composite_fixture_rows("risk_budget.json"),
                "rebalance_frequency": "monthly",
                "target_gross_exposure": 1.0,
                "min_history": 3,
                "max_weight": 0.55,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )
    payload, payload_name = optimization_algorithm.interactive_report_payloads()[0]
    assert (
        payload_name
        == "rebalance_report_constrained_multi_factor_optimization_PORTFOLIO"
    )
    assert (
        payload["data"]["metadata"]["catalog_ref"]
        == payload["portfolio"]["metadata"]["catalog_ref"]
    )

    regime_algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "BTCUSD",
            "alg_key": "regime_switching_hmm_gating",
            "alg_param": {
                "rows": [
                    {
                        "timestamp": "2025-01-01",
                        "regime_probabilities": {"risk_on": 0.9, "risk_off": 0.1},
                        "child_outputs": [
                            {
                                "child_key": "trend_child",
                                "signal_label": "buy",
                                "score": 0.8,
                                "confidence": 0.9,
                            }
                        ],
                    }
                ],
                "regime_field": "regime_probabilities",
                "regime_map": {"risk_on": ["trend_child"]},
                "default_signal": "neutral",
                "smoothing": 0.0,
                "switch_threshold": 0.55,
                "expected_child_count": 1,
            },
            "buy": True,
            "sell": True,
        },
        report_base_path=str(tmp_path),
    )
    regime_payload, regime_payload_name = (
        regime_algorithm.interactive_report_payloads()[0]
    )
    assert regime_payload_name == "composite_report_regime_switching_hmm_gating_BTCUSD"
    assert regime_payload["data"]["metadata"]["catalog_ref"] == "combination:7"

    assert (
        get_performance_smoke_case("combination:4").performance_budget_id
        == "perf.cross_sectional_rebalance_v1"
    )
    assert (
        get_performance_smoke_case("combination:7").performance_budget_id
        == "perf.composite_signal_v1"
    )
