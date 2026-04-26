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


def test_composite_wave_5_registration_metadata_matches_manifest_contract() -> None:
    expected = {
        "rl_allocation_controller": (
            "combination:11",
            "reinforcement_learning",
            "rl",
            "portfolio",
            "rl_environment",
        ),
        "hierarchical_controller_meta_policy": (
            "combination:12",
            "reinforcement_learning",
            "hierarchical",
            "portfolio",
            "rl_environment",
        ),
    }

    for alg_key, (
        catalog_ref,
        family,
        subcategory,
        asset_scope,
        input_domain,
    ) in expected.items():
        spec = get_alert_algorithm_spec_by_key(alg_key)
        assert spec.catalog_ref == catalog_ref
        assert spec.family == family
        assert spec.subcategory == subcategory
        assert spec.asset_scope == asset_scope
        assert spec.input_domains == (input_domain,)


def test_rl_allocation_controller_fixture_behavior_and_contract(tmp_path: Path) -> None:
    rows = _load_composite_fixture_rows("rl_policy_stub.json")
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "PORTFOLIO",
            "alg_key": "rl_allocation_controller",
            "alg_param": {
                "rows": rows,
                "min_history": 1,
                "gross_exposure_limit": 1.0,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    portfolio = algorithm.portfolio_output()
    payload, payload_name = algorithm.interactive_report_payloads()[0]

    assert output.metadata["catalog_ref"] == "combination:11"
    assert output.metadata["family"] == "reinforcement_learning"
    assert output.metadata["reporting_mode"] == "allocation_trace"
    assert output.summary_metrics == {"rebalance_count": 2, "selection_count": 2}
    assert output.points[0].signal_label == "buy"
    assert output.points[1].signal_label == "buy"
    assert output.points[0].reason_codes == ("selection_ready",)
    assert output.points[0].diagnostics["selection_reason"] == "selection_ready"
    assert (
        output.points[0].diagnostics["aggregation_method"] == "rl_allocation_controller"
    )
    assert output.points[0].diagnostics["policy_confidence"] == pytest.approx(0.55)
    assert output.derived_series["selected_symbols"][0] == ["trend", "value", "carry"]
    assert output.derived_series["gross_exposure"] == [1.0, 1.0]
    assert output.derived_series["net_exposure"] == [1.0, 1.0]
    assert portfolio.rebalances[0].weights["trend"] == pytest.approx(0.7)
    assert portfolio.rebalances[1].weights["carry"] == pytest.approx(0.6)
    assert portfolio.rebalances[1].diagnostics["aggregation_method"] == (
        "rl_allocation_controller"
    )
    assert portfolio.rebalances[1].diagnostics["environment_contract"] == {
        "state_key_count": 3,
        "action_key_count": 5,
    }
    assert payload_name == "rl_report_rl_allocation_controller_PORTFOLIO"
    assert payload["portfolio"]["metadata"]["catalog_ref"] == "combination:11"
    assert payload["data"]["summary_metrics"]["rebalance_count"] == 2
    assert payload["data"]["derived_series"]["decision_reason"] == [
        "selection_ready",
        "selection_ready",
    ]
    assert payload["portfolio"]["rebalances"][0]["diagnostics"]["selected_count"] == 3


def test_hierarchical_controller_meta_policy_fixture_behavior_and_contract(
    tmp_path: Path,
) -> None:
    rows = _load_composite_fixture_rows("rl_policy_stub.json")
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "PORTFOLIO",
            "alg_key": "hierarchical_controller_meta_policy",
            "alg_param": {
                "rows": rows,
                "min_history": 1,
                "gross_exposure_limit": 1.0,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    output = algorithm.normalized_output()
    portfolio = algorithm.portfolio_output()
    payload, payload_name = algorithm.interactive_report_payloads()[0]

    assert output.metadata["catalog_ref"] == "combination:12"
    assert output.points[0].signal_label == "buy"
    assert output.points[1].signal_label == "buy"
    assert output.points[0].diagnostics["preferred_family"] == "trend_family"
    assert portfolio.rebalances[0].diagnostics["preferred_family"] == "trend_family"
    assert (
        portfolio.rebalances[0].diagnostics["raw_action_key"]
        == "trend_family_aggressive"
    )
    assert (
        portfolio.rebalances[1].diagnostics["raw_action_key"]
        == "trend_family_defensive"
    )
    assert portfolio.rebalances[1].weights["carry"] == pytest.approx(0.6)
    assert portfolio.rebalances[1].diagnostics["aggregation_method"] == (
        "hierarchical_controller_meta_policy"
    )
    assert payload_name == "rl_report_hierarchical_controller_meta_policy_PORTFOLIO"
    assert payload["data"]["metadata"]["catalog_ref"] == "combination:12"
    assert payload["portfolio"]["rebalances"][1]["diagnostics"]["preferred_family"] == (
        "trend_family"
    )


def test_composite_wave_5_alias_and_template_fallback_behavior(tmp_path: Path) -> None:
    rows = _load_composite_fixture_rows("rl_policy_stub.json")
    candidate_weights = rows[0]["candidate_weights"]
    assert isinstance(candidate_weights, dict)
    rows[0]["candidate_weights"] = {
        "balanced": candidate_weights["balanced"],
        "trend_family_aggressive": candidate_weights["trend_family_aggressive"],
        "trend_family_defensive": candidate_weights["trend_family_defensive"],
    }
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "PORTFOLIO",
            "alg_key": "rl_allocation_controller",
            "alg_param": {
                "rows": rows,
                "min_history": 1,
                "gross_exposure_limit": 0.6,
                "action_aliases": {"aggressive": "risk_on_template"},
                "action_overrides": {"aggressive": 0.95},
                "action_weight_templates": {
                    "risk_on_template": {
                        "trend": 0.8,
                        "value": 0.2,
                    }
                },
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )

    portfolio = algorithm.portfolio_output()
    output = algorithm.normalized_output()

    assert portfolio.rebalances[0].weights == {
        "trend": pytest.approx(0.48),
        "value": pytest.approx(0.12),
    }
    assert portfolio.rebalances[0].diagnostics["raw_action_key"] == "aggressive"
    assert portfolio.rebalances[0].diagnostics["resolved_action_key"] == (
        "risk_on_template"
    )
    assert portfolio.rebalances[0].diagnostics["selected_symbols"] == ["trend", "value"]
    assert portfolio.rebalances[0].diagnostics["gross_exposure"] == pytest.approx(0.6)
    assert output.points[0].diagnostics["action_score"] == pytest.approx(0.95)
    assert output.derived_series["selected_count"][0] == 2


def test_composite_wave_5_warmup_and_validation_behaviors(tmp_path: Path) -> None:
    rows = _load_composite_fixture_rows("rl_policy_stub.json")
    algorithm, _ = create_alertgen_algorithm(
        sensor_config={
            "symbol": "PORTFOLIO",
            "alg_key": "rl_allocation_controller",
            "alg_param": {
                "rows": rows,
                "min_history": 2,
                "gross_exposure_limit": 1.0,
            },
            "buy": True,
            "sell": False,
        },
        report_base_path=str(tmp_path),
    )
    output = algorithm.normalized_output()
    portfolio = algorithm.portfolio_output()
    assert output.points[0].signal_label == "neutral"
    assert output.points[0].reason_codes == ("warmup_pending",)
    assert output.points[0].diagnostics["warmup_ready"] is False
    assert output.summary_metrics == {"rebalance_count": 2, "selection_count": 1}
    assert portfolio.rebalances[0].weights == {}
    assert portfolio.rebalances[0].diagnostics["environment_contract"] == {
        "state_key_count": 3,
        "action_key_count": 5,
    }

    with pytest.raises(ValueError, match="gross_exposure_limit must be > 0"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "PORTFOLIO",
                "alg_key": "rl_allocation_controller",
                "alg_param": {
                    "rows": rows,
                    "min_history": 1,
                    "gross_exposure_limit": 0.0,
                },
                "buy": True,
                "sell": False,
            }
        )

    with pytest.raises(ValueError, match="action_aliases must be a dict"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "PORTFOLIO",
                "alg_key": "hierarchical_controller_meta_policy",
                "alg_param": {
                    "rows": rows,
                    "min_history": 1,
                    "gross_exposure_limit": 1.0,
                    "action_aliases": [],
                },
                "buy": True,
                "sell": False,
            }
        )

    with pytest.raises(ValueError, match="action_weight_templates must be a dict"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "PORTFOLIO",
                "alg_key": "rl_allocation_controller",
                "alg_param": {
                    "rows": rows,
                    "min_history": 1,
                    "gross_exposure_limit": 1.0,
                    "action_weight_templates": [],
                },
                "buy": True,
                "sell": False,
            }
        )

    with pytest.raises(ValueError, match="action_overrides must be a dict"):
        normalize_alertgen_sensor_config(
            {
                "symbol": "PORTFOLIO",
                "alg_key": "hierarchical_controller_meta_policy",
                "alg_param": {
                    "rows": rows,
                    "min_history": 1,
                    "gross_exposure_limit": 1.0,
                    "action_overrides": [],
                },
                "buy": True,
                "sell": False,
            }
        )


def test_composite_wave_5_performance_smoke_mapping() -> None:
    assert get_performance_smoke_case("combination:11").performance_budget_id == (
        "perf.composite_signal_v1"
    )
    assert get_performance_smoke_case("combination:11").fixture_ids == (
        "fixture.composite_rl_policy_stub_v1",
    )
    assert get_performance_smoke_case("combination:12").performance_budget_id == (
        "perf.composite_signal_v1"
    )
    assert get_performance_smoke_case("combination:12").fixture_ids == (
        "fixture.composite_rl_policy_stub_v1",
    )
